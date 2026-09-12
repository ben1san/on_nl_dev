#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "soundfile", "matplotlib"]
# ///
"""
聴覚演出の音を dimtakt の参照録音と同じ物差しで測る。

    uv run audio_visual/dimtakt_compare.py mysound.wav
    uv run audio_visual/dimtakt_compare.py mysound.wav --plot out.png
    uv run audio_visual/dimtakt_compare.py a.wav b.wav c.wav      # 並べて比較
    uv run audio_visual/dimtakt_compare.py mysound.wav --seg 3 33 # 区間を指定

SuperColliderから測定用の30秒を録るには、音を鳴らした状態で:

    s.record(duration: 30);          // ~/Music/SuperCollider Recordings/ に出る
    // 録り終わったら
    s.stopRecording;

目標帯は dimtakt 録音の3区間(5-35s / 100-130s / 140-170s)の実測から引いた。
参照録音を差し替えたときは --calibrate で目標帯を引き直せる。

    uv run audio_visual/dimtakt_compare.py --calibrate ref.mp3 5 35 100 130 140 170

各指標が何を捉えているかは、対応する関数のdocstringに書いてある。
指標の選定理由と、耳による自己診断のうち何が誤診だったかは未ノート化。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

SR = 44100
ENV_SR = 100  # 包絡線の解析レート

# ---------------------------------------------------------------------------
# 目標帯: dimtakt録音(172秒)の7区間 5-35 / 40-70 / 60-90 / 75-105 / 100-130 /
# 115-145 / 140-170 秒の実測レンジ。lo/hiどちらかがNoneなら片側だけ見る。
# 上限を切っていない指標は「参照より多い分には困らない」もの。
# under/over は目標帯を外れたときの言い方。指標によって「小さい=悪い」とは限らない
# ので(LR相関は小さいほどステレオが広い)、方向ごとに言葉を持たせている。
# TOL は境界での測定ゆらぎを飲むための相対余裕。
# ---------------------------------------------------------------------------
TOL = 0.02

TARGETS = {
    # 参考値。合格判定には使わない(gate=False)。理由は3点:
    #  1. 試聴評価と逆相関した。この帯域を目標帯へ戻そうと発音を明るくしたところ
    #     「聴きごこちが悪くなった」と評された。良いとされた音はこの指標を落ちていた
    #  2. 再現性がない。同一設定の60秒レンダリングで 0.58 と 7.32 が出る。少数の
    #     高い発音がこの帯域を支配する裾の重い分布のため
    #  3. 残る指標だけで矛盾なく評価を説明できる
    "hf_2_8k":      dict(label="2-8kHz エネルギー [%]",   lo=0.9,   hi=5.6,  fmt="8.2f",
                         under="不足",       over="過多", gate=False),
    "ltas_flat":    dict(label="LTAS平坦度 100-2000Hz",   lo=0.024, hi=None, fmt="8.4f",
                         under="線が細い",   over=""),
    # 参考値。持続する層を足すと必ず下がるが、試聴では持続層のある方が好まれた。
    # 音色の動きは変化率のSDが捉えており、この指標は重複している。
    "centroid_p1090": dict(label="重心 p10-p90幅 [Hz]",   lo=1000,  hi=None, fmt="8.0f",
                         under="音色が動かない", over="", gate=False),
    "flux_sd":      dict(label="スペクトル変化率のSD",      lo=0.027, hi=None, fmt="8.4f",
                         under="変化が一様",  over=""),
    "decay_per30":  dict(label="減衰イベント数 /30秒",      lo=7,     hi=None, fmt="8.1f",
                         under="出来事が少ない", over=""),
    "rt60":         dict(label="RT60推定 [s]",           lo=1.5,   hi=2.6,  fmt="8.2f",
                         under="残響が短い",  over="残響が長い"),
    "lr_corr":      dict(label="LR相関 (1=モノ)",         lo=0.78,  hi=0.94, fmt="8.3f",
                         under="広がりすぎ",  over="狭すぎ"),
    "bass_cents":   dict(label="低音ピーク幅 [cent]",      lo=11,    hi=33,   fmt="8.0f",
                         under="低音が固定的", over="低音が不安定"),
    # 撤回した指標: 脈動 3-40Hz比率。「ヘリコプターみたい」という評を捉えるつもりで
    # 追加したが、好評だったdimtaktのアルスエレクトロニカ区間が86.3%、光と光の区間が
    # 73.9%を示した。参照自身が満ちている量を欠陥として測ることはできない。参考値
    # としても誤解を招くので外した。同じ理由で 2-8kHz を下げる方向も誤りだった
    # (参照は24〜40%ある)。
    #
    # 軌跡の連続性。**必ず「ばらつき」と対で見ること。** 動かない音は自動的に
    # 滑らかになるので、自己相関だけを見ると連続体層(ばらつき0.204)が満点を取る。
    "gesture_ac":   dict(label="軌跡の自己相関",           lo=0.2,   hi=None, fmt="8.3f",
                         under="飛び跳ねている", over=""),
    "gesture_sd":   dict(label="重心軌跡のばらつき",        lo=0.6,   hi=None, fmt="8.3f",
                         under="動いていない",   over=""),
}
ORDER = list(TARGETS)


# ---------------------------------------------------------------------------
# 読み込み
# ---------------------------------------------------------------------------
def load(path: str, seg: tuple[float, float] | None = None) -> np.ndarray:
    """任意の音声ファイルを 44.1kHz ステレオの float 配列で返す。
    soundfileが開けない形式(mp3/webm等)はffmpegで一旦wavへ落とす。"""
    p = Path(path)
    if not p.exists():
        sys.exit(f"ファイルがありません: {path}")
    try:
        x, sr = sf.read(str(p), always_2d=True)
    except Exception:
        if not _has_ffmpeg():
            sys.exit(f"{p.suffix} を読むには ffmpeg が要ります (brew install ffmpeg)")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(p), "-ar", str(SR), tmp.name],
                check=True,
            )
            x, sr = sf.read(tmp.name, always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    if sr != SR:
        x = signal.resample_poly(x, SR, sr, axis=0)
    if seg is not None:
        x = x[int(seg[0] * SR): int(seg[1] * SR)]
    if len(x) < SR * 5:
        sys.exit(f"{path}: 5秒未満は測れません (長さ {len(x)/SR:.1f}s)")
    return x


def _has_ffmpeg() -> bool:
    return subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0


def _bandpass(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    ny = SR / 2
    if lo <= 0:
        sos = signal.butter(4, hi / ny, btype="low", output="sos")
    elif hi >= ny * 0.99:
        sos = signal.butter(4, lo / ny, btype="high", output="sos")
    else:
        sos = signal.butter(4, [lo / ny, hi / ny], btype="band", output="sos")
    return signal.sosfilt(sos, x)


def _envelope(x: np.ndarray) -> np.ndarray:
    e = np.abs(signal.hilbert(x))
    e = signal.sosfilt(signal.butter(4, 20 / (SR / 2), btype="low", output="sos"), e)
    # ダウンサンプルのリンギングで包絡線がわずかに負へ振れることがあり、
    # そのままdB化するとNaNになるので0で切る
    return np.maximum(signal.resample_poly(e, ENV_SR, SR), 0.0)


# ---------------------------------------------------------------------------
# 8指標
# ---------------------------------------------------------------------------
def hf_energy_and_flatness(mono: np.ndarray) -> tuple[float, float]:
    """2-8kHzのエネルギー比 [%] と、100-2000HzのLTAS平坦度。

    平坦度は倍音の線と線の間がどれだけ埋まっているかを表す。1に近いほど
    連続的な音の層があり、0に近いほど細い線だけで隙間が空いている。"""
    f, P = signal.welch(mono, SR, nperseg=16384, noverlap=12288)
    hf = 100 * P[(f >= 2000) & (f <= 8000)].sum() / P.sum()
    band = P[(f >= 100) & (f <= 2000)]
    flat = float(np.exp(np.mean(np.log(band))) / np.mean(band))
    return float(hf), flat


def centroid_spread(mono: np.ndarray) -> float:
    """スペクトル重心のp10-p90幅 [Hz]。音色が時間の中でどれだけ振れるか。"""
    f, _, S = signal.spectrogram(mono, SR, nperseg=4096, noverlap=2048, mode="magnitude")
    c = (f[:, None] * S).sum(axis=0) / (S.sum(axis=0) + 1e-12)
    p10, p90 = np.percentile(c, [10, 90])
    return float(p90 - p10)


def flux_sd(mono: np.ndarray) -> float:
    """スペクトル変化率の標準偏差。

    平均ではなくSDを見るのが要点。平均が同じでも、SDが小さい音は「常に一定の
    速さで変わり続ける」= 無機的に聞こえ、SDが大きい音は「動かない時間と激変
    する瞬間が交互に来る」= 有機的に聞こえる。フレームごとに正規化して音量変化
    を落とし、音色の変化だけを見ている。"""
    _, _, S = signal.spectrogram(mono, SR, nperseg=4096, noverlap=2048, mode="magnitude")
    S = S / (S.sum(axis=0, keepdims=True) + 1e-12)
    d = np.sqrt((np.diff(S, axis=1) ** 2).sum(axis=0))
    return float(d.std())


def decay_stats(mono: np.ndarray) -> tuple[float | None, float]:
    """RT60推定 [s] と、30秒あたりの減衰イベント数。

    突出10dB以上のピークの直後 50-350ms を直線当てはめし、単調に落ちている
    ものだけを残す。持続音一色だと1つも取れず None を返す ―― それ自体が
    「出来事がない」ことの検出になっている。"""
    e = _envelope(mono)
    edb = 20 * np.log10(e + 1e-10)
    peaks, _ = signal.find_peaks(edb, prominence=10, distance=int(0.5 * ENV_SR))
    slopes = []
    for i in peaks:
        a, b = i + int(0.05 * ENV_SR), i + int(0.35 * ENV_SR)
        if b >= len(edb):
            continue
        seg = edb[a:b]
        t = np.arange(len(seg)) / ENV_SR
        slope = np.polyfit(t, seg, 1)[0]
        r = np.corrcoef(t, seg)[0, 1]
        if slope < -3 and r < -0.8:          # 単調でしっかり落ちるものだけ
            slopes.append(slope)
    per30 = len(slopes) * 30.0 / (len(mono) / SR)
    if len(slopes) < 4:
        return None, per30
    return float(-60 / np.median(slopes)), per30


def gesture(mono: np.ndarray) -> tuple[float, float]:
    """スペクトル重心の軌跡が「滑らかに移動する」か「飛び跳ねる」か、
    および軌跡がどれだけ動くか。

    参照(dimtakt)は4区間すべてで自己相関 +0.22〜+0.39、ばらつき 0.36〜1.57。
    つまり「大きく動き、かつ滑らかに動く」。独立な乱数で発音を撃つ設計だと、
    動く量は同等でも自己相関が0付近になる(実測 -0.008)。持続音は逆に滑らか
    だが動かない(ばらつき0.204)。

    同じ明るさでも、グライドして到達した高域と、いきなり出現する高域は
    別物に聞こえる。エネルギー量の指標では捉えられなかった差がここに出る。"""
    f, _, S = signal.spectrogram(mono, SR, nperseg=2048, noverlap=1536, mode="magnitude")
    c = (f[:, None] * S).sum(axis=0) / (S.sum(axis=0) + 1e-12)
    lc = np.log2(c + 1e-9)
    d = np.diff(lc)
    if len(d) < 3:
        return 0.0, 0.0
    ac = float(np.corrcoef(d[:-1], d[1:])[0, 1])
    return ac, float(np.std(lc))


def lr_correlation(x: np.ndarray) -> float:
    return float(np.corrcoef(x[:, 0], x[:, 1])[0, 1])


def bass_peak_width(mono: np.ndarray, fmin=40.0, fmax=400.0) -> tuple[float | None, float]:
    """低音の最強ピークの半値幅 [cent] と、そのピーク周波数 [Hz]。

    狭いほど「一度も動かない音程」。数学的に固定されたドローンは10cent前後、
    うなりやドリフトを持つ音は広くなる。"""
    f, P = signal.welch(mono, SR, nperseg=65536, noverlap=49152)
    m = (f >= fmin) & (f <= fmax)
    fb, pb = f[m], P[m]
    if len(fb) < 8:
        return None, 0.0
    i = int(pb.argmax())
    half = pb[i] / 2
    lo = i
    while lo > 0 and pb[lo] > half:
        lo -= 1
    hi = i
    while hi < len(pb) - 1 and pb[hi] > half:
        hi += 1
    if pb[lo] > half or pb[hi] > half:       # 端まで下がりきらない = 測れない
        return None, float(fb[i])
    return float(1200 * np.log2(fb[hi] / fb[lo])), float(fb[i])


def measure(x: np.ndarray) -> dict:
    mono = x.mean(axis=1)
    mono = mono / (np.sqrt(np.mean(mono ** 2)) + 1e-12)   # 音量差を消す
    hf, flat = hf_energy_and_flatness(mono)
    rt60, per30 = decay_stats(mono)
    cents, bass_hz = bass_peak_width(mono)
    g_ac, g_sd = gesture(mono)
    return dict(
        gesture_ac=g_ac,
        gesture_sd=g_sd,
        hf_2_8k=hf,
        ltas_flat=flat,
        centroid_p1090=centroid_spread(mono),
        flux_sd=flux_sd(mono),
        decay_per30=per30,
        rt60=rt60,
        lr_corr=lr_correlation(x),
        bass_cents=cents,
        _bass_hz=bass_hz,
        _dur=len(mono) / SR,
    )


# ---------------------------------------------------------------------------
# 判定と出力
# ---------------------------------------------------------------------------
def is_gate(key: str) -> bool:
    return TARGETS[key].get("gate", True)


def verdict(key: str, v: float | None) -> str:
    t = TARGETS[key]
    if not is_gate(key):
        return "参考"
    if v is None:
        return "測定不能"
    if t["lo"] is not None and v < t["lo"] * (1 - TOL):
        gap = t["lo"] / v if v > 0 else float("inf")
        return f"{t['under']} (×{gap:.1f})" if gap < 100 else f"{t['under']} (桁違い)"
    if t["hi"] is not None and v > t["hi"] * (1 + TOL):
        return f"{t['over']} (×{v / t['hi']:.1f})"
    return "OK"


def target_str(key: str) -> str:
    t = TARGETS[key]
    if not is_gate(key):
        return "(参考)"
    lo, hi = t["lo"], t["hi"]
    g = lambda v: f"{v:g}"
    if lo is not None and hi is not None:
        return f"{g(lo)} 〜 {g(hi)}"
    return f"≥ {g(lo)}" if lo is not None else f"≤ {g(hi)}"


def report(results: dict[str, dict]) -> None:
    names = list(results)
    wname = max(14, max(len(n) for n in names) + 2)
    head = f"{'指標':<26}{'目標帯':>14}" + "".join(n.rjust(wname) for n in names)
    print("=" * len(head))
    print(head)
    print("=" * len(head))
    for key in ORDER:
        row = f"{TARGETS[key]['label']:<26}{target_str(key):>14}"
        for n in names:
            v = results[n][key]
            row += ("---" if v is None else format(v, TARGETS[key]["fmt"])).rjust(wname)
        print(row)
        if len(names) == 1:
            n = names[0]
            print(f"{'':<26}{'':>14}" + verdict(key, results[n][key]).rjust(wname))
    print("=" * len(head))

    for n in names:
        r = results[n]
        ng = [k for k in ORDER if is_gate(k) and verdict(k, r[k]) != "OK"]
        bass = f"{r['_bass_hz']:.1f}Hz" if r["_bass_hz"] else "?"
        print(f"\n{n}  ({r['_dur']:.1f}秒 / 追跡した低音 {bass})")
        ngate = sum(1 for k in ORDER if is_gate(k))
        if not ng:
            print(f"  合格判定の{ngate}指標すべて目標帯に入っている。")
        else:
            print(f"  未達 {len(ng)}/{ngate}:")
            for k in ng:
                print(f"    - {TARGETS[k]['label']}: {verdict(k, r[k])}")


# ---------------------------------------------------------------------------
# 図
# ---------------------------------------------------------------------------
def _use_cjk_font(matplotlib) -> bool:
    """日本語が出せるフォントがあれば使う。無ければ図のラベルは英語に落とす
    (matplotlibの既定フォントは日本語を豆腐□にしてしまう)。"""
    from matplotlib import font_manager as fm
    have = {f.name for f in fm.fontManager.ttflist}
    for cand in ("Hiragino Sans", "Hiragino Kaku Gothic Pro", "Noto Sans CJK JP",
                 "YuGothic", "Meiryo", "IPAexGothic", "Arial Unicode MS"):
        if cand in have:
            matplotlib.rcParams["font.family"] = cand
            matplotlib.rcParams["axes.unicode_minus"] = False
            return True
    return False


def plot(sources: dict[str, np.ndarray], out: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ja = _use_cjk_font(matplotlib)
    L = dict(
        ltas="LTAS (音量正規化・1/6oct平滑)。灰色帯=2-8kHz" if ja
             else "LTAS (level-normalized, 1/6-oct). shaded = 2-8kHz",
        mod="変調スペクトル (包絡線のFFT) = ゆらぎの周期分布" if ja
            else "Modulation spectrum (envelope FFT) = distribution of fluctuation rates",
        modx="変調周波数 [Hz]" if ja else "modulation frequency [Hz]",
    )
    n = len(sources)
    fig = plt.figure(figsize=(15, 4 + 2.6 * n))
    gs = fig.add_gridspec(1 + n, 2, height_ratios=[1.5] + [1] * n)
    ax0, ax1 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])

    for name, x in sources.items():
        mono = x.mean(axis=1)
        mono = mono / (np.sqrt(np.mean(mono ** 2)) + 1e-12)
        f, P = signal.welch(mono, SR, nperseg=8192)
        m = (f >= 20) & (f <= 18000)
        sm = np.array([P[(f >= fc * 2 ** (-1 / 12)) & (f <= fc * 2 ** (1 / 12))].mean()
                       for fc in f[m]])
        ax0.semilogx(f[m], 10 * np.log10(sm + 1e-20), lw=1.5, label=name)

        e = _envelope(_bandpass(mono, 20, 16000))
        e = e / (e.mean() + 1e-12)
        nper = min(len(e), ENV_SR * 20)
        mf, mp = signal.welch(e - e.mean(), ENV_SR, nperseg=nper, noverlap=nper // 2)
        sel = (mf >= 0.1) & (mf <= 20)
        ax1.semilogx(mf[sel], 10 * np.log10(mp[sel] + 1e-20), lw=1.5, label=name)

    ax0.axvspan(2000, 8000, color="k", alpha=.07)
    ax0.set(title=L["ltas"], xlabel="Hz", ylabel="dB", ylim=(-95, -15))
    ax0.grid(True, which="both", alpha=.3); ax0.legend(fontsize=8)
    ax1.set(title=L["mod"], xlabel=L["modx"], ylabel="dB")
    ax1.grid(True, which="both", alpha=.3); ax1.legend(fontsize=8)

    for i, (name, x) in enumerate(sources.items()):
        ax = fig.add_subplot(gs[1 + i, :])
        mono = x.mean(axis=1)
        f, t, S = signal.spectrogram(mono, SR, nperseg=4096, noverlap=3072, mode="magnitude")
        m = (f >= 20) & (f <= 12000)
        ax.pcolormesh(t, f[m], 20 * np.log10(S[m] + 1e-8), shading="auto",
                      vmin=-100, vmax=-30, cmap="magma")
        ax.set(yscale="log", ylabel="Hz", title=name)
    ax.set_xlabel("time [s]")

    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"\n図を書き出した: {out}")


# ---------------------------------------------------------------------------
def calibrate(args: list[str]) -> None:
    """参照録音の複数区間から目標帯を引き直し、TARGETSに貼れる形で出す。"""
    path, nums = args[0], [float(v) for v in args[1:]]
    if len(nums) % 2 or not nums:
        sys.exit("--calibrate ref.mp3 開始 終了 [開始 終了 ...] の形で指定")
    segs = list(zip(nums[::2], nums[1::2]))
    rs = [measure(load(path, s)) for s in segs]
    print(f"# {Path(path).name} の {len(segs)} 区間 {segs} から引いた目標帯")
    for k in ORDER:
        vals = [r[k] for r in rs if r[k] is not None]
        if not vals:
            print(f'#   {k}: 全区間で測定不能'); continue
        print(f'#   {k}: 実測 {" / ".join(f"{v:g}" for v in vals)}'
              f'  → lo={min(vals):.4g}, hi={max(vals):.4g}')


def main() -> None:
    if "--calibrate" in sys.argv:
        i = sys.argv.index("--calibrate")
        return calibrate(sys.argv[i + 1:])

    ap = argparse.ArgumentParser(
        description="聴覚演出の音をdimtakt参照の8指標で測る",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("files", nargs="+", help="測る音声ファイル (wav/mp3/webm/flac...)")
    ap.add_argument("--seg", nargs=2, type=float, metavar=("開始", "終了"),
                    help="解析する区間 [秒]。省略時は全体")
    ap.add_argument("--plot", metavar="PNG", help="LTAS・変調スペクトル・スペクトログラムを書き出す")
    a = ap.parse_args()

    seg = tuple(a.seg) if a.seg else None
    sources, results = {}, {}
    for f in a.files:
        name = Path(f).stem[:24]
        x = load(f, seg)
        sources[name] = x
        results[name] = measure(x)

    report(results)
    if a.plot:
        plot(sources, a.plot)


if __name__ == "__main__":
    main()
