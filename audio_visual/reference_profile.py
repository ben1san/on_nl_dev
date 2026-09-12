#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "soundfile"]
# ///
"""参照録音を「自分の音と比べる」のではなく「そのものを記述する」ために測る。

    uv run audio_visual/reference_profile.py ref.mp3
    uv run audio_visual/reference_profile.py ref.mp3 --segments 12
    uv run audio_visual/reference_profile.py ref.mp3 --json out.json

dimtakt_compare.py との役割の違い:
  compare  = 手で決めた区間から引いた目標帯に、自分の音が入っているかを判定する
  profile  = 録音を自動で区分し、各区間が何であるかを数値で書き出す(判定しない)

区間の切り方は人が決めない。自己相似行列にチェッカーボード核を当てて
新規性のピークを境界に採る(Foote 2000)。「参照は複合的で区間により
30倍違う」という既知の事実に対し、その区間自体を録音から出させるため。

回転の位相順序(rotation ordering)は、既存ノートが未解決として残していた
「回転とうねりを数値で区別する手段がない」への実装。帯域ごとの包絡線を
支配的な巡回周波数で複素フーリエ係数に落とし、その位相が帯域の順に
単調に進むかを測る。順序があれば回転、無ければうねり。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rotation_index as ri  # noqa: E402

SR = 44100
NFFT = 4096
HOP = 1024
FRAME_RATE = SR / HOP  # 43.07 Hz
ENV_SR = 200.0  # 包絡線の解析レート(粗さ帯域まで見るため高め)


# ---------------------------------------------------------------------------
# 読み込み
# ---------------------------------------------------------------------------
def load(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """(stereo[n,2], mono[n]) を SR で返す。mp3/webm/wav すべて ffmpeg 経由。"""
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "d.wav"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(path),
             "-ac", "2", "-ar", str(SR), "-f", "wav", str(wav)],
            check=True,
        )
        x, sr = sf.read(str(wav), always_2d=True, dtype="float64")
    assert sr == SR
    return x, x.mean(axis=1)


def stft_mag(mono: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(freqs, mag[n_freq, n_frame])。"""
    f, _, Z = signal.stft(
        mono, fs=SR, window="hann", nperseg=NFFT, noverlap=NFFT - HOP,
        boundary=None, padded=False,
    )
    return f, np.abs(Z)


# ---------------------------------------------------------------------------
# 自動区分
# ---------------------------------------------------------------------------
def log_bands(freqs: np.ndarray, mag: np.ndarray, n: int = 48,
              lo: float = 60.0, hi: float = 12000.0) -> np.ndarray:
    """対数間隔の帯域へ畳んだパワー[n, n_frame]。"""
    edges = np.geomspace(lo, hi, n + 1)
    power = mag ** 2
    out = np.empty((n, power.shape[1]))
    for i in range(n):
        sel = (freqs >= edges[i]) & (freqs < edges[i + 1])
        out[i] = power[sel].sum(axis=0) if sel.any() else 0.0
    return out


def novelty_boundaries(bands: np.ndarray, n_seg: int,
                       kernel_sec: float = 6.0,
                       min_sec: float = 8.0) -> np.ndarray:
    """チェッカーボード核による新規性から境界フレームを返す。"""
    feat = np.log10(bands + 1e-12)
    # 4フレーム(≈93ms)へ間引いてから正規化
    step = 4
    feat = feat[:, ::step]
    feat -= feat.mean(axis=1, keepdims=True)
    norm = np.linalg.norm(feat, axis=0) + 1e-12
    feat /= norm
    sim = feat.T @ feat  # コサイン自己相似行列

    m = int(kernel_sec * FRAME_RATE / step) // 2 * 2  # 偶数
    half = m // 2
    g = np.outer(*[signal.windows.gaussian(m, half / 2.0)] * 2)
    ker = np.ones((m, m))
    ker[:half, half:] = -1.0
    ker[half:, :half] = -1.0
    ker *= g
    ker /= np.abs(ker).sum()

    n = sim.shape[0]
    nov = np.zeros(n)
    for i in range(half, n - half):
        nov[i] = (sim[i - half:i + half, i - half:i + half] * ker).sum()
    nov = np.clip(nov, 0, None)
    if nov.max() > 0:
        nov /= nov.max()

    dist = int(min_sec * FRAME_RATE / step)
    peaks, props = signal.find_peaks(nov, distance=dist)
    order = np.argsort(props["peak_heights"] if "peak_heights" in props
                       else nov[peaks])[::-1]
    keep = np.sort(peaks[order[:max(n_seg - 1, 0)]])
    return keep * step


