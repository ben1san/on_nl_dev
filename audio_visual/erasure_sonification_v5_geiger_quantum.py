"""宇宙2へガイガーパートを重ねる。不規則さは量子乱数 r から取る。

判断2はポアソン過程を「実回路は決定論的タイミングだから」として却下した。
しかし装置内で唯一ほんとうに確率的なのは量子乱数 r であり、ガイガーカウンターが
放射性崩壊という量子的不確定性でクリックするのと同じ物理に属する。
そこで発火判定を r の実バイト列から取る。ポアソン過程の捏造ではなく、
実際に消去へ使う乱数そのものが鳴る。判断2の趣旨を保ったまま不規則さが得られる。

不穏さ対策(Edworthyの切迫感3条件を外す):
  アタック 0.08ms -> 3.5ms / 帯域 1.2-9kHz -> 回路分周の940・1254Hz共鳴
  ドライ -> 残響65%で遠景へ / 音高を純正律に乗せて協和させる
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve, stft

SR = 44100
R, C_CAP = 117.0, 71e-9
F_CYCLE = 1.0 / (16 * R * C_CAP)
BLOCK_TIME = 4096 / F_CYCLE
SUBDIV = 8                                  # ブロックを8分割して判定 = 512 byte ごと
STEP = BLOCK_TIME / SUBDIV                  # 68.05 ms
THRESH = 256 // SUBDIV                      # r < 32 で発火 -> 平均 1.837 Hz
SRC = "erasure_v5_stem_2to4_各5秒連結_dimtakt_宇宙2.wav"

sr, base = wavfile.read(SRC)
base = base.astype(np.float64) / 32768.0
n = len(base); dur = n / SR
rng = np.random.default_rng(1618)


def lp(x, fc, o=2):
    b, a = butter(o, min(fc/(SR/2), .99), btype="low"); return lfilter(b, a, x)
def hp(x, fc, o=2):
    b, a = butter(o, max(fc/(SR/2), 1e-4), btype="high"); return lfilter(b, a, x)
def bp(x, fc, q=6.0):
    bw = fc/q; lo = max(20., fc-bw/2)/(SR/2); hi = min(fc+bw/2, SR/2-100)/(SR/2)
    b, a = butter(2, [lo, hi], btype="band"); return lfilter(b, a, x)


def make_ir(seconds=9.0, seed=0, top=14000):
    g = np.random.default_rng(seed); ln = int(seconds*SR)
    tt = np.linspace(0, seconds, ln)
    ir = g.normal(0, 1, ln) * np.exp(-tt*(3.8/seconds))
    ir = hp(lp(ir, top), 90)
    ir = np.concatenate([np.zeros(int(0.06*SR)), ir])
    return ir/(np.sqrt(np.sum(ir**2))+1e-12)


IR_L, IR_R = make_ir(seed=101), make_ir(seed=202)
def verb(x): return fftconvolve(x, IR_L)[:n], fftconvolve(x, IR_R)[:n]


def click(amp_byte, seed):
    """GM管の放電。共鳴を回路分周(940.47/1253.96Hz)に乗せて協和させる"""
    g = np.random.default_rng(seed)
    ln = int(0.30*SR); tt = np.arange(ln)/SR
    atk = int(0.0035*SR)                     # 3.5ms: 噛みつかないが粒は立つ
    env = np.exp(-tt/0.028)
    env[:atk] *= 0.5*(1-np.cos(np.linspace(0, np.pi, atk)))
    x = g.normal(0, 1, ln)*env
    x = 0.62*bp(x, F_CYCLE/8, 3.0) + 0.38*bp(x, F_CYCLE/6, 4.0)
    tone = np.sin(2*np.pi*(F_CYCLE/8)*tt)*np.exp(-tt/0.055)
    x = x/(np.max(np.abs(x))+1e-12) + 0.22*tone
    return x*(0.55 + 0.45*(amp_byte/255.0))  # 振幅も実バイト値から


# --- r の実バイト列で発火判定(疑似乱数はQRNGの代替。v5と同じ扱い) ---
n_slots = int(dur/STEP)
r_bytes = rng.integers(0, 256, n_slots, dtype=np.uint8)
fire = np.where(r_bytes < THRESH)[0]

bus = np.zeros(n)
for k, idx in enumerate(fire):
    s = int(idx*STEP*SR)
    c = click(int(r_bytes[idx]), 4000+k)
    e = min(s+len(c), n)
    if s < n: bus[s:e] += c[:e-s]

gl, gr = verb(bus)
GAIN = 0.115
out = np.empty_like(base)
out[:, 0] = base[:, 0] + GAIN*(0.35*bus + 0.65*gl)     # 残響65% = 遠景
out[:, 1] = base[:, 1] + GAIN*(0.34*bus + 0.65*gr)

tail = int(0.8*SR); out[-tail:] *= np.linspace(1, 0, tail)[:, None]
pk = np.max(np.abs(out))
if pk > 0.95: out *= 0.95/pk
fn = "erasure_v5_stem_2to4_各5秒連結_dimtakt_宇宙2_ガイガー.wav"
wavfile.write(fn, SR, (np.clip(out, -1, 1)*32767).astype(np.int16))


def sharp(d):
    m = d.mean(1); f, t, Z = stft(m, SR, nperseg=4096, noverlap=3072)
    env = np.sqrt(np.mean(np.abs(Z)**2, 0)); de = np.diff(env)
    return float(np.mean(de[de > 0])/(np.mean(env)+1e-12))

iv = np.diff(fire*STEP)
print(f"{fn}")
print(f"  クリック {len(fire)}発 / 平均間隔 {np.mean(iv):.3f}s "
      f"標準偏差 {np.std(iv):.3f}s (理論 {1/1.837:.3f}s)")
print(f"  発火判定: {STEP*1000:.1f}ms ごとに r<{THRESH} (512 byte ごと・平均1.837Hz)")
print(f"  立上り鋭さ  宇宙2={sharp(base):.3f} -> ガイガー入り={sharp(out):.3f} "
      f"(旧ガイガー版=0.080 / 参照=0.034)")
print(f"  peak={pk:.3f}")
