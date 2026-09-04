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

出力: erasure_v5_stem_*.wav (背景共通のステム5本、ステレオ)
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

# ---- ステム書き出し ----
# 背景(純正律ドローン床)は一度だけ合成し、全ファイルで同一の配列を使い回す。
# 正規化係数も全ミックス共通のスカラー1個を使うため、背景の絶対音量まで一致する。
# v5本編は層を足してから劣化(bitcrush)を掛けていたが、ここでは層ごとに個別へ掛ける。
# bitcrushは非線形なので、ステムの単純和はv5本編と厳密には一致しない(下で誤差を表示)。
p_curve = 0.55 * np.linspace(0, 1, total_n)


def chain(x):
    """v5と同じ後段(劣化ブレンド→ディレイ→残響)を、層ごとに個別に通す"""
    y = x * (1 - 0.25 * p_curve) + bitcrush(x, 0.55) * (0.25 * p_curve)
    y = delay_fx(y)
    return reverb(y, wet=0.62)


bed_L, bed_R = chain(0.55 * bed)          # 背景: 純正律ドローン床
voi_L, voi_R = chain(0.42 * voice)        # 記憶の声(連続グライド)
shm_L, shm_R = chain(shimmer)             # きらめき
rnd_L, rnd_R = r_tex, r_tex * 0.92        # 乱数テクスチャ(残響を通さずドライ)

fade_in = int(3.5 * SR)
env = np.ones(total_n)
env[:fade_in] = np.linspace(0, 1, fade_in) ** 1.6
tail = int(9.0 * SR)
env[-tail:] *= np.exp(-np.linspace(0, 9.0, tail) / NTC_TAU)

BED = (bed_L, bed_R)
VOICE = (voi_L, voi_R)
SHIMMER = (shm_L, shm_R)
RANDOM = (rnd_L, rnd_R)


def mix(parts):
    L = np.zeros(total_n)
    R = np.zeros(total_n)
    for pl, pr in parts:
        L = L + pl
        R = R + pr
    return L * env, R * env


# 正規化係数は全部入りのピークから1回だけ決め、全ステムへ同じ値を適用する
full_L, full_R = mix([BED, VOICE, SHIMMER, RANDOM])
GAIN = 0.88 / (max(np.max(np.abs(full_L)), np.max(np.abs(full_R))) + 1e-9)

STEMS = [
    ("erasure_v5_stem_0_全部.wav", [BED, VOICE, SHIMMER, RANDOM]),
    ("erasure_v5_stem_1_背景のみ.wav", [BED]),
    ("erasure_v5_stem_2_背景と記憶の声.wav", [BED, VOICE]),
    ("erasure_v5_stem_3_背景ときらめき.wav", [BED, SHIMMER]),
    ("erasure_v5_stem_4_背景と乱数テクスチャ.wav", [BED, RANDOM]),
]

print("\n=== ステム書き出し(背景は全ファイル共通・正規化係数も共通) ===")
written = {}
for fname, parts in STEMS:
    L, R = mix(parts)
    st = np.stack([L, R], axis=1) * GAIN
    data = (np.clip(st, -1.0, 1.0) * 32767).astype(np.int16)
    wavfile.write(fname, SR, data)
    written[fname] = data
    rms = np.sqrt(np.mean((st ** 2)))
    print(f"  {fname:<42s} peak={np.max(np.abs(st)):.3f} RMS={rms:.4f}")

# 背景が全ファイルで同一であることの検証:
# 「背景と記憶の声」から「背景のみ」を引いた差が、記憶の声だけの寄与と一致するか
diff = (written["erasure_v5_stem_2_背景と記憶の声.wav"].astype(np.float64)
        - written["erasure_v5_stem_1_背景のみ.wav"].astype(np.float64))
expect = np.stack([voi_L * env, voi_R * env], axis=1) * GAIN * 32767
print(f"\n背景の同一性検証: 差分と記憶の声単体の最大偏差 = "
      f"{np.max(np.abs(diff - expect)):.2f} LSB (int16量子化のみなら1未満)")

# v5本編と同じ順序(層を足し合わせてから劣化を掛ける)で作った参照ミックスとの差。
# bitcrushが非線形なので、層ごとに劣化を掛ける本スクリプトとは厳密には一致しない。
wet_ref = 0.55 * bed + 0.42 * voice + shimmer
wet_ref = wet_ref * (1 - 0.25 * p_curve) + bitcrush(wet_ref, 0.55) * (0.25 * p_curve)
wet_ref = delay_fx(wet_ref)
ref_l, ref_r = reverb(wet_ref, wet=0.62)
ref = np.stack([(ref_l + r_tex) * env, (ref_r + r_tex * 0.92) * env], axis=1) * GAIN
cur = np.stack([full_L, full_R], axis=1) * GAIN
print(f"v5本編(層を足してから劣化)との差: 最大 {np.max(np.abs(ref - cur)):.5f} / "
      f"RMS {np.sqrt(np.mean((ref - cur) ** 2)):.6f} (フルスケール1.0に対して)")
print(f"総尺={total_n/SR:.1f}s ステレオ {len(STEMS)}ファイル")