# ---------------------------------------------------------------------------
# 区間ごとの記述
# ---------------------------------------------------------------------------
@dataclass
class Partial:
    freq: float
    level_db: float


@dataclass
class SegmentProfile:
    t0: float
    t1: float
    rms_db: float
    centroid_hz: float
    centroid_sd_oct: float
    centroid_autocorr_1s: float
    flux_sd: float
    ratio_2k_8k: float
    ratio_below_200: float
    ltas_flatness: float
    partials: list[Partial] = field(default_factory=list)
    f0_hz: float | None = None
    inharm_alpha: float | None = None
    inharm_resid_cent: float | None = None
    sweep_hz: float | None = None
    sweep_period_s: float | None = None
    sweep_prominence_db: float | None = None
    rot_f0: float | None = None
    rot_prog: float | None = None
    rot_null: float | None = None
    rot_turns: float | None = None
    rot_lin_oct: float | None = None
    rot_pan_offset: float | None = None
    rot_verdict: str = ""
    event_rate_hz: float = 0.0
    decay_t60_s: float | None = None
    rough_3_40_pct: float = 0.0
    lr_corr: float = 0.0
    side_pct: float = 0.0


def spectral_centroid(freqs: np.ndarray, mag: np.ndarray) -> np.ndarray:
    p = mag ** 2
    tot = p.sum(axis=0) + 1e-20
    return (freqs[:, None] * p).sum(axis=0) / tot


def spectral_flux(mag: np.ndarray) -> np.ndarray:
    """フレーム間の正規化スペクトル差。無音でも暴れないよう L1 正規化する。"""
    p = mag / (mag.sum(axis=0, keepdims=True) + 1e-20)
    return np.abs(np.diff(p, axis=1)).sum(axis=0)


def find_partials(freqs: np.ndarray, ltas_db: np.ndarray,
                  n_max: int = 14) -> list[Partial]:
    """LTASの山を部分音として採る。60Hz-8kHzに限る。"""
    band = (freqs >= 60) & (freqs <= 8000)
    f = freqs[band]
    y = ltas_db[band]
    y = signal.savgol_filter(y, 9, 3)
    peaks, props = signal.find_peaks(y, prominence=3.0, distance=3)
    if len(peaks) == 0:
        return []
    order = np.argsort(props["prominences"])[::-1][:n_max]
    idx = np.sort(peaks[order])
    return [Partial(float(f[i]), float(y[i] - y.max())) for i in idx]


def fit_inharmonicity(partials: list[Partial]) -> tuple[float | None, float | None, float | None]:
    """f_k = f0 * k^alpha を最小二乗で当てる。

    alpha=1 なら調和、>1 なら上へ開く非調和(打楽器・金属質)。
    残差(セント)が大きいなら「そもそも整数列で説明できない」ことの検出。
    """
    if len(partials) < 4:
        return None, None, None
    fs = np.array([p.freq for p in partials])
    fs.sort()
    best = None
    # 最低部分音が第k次である可能性を総当たりし、整数列との残差が最小のものを採る
    for k0 in range(1, 4):
        f0_guess = fs[0] / k0
        ks = np.rint(fs / f0_guess)
        if np.any(ks < 1) or len(np.unique(ks)) != len(ks):
            continue
        A = np.column_stack([np.ones(len(fs)), np.log(ks)])
        b = np.log(fs)
        coef, *_ = np.linalg.lstsq(A, b, rcond=None)
        pred = A @ coef
        resid_cent = float(np.sqrt(np.mean((b - pred) ** 2)) * 1200 / np.log(2))
        if best is None or resid_cent < best[2]:
            best = (float(np.exp(coef[0])), float(coef[1]), resid_cent)
    return best if best else (None, None, None)


def envelope(x: np.ndarray, sr_in: float = FRAME_RATE) -> np.ndarray:
    return x


