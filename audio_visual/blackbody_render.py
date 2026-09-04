"""黒体放射の色をプランクの法則から実際に計算する。

enclosure_design.md 3節「色は黒体放射スペクトルに沿わせる。低強度時は暗い赤、
消去のピークで白〜青白へ遷移させ、比喩ではなく黒体放射の物理カーブをなぞる」を
実装可能な形にし、忘却炉の実温度域で何が起きるかを数値と画像で示す。

手順:
  プランクの法則で分光放射輝度 -> CIE1931等色関数で積分 -> XYZ -> sRGB
等色関数はWyman, Sloan & Shirley (2013) の多ローブガウス近似を使う
(CIEの数表を持たずに済み、可視域で十分な精度がある)。

出力:
  blackbody_locus.png     温度と色の対応(黒体軌跡)。忘却炉の実温度域を明示
  blackbody_mapping.png   宣言的な誇張マッピングの候補比較
"""
import numpy as np
from PIL import Image

# 物理定数(CODATA)
H, C, KB = 6.62607015e-34, 2.99792458e8, 1.380649e-23

LAM = np.arange(360e-9, 830e-9, 1e-9)      # 可視域 360-830nm


def planck(lam, T):
    """分光放射輝度 B_λ(T) [W/(m^2 sr m)]"""
    a = 2.0 * H * C ** 2 / lam ** 5
    x = H * C / (lam * KB * T)
    return a / np.expm1(np.clip(x, None, 700.0))


def _g(x, mu, s1, s2):
    s = np.where(x < mu, s1, s2)
    return np.exp(-0.5 * ((x - mu) / s) ** 2)


def cie_xyz_bar(lam_nm):
    """CIE1931等色関数の解析近似 (Wyman et al. 2013, multi-lobe)"""
    x = (1.056 * _g(lam_nm, 599.8, 37.9, 31.0)
         + 0.362 * _g(lam_nm, 442.0, 16.0, 26.7)
         - 0.065 * _g(lam_nm, 501.1, 20.4, 26.2))
    y = (0.821 * _g(lam_nm, 568.8, 46.9, 40.5)
         + 0.286 * _g(lam_nm, 530.9, 16.3, 31.1))
    z = (1.217 * _g(lam_nm, 437.0, 11.8, 36.0)
         + 0.681 * _g(lam_nm, 459.0, 26.0, 13.8))
    return x, y, z


XB, YB, ZB = cie_xyz_bar(LAM * 1e9)

# XYZ -> linear sRGB (IEC 61966-2-1, D65)
M = np.array([[3.2406, -1.5372, -0.4986],
              [-0.9689, 1.8758, 0.0415],
              [0.0557, -0.2040, 1.0570]])


def xyz_of(T):
    b = planck(LAM, T)
    return np.array([np.trapezoid(b * XB, LAM),
                     np.trapezoid(b * YB, LAM),
                     np.trapezoid(b * ZB, LAM)])


def srgb_of(T, normalize=True):
    """normalize=True で色度のみ(明るさを正規化)、False で絶対輝度のまま"""
    xyz = xyz_of(T)
    if normalize:
        if xyz[1] <= 0:
            return np.zeros(3), np.zeros(3)
        xyz = xyz / xyz[1]
    rgb = M @ xyz
    rgb = np.clip(rgb, 0, None)
    if normalize and rgb.max() > 0:
        rgb = rgb / rgb.max()
    lin = rgb.copy()
    srgb = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)
    return np.clip(srgb, 0, 1), lin


def visible_radiance(T):
    """可視域(380-780nm)の放射輝度を積分 [W/(m^2 sr)]"""
    m = (LAM >= 380e-9) & (LAM <= 780e-9)
    return float(np.trapezoid(planck(LAM[m], T), LAM[m]))


def hexstr(c):
    return "#%02X%02X%02X" % tuple(int(round(v * 255)) for v in c)


