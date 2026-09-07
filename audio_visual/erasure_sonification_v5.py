"""
忘却炉 聴覚演出プロトタイプ v5 — ノーツを廃し、連続する持続音だけで構成する

v4までの構造的な誤り:
    ブロックごとに減衰する短い音(グレイン)を「発音」させていたが、
    audio_visual/聴覚演出はノーバッファの連続グライド楽器...md は元々
    「ブロックごとに新しい音を都度トリガーするのではなく、常時鳴り続ける
    一本のオシレーターを、ブロックが来るたびに次の目標値へポルタメントで
    滑らかに追従させる」と決めていた。v1〜v4はこの決定から外れていた。

v5の方針:
    離散的な発音を全廃し、すべてを持続音のゆるやかな変化として表現する。
    ブロック統計量は「音を鳴らすトリガー」ではなく「鳴り続けている音の
    パラメータ目標値」として使い、ブロック周期(0.544s)ごとに更新される
    目標値へ滑らかに補間する。回路由来のタイミングは保たれるが、
    アタックが無いため耳には切れ目のない連続音として届く。

安らかさのための設計:
    1. 回路クロックの整数分周が作る純正律
         f_cycle/64, /48, /32, /24, /16, /12, /8 は互いに 4:3・3:2・2:1 の
         整数比になる。つまりオクターブと完全4度/5度だけで構成された
         開いた響き(オルガヌム的)が、回路定数から自動的に得られる。
         協和音程を「選んだ」のではなく、分周がもともと協和である。
    2. 暗さの解消 — v4は残響IRを2.6kHzで切っており全体が籠っていた。
         残響を明るくし、上方の分周(/8, /6)を薄く重ねて空気感を足す。
    3. アタックの全廃 — 立ち上がりのある音を一切使わない。
    4. 劣化はビットクラッシュの「音色変化」としてのみ効かせ、
       ドロップアウト(プチプチ)は使わない。安らかさを壊すため。

出力: erasure_sonification_v5.wav (ステレオ)
"""
import numpy as np, glob, math
from scipy.io import wavfile
from scipy.signal import fftconvolve, lfilter, butter

SR = 44100
R, C_CAP = 117.0, 71e-9
TAU = R * C_CAP
F_CYCLE = 1.0 / (16 * TAU)          # ~7523.8 Hz
BLOCK_BYTES = 4096
BLOCK_TIME = BLOCK_BYTES / F_CYCLE  # ~0.5444 s
DELAY_TIME = BLOCK_TIME             # ブロック周期そのもの(回路由来)
REVERB_SEC = 7.5
NTC_TAU = 8.0
N_HALFCELLS = 16
CAP_TOLERANCE = 0.0075

# 回路クロックの整数分周。互いに 2:1 / 3:2 / 4:3 の純正な比になる
DIVISORS = [64, 48, 32, 24, 16, 12, 8]
LAYER_GAIN = [0.85, 0.45, 0.80, 0.40, 0.70, 0.28, 0.16]

rng = np.random.default_rng(1618)


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


def hp(x, fc, order=2):
    b, a = butter(order, max(fc / (SR / 2), 1e-4), btype="high")
    return lfilter(b, a, x)


def bp(x, fc, q=6.0):
    bw = fc / q
    lo = max(20.0, fc - bw / 2) / (SR / 2)
    hi = min(fc + bw / 2, SR / 2 - 100) / (SR / 2)
    b, a = butter(2, [lo, hi], btype="band")
    return lfilter(b, a, x)


def make_ir(seconds=REVERB_SEC, seed=0):
    """v4より明るい残響。籠りの原因だった低いカットオフを引き上げる"""
    g = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.linspace(0, seconds, n)
    ir = g.normal(0, 1, n) * np.exp(-t * (4.2 / seconds))
    ir = lp(ir, 5200)                    # v4は2600でここが暗さの主因
    ir = hp(ir, 120)                     # 低域の濁りを削って見通しを良くする
    ir = np.concatenate([np.zeros(int(0.04 * SR)), ir])
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-12)


IR_L, IR_R = make_ir(seed=101), make_ir(seed=202)


def reverb(x, wet=0.62):
    l = fftconvolve(x, IR_L)[: len(x)]
    r = fftconvolve(x, IR_R)[: len(x)]
    return (1 - wet) * x + wet * l, (1 - wet) * x + wet * r