def sweep_candidates(centroid: np.ndarray, n: int = 3,
                     lo: float = 0.05, hi: float = 2.0
                     ) -> list[tuple[float, float]]:
    """重心時系列の変調スペクトルから巡回周波数の候補を上位n個返す。

    [(周波数Hz, 中央値からの突出dB), ...] を突出の大きい順で返す。

    最大ピーク1つに絞ってはいけない。対数重心の変調スペクトルは1/f的に
    低域が重いため、必ず区間規模のゆっくりしたドリフト(0.04〜0.09Hz)が
    勝ち、実際に回転として知覚される速さが埋もれる。どれが回転かは
    突出量では決まらず、位相順序が立つかどうかで決める。
    """
    c = np.log2(np.clip(centroid, 20, None))
    if len(c) < int(6 * FRAME_RATE):
        return []
    c = signal.detrend(c)
    spec = np.abs(np.fft.rfft(c * np.hanning(len(c)))) ** 2
    fr = np.fft.rfftfreq(len(c), d=1.0 / FRAME_RATE)
    band = (fr >= lo) & (fr <= hi)
    if not band.any():
        return []
    fb, sb = fr[band], spec[band]
    med = np.median(sb) + 1e-20
    peaks, _ = signal.find_peaks(sb)
    if len(peaks) == 0:
        peaks = np.array([int(np.argmax(sb))])
    order = np.argsort(sb[peaks])[::-1][:n]
    return [(float(fb[p]), float(10 * np.log10(sb[p] / med)))
            for p in peaks[order]]


def rotation(stereo: np.ndarray) -> dict:
    """区間が回転しているかを rotation_index.py に測らせる。

    位相順序の推定はここに実装しない。`rotation_index.py` が偶然の水準
    (無作為な位相での95%点)・重みの偏りによる測定不能判定・合成音での
    自己検証まで持っており、二重に実装すると劣った方が使われる。

    変調周波数は掃引して最も順行する速さを採る。**掃引した中の最良を採る
    以上これは検定ではない**(rotation_index.scan のdocstringの警告どおり)。
    区間の記述としては使えるが、有意性を主張したいなら見つけた速さで
    `rotation_index.py --f0` を別途1回だけ回すこと。
    """
    out: dict = dict(f0=None, prog=None, null=None, turns=None,
                     lin_oct=None, pan_offset=None, verdict="測定不能")
    if len(stereo) < int(8 * SR):
        return out
    try:
        s = ri.scan(stereo)
        # **変調の深さに下限を課さないと向きが逆に出る。** 順行性から偶然の水準を
        # 引いた値だけで選ぶと、深さ0.02(ほぼ雑音)の高い成分が勝つことがあり、
        # 実測で系統A(0-22s)の巡回の向きが低→高から高→低へ反転した。
        floor = 0.2 * s["mag"].max()
        cand = [i for i in s["order"] if s["prog"][i] > s["null"][i]
                and abs(s["turns"][i]) >= 0.25 and s["mag"][i] >= floor]
        f0 = float(s["freqs"][cand[0]]) if cand else None
        r = ri.measure(stereo, f0_fixed=f0)
    except Exception as e:  # 区間が短い等で測れないことがある
        out["verdict"] = f"測定不能({type(e).__name__})"
        return out
    return dict(f0=r["f0"], prog=r["prog"], null=r["null"],
                turns=r["wavenumber"], lin_oct=r["lin_oct"],
                pan_offset=r["pan_offset"], verdict=ri.verdict(r))


def event_analysis(mono: np.ndarray, mag: np.ndarray) -> tuple[float, float | None]:
    """立ち上がりの密度と、立ち上がり後の減衰時間(T60換算)。"""
    flux = spectral_flux(mag)
    if len(flux) < 10:
        return 0.0, None
    f = flux - signal.medfilt(flux, kernel_size=21)
    thr = f.mean() + 2.0 * f.std()
    peaks, _ = signal.find_peaks(f, height=thr, distance=int(0.15 * FRAME_RATE))
    dur = len(flux) / FRAME_RATE
    rate = len(peaks) / dur

    # 各立ち上がりの後 1.5 秒の対数包絡線の傾きから T60 を推定
    env = np.sqrt((mag ** 2).sum(axis=0))
    env_db = 20 * np.log10(env + 1e-12)
    slopes = []
    win = int(1.5 * FRAME_RATE)
    for p in peaks:
        seg = env_db[p:p + win]
        if len(seg) < win // 2:
            continue
        seg = seg - seg[0]
        # 単調に落ちている区間だけを使う(次の発音が来たら打ち切る)
        stop = np.argmax(seg > 1.0) if (seg > 1.0).any() else len(seg)
        if stop < int(0.3 * FRAME_RATE):
            continue
        s = seg[:stop]
        tt = np.arange(len(s)) / FRAME_RATE
        a = np.polyfit(tt, s, 1)[0]
        if a < -1.0:
            slopes.append(a)
    t60 = float(-60.0 / np.median(slopes)) if slopes else None
    return float(rate), t60


