"""
忘却炉 聴覚演出プロトタイプ v2 — 実データ駆動版

v1(erasure_sonification_prototype.py)の欠陥:
    グレインの音高をブロックの「平均バイト値」から導出していたが、テストデータに
    疑似乱数を使っていたため、中心極限定理により4096byteブロックの平均値は
    ほぼ128に張り付き(std=1.3)、全グレインが同じ音高になっていた。
    「一定間隔で鳴る同じ音」はこれが原因。

v2の変更:
    (1) 音高の主軸を平均バイト値からブロックのシャノンエントロピーに変更
        (FR-02で既に算出している量。実データでのダイナミックレンジが桁違いに広い)
    (2) テストデータをボールト内の実際の日本語markdown(=消去される記憶)に変更
    (3) 比較用に、同じエンジンへ乱数を流した区間を末尾に置き、差を可聴化

出力: erasure_sonification_v2.wav
    A (0-12s)  実データ・セッション前半 (劣化 p: 0.00->0.30)
    B (13-25s) 実データ・セッション終盤 (劣化 p: 0.70->1.00)
    C (26-38s) 乱数データ (v1と同じ条件。単調さの比較用)
    全区間を通してドローン(f_cycle/16)が鳴り、Cの末尾でNTC冷却時定数に同期して減衰
"""
import numpy as np, glob, math
from scipy.io import wavfile

SR = 44100
R, C_CAP = 117.0, 71e-9
TAU = R * C_CAP
CYCLE_TIME = 16 * TAU
F_CYCLE = 1.0 / CYCLE_TIME          # ~7523.8 Hz
F_DRONE = F_CYCLE / 16              # ~470.24 Hz
BLOCK_BYTES = 4096
BLOCK_TIME = BLOCK_BYTES / F_CYCLE  # ~0.5444 s
NTC_TAU = 8.0                       # 接触プレート冷却時定数の仮値(秒)

def shannon_entropy(b):
    c = np.bincount(b, minlength=256); p = c[c > 0] / len(b)
    return float(-np.sum(p * np.log2(p)))

def bit_transition_density(b):
    x = np.bitwise_xor(b[:-1], b[1:])
    return float(np.mean([bin(v).count('1') for v in x]))

def rc_shape(n, tau_ratio=0.28):
    t = np.linspace(0, 1, n, endpoint=False); half = n // 2
    ch = 1 - np.exp(-t[:half] / (tau_ratio * 0.5))
    di = np.exp(-t[:n - half] / (tau_ratio * 0.5))
    return np.concatenate([ch / ch.max(), -di / di.max()])