def delay_fx(x, t=DELAY_TIME, fb=0.38, wet=0.26):
    d = int(t * SR)
    out = x.copy()
    for k in range(1, 5):
        sh = d * k
        if sh >= len(x):
            break
        out[sh:] += wet * (fb ** (k - 1)) * lp(x[: len(x) - sh], 3600)
    return out


def bitcrush(x, p):
    """劣化は音色変化としてのみ効かせる。ドロップアウトは安らかさを壊すので使わない"""
    if p <= 0:
        return x
    bits = max(4, 16 - round(10 * p))
    lv = 2 ** bits
    return np.round(x * (lv / 2)) / (lv / 2)


def smooth_ramp(values, n_total, n_block):
    """ブロックごとの目標値を、切れ目なく補間した連続カーブへ展開する"""
    idx = np.arange(n_total) / n_block
    i0 = np.clip(idx.astype(int), 0, len(values) - 1)
    i1 = np.clip(i0 + 1, 0, len(values) - 1)
    fr = idx - i0
    fr = fr * fr * (3 - 2 * fr)          # smoothstep: 折れ線の角を消す
    return values[i0] * (1 - fr) + values[i1] * fr


# ---- データ ----
buf = b""
for fp in sorted(glob.glob("../research/**/*.md", recursive=True)):
    with open(fp, "rb") as fh:
        buf += fh.read()
    if len(buf) > 500_000:
        break
d_data = np.frombuffer(buf, dtype=np.uint8)
r_data = rng.integers(0, 256, 500_000, dtype=np.uint8)