def roughness(mono: np.ndarray) -> float:
    """包絡線変調のうち 3-40Hz が占める割合[%]。粗さ・脈動の量。"""
    # ヒルベルト変換は長尺で重いので、整流+ローパスで包絡線を作る
    x = np.abs(mono)
    q = int(SR / ENV_SR)
    b, a = signal.butter(4, (ENV_SR / 2) / (SR / 2), "low")
    e = signal.filtfilt(b, a, x)[::q]
    e = e - e.mean()
    if len(e) < 64:
        return 0.0
    w = np.hanning(len(e))
    spec = np.abs(np.fft.rfft(e * w)) ** 2
    fr = np.fft.rfftfreq(len(e), d=1.0 / ENV_SR)
    tot = spec[(fr > 0.2) & (fr < 80)].sum() + 1e-20
    rough = spec[(fr >= 3) & (fr <= 40)].sum()
    return float(100 * rough / tot)


def profile_segment(stereo: np.ndarray, mono: np.ndarray, freqs: np.ndarray,
                    mag: np.ndarray, t0: float, t1: float) -> SegmentProfile:
    ltas = (mag ** 2).mean(axis=1)
    ltas_db = 10 * np.log10(ltas + 1e-20)
    p = mag ** 2
    tot = p.sum() + 1e-20
    b28 = ((freqs >= 2000) & (freqs <= 8000))
    blo = freqs < 200

    centroid = spectral_centroid(freqs, mag)
    c_oct = np.log2(np.clip(centroid, 20, None))
    lag = int(FRAME_RATE)
    if len(c_oct) > lag + 10:
        a = c_oct[:-lag] - c_oct.mean()
        b = c_oct[lag:] - c_oct.mean()
        ac = float((a * b).mean() / (c_oct.var() + 1e-20))
    else:
        ac = float("nan")

    flux = spectral_flux(mag)
    partials = find_partials(freqs, ltas_db)
    f0, alpha, resid = fit_inharmonicity(partials)
    # 重心変調の最強成分。これは「回転の速さ」ではない(区間規模の抑揚が勝つ)。
    cands = sweep_candidates(centroid, n=1)
    f_sw, prom = cands[0] if cands else (None, None)
    per = 1.0 / f_sw if f_sw else None
    rot = rotation(stereo)
    rate, t60 = event_analysis(mono, mag)

    # LTAS平坦度(幾何平均/算術平均)。1に近いほど平坦
    band = (freqs >= 100) & (freqs <= 8000)
    lt = ltas[band] + 1e-20
    flat = float(np.exp(np.mean(np.log(lt))) / np.mean(lt))

    L, R = stereo[:, 0], stereo[:, 1]
    denom = (np.std(L) * np.std(R) + 1e-20)
    lr = float(np.mean((L - L.mean()) * (R - R.mean())) / denom)
    mid = (L + R) / 2
    side = (L - R) / 2
    side_pct = float(100 * np.mean(side ** 2) / (np.mean(mid ** 2) + np.mean(side ** 2) + 1e-20))

    return SegmentProfile(
        t0=round(t0, 1), t1=round(t1, 1),
        rms_db=float(20 * np.log10(np.sqrt(np.mean(mono ** 2)) + 1e-12)),
        centroid_hz=float(centroid.mean()),
        centroid_sd_oct=float(c_oct.std()),
        centroid_autocorr_1s=ac,
        flux_sd=float(flux.std()),
        ratio_2k_8k=float(100 * p[b28].sum() / tot),
        ratio_below_200=float(100 * p[blo].sum() / tot),
        ltas_flatness=flat,
        partials=partials,
        f0_hz=f0, inharm_alpha=alpha, inharm_resid_cent=resid,
        sweep_hz=f_sw, sweep_period_s=per, sweep_prominence_db=prom,
        rot_f0=rot["f0"], rot_prog=rot["prog"], rot_null=rot["null"],
        rot_turns=rot["turns"], rot_lin_oct=rot["lin_oct"],
        rot_pan_offset=rot["pan_offset"], rot_verdict=rot["verdict"],
        event_rate_hz=rate, decay_t60_s=t60,
        rough_3_40_pct=roughness(mono),
        lr_corr=lr, side_pct=side_pct,
    )


