"""
忘却炉 聴覚演出プロトタイプ v4 — dimtakt由来の宇宙的質感を導入

v3までの不足:
    構造(ドローン + d グレイン + r バースト)は回路と整合していたが、音響的には
    完全にドライで、audio_visual/聴覚演出はノーバッファの連続グライド楽器...md が
    既に到達していた dimtakt 由来の質感(長い残響、ユニゾンデチューン、フォルマント
    共鳴、ポルタメント、点描的スパークル)が一つも入っていなかった。

v4で導入した要素と、それぞれの回路的な裏付け:
    1. ユニゾンデチューン(16声)
         16個のハーフセルは X7R コンデンサの容量公差を個別に持つため、
         tau=RC が1個ずつ僅かに違う。つまり各セルの発振周波数はもともと
         揃っていない。デチューンは装飾ではなく部品公差の可聴化である。
    2. 長い残響(6.5秒) + ディレイ(ブロック周期の半分 = 0.272秒)
         ディレイ時間は回路クロック由来。残響それ自体が「エネルギーが空間へ
         不可逆に散逸する過程」であり、この作品の主題と同型。
    3. フォルマント共鳴2バンド  … 有機的な声の質感(dimtakt)
    4. ポルタメント … 前グレインの音高から今の目標値へ滑らかに移行
    5. スパークル … 連続ホワイトノイズではなく確率的な瞬き(既存ノートの試聴結果)
    6. ドライ/ウェットの対比
         d グレイン(記憶) = 残響たっぷり = 遠い宇宙
         r バースト(乱数)  = ドライ       = 手元の熱源の近さ
         鎮静相こそ真のランダウアー支払い(=発熱)なので、r が「近い」のは物理的にも正しい

出力: erasure_sonification_v4.wav (ステレオ)
"""
import numpy as np, glob, math
from scipy.io import wavfile
from scipy.signal import fftconvolve, lfilter, butter

SR = 44100
R, C_CAP = 117.0, 71e-9
TAU = R * C_CAP
F_CYCLE = 1.0 / (16 * TAU)
F_DRONE = F_CYCLE / 16
BLOCK_BYTES = 4096
BLOCK_TIME = BLOCK_BYTES / F_CYCLE
DELAY_TIME = BLOCK_TIME / 2          # 0.272s: 回路クロック由来
REVERB_SEC = 6.5                     # 既存ノートの試聴で決まった値
NTC_TAU = 8.0
N_HALFCELLS = 16                     # 8bit x 2 (相補ペア)
CAP_TOLERANCE = 0.0075                # ユニゾン用の実効デチューン幅(未検証 参照)

rng = np.random.default_rng(2718)


def shannon_entropy(b):
    c = np.bincount(b, minlength=256)
    p = c[c > 0] / len(b)
    return float(-np.sum(p * np.log2(p)))


def bit_transition_density(b):
    x = np.bitwise_xor(b[:-1], b[1:])
    return float(np.mean([bin(v).count("1") for v in x]))


def lp(x, fc, order=2):
    b, a = butter(order, min(fc / (SR / 2), 0.99), btype="low")
    return lfilter(b, a, x)


def bp(x, fc, q=8.0):
    bw = fc / q
    lo = max(20.0, fc - bw / 2) / (SR / 2)
    hi = min(fc + bw / 2, SR / 2 - 100) / (SR / 2)
    b, a = butter(2, [lo, hi], btype="band")
    return lfilter(b, a, x)


def formant(x, f1=380.0, f2=920.0, mix=0.55):
    """声のようなフォルマント共鳴2バンド(dimtakt由来の有機的な音色)"""
    return (1 - mix) * x + mix * (0.65 * bp(x, f1) + 0.35 * bp(x, f2))


def make_ir(seconds=REVERB_SEC, seed=0):
    """指数減衰ノイズによる残響IR。高域ほど速く減衰させ暗く広い空間にする"""
    g = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.linspace(0, seconds, n)
    ir = g.normal(0, 1, n) * np.exp(-t * (4.6 / seconds))
    ir = lp(ir, 2600)
    ir = np.concatenate([np.zeros(int(0.035 * SR)), ir])   # プリディレイ
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-12)


IR_L, IR_R = make_ir(seed=11), make_ir(seed=22)            # L/R非相関 = 横の広がり


def reverb(x, wet=0.55):
    l = fftconvolve(x, IR_L)[: len(x)]
    r = fftconvolve(x, IR_R)[: len(x)]
    return (1 - wet) * x + wet * l, (1 - wet) * x + wet * r