DUR = 48.0
n_blocks = min(int(DUR / BLOCK_TIME), len(d_data) // BLOCK_BYTES)
n_block_smp = int(BLOCK_TIME * SR)
total_n = n_blocks * n_block_smp

# ブロックごとの統計量(=鳴り続ける音のパラメータ目標値。発音トリガーではない)
Hs, means, bts = [], [], []
for i in range(n_blocks):
    bd = d_data[i * BLOCK_BYTES:(i + 1) * BLOCK_BYTES]
    Hs.append(shannon_entropy(bd))
    means.append(float(bd.mean()))
    bts.append(bit_transition_density(bd))
Hs, means, bts = np.array(Hs), np.array(means), np.array(bts)

print(f"f_cycle={F_CYCLE:.1f}Hz block={BLOCK_TIME*1000:.1f}ms blocks={n_blocks}")
print("純正律レイヤー(回路クロックの整数分周):")
for dv, g in zip(DIVISORS, LAYER_GAIN):
    print(f"  f_cycle/{dv:<3d} = {F_CYCLE/dv:7.2f} Hz  gain={g}")
print(f"H(d) = {Hs.min():.2f} - {Hs.max():.2f}\n")

t = np.linspace(0, total_n / SR, total_n, endpoint=False)

# 記憶データの連続カーブ(すべて滑らかに補間され、アタックを持たない)
H_curve = smooth_ramp(Hs, total_n, n_block_smp)
m_curve = smooth_ramp(means, total_n, n_block_smp)
bt_curve = smooth_ramp(bts, total_n, n_block_smp)
purity = np.clip((H_curve - 5.0) / 1.6, 0, 1)      # 記憶の「純度」

# ---- 1. 純正律のドローン床(装置自身の身体) ----
bed = np.zeros(total_n)
vib = (1.0 + 0.0030 * np.sin(2 * np.pi * 0.043 * t)
       + 0.0018 * np.sin(2 * np.pi * 0.017 * t + 2.1))
detune = 1.0 / (1.0 + rng.normal(0, CAP_TOLERANCE, N_HALFCELLS))
for dv, gain in zip(DIVISORS, LAYER_GAIN):
    f0 = F_CYCLE / dv
    # 高いレイヤーほど記憶の純度で開く = 明るさが記憶に連動する
    lift = 1.0 if dv >= 24 else (0.35 + 0.65 * purity)
    n_voice = 4 if dv >= 24 else 3
    layer = np.zeros(total_n)
    for k in range(n_voice):
        ph = 2 * np.pi * f0 * detune[k] * np.cumsum(vib) / SR + rng.random() * 2 * np.pi
        layer += np.sin(ph)
    bed += gain * lift * layer / n_voice
bed /= (np.max(np.abs(bed)) + 1e-9)

# ---- 2. 記憶の声(連続グライド。ノーツではない) ----
# H(d)を音高へ写像するが、発音せず常時鳴り続ける1本の声として滑らかに動く
voice_f = (F_CYCLE / 16) * (2 ** ((H_curve - 6.0) / 4.0)) * (2 ** (((m_curve - 128) / 128) * 0.03))
vph = 2 * np.pi * np.cumsum(voice_f * vib) / SR
voice = np.sin(vph) + 0.30 * np.sin(2 * vph) + 0.12 * np.sin(3 * vph)
# フォルマントを高めに置き、暗くならないようにする
voice = 0.45 * voice + 0.55 * (0.6 * bp(voice, 620) + 0.4 * bp(voice, 1450))
voice *= (0.35 + 0.45 * purity)
voice = bitcrush(voice, 0.0)

# ---- 3. 上方のきらめき(安らかさのための空気感) ----
shimmer_f = (F_CYCLE / 8) * 2
sph = 2 * np.pi * shimmer_f * np.cumsum(vib) / SR
shimmer = np.sin(sph) * (0.10 + 0.16 * purity)
shimmer *= (0.55 + 0.45 * np.sin(2 * np.pi * 0.021 * t))   # ごくゆるやかな呼吸

# ---- 4. 乱数 r の連続テクスチャ(バーストではなく、ひとつづきの息) ----
idx = (np.arange(total_n) * len(r_data) // total_n).astype(int)
r_raw = (r_data[idx].astype(np.float64) - 127.5) / 127.5
r_tex = lp(hp(r_raw, 400), 3000)
r_tex /= (np.max(np.abs(r_tex)) + 1e-9)
# 消去が進むほど乱数の気配が増す(唯一の進行感)
r_env = 0.030 + 0.045 * np.linspace(0, 1, total_n)
r_tex = r_tex * r_env * (0.7 + 0.3 * np.sin(2 * np.pi * 0.013 * t))

# ---- ミックス ----
p_curve = 0.55 * np.linspace(0, 1, total_n)
wet = 0.55 * bed + 0.42 * voice + shimmer
wet = wet * (1 - 0.25 * p_curve) + bitcrush(wet, 0.55) * (0.25 * p_curve)
wet = delay_fx(wet)

L, Rr = reverb(wet, wet=0.62)
L = L + r_tex
Rr = Rr + r_tex * 0.92

# 全体のフェードイン(アタックを持たせない)と、NTC冷却時定数に同期した減衰
fade_in = int(3.5 * SR)
env = np.ones(total_n)
env[:fade_in] = np.linspace(0, 1, fade_in) ** 1.6
tail = int(9.0 * SR)
env[-tail:] *= np.exp(-np.linspace(0, 9.0, tail) / NTC_TAU)
L *= env
Rr *= env

st = np.stack([L, Rr], axis=1)
st = st / (np.max(np.abs(st)) + 1e-9) * 0.88


def an(s, lab):
    rms = np.sqrt(np.mean(s ** 2))
    pk = np.max(np.abs(s)) + 1e-12
    sp = np.abs(np.fft.rfft(s * np.hanning(len(s))))
    fr = np.fft.rfftfreq(len(s), 1 / SR)
    print(f"  {lab:<18s} RMS={rms:.4f} crest={20*np.log10(pk/rms):5.1f}dB "
          f"centroid={np.sum(fr*sp)/np.sum(sp):7.1f}Hz")


print("=== 音響解析 ===")
an(bed, "純正律ドローン床")
an(voice, "記憶の声(連続)")
an(r_tex, "乱数テクスチャ")
an(L, "最終 L")
an(Rr, "最終 R")
print(f"  L/R相関 = {float(np.corrcoef(L, Rr)[0,1]):.3f}")
print(f"  声の音高 {voice_f.min():.1f}-{voice_f.max():.1f}Hz "
      f"({12*math.log2(voice_f.max()/voice_f.min()):.2f}半音、連続グライド)")

wavfile.write("erasure_sonification_v5.wav", SR, (st * 32767).astype(np.int16))
print(f"\n書き出し: erasure_sonification_v5.wav 総尺={total_n/SR:.1f}s ステレオ")
