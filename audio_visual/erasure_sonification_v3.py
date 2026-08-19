"""
忘却炉 聴覚演出プロトタイプ v3 — d(記憶)とr(乱数)の対提示版

v2までの構造的な欠落:
    グレインは投入相の記憶データ d の統計量だけから作られており、乱数 r は
    一切음になっていなかった。しかし architecture.md 4.6節によれば、
    真のランダウア消去(Q>=kT ln2 の支払いが無条件に強制される唯一の段階)は
    r を放電する「鎮静相」である。つまり v2 の音は、この作品が主張する
    熱力学的な核心の瞬間を鳴らしていなかった。

v3の変更:
    1ブロックにつき「音高を持つグレイン(=d、構造を持つ記憶)」と
    「無音高のノイズバースト(=r、最大エントロピーの乱数)」を対にして鳴らす。
    記憶が乱数に置き換わるという4相サイクルの意味を、ブロック尺度で可聴化する。

出力: erasure_sonification_v3.wav
"""
import numpy as np, glob, math
from scipy.io import wavfile

SR = 44100
R, C_CAP = 117.0, 71e-9
TAU = R * C_CAP
F_CYCLE = 1.0 / (16 * TAU)
F_DRONE = F_CYCLE / 16
BLOCK_BYTES = 4096
BLOCK_TIME = BLOCK_BYTES / F_CYCLE
NTC_TAU = 8.0

def shannon_entropy(b):
    c = np.bincount(b, minlength=256); p = c[c > 0] / len(b)
    return float(-np.sum(p * np.log2(p)))

def bit_transition_density(b):
    x = np.bitwise_xor(b[:-1], b[1:])
    return float(np.mean([bin(v).count('1') for v in x]))

def rc_shape(n, tr=0.28):
    t = np.linspace(0, 1, n, endpoint=False); h = n // 2
    ch = 1 - np.exp(-t[:h] / (tr * 0.5)); di = np.exp(-t[:n - h] / (tr * 0.5))
    return np.concatenate([ch / ch.max(), -di / di.max()])

def lowpass(x, a=0.12):
    out = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); out[i] = acc
    return out