def delay_fx(x, t=DELAY_TIME, fb=0.42, wet=0.34):
    d = int(t * SR)
    out = x.copy()
    for k in range(1, 5):
        sh = d * k
        if sh >= len(x):
            break
        out[sh:] += wet * (fb ** (k - 1)) * lp(x[: len(x) - sh], 3200)
    return out


def degrade(sig, p, seed):
    """Play/Destroy的な不可逆劣化(ベクトル化版)"""
    if p <= 0:
        return sig.copy()
    g = np.random.default_rng(seed)
    bits = max(2, 16 - round(13 * p))
    lv = 2 ** bits
    cr = np.round(sig * (lv / 2)) / (lv / 2)
    mask = g.random(len(sig)) < 0.22 * p
    idx = np.where(~mask, np.arange(len(sig)), 0)
    idx = np.maximum.accumulate(idx)
    return cr[idx]


def cell_detune_ratios():
    """16ハーフセルの容量公差 -> 周波数比。f ∝ 1/(RC) なので f_i = f/(1+d_i)"""
    d = rng.normal(0, CAP_TOLERANCE, N_HALFCELLS)
    return 1.0 / (1.0 + d)


DETUNE = cell_detune_ratios()


def render_drone(n, amp=0.15):
    """16ハーフセル分のユニゾン。個体差による微小デチューンで厚みを出す"""
    dur = n / SR
    t = np.linspace(0, dur, n, endpoint=False)
    vib = (1.0 + 0.0035 * np.sin(2 * np.pi * 0.07 * t)
           + 0.0020 * np.sin(2 * np.pi * 0.031 * t + 1.3))
    acc = np.zeros(n)
    for ratio in DETUNE:
        ph = 2 * np.pi * F_DRONE * ratio * np.cumsum(vib) / SR + rng.random() * 2 * np.pi
        acc += np.sin(ph) + 0.18 * np.sin(2 * ph)
    acc = lp(formant(acc / N_HALFCELLS, 380, 920, mix=0.5), 4200)
    return amp * acc / (np.max(np.abs(acc)) + 1e-9)


def render_grain(dur, p_from, p_to, bright, p, seed):
    """d のグレイン。前グレインの音高からポルタメントで滑らかに移行する"""
    n = int(dur * SR)
    t = np.linspace(0, dur, n, endpoint=False)
    glide = np.linspace(0, 1, n) ** 0.5
    f = p_from * (p_to / p_from) ** glide          # 指数補間のポルタメント
    vib = 1.0 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.linspace(0, 1, n)
    env = np.exp(-t / (dur * 0.30)) * (1 - np.exp(-t / (dur * 0.05)))
    acc = np.zeros(n)
    for det in (-0.004, 0.0, 0.005):               # 3声ユニゾン(dimtakt)
        ph = 2 * np.pi * np.cumsum(f * vib * (1 + det)) / SR
        acc += (np.sin(ph) + bright * 0.45 * np.sin(2 * ph)
                + (bright ** 2) * 0.2 * np.sin(3 * ph))
    acc = formant(acc / 3, 420, 1050, mix=0.45) * env
    acc /= (np.max(np.abs(acc)) + 1e-9)
    return 0.42 * degrade(acc, p, seed) * env