# ---------------------------------------------------------------------------
def fmt(v, spec="6.2f", none="   -- "):
    return none if v is None or (isinstance(v, float) and np.isnan(v)) else format(v, spec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--segments", type=int, default=10,
                    help="採る区間数の目安(新規性ピークの上位から)")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    stereo, mono = load(args.path)
    dur = len(mono) / SR
    freqs, mag = stft_mag(mono)
    bands = log_bands(freqs, mag)
    bnd = novelty_boundaries(bands, args.segments)
    edges = [0] + [int(b) for b in bnd] + [mag.shape[1]]

    print(f"\n参照: {args.path.name}  {dur:.1f}s  自動区分 {len(edges)-1} 区間\n")

    profs: list[SegmentProfile] = []
    for i in range(len(edges) - 1):
        f0, f1 = edges[i], edges[i + 1]
        if f1 - f0 < int(4 * FRAME_RATE):
            continue
        s0, s1 = int(f0 * HOP), min(int(f1 * HOP + NFFT), len(mono))
        profs.append(profile_segment(
            stereo[s0:s1], mono[s0:s1], freqs, mag[:, f0:f1],
            f0 / FRAME_RATE, f1 / FRAME_RATE))

    print("区間        RMS  重心Hz 重心SD  自相関  変化率  2-8k%  <200%  平坦度")
    for p in profs:
        print(f"{p.t0:5.1f}-{p.t1:5.1f} {p.rms_db:5.1f} {p.centroid_hz:7.0f} "
              f"{p.centroid_sd_oct:6.3f} {fmt(p.centroid_autocorr_1s,'7.3f')} "
              f"{p.flux_sd:7.4f} {p.ratio_2k_8k:6.2f} {p.ratio_below_200:6.2f} "
              f"{p.ltas_flatness:7.4f}")

    print("\n重心変調の最強成分(回転の速さではない)と、位相順序による回転の判定")
    print("区間        変調Hz  周期s  突出dB | 回転f0  順行性  偶然   波数  直線性 定位差  判定")
    for p in profs:
        print(f"{p.t0:5.1f}-{p.t1:5.1f} {fmt(p.sweep_hz,'7.3f')} "
              f"{fmt(p.sweep_period_s,'6.2f')} {fmt(p.sweep_prominence_db,'7.2f')} | "
              f"{fmt(p.rot_f0,'6.3f')} {fmt(p.rot_prog,'7.3f')} {fmt(p.rot_null,'6.3f')} "
              f"{fmt(p.rot_turns,'6.2f')} {fmt(p.rot_lin_oct,'6.3f')} "
              f"{fmt(p.rot_pan_offset,'6.0f')}  {p.rot_verdict}")

    print("\n区間        f0Hz  α非調和 残差cent 発音/s   T60s  粗さ3-40%  LR相関  Side%")
    for p in profs:
        print(f"{p.t0:5.1f}-{p.t1:5.1f} {fmt(p.f0_hz,'7.1f')} "
              f"{fmt(p.inharm_alpha,'7.3f')} {fmt(p.inharm_resid_cent,'8.1f')} "
              f"{p.event_rate_hz:6.2f} {fmt(p.decay_t60_s,'6.2f')} "
              f"{p.rough_3_40_pct:9.1f} {p.lr_corr:7.3f} {p.side_pct:6.2f}")

    print("\n部分音(上位、最強を0dBとした相対レベル)")
    for p in profs:
        s = "  ".join(f"{q.freq:.0f}({q.level_db:+.0f})" for q in p.partials[:9])
        print(f"{p.t0:5.1f}-{p.t1:5.1f}  {s}")

    if args.json:
        args.json.write_text(json.dumps(
            [asdict(p) for p in profs], ensure_ascii=False, indent=2))
        print(f"\n→ {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
