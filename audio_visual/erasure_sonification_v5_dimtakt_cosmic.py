"""参照(furnace-20260826-204246)の実測構造へ寄せて宇宙感を強める。

実測で判明した参照の構造:
  低域20-200Hz=46.8% / 中高800-3k=1.4% / 8k超=0.056% / 立上り鋭さ0.034
自作(dimtakt)は 11.3% / 40.1% / 0.000% / 0.080 で、低域不足・中域過多・空気皆無。

対処:
  1. サブドローンを追加。f_cycle/128, /192, /256 という整数分周の続き
     (既存の/64..8と同じ原理。オクターブ関係なので純正律のまま)
  2. 800-3kHzを掘る。中域を空洞にすると「遠さ」が出る
  3. 残響IRの上限を5.6k -> 14kHzへ開き、8k超の空気を作る
  4. ピンのアタックを28ms -> 75msへさらに鈍らせる
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve, stft

SR = 44100
R, C_CAP = 117.0, 71e-9
F_CYCLE = 1.0 / (16 * R * C_CAP)
BLOCK_TIME = 4096 / F_CYCLE
DIVISORS = [64, 48, 32, 24, 16, 12, 8]
SUB_DIVISORS = [256, 192, 128]           # 整数分周の続き = 宇宙的な土台
CAP_TOL = 0.0075
SRC = "erasure_v5_stem_2to4_各5秒連結.wav"

sr, base = wavfile.read(SRC)
base = base.astype(np.float64) / 32768.0
n = len(base); dur = n / SR
rng = np.random.default_rng(1618)
t = np.arange(n) / SR


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


def scoop(x, centers=((1020, 1.9), (2350, 1.25)), amt=0.70):
    """中高域を掘って空洞を作る。遠さ=宇宙感の中核"""
    y = x.copy()
    for fc, q in centers:
        y = y - amt*bp(x, fc, q)
    return y


# ---- 1. サブドローン(整数分周の続き・ドライ) ----
vib = 1.0 + 0.0026*np.sin(2*np.pi*0.037*t) + 0.0015*np.sin(2*np.pi*0.013*t+1.7)
sub = np.zeros(n)
for div, g in zip(SUB_DIVISORS, [0.30, 0.42, 1.00]):
    f0 = F_CYCLE/div
    for k in range(3):
        det = 1.0/(1.0+rng.normal(0, CAP_TOL))
        ph = 2*np.pi*f0*det*np.cumsum(vib)/SR + rng.random()*2*np.pi
        sub += g*(np.sin(ph) + 0.16*np.sin(2*ph))/3
sub = lp(sub, 240)
sub *= 0.55 + 0.45*np.sin(2*np.pi*0.019*t)      # ごく緩い呼吸
sub /= (np.max(np.abs(sub))+1e-9)

# ---- 2. ピン(アタックをさらに鈍らせ、フォルマントを弱める) ----
def ping(f0, seconds=3.2):
    ln = int(seconds*SR); tt = np.arange(ln)/SR
    glide = 2**((30.0*np.exp(-tt/0.5))/1200.0)
    x = np.zeros(ln)
    for cents in (-19., 0., +17.):
        f = f0*(2**(cents/1200.))*glide
        ph = 2*np.pi*np.cumsum(f)/SR + rng.random()*2*np.pi
        x += np.sin(ph) + 0.14*np.sin(2*ph) + 0.04*np.sin(3*ph)
    x /= 3.0
    x = 0.55*x + 0.45*(0.6*bp(x, 620) + 0.4*bp(x, 1450))    # フォルマントを控えめに
    atk = int(0.105*SR)                                      # 75ms アタック
    env = np.exp(-tt/1.15)
    env[:atk] *= 0.5*(1-np.cos(np.linspace(0, np.pi, atk)))
    return x*env


SPARK_DIV = [4, 3, 2, 1]        # 1881, 2508, 3762, 7524 Hz (f_cycle/1 は実スイッチング周波数そのもの)


def sparkle(f0, seconds=0.85):
    """点描的スパークル: 判断5が dimtakt から引いた質感。連続ノイズでは代替できない"""
    ln = int(seconds * SR); tt = np.arange(ln) / SR
    ph = 2 * np.pi * f0 * tt
    e = np.exp(-tt / 0.19)
    atk = int(0.014 * SR)
    e[:atk] *= 0.5 * (1 - np.cos(np.linspace(0, np.pi, atk)))
    return (np.sin(ph) + 0.25 * np.sin(2 * ph)) * e

step = BLOCK_TIME*2
times = np.arange(0.4, dur, step)
bus = np.zeros(n)
spk = np.zeros(n)
for i, tt in enumerate(times):
    s = int(tt*SR)
    div = DIVISORS[int((i*0.6180339887)*len(DIVISORS)) % len(DIVISORS)]
    f0 = F_CYCLE/div
    if f0 < 200: f0 *= 2.0
    p = ping(f0); e = min(s+len(p), n)
    if s < n: bus[s:e] += 0.55*p[:e-s]
    if i % 2 == 1:                       # 点描的に間引く
        sf = F_CYCLE / SPARK_DIV[(i // 2) % len(SPARK_DIV)]
        sp = sparkle(sf); s2 = s + int(0.11*SR); e2 = min(s2+len(sp), n)
        if s2 < n: spk[s2:e2] += 0.10*sp[:e2-s2]

pl, pr = verb(bus)
pingL, pingR = 0.10*bus + 0.90*pl, 0.10*bus + 0.90*pr
sl_, sr2_ = verb(spk)
spkL, spkR = 0.30*spk + 0.70*sl_, 0.30*spk + 0.70*sr2_

# ---- 3. 空気(8k超)。参照が持っていて自作にゼロだった帯域 ----
air_n = rng.normal(0, 1, n)
air = hp(air_n, 4200)
air *= (0.5 + 0.5*np.sin(2*np.pi*0.023*t))*(0.6 + 0.4*np.sin(2*np.pi*0.0071*t+2.2))
air /= (np.max(np.abs(air))+1e-9)
al, ar = verb(air*0.5)

# ---- 4. ミックス(中高域を掘る) ----
bl = scoop(base[:, 0]); br = scoop(base[:, 1])
wl, wr = verb(base.mean(1))

out = np.empty_like(base)
out[:, 0] = bl + 0.30*pingL + 0.30*sub + 0.008*air + 0.020*al + 0.55*spkL + 0.23*wl
out[:, 1] = br + 0.30*pingR + 0.30*sub + 0.0078*air + 0.020*ar + 0.55*spkR + 0.23*wr

f_in = int(0.05*SR); out[:f_in] *= np.linspace(0, 1, f_in)[:, None]
tail = int(0.8*SR); out[-tail:] *= np.linspace(1, 0, tail)[:, None]
pk = np.max(np.abs(out))
if pk > 0.95: out *= 0.95/pk

fn = "erasure_v5_stem_2to4_各5秒連結_dimtakt_宇宙2.wav"
wavfile.write(fn, SR, (np.clip(out, -1, 1)*32767).astype(np.int16))


def metrics(d):
    m = d.mean(1); N = len(m)
    S = np.abs(np.fft.rfft(m*np.hanning(N))); fr = np.fft.rfftfreq(N, 1/SR)
    tot = np.sum(S**2); band = lambda a, b: np.sum(S[(fr >= a) & (fr < b)]**2)/tot*100
    f, tt, Z = stft(m, SR, nperseg=4096, noverlap=3072)
    env = np.sqrt(np.mean(np.abs(Z)**2, 0)); de = np.diff(env)
    return (band(20, 200), band(200, 800), band(800, 3000), band(3000, 8000),
            band(8000, 22050), float(np.corrcoef(d[:, 0], d[:, 1])[0, 1]),
            float(np.mean(de[de > 0])/(np.mean(env)+1e-12)))

sr2, ref = wavfile.read("_ref_tmp.wav"); ref = ref.astype(np.float64)/32768.0
lab = ["低域20-200", "中低200-800", "中高800-3k", "高域3k-8k", "超高8k超", "LR相関", "立上り鋭さ"]
r, o, b = metrics(ref), metrics(out), metrics(base)
print(f"{'指標':<14s}{'参照':>10s}{'旧(dimtakt)':>13s}{'新(宇宙)':>11s}")
for i, L in enumerate(lab):
    print(f"{L:<14s}{r[i]:>10.3f}{b[i]:>13.3f}{o[i]:>11.3f}")
print(f"\n書き出し: {fn}  {dur:.1f}s  peak={pk:.3f}")
