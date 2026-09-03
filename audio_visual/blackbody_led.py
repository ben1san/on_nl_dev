"""カラーマップを実際のLED駆動へ落とすための道具。

用途は設計の分岐で2つに分かれる。
  A) 色を固定する場合(視覚演出ノートの決定): 設計時に1回だけ使い、
     LEDの購入仕様(CCT・Duv・xy)を出す。実行時に色計算は存在しない。
  B) 温度連動にする場合(enclosure_design 3節の原案): 実行時LUTを作る。
     ただしPicoでプランク積分は回さず、ここで焼いたテーブルを埋め込む。
"""
import numpy as np
import blackbody_render as bb


def planck_xy(T):
    X, Y, Z = bb.xyz_of(T)
    s = X + Y + Z
    return X / s, Y / s


def xy_to_uv60(x, y):
    """CIE1960 uv (Duv算出に使う)"""
    d = -2 * x + 12 * y + 3
    return 4 * x / d, 6 * y / d


def cct_duv_from_xy(x, y):
    """買ったLEDのxyからCCTとDuvを出す。軌跡上ならDuv=0"""
    u, v = xy_to_uv60(x, y)
    Ts = np.geomspace(1000, 10000, 4000)
    uv = np.array([xy_to_uv60(*planck_xy(t)) for t in Ts])
    d = np.hypot(uv[:, 0] - u, uv[:, 1] - v)
    i = int(np.argmin(d))
    sign = 1.0 if v > uv[i, 1] else -1.0
    return Ts[i], sign * d[i]


# ---- A) 色を固定する場合: LEDの購入仕様を出す ----
print("=== A) 固定色の場合: 設計時に1回だけ使う ===")
for T in (1800, 1900, 2000):
    x, y = planck_xy(T)
    srgb, lin = bb.srgb_of(T)
    print(f"  {T}K  CIE xy=({x:.4f},{y:.4f})  Duv=0.0000  "
          f"sRGB={bb.hexstr(srgb)}  linearRGB=({lin[0]:.3f},{lin[1]:.3f},{lin[2]:.3f})")
print("  -> 発注仕様は sRGB値ではなく『CCT 1900K / Duv 0 / xy(0.55,0.41)』の形で書く")
print("  -> 実行時のカラーマップ参照は存在しない。LEDの品種選定と受入検査だけに使う")

# 受入検査の例: 買ったLEDの実測xyが軌跡に乗っているか
print("\n  受入検査の例(実測xyを入れてCCT/Duvを逆算):")
for name, xy in [("候補1 電球色LED", (0.5500, 0.4100)),
                 ("候補2 やや緑寄り", (0.5500, 0.4400)),
                 ("候補3 単色アンバー590nm", (0.5752, 0.4243))]:
    cct, duv = cct_duv_from_xy(*xy)
    ok = "軌跡上" if abs(duv) < 0.006 else "軌跡から外れる"
    print(f"    {name:<22s} CCT={cct:6.0f}K Duv={duv:+.4f}  {ok}")

# ---- B) 温度連動の場合: 実行時LUTを焼く ----
print("\n=== B) 温度連動の場合: LUTを焼いてファームに埋める ===")
T_LO, T_HI = 1638.0, 1900.0        # 宣言した誇張マッピング(会場で見える下限〜アンバー)
PLATE_LO, PLATE_HI = 25.0, 42.0    # 実測されるプレート温度
N = 256

lut_lin, lum = [], []
for i in range(N):
    f = i / (N - 1)
    T = T_LO + (T_HI - T_LO) * f
    _, lin = bb.srgb_of(T)                     # 色度(明るさ正規化済み)
    lut_lin.append(lin)
    lum.append(bb.visible_radiance(T))
lum = np.array(lum)
print(f"  マッピング: プレート{PLATE_LO}-{PLATE_HI}C -> {T_LO:.0f}-{T_HI:.0f}K "
      f"(絶対温度で約{((T_LO+T_HI)/2)/((273.15+(PLATE_LO+PLATE_HI)/2)):.1f}倍の誇張)")
print(f"  この区間の可視放射輝度の比 = {lum[-1]/lum[0]:.1f} : 1")
need_bits = int(np.ceil(np.log2(lum[-1] / lum[0] * 16)))
print(f"  -> 明るさを物理どおり動かすと{lum[-1]/lum[0]:.0f}倍のダイナミックレンジ。"
      f"最小側に16段確保するには約{need_bits}bit PWMが要る(8bitでは不足)")

# ファーム埋め込み用のC配列(線形RGB、8bit)
rows = []
for lin in lut_lin:
    r, g, b = (np.clip(lin, 0, 1) * 255).astype(int)
    rows.append(f"{{{r:3d},{g:3d},{b:3d}}}")
c = ("// blackbody_led.py が生成。線形RGB(ガンマ非適用)。\n"
     f"// プレート{PLATE_LO}-{PLATE_HI}C -> {T_LO:.0f}-{T_HI:.0f}K の宣言マッピング\n"
     "const uint8_t BB_LUT[256][3] = {\n  "
     + ",\n  ".join(", ".join(rows[i:i + 4]) for i in range(0, N, 4))
     + "\n};\n")
open("blackbody_lut.h", "w", encoding="utf-8").write(c)
print(f"  出力: blackbody_lut.h ({N}エントリ)")
print(f"  先頭 {rows[0]}  中央 {rows[N//2]}  末尾 {rows[-1]}")
