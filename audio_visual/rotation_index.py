#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "soundfile", "matplotlib"]
# ///
"""回転とうねりを数値で区別する。

    uv run audio_visual/rotation_index.py take.wav
    uv run audio_visual/rotation_index.py a.wav b.wav        # 並べて比較
    uv run audio_visual/rotation_index.py take.wav --plot p.png
    uv run audio_visual/rotation_index.py --selftest         # 合成音で妥当性を確認

`dimtakt_compare.py` の軌跡の自己相関は「重心が滑らかに動くか」しか見ないので、
うねりでも回転でも同じ値になる。ここで測るのは**部分音どうしの位相の順序**である。

帯域ごとの包絡線を取り、共通の変調周波数 f0 における位相 φ_k を求める。回転なら
膨らみが低い方から高い方へ順に通るので、φ_k は周波数に対して**一方向に進み続ける**。
うねりなら行きつ戻りつする。隣接帯域の位相差 Δφ_k を集めて

    順行性 = |Σ Δφ| / Σ|Δφ|

とすれば、1が完全な一方向、0が行き当たりばったりになる。この量は位相が周波数の
どんな座標(番号・対数・線形)で進むかを仮定しないので、巡回の作り方を変えても
そのまま使える。総和 Σ Δφ / 2π がそのまま**波数**(解析範囲を何周するか)になる。

    波数 ≈ 0                → トレモロ(明滅)。回転ではない
    波数 ≠ 0 + 順行性 低     → うねり
    波数 ≠ 0 + 順行性 高     → 回転

**直線性**は別の量である。順行性は「一方向か」しか見ず、進む速さのむらは見ない。
位相が対数周波数に対して直線なら、膨らみはオクターブ/秒が一定で掃引する。部分音の
番号に対して等速だと、低音側を駆け抜けて高音側で失速する(そのぶん直線性が落ちる)。

帯域数が有限なので、位相が無作為でも順行性はある程度出る。無作為な位相での95%点を
「偶然の水準」として併記してあり、これを超えていなければ順行と言ってはいけない。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dimtakt_compare import SR, load  # noqa: E402

NPERSEG, NOVERLAP = 4096, 3072
FRAME_SR = SR / (NPERSEG - NOVERLAP)      # 43.07 Hz
FMIN, FMAX = 80.0, 10000.0                # 解析する周波数範囲
NBANDS = 24
F0_RANGE = (0.04, 4.0)                    # 回転として探す変調周波数 [Hz]


# ---------------------------------------------------------------------------
def find_partials(mono: np.ndarray, nmax: int = NBANDS) -> np.ndarray:
    """長時間平均スペクトルの山を、周波数の低い順に返す [Hz]。

    **対数等間隔の帯域では測れない。** 帯域の境目が部分音とずれるうえ、窓の
    漏れ込みで隣り合う帯域が同じ部分音を分け合い、位相が人工的に相関する。
    無作為な位相を与えた音でも順行して見えるほど効く(合成音での実測: 0.75)。
    山だけを追えば、位相は部分音の数だけ独立に取れる。"""
    f, P = signal.welch(mono, SR, nperseg=16384, noverlap=12288)
    m = (f >= FMIN) & (f <= FMAX)
    f, P = f[m], P[m]
    db = 10 * np.log10(P + 1e-20)
    pk, props = signal.find_peaks(db, prominence=6, distance=3)
    if len(pk) == 0:
        return np.geomspace(FMIN, FMAX, nmax)          # 山がなければ等間隔へ退避
    order = np.argsort(props["prominences"])[::-1][:nmax]
    return np.sort(f[pk[order]])


def band_envelopes(x: np.ndarray, centers: np.ndarray
                   ) -> tuple[np.ndarray, np.ndarray]:
    """部分音ごとの振幅包絡線 [部分音, 時間] を L/R 別に返す。

    和が音量、差が定位になる。ヒルベルト変換ではなくスペクトログラムの帯域和を
    使う。桁で速く、43Hzのフレームレートは0.04〜4Hzの変調には十分すぎる。"""
    df = SR / NPERSEG
    half = np.maximum(3 * df, centers * 0.029)         # 最低3ビン / ±1/4音
    out = []
    for ch in range(2):
        f, _, S = signal.spectrogram(x[:, ch], SR, nperseg=NPERSEG,
                                     noverlap=NOVERLAP, mode="magnitude")
        out.append(np.array([S[(f >= c - h) & (f <= c + h)].sum(axis=0)
                             for c, h in zip(centers, half)]))
    return out[0], out[1]


def band_pitch(mono: np.ndarray, centers: np.ndarray) -> np.ndarray:
    """部分音ごとの瞬時の高さ [cent] を返す。帯域内の重心を追う。

    ドップラーは音量ではなく高さに出るので、包絡線だけを見ていると存在ごと
    見落とす。帯域の幅より小さい揺れしか追えない(数セントの検出には十分)。"""
    df = SR / NPERSEG
    half = np.maximum(3 * df, centers * 0.029)
    f, _, S = signal.spectrogram(mono, SR, nperseg=NPERSEG,
                                 noverlap=NOVERLAP, mode="magnitude")
    rows = []
    for c, h in zip(centers, half):
        m = (f >= c - h) & (f <= c + h)
        cen = (f[m][:, None] * S[m]).sum(axis=0) / (S[m].sum(axis=0) + 1e-12)
        rows.append(1200 * np.log2(np.maximum(cen, 1e-6) / c))
    return np.array(rows)


def _phases_at(env: np.ndarray, f0_range=F0_RANGE, f0_fixed: float | None = None):
    """各帯域の包絡線から、共通の変調周波数 f0 とそこでの位相・振幅を取る。

    振幅は正規化せずに返す。**重みは「実際にどれだけ揺れているか」でなければ
    ならない。** 帯域ごとに平均で割ると、エネルギーの無い帯域(部分音と部分音の
    隙間)の雑音が深い変調に見え、位相の推定を乗っ取る。"""
    e = env - env.mean(axis=1, keepdims=True)
    n = e.shape[1]
    w = np.hanning(n)
    X = np.fft.rfft(e * w, axis=1)
    freqs = np.fft.rfftfreq(n, 1 / FRAME_SR)

    if f0_fixed is not None:
        b = int(np.argmin(np.abs(freqs - f0_fixed)))
    else:
        sel = (freqs >= f0_range[0]) & (freqs <= f0_range[1])
        power = (np.abs(X) ** 2).sum(axis=0)
        b = int(np.arange(len(freqs))[sel][power[sel].argmax()])
    return float(freqs[b]), np.angle(X[:, b]), np.abs(X[:, b])


def _progression(phi: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """隣接帯域の位相差から、順行性と波数を出す。

    Δφ は ±π へ折り返す。折り返す以上、1帯域あたり半周を超える巡回は原理的に
    測れない(帯域数の半分が波数の上限)。順行性は座標に依存しないので、位相を
    部分音番号に配ろうが対数周波数に配ろうが同じ物差しで比べられる。"""
    d = np.angle(np.exp(1j * np.diff(phi)))
    v = np.sqrt(w[:-1] * w[1:])                       # 対の重み
    num, den = float((v * d).sum()), float((v * np.abs(d)).sum())
    prog = abs(num) / (den + 1e-12)
    # 波数は重みを掛けずに総和で取る。**重み付き平均×対の数では測れない。**
    # 対数周波数に等速な巡回では低い部分音ほど位相差が大きく、そこに重みも
    # 集まるため、同じ一周が1.31周と出る(実測)。総和なら座標に依らず一周は一周。
    turns = float(d.sum()) / (2 * np.pi)
    return prog, turns


def _null_level(w: np.ndarray, ntrial: int = 2000) -> float:
    """位相が無作為なときの順行性の95%点 = 偶然の水準。

    **並べ替えではなく無作為な位相を引く。** 並べ替えは位相の分布を保つので、
    全帯域が同位相のとき(トレモロ)に何も壊さず、帰無分布が退化する。"""
    rng = np.random.default_rng(0)
    vals = [_progression(rng.uniform(-np.pi, np.pi, len(w)), w)[0] for _ in range(ntrial)]
    return float(np.percentile(vals, 95))


def _linearity(phi: np.ndarray, w: np.ndarray, u: np.ndarray, ngrid: int = 4001):
    """φ ≈ α + s·u への円回帰。合成ベクトル長を最大にする傾きsを探す。

    座標uを差し替えることで「何に対して等速か」を測り分けられる。u=部分音番号
    なら現在の実装、u=log2(周波数) ならオクターブ/秒が一定の掃引に対応する。
    順行していても速さにむらがあれば下がる。"""
    z = w * np.exp(1j * phi)
    smax = np.pi / max(np.diff(u).max(), 1e-9)        # 隣接で半周を超えたら測れない
    s = np.linspace(-smax, smax, ngrid)
    r = np.abs(np.exp(-1j * np.outer(s, u)) @ z) / (w.sum() + 1e-12)
    i = int(r.argmax())
    return float(r[i]), float(s[i])


def scan(x: np.ndarray, nbands: int = NBANDS, ntrial: int = 400) -> dict:
    """変調周波数を掃引し、どの速さで位相がもっとも順行しているかを探す。

    **実際の演奏では、最大の変調成分は回転ではなく全体の抑揚である。** 参照録音
    では0.05Hzの抑揚が最強で、そこだけを見ると「うねり」としか出ない。回転が
    あるとすればどの速さかは、探しにいかないと分からない。

    **掃引した中の最良を採る以上、これは仮説検定にならない。** 探索に使い、
    見つけた速さを別途 --f0 で1回だけ検定すること。帰無水準は各周波数ごとの
    95%点で、掃引による水増しは補正していない。"""
    mono = x.mean(axis=1)
    centers = find_partials(mono, nbands)
    envL, envR = band_envelopes(x, centers)
    env = envL + envR
    e = env - env.mean(axis=1, keepdims=True)
    X = np.fft.rfft(e * np.hanning(e.shape[1]), axis=1)
    freqs = np.fft.rfftfreq(e.shape[1], 1 / FRAME_SR)
    sel = np.where((freqs >= F0_RANGE[0]) & (freqs <= F0_RANGE[1]))[0]

    phi = np.angle(X[:, sel]).T                       # [bin, 部分音]
    mag = np.abs(X[:, sel]).T
    d = np.angle(np.exp(1j * np.diff(phi, axis=1)))
    v = np.sqrt(mag[:, :-1] * mag[:, 1:])
    prog = np.abs((v * d).sum(1)) / ((v * np.abs(d)).sum(1) + 1e-12)
    turns = d.sum(1) / (2 * np.pi)

    rng = np.random.default_rng(0)
    rp = rng.uniform(-np.pi, np.pi, (ntrial, len(sel), len(centers)))
    rd = np.angle(np.exp(1j * np.diff(rp, axis=2)))
    rprog = np.abs((v * rd).sum(2)) / ((v * np.abs(rd)).sum(2) + 1e-12)
    null = np.percentile(rprog, 95, axis=0)
    eff = v.sum(1) ** 2 / ((v ** 2).sum(1) + 1e-12)      # 有効な対の数

    ok = (np.abs(turns) >= 0.25) & (prog > null)
    order = np.argsort(np.where(ok, prog - null, -9))[::-1]
    return dict(freqs=freqs[sel], prog=prog, turns=turns, mag=mag.sum(1),
                order=order, null=null, eff=eff)


def measure(x: np.ndarray, nbands: int = NBANDS, f0_fixed: float | None = None) -> dict:
    mono = x.mean(axis=1)
    centers = find_partials(mono, nbands)
    envL, envR = band_envelopes(x, centers)
    amp_env = envL + envR
    f0, phi, mag = _phases_at(amp_env, f0_fixed=f0_fixed)
    prog, wavenumber = _progression(phi, mag)
    null = _null_level(mag)
    vv = np.sqrt(mag[:-1] * mag[1:])
    eff_pairs = float(vv.sum() ** 2 / ((vv ** 2).sum() + 1e-12))
    lin_idx, beta = _linearity(phi, mag, np.arange(len(phi), dtype=float))
    lin_oct, _ = _linearity(phi, mag, np.log2(centers))
    tremolo = float(np.abs((mag * np.exp(1j * phi)).sum()) / (mag.sum() + 1e-12))

    span_oct = float(np.log2(centers[-1] / centers[0])) if len(centers) > 1 else 0.0
    oct_per_turn = np.inf if abs(wavenumber) < 1e-6 else span_oct / wavenumber

    # ---- 音像が巡っているか(レスリー性) ----
    # **部分音ごとの定位を測ってはいけない。** 現在の実装では各部分音の定位は
    # 時間的に一切動かず(cos(phases[i])は定数)、動くのは「今どの部分音が鳴って
    # いるか」だけである。測るべきは音像全体の位置 p(t) が、明るさの巡回 c(t) と
    # どういう位相関係で振れるか。位相差±90度なら音源が周回している形、0/180度
    # なら明るい方向へ像が寄るだけで周回にはならない。
    tot = amp_env.sum(axis=0) + 1e-12
    p_t = (envL - envR).sum(axis=0) / tot
    c_t = (np.log2(centers)[:, None] * amp_env).sum(axis=0) / tot
    _, ang, mg = _phases_at(np.stack([p_t, c_t]), f0_fixed=f0)
    scale = 2 / (len(p_t) * 0.5)               # ハン窓込みで振幅へ戻す
    pan_swing = float(mg[0] * scale)
    pan_offset = float(np.degrees(np.angle(np.exp(1j * (ang[0] - ang[1])))))
    sweep_oct = float(mg[1] * scale)

    # ---- 音高が巡回と連動しているか(ドップラー) ----
    # 近づきながら明るくなる音源では、音高は音量より1/4周期**先**に頂点へ来る。
    # 位相差が+90度付近なら回転している物体、0度なら単に明るい所で高いだけ。
    cents = band_pitch(mono, centers)
    _, ang_p, mag_p = _phases_at(cents, f0_fixed=f0)
    scale = 2 / (cents.shape[1] * 0.5)
    dop_cents = float(np.median(mag_p * scale))
    wv = mag * mag_p
    dz = (wv * np.exp(1j * (ang_p - phi))).sum() / (wv.sum() + 1e-12)
    dop_lock, dop_offset = float(np.abs(dz)), float(np.degrees(np.angle(dz)))

    depth = float(np.median(amp_env.std(axis=1) / (amp_env.mean(axis=1) + 1e-12)))
    return dict(prog=prog, lin_idx=lin_idx, lin_oct=lin_oct, null=null,
                wavenumber=wavenumber, f0=f0, npartials=float(len(centers)),
                eff_pairs=eff_pairs,
                oct_per_turn=oct_per_turn, tremolo=tremolo, depth=depth,
                pan_swing=pan_swing, pan_offset=pan_offset, sweep_oct=sweep_oct,
                dop_cents=dop_cents, dop_lock=dop_lock, dop_offset=dop_offset,
                _phi=phi, _mag=mag, _beta=beta, _centers=centers,
                _env=amp_env, _dur=len(x) / SR)


def verdict(r: dict) -> str:
    if r["depth"] < 0.02:
        return "変調がない(測定不能)"
    if r["null"] > 0.95:
        # 重みが少数の対に集中すると、順行性は無作為な位相でもほぼ1に張り付く。
        # このとき指標に検出力はなく、値が高いことを根拠にしてはいけない。
        return f"測定不能 — 重みが偏りすぎ(有効な対 {r['eff_pairs']:.1f})"
    if abs(r["wavenumber"]) < 0.25:
        return "トレモロ — 全帯域がほぼ同位相で明滅している"
    if r["prog"] < r["null"]:
        return "うねり — 位相が行きつ戻りつする"
    d = "低→高" if r["wavenumber"] > 0 else "高→低"
    s = "回転" if r["prog"] >= 0.7 else "弱い回転"
    sweep = "" if np.isinf(r["oct_per_turn"]) else \
        f" / 平均 {abs(r['oct_per_turn']) * r['f0']:.2f} oct/s"
    if r["lin_oct"] >= 0.95:
        pace = "オクターブ/秒が一定"
    elif r["lin_idx"] > r["lin_oct"]:
        pace = "部分音の番号に等速(低音を駆け抜け高音で失速)"
    else:
        pace = "速さにむらがある"
    return f"{s} — {d}へ巡回{sweep} / {pace}"


ROWS = [
    ("位相の順行性 (0-1)", "prog", "8.3f"),
    ("  偶然の水準 (95%)", "null", "8.3f"),
    ("波数 (解析範囲の周回数)", "wavenumber", "8.2f"),
    ("巡回の速さ f0 [Hz]", "f0", "8.3f"),
    ("1周あたり [oct]", "oct_per_turn", "8.2f"),
    ("直線性: 部分音番号に等速", "lin_idx", "8.3f"),
    ("直線性: 対数周波数に等速", "lin_oct", "8.3f"),
    ("同位相度 (トレモロ性)", "tremolo", "8.3f"),
    ("変調の深さ", "depth", "8.3f"),
    ("音像の振れ幅 (0-1)", "pan_swing", "8.3f"),
    ("  明るさとの位相差 [度]", "pan_offset", "8.0f"),
    ("重心の振れ幅 [oct]", "sweep_oct", "8.2f"),
    ("音高の揺れ [cent]", "dop_cents", "8.1f"),
    ("  巡回との連動度", "dop_lock", "8.3f"),
    ("  音量との位相差 [度]", "dop_offset", "8.0f"),
    ("追跡した部分音の数", "npartials", "8.0f"),
    ("有効な対の数", "eff_pairs", "8.1f"),
]


def report(results: dict[str, dict]) -> None:
    names = list(results)
    w = max(12, max(len(n) for n in names) + 2)
    head = f"{'':<26}" + "".join(n.rjust(w) for n in names)
    print("=" * len(head)); print(head); print("=" * len(head))
    for label, key, fmt in ROWS:
        row = f"{label:<26}"
        for n in names:
            v = results[n][key]
            row += ("inf" if np.isinf(v) else format(v, fmt)).rjust(w)
        print(row)
    print("=" * len(head))
    for n in names:
        print(f"{n:<26}{verdict(results[n])}")


# ---------------------------------------------------------------------------
def _synth(kind: str, dur: float = 60.0, np_: int = 12, f0: float = 0.35) -> np.ndarray:
    """指標そのものを検証するための合成音。何が鳴っているか既知の4種。"""
    t = np.arange(int(dur * SR)) / SR
    rng = np.random.default_rng(1)
    base = 235.12
    if kind == "rotation":
        ph = 2 * np.pi * np.arange(np_) / np_
    elif kind == "tremolo":
        ph = np.zeros(np_)
    elif kind == "wobble":
        ph = rng.uniform(0, 2 * np.pi, np_)
    elif kind == "static":
        ph = None
    else:
        raise SystemExit(f"不明: {kind}")
    l = np.zeros_like(t); r = np.zeros_like(t)
    for i in range(np_):
        f = base * (i + 1)
        if f > SR / 2.2:
            break
        car = np.sin(2 * np.pi * f * t)
        if ph is None:
            env, pan = np.ones_like(t), 0.0
        else:
            env = 0.12 + 0.88 * np.maximum(np.sin(2 * np.pi * f0 * t + ph[i]), 0) ** 3
            pan = 0.8 * np.cos(ph[i])
        s = car * env / (i + 1) ** 0.8
        l += s * (0.5 + 0.5 * pan); r += s * (0.5 - 0.5 * pan)
    x = np.stack([l, r], axis=1)
    return x / (np.abs(x).max() + 1e-12) * 0.7


def selftest() -> None:
    print("合成音で指標を検証する。何が鳴っているかは既知。\n")
    res = {k: measure(_synth(k)) for k in ("rotation", "tremolo", "wobble", "static")}
    report(res)
    print("\n期待: rotation=回転 / tremolo=トレモロ / wobble=うねり / static=測定不能")


def plot(sources: dict[str, dict], out: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from dimtakt_compare import _use_cjk_font
    _use_cjk_font(matplotlib)

    n = len(sources)
    fig, axes = plt.subplots(n, 2, figsize=(13, 3.4 * n), squeeze=False)
    for i, (name, r) in enumerate(sources.items()):
        ax = axes[i][0]
        e = r["_env"] / (r["_env"].max(axis=1, keepdims=True) + 1e-12)
        tt = np.arange(e.shape[1]) / FRAME_SR
        ax.pcolormesh(tt, np.arange(e.shape[0]), e, shading="auto", cmap="magma")
        ax.set(title=f"{name}: 帯域ごとの包絡線", xlabel="時間 [s]", ylabel="帯域",
               xlim=(0, min(30, tt[-1])))

        ax = axes[i][1]
        k = np.arange(len(r["_phi"]))
        a0 = np.angle((r["_mag"] * np.exp(1j * (r["_phi"] - r["_beta"] * k))).sum())
        fit = np.angle(np.exp(1j * (a0 + r["_beta"] * k)))
        ax.scatter(k, np.degrees(np.angle(np.exp(1j * r["_phi"]))),
                   s=6 + 300 * r["_mag"] / (r["_mag"].max() + 1e-12), alpha=.7)
        ax.plot(k, np.degrees(fit), lw=1, color="r", alpha=.6)
        ax.set(title=f"{name}: 帯域ごとの位相 (順行性 {r['prog']:.2f} / "
                     f"波数 {r['wavenumber']:.2f})",
               xlabel="帯域", ylabel="位相 [度]", ylim=(-190, 190))
        ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out, dpi=130)
    print(f"\n図を書き出した: {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description="回転とうねりを位相の順序で区別する",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--selftest", action="store_true", help="合成音で指標を検証する")
    ap.add_argument("--seg", nargs=2, type=float, metavar=("開始", "終了"))
    ap.add_argument("--f0", type=float, help="変調周波数を手で与える [Hz]")
    ap.add_argument("--bands", type=int, default=NBANDS)
    ap.add_argument("--plot", metavar="PNG")
    ap.add_argument("--scan", action="store_true",
                    help="変調周波数を掃引し、最も順行している速さを探す")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.scan:
        seg = tuple(a.seg) if a.seg else None
        for f in a.files:
            s = scan(load(f, seg), a.bands)
            print(f"\n{Path(f).stem[:40]}  (掃引は探索用。検定は --f0 で1回だけ)")
            print(f"  {'変調周波数':>10} {'順行性':>8} {'偶然':>7} {'波数':>7}"
                  f" {'有効な対':>8} {'変調の強さ':>10}")
            for i in sorted(s["order"][:8], key=lambda j: s["freqs"][j]):
                print(f"  {s['freqs'][i]:10.3f} {s['prog'][i]:8.3f} {s['null'][i]:7.3f}"
                      f" {s['turns'][i]:7.2f} {s['eff'][i]:8.1f}"
                      f" {s['mag'][i] / s['mag'].max():10.2f}")
        return
    if not a.files:
        ap.error("測るファイルを指定するか --selftest を使う")

    seg = tuple(a.seg) if a.seg else None
    res = {Path(f).stem[:22]: measure(load(f, seg), a.bands, a.f0) for f in a.files}
    report(res)
    if a.plot:
        plot(res, a.plot)


if __name__ == "__main__":
    main()