def render_drone(dur, amp=0.13):
    n = int(dur * SR); per = max(4, int(round(SR / F_DRONE)))
    reps = int(np.ceil(n / per))
    raw = 0.85*np.tile(rc_shape(per), reps)[:n] + 0.15*np.tile(rc_shape(max(4,per//2)), reps*2)[:n]
    o = lowpass(raw)
    return amp * o / (np.max(np.abs(o)) + 1e-9)

def degrade(sig, p, seed):
    if p <= 0: return sig.copy()
    g = np.random.default_rng(seed)
    bits = max(2, 16 - round(13 * p)); lv = 2 ** bits
    cr = np.round(sig * (lv/2)) / (lv/2)
    mask = g.random(len(sig)) < 0.22 * p
    out = np.empty_like(cr); last = 0.0
    for i in range(len(cr)):
        if mask[i]: out[i] = last
        else: out[i] = cr[i]; last = cr[i]
    return out

def grain_d(dur, pitch, bright, p, seed):
    """投入相: 記憶データ d。音高を持ち、旋律になる"""
    n = int(dur*SR); t = np.linspace(0, dur, n, endpoint=False)
    env = np.exp(-t / (dur * 0.22))
    tone = np.sin(2*np.pi*pitch*t) + bright*np.sin(2*np.pi*pitch*2*t) \
         + (bright**2)*0.4*np.sin(2*np.pi*pitch*3*t)
    tone = tone*env; tone /= (np.max(np.abs(tone))+1e-9)
    return 0.5 * degrade(tone, p, seed) * env

def burst_r(dur, r_block, amp=0.30):
    """鎮静相: 乱数 r。最大エントロピーゆえ音高を持てず、必ず無旋律になる。
    r_block の実バイト列をそのまま波形サンプルへ写像する(合成ではなく実データ)"""
    n = int(dur*SR)
    idx = (np.arange(n) * len(r_block) // n).astype(int)
    raw = (r_block[idx].astype(np.float64) - 127.5) / 127.5
    t = np.linspace(0, dur, n, endpoint=False)
    env = np.exp(-t / (dur*0.30)) * (1 - np.exp(-t / (dur*0.06)))
    return amp * lowpass(raw, a=0.35) * env

def map_block(blk):
    H = shannon_entropy(blk); m = float(blk.mean()); bt = bit_transition_density(blk)
    pitch = F_DRONE * (2 ** ((H - 6.0)/3.0)) * (2 ** (((m-128)/128)*0.04))
    return pitch, float(np.clip(bt/4.0, 0, 1.2)), H

def render(data_d, data_r, p0, p1, dur, label, seed0, pair=True):
    nb = min(int(dur/BLOCK_TIME), len(data_d)//BLOCK_BYTES, len(data_r)//BLOCK_BYTES)
    chunks, Hs, pitches = [], [], []
    for i in range(nb):
        bd = data_d[i*BLOCK_BYTES:(i+1)*BLOCK_BYTES]
        br = data_r[i*BLOCK_BYTES:(i+1)*BLOCK_BYTES]
        pitch, bright, H = map_block(bd)
        p = p0 + (p1-p0)*(i/max(1, nb-1))
        seg = np.zeros(int(BLOCK_TIME*SR))
        # 前半: d のグレイン / 後半: r のバースト(pair=Falseなら d のみ)
        gd = grain_d(BLOCK_TIME*0.42, pitch, bright, p, seed0+i)
        seg[:len(gd)] += gd
        if pair:
            off = int(BLOCK_TIME*0.46*SR)
            bo = burst_r(BLOCK_TIME*0.40, br)
            seg[off:off+len(bo)] += bo[:len(seg)-off]
        chunks.append(seg); Hs.append(H); pitches.append(pitch)
    sig = np.concatenate(chunks); pa = np.array(pitches)
    span = 12*math.log2(pa.max()/pa.min()) if pa.min()>0 else 0
    print(f"[{label}] blocks={nb} dur={len(sig)/SR:.1f}s "
          f"H(d)={min(Hs):.2f}-{max(Hs):.2f} 音程幅={span:.2f}半音")
    return sig

buf = b""
for f in sorted(glob.glob("../research/**/*.md", recursive=True)):
    with open(f, "rb") as fh: buf += fh.read()
    if len(buf) > 400_000: break
d_data = np.frombuffer(buf, dtype=np.uint8)
r_data = np.random.default_rng(31415).integers(0, 256, 400_000, dtype=np.uint8)

print(f"f_drone={F_DRONE:.2f}Hz block={BLOCK_BYTES}B ({BLOCK_TIME*1000:.1f}ms)")
print(f"H(r) = {shannon_entropy(r_data[:BLOCK_BYTES]):.3f} bits/byte  <- 乱数は常にほぼ8\n")

A = render(d_data, r_data, 0.0, 0.25, 11.0, "A v2相当: dのみ",      1000, pair=False)
B = render(d_data, r_data, 0.0, 0.25, 11.0, "B v3: d+r 対提示・前半", 2000, pair=True)
Cs= render(d_data[len(d_data)//2:], r_data, 0.75, 1.0, 11.0, "C v3: d+r 対提示・終盤", 3000, pair=True)

gap = np.zeros(int(SR))
grains = np.concatenate([A, gap, B, gap, Cs])
drone = render_drone(len(grains)/SR)
n = min(len(drone), len(grains)); drone, grains = drone[:n], grains[:n]
tail = int(6*SR); env = np.ones(n); env[-tail:] = np.exp(-np.linspace(0,6,tail)/NTC_TAU)
full = drone*env + grains
full = full/(np.max(np.abs(full))+1e-9)*0.92

def an(s, lab):
    rms = np.sqrt(np.mean(s**2)); pk = np.max(np.abs(s))+1e-12
    sp = np.abs(np.fft.rfft(s*np.hanning(len(s)))); fr = np.fft.rfftfreq(len(s),1/SR)
    print(f"  {lab:<24s} RMS={rms:.4f} crest={20*np.log10(pk/rms):5.1f}dB "
          f"centroid={np.sum(fr*sp)/np.sum(sp):7.1f}Hz")
print("\n=== 音響解析 ===")
an(A,"A dのみ"); an(B,"B d+r 前半"); an(Cs,"C d+r 終盤")
wavfile.write("erasure_sonification_v3.wav", SR, (full*32767).astype(np.int16))
print(f"\n書き出し: erasure_sonification_v3.wav 総尺={len(full)/SR:.1f}s")