def render_burst(dur, r_block, amp=0.26):
    """r のバースト。合成ノイズではなく乱数の実バイト列を波形へ写像する"""
    n = int(dur * SR)
    idx = (np.arange(n) * len(r_block) // n).astype(int)
    raw = (r_block[idx].astype(np.float64) - 127.5) / 127.5
    t = np.linspace(0, dur, n, endpoint=False)
    env = np.exp(-t / (dur * 0.26)) * (1 - np.exp(-t / (dur * 0.04)))
    return amp * lp(raw, 5200) * env


def render_sparkle(n_total, H, seed):
    """点描的な瞬き。連続ノイズは既存ノートの試聴で却下されている"""
    g = np.random.default_rng(seed)
    out = np.zeros(n_total)
    purity = np.clip((H - 4.5) / 3.0, 0, 1)
    for _ in range(int(3 * purity) + 1):
        if g.random() > 0.55:
            continue
        pos = int(g.integers(0, max(1, n_total - 2000)))
        ln = min(int(g.integers(400, 1800)), n_total - pos)
        tt = np.linspace(0, ln / SR, ln, endpoint=False)
        f = F_DRONE * g.choice([4, 5, 6, 8])
        out[pos:pos + ln] += 0.10 * np.sin(2 * np.pi * f * tt) * np.exp(-tt / (ln / SR * 0.22))
    return out


buf = b""
for fp in sorted(glob.glob("../research/**/*.md", recursive=True)):
    with open(fp, "rb") as fh:
        buf += fh.read()
    if len(buf) > 500_000:
        break
d_data = np.frombuffer(buf, dtype=np.uint8)
r_data = rng.integers(0, 256, 500_000, dtype=np.uint8)

DUR = 46.0
n_blocks = min(int(DUR / BLOCK_TIME), len(d_data) // BLOCK_BYTES)
print(f"f_drone={F_DRONE:.2f}Hz block={BLOCK_TIME*1000:.1f}ms delay={DELAY_TIME*1000:.1f}ms")
print(f"ユニゾン16声 デチューン幅 = {1200*math.log2(DETUNE.max()/DETUNE.min()):.1f} cent")
print(f"blocks={n_blocks}\n")

total_n = int((n_blocks + 1) * BLOCK_TIME * SR)
wet_bus = np.zeros(total_n)      # 残響へ送る(記憶 = 遠い)
dry_bus = np.zeros(total_n)      # ドライ(乱数 = 近い)
prev_pitch = F_DRONE
Hs, pitches = [], []

for i in range(n_blocks):
    bd = d_data[i * BLOCK_BYTES:(i + 1) * BLOCK_BYTES]
    br = r_data[i * BLOCK_BYTES:(i + 1) * BLOCK_BYTES]
    H = shannon_entropy(bd)
    m = float(bd.mean())
    bt = bit_transition_density(bd)
    pitch = F_DRONE * (2 ** ((H - 6.0) / 3.0)) * (2 ** (((m - 128) / 128) * 0.04))
    bright = float(np.clip(bt / 4.0, 0, 1.2))
    p = 0.60 * (i / max(1, n_blocks - 1))
    off = int(i * BLOCK_TIME * SR)

    g = render_grain(BLOCK_TIME * 0.62, prev_pitch, pitch, bright, p, 5000 + i)
    wet_bus[off:off + len(g)] += g
    sp = render_sparkle(int(BLOCK_TIME * 0.62 * SR), H, 7000 + i)
    wet_bus[off:off + len(sp)] += sp

    bo = render_burst(BLOCK_TIME * 0.34, br)
    ob = off + int(BLOCK_TIME * 0.60 * SR)
    dry_bus[ob:ob + len(bo)] += bo[:len(dry_bus) - ob]

    prev_pitch = pitch
    Hs.append(H)
    pitches.append(pitch)

pa = np.array(pitches)
print(f"H(d)={min(Hs):.2f}-{max(Hs):.2f}  pitch={pa.min():.1f}-{pa.max():.1f}Hz "
      f"({12*math.log2(pa.max()/pa.min()):.2f}半音)")

drone = render_drone(total_n)
wet_bus = delay_fx(wet_bus + drone * 0.9)
L, Rr = reverb(wet_bus, wet=0.58)
L = L + dry_bus
Rr = Rr + dry_bus

tail = int(7.0 * SR)
env = np.ones(total_n)
env[-tail:] = np.exp(-np.linspace(0, 7.0, tail) / NTC_TAU)
L *= env
Rr *= env
st = np.stack([L, Rr], axis=1)
st = st / (np.max(np.abs(st)) + 1e-9) * 0.90


def an(s, lab):
    rms = np.sqrt(np.mean(s ** 2))
    pk = np.max(np.abs(s)) + 1e-12
    sp = np.abs(np.fft.rfft(s * np.hanning(len(s))))
    fr = np.fft.rfftfreq(len(s), 1 / SR)
    print(f"  {lab:<20s} RMS={rms:.4f} crest={20*np.log10(pk/rms):5.1f}dB "
          f"centroid={np.sum(fr*sp)/np.sum(sp):7.1f}Hz")


print("\n=== 音響解析 ===")
an(drone, "ドローン(16声)")
an(dry_bus, "r バースト(dry)")
an(L, "最終 L")
an(Rr, "最終 R")
print(f"  L/R相関 = {float(np.corrcoef(L, Rr)[0,1]):.3f} (1.0=モノラル、低いほど広い)")

wavfile.write("erasure_sonification_v4.wav", SR, (st * 32767).astype(np.int16))
print(f"\n書き出し: erasure_sonification_v4.wav 総尺={total_n/SR:.1f}s ステレオ")