def render_drone(dur, amp=0.14):
    n = int(dur * SR); per = max(4, int(round(SR / F_DRONE)))
    reps = int(np.ceil(n / per))
    w = np.tile(rc_shape(per), reps)[:n]
    w2 = np.tile(rc_shape(max(4, per // 2)), reps * 2)[:n]
    raw = 0.85 * w + 0.15 * w2
    # v1でクレストファクタ4.2dBと硬すぎた反省。1次ローパスで角を丸める
    a = 0.12; out = np.empty_like(raw); acc = 0.0
    for i, v in enumerate(raw):
        acc += a * (v - acc); out[i] = acc
    return amp * out / (np.max(np.abs(out)) + 1e-9)

def degrade(sig, p, seed):
    if p <= 0: return sig.copy()
    g = np.random.default_rng(seed)
    bits = max(2, 16 - round(13 * p)); lv = 2 ** bits
    cr = np.round(sig * (lv / 2)) / (lv / 2)
    mask = g.random(len(sig)) < 0.22 * p
    out = np.empty_like(cr); last = 0.0
    for i in range(len(cr)):
        if mask[i]: out[i] = last
        else: out[i] = cr[i]; last = cr[i]
    return out

def render_grain(dur, pitch, bright, p, seed):
    n = int(dur * SR); t = np.linspace(0, dur, n, endpoint=False)
    env = np.exp(-t / (dur * 0.22))
    tone = np.sin(2*np.pi*pitch*t) + bright*np.sin(2*np.pi*pitch*2*t) \
         + (bright**2)*0.4*np.sin(2*np.pi*pitch*3*t)
    tone *= env; tone /= (np.max(np.abs(tone)) + 1e-9)
    return 0.5 * degrade(tone, p, seed) * env

def map_block(blk):
    """ブロック -> 音響パラメータ。導出後にブロックは破棄する(ノーバッファ制約)"""
    H = shannon_entropy(blk)                      # 0..8 bits/byte
    m = float(blk.mean())                         # 0..255
    bt = bit_transition_density(blk)              # 0..8
    pitch = F_DRONE * (2 ** ((H - 6.0) / 3.0))    # 主軸: エントロピー
    pitch *= 2 ** (((m - 128) / 128) * 0.04)      # 微細デチューン(±~50cent)
    bright = float(np.clip(bt / 4.0, 0.0, 1.2))   # 倍音量
    return pitch, bright, H, m, bt

def render_section(data, p0, p1, dur, label, seed0):
    n_blocks = min(int(dur / BLOCK_TIME), len(data) // BLOCK_BYTES)
    chunks, pitches, Hs = [], [], []
    for i in range(n_blocks):
        blk = data[i*BLOCK_BYTES:(i+1)*BLOCK_BYTES]
        pitch, bright, H, m, bt = map_block(blk)
        p = p0 + (p1 - p0) * (i / max(1, n_blocks - 1))
        glen = BLOCK_TIME * 0.85
        chunks.append(render_grain(glen, pitch, bright, p, seed0 + i))
        chunks.append(np.zeros(int((BLOCK_TIME - glen) * SR)))
        pitches.append(pitch); Hs.append(H)
    sig = np.concatenate(chunks)
    pa, ha = np.array(pitches), np.array(Hs)
    semitone_span = 12*math.log2(pa.max()/pa.min()) if pa.min() > 0 else 0
    print(f"[{label}] blocks={n_blocks} dur={len(sig)/SR:.1f}s  "
          f"entropy {ha.min():.2f}-{ha.max():.2f}  "
          f"pitch {pa.min():.1f}-{pa.max():.1f}Hz (音程幅 {semitone_span:.2f}半音)")
    return sig, semitone_span

# ---- データ準備 ----
buf = b""
for f in sorted(glob.glob("../research/**/*.md", recursive=True)):
    with open(f, "rb") as fh: buf += fh.read()
    if len(buf) > 400_000: break
real = np.frombuffer(buf, dtype=np.uint8)
rand = np.random.default_rng(20260817).integers(0, 256, 400_000, dtype=np.uint8)

print(f"f_cycle={F_CYCLE:.1f}Hz  f_drone={F_DRONE:.2f}Hz  "
      f"block={BLOCK_BYTES}B ({BLOCK_TIME*1000:.1f}ms, {1/BLOCK_TIME:.2f}Hz)")
print(f"実データ {len(real)}B / 乱数 {len(rand)}B\n")

secA, spanA = render_section(real, 0.00, 0.30, 12.0, "A 実データ・前半", 1000)
secB, spanB = render_section(real[len(real)//2:], 0.70, 1.00, 12.0, "B 実データ・終盤", 2000)
secC, spanC = render_section(rand, 0.00, 0.30, 12.0, "C 乱数(v1相当)", 3000)

gap = np.zeros(int(1.0 * SR))
grains = np.concatenate([secA, gap, secB, gap, secC])
drone = render_drone(len(grains) / SR)
n_common = min(len(drone), len(grains))
drone, grains = drone[:n_common], grains[:n_common]
# 末尾: NTC冷却時定数に同期してドローンを減衰(フロー⑧に対応)
tail_n = int(6.0 * SR); t_tail = np.linspace(0, 6.0, tail_n)
env = np.ones(len(drone)); env[-tail_n:] = np.exp(-t_tail / NTC_TAU)
full = drone * env + grains
full = full / (np.max(np.abs(full)) + 1e-9) * 0.92

def analyze(s, lab):
    rms = np.sqrt(np.mean(s**2)); pk = np.max(np.abs(s)) + 1e-12
    sp = np.abs(np.fft.rfft(s * np.hanning(len(s))))
    fr = np.fft.rfftfreq(len(s), 1/SR)
    print(f"  {lab:<22s} RMS={rms:.4f} crest={20*np.log10(pk/(rms+1e-12)):5.1f}dB "
          f"centroid={np.sum(fr*sp)/(np.sum(sp)+1e-12):7.1f}Hz")

print("\n=== 音響解析 ===")
analyze(secA, "A 実データ前半"); analyze(secB, "B 実データ終盤")
analyze(secC, "C 乱数"); analyze(drone, "ドローン単体(v2)")

wavfile.write("erasure_sonification_v2.wav", SR, (full*32767).astype(np.int16))
print(f"\n書き出し: erasure_sonification_v2.wav  総尺={len(full)/SR:.1f}s")
print(f"音程幅の比較: 実データ {spanA:.2f}半音 vs 乱数 {spanC:.2f}半音")