# ---- 1. 忘却炉の実温度域で何が起きるか ----
print("=== 忘却炉の実温度と黒体放射 ===")
print(f"{'対象':<26s}{'T[K]':>8s}{'ピーク波長':>12s}{'可視放射輝度':>16s}{'色(色度)':>10s}")
ref = visible_radiance(2000.0)
rows = [
    ("室温 25C (プレート初期)", 298.15),
    ("40C デューティ制御点", 313.15),
    ("42C ハードカット", 315.15),
    ("ドレイパー点(可視の下限)", 798.0),
    ("暗いアンバー", 1900.0),
    ("白熱電球", 2700.0),
    ("昼光 D65 相当", 6500.0),
]
for lab, T in rows:
    lam_max = 2.897771955e-3 / T
    v = visible_radiance(T)
    c, _ = srgb_of(T)
    print(f"{lab:<26s}{T:>8.1f}{lam_max*1e6:>10.2f}um{v:>16.3e}   {hexstr(c)}")

v42, v1900 = visible_radiance(315.15), visible_radiance(1900.0)
print(f"\n42C と 1900K の可視放射輝度比 = {v42/v1900:.3e}")
print(f"  つまり 42C は暗いアンバーの {v42/v1900:.1e} 倍しか可視光を出さない")
print(f"ドレイパー点 798K / 42C 315.15K = 絶対温度で {798/315.15:.2f} 倍")
print(f"D65 6500K / 42C 315.15K       = 絶対温度で {6500/315.15:.2f} 倍")

# ---- 2. 黒体軌跡の画像 ----
W, HGT = 1100, 260
img = np.zeros((HGT, W, 3))
Ts = np.geomspace(300, 12000, W)
for i, T in enumerate(Ts):
    c, _ = srgb_of(T)
    img[20:130, i] = c                                  # 色度(明るさ正規化)
for i, T in enumerate(Ts):                              # 絶対輝度(2000K基準)
    c, _ = srgb_of(T, normalize=False)
    s = visible_radiance(T) / ref
    img[150:240, i] = np.clip(c * min(s, 1.0) ** (1 / 2.4), 0, 1)
for T in (315.15, 798, 1900, 2700, 6500):               # 目盛
    i = int(np.searchsorted(Ts, T))
    if 0 <= i < W:
        img[10:20, max(0, i - 1):i + 2] = 1.0
        img[240:250, max(0, i - 1):i + 2] = 1.0
Image.fromarray((img * 255).astype(np.uint8)).save("blackbody_locus.png")

# ---- 3. 宣言的な誇張マッピングの候補 ----
T_PLATE = (298.15, 315.15)          # 実測される範囲(25C - 42C)
CANDS = [
    ("実物理(誇張なし)", 298.15, 315.15),
    ("x2.53 ドレイパー点まで", 755.0, 798.0),
    ("x6 暗赤〜アンバー", 1790.0, 1900.0),
    ("原案 暗赤→白〜青白", 1000.0, 6500.0),
]
bar = np.zeros((len(CANDS) * 60, 900, 3))
print("\n=== 宣言的マッピングの候補 ===")
for r, (lab, lo, hi) in enumerate(CANDS):
    for i in range(900):
        f = i / 899
        T = lo + (hi - lo) * f
        c, _ = srgb_of(T)
        s = min(visible_radiance(T) / ref, 1.0) ** (1 / 2.4)
        bar[r * 60:(r + 1) * 60, i] = np.clip(c * s, 0, 1)
    fac = ((lo + hi) / 2) / ((T_PLATE[0] + T_PLATE[1]) / 2)
    c_lo, c_hi = srgb_of(lo)[0], srgb_of(hi)[0]
    print(f"{lab:<22s} {lo:6.0f}K->{hi:6.0f}K  絶対温度で約{fac:5.2f}倍の誇張  "
          f"{hexstr(c_lo)} -> {hexstr(c_hi)}")
Image.fromarray((bar * 255).astype(np.uint8)).save("blackbody_mapping.png")
print("\n出力: blackbody_locus.png / blackbody_mapping.png")
