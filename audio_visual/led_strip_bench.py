#!/usr/bin/env python3
"""アナログRGBテープ(5V・コモンアノード・5050)をRaspberry Piから焚くベンチ用スクリプト。

目的は演出の実装ではなく、視覚演出ノートが「未検証」として残した項目を現物で潰すこと。
  1. 消費電力: 密閉筐体の熱収支(正味加熱+0.5W)に対してテープが何Wを持ち込むか
  2. 色      : 1900K相当のアンバーが、このテープの実原色でどのRG比になるか
  3. 見え    : 拡散材越しに一様に見えるか、10秒の呼吸が呼吸に見えるか、
               完了後の exp(-t/8s) 残光が滑らかに落ちるか

配線(必須。GPIOへ直結すると壊れる):
    テープ 5V+  --- 5V電源(+)
    テープ R    --- Nch MOSFET#1 ドレイン
    テープ G    --- Nch MOSFET#2 ドレイン
    テープ B    --- Nch MOSFET#3 ドレイン        (アンバー固定では未使用)
    各 MOSFET ソース --- GND (電源GNDとPiのGNDを必ず共通にする)
    各 MOSFET ゲート --- 220Ω --- GPIO
    各 ゲート-GND間  --- 10kΩ プルダウン (Pi起動時にGPIOは入力なので、
                          これが無いとゲートが浮いて点灯状態が不定になる)

    MOSFETはロジックレベル品(AO3400 / IRLML2502等)。手元に無ければ ULN2803 でもよい
    (8chダーレイアレイ、ゲート抵抗内蔵でGPIO直結可、500mA/ch、約1Vの電圧降下)。
    2N7000は200mAまでなので全開テストには使えない。

    テープを1m全開(白)で焚くと5Vで約3.6A流れる。Piの5Vピンから取らないこと。
    測定は本番の線長に合わせて約170mm(60LED/mなら10個)を目安にする。

使い方:
    python3 led_strip_bench.py hold    --level 0.1      色と明るさを固定して保持(電流測定用)
    python3 led_strip_bench.py steps                    輝度を段階的に落として電流を測る
    python3 led_strip_bench.py ratio                    RG比を振ってアンバーの見えを決める
    python3 led_strip_bench.py breath --level 0.1       10秒周期の呼吸
    python3 led_strip_bench.py session --speed 10       儀式全体(消去→停止→残光)の早回し
    python3 led_strip_bench.py off                      全消灯
    --dry を付けるとGPIOを触らず数値だけ出す(Pi以外での確認用)
"""
import argparse
import math
import signal
import sys
import time

# ---- 色 --------------------------------------------------------------------
# blackbody_render.srgb_of(1900) の linear RGB。プランクの法則からの計算値であり、
# 「テープの実原色 = sRGB原色」を仮定している。この仮定は正しくないので(部品ノートが
# 指摘するメタメリズムと同じ問題)、実際の比は ratio モードで目視補正して上書きする。
AMBER_1900K = (1.0000, 0.2425, 0.0000)

# 参考: 1638K=(1.0,0.179,0.0) 1800K=(1.0,0.2184,0.0) 2000K=(1.0,0.2663,0.0077)
#       2700K=(1.0,0.4231,0.0996) ← 電球色白テープの色。仕様(1900K)からは明確に外れる

TAU_COOL = 8.0        # NTC冷却時定数[s]。完了後の残光の減衰
BREATH_PERIOD = 10.0  # デューティ制御の往復周期[s]。掌側熱伝達係数次第で数秒〜数十秒
SESSION_SEC = 140.0   # 1MBセッションの尺[s]

DEFAULT_PINS = (12, 13, 19)   # R, G, B。12/13は全機種でハードウェアPWMに使えるピン


class Strip:
    """RGB3chをPWMで焚く。value は放射量に比例する線形デューティ(ガンマは掛けない)。

    残光の exp(-t/8s) は物理量の減衰なので、知覚補正を入れると嘘になる。
    そのぶん低輝度側の分解能が要るが、アナログテープならPWM分解能がそのまま効く
    (アドレサブルLEDの1ch 8bit固定という制約が無いのが、このテープの利点)。
    """

    def __init__(self, pins=DEFAULT_PINS, freq=2000, dry=False):
        self.dry = dry
        self.last = None
        if dry:
            self.ch = None
            return
        from gpiozero import PWMLED
        self.ch = [PWMLED(p, frequency=freq, initial_value=0) for p in pins]

    def set(self, r, g, b):
        v = tuple(min(1.0, max(0.0, x)) for x in (r, g, b))
        if self.dry:
            if v != self.last:
                print(f"    R={v[0]:.4f} G={v[1]:.4f} B={v[2]:.4f}")
        else:
            for c, x in zip(self.ch, v):
                c.value = x
        self.last = v

    def amber(self, level, ratio=AMBER_1900K):
        self.set(ratio[0] * level, ratio[1] * level, ratio[2] * level)

    def close(self):
        self.set(0, 0, 0)
        if not self.dry:
            for c in self.ch:
                c.close()


# ---- 各モード ---------------------------------------------------------------

def mode_hold(s, a):
    s.amber(a.level, a.ratio)
    print(f"アンバー保持 level={a.level}")
    print(f"  デューティ R={a.ratio[0]*a.level:.4f} G={a.ratio[1]*a.level:.4f}")
    print("  電源側の電流を測る。Ctrl-Cで終了")
    signal.pause() if not a.dry else time.sleep(1)


def mode_steps(s, a):
    """輝度と消費電流の対応を取る。熱収支に載せられる上限を決めるための測定。"""
    levels = [1.0, 0.5, 0.25, 0.10, 0.05, 0.02, 0.01]
    print(f"各段を{a.dwell}秒保持する。電源側の電流[mA]を読んで記録すること。")
    print("  正味加熱+0.5Wに対し、テープは100mW(5Vなら20mA)以下に収めたい\n")
    print("  level |  R duty |  G duty | 実測電流[mA] | 電力[mW]")
    print("  ------+---------+---------+--------------+---------")
    for lv in levels:
        s.amber(lv, a.ratio)
        print(f"  {lv:5.2f} | {a.ratio[0]*lv:7.4f} | {a.ratio[1]*lv:7.4f} |"
              f"              |")
        time.sleep(a.dwell)
    s.set(0, 0, 0)
    print("\n  消灯。暗電流(MOSFETのリーク)も一度測っておくとよい")


def mode_ratio(s, a):
    """G/R比を振ってアンバーの見えを決める。1900Kの計算値0.2425は出発点にすぎない。"""
    gains = [0.00, 0.10, 0.18, 0.2425, 0.30, 0.40, 0.55]
    labels = ["純赤(黒体軌跡上に無い)", "1500K付近の見え", "1638K相当",
              "1900K相当(計算値)", "2100K付近の見え", "2500K付近の見え", "3000K超(白すぎる)"]
    print(f"G/R比を{a.dwell}秒ずつ振る。『可視域で最も低温側の熱放射の色』に見えるものを選ぶ")
    print("拡散材(トレーシングペーパー等)を必ず被せて見ること。生のチップは色が読めない\n")
    for g, lab in zip(gains, labels):
        print(f"  G/R = {g:.4f}   {lab}")
        s.set(a.level, a.level * g, 0)
        time.sleep(a.dwell)
    s.set(0, 0, 0)
    print("\n  選んだ値は --ratio R,G,B で他のモードへ渡せる")


def _breath_level(t, a):
    """疑似サーモスタットのデューティ。明るい=温度上昇中、暗い=冷却中。"""
    ph = (t % a.period) / a.period
    if a.shape == "square":            # バンバン制御。実装がこれなら光は矩形になる
        return a.level if ph < 0.5 else a.level * a.low
    lo = a.level * a.low               # なめらかな比例制御に近い形
    return lo + (a.level - lo) * 0.5 * (1 - math.cos(2 * math.pi * ph))


def mode_breath(s, a):
    print(f"呼吸 period={a.period}s shape={a.shape} low={a.low}")
    print("  0.1Hz。光過敏性の懸念帯(3〜30Hz)からも保守的な2Hz推奨からも十分下。Ctrl-Cで終了")
    t0 = time.time()
    while True:
        t = time.time() - t0
        s.amber(_breath_level(t, a), a.ratio)
        time.sleep(0.02)
        if a.dry and t > a.period:
            return


def mode_session(s, a):
    """儀式全体。消去中は呼吸、完了で停止、以後はNTC冷却曲線に従う残光だけが残る。

    見るべきは『光の様式の断絶』が閃光なしで消去の瞬間を伝えられるかどうか。
    """
    dur = SESSION_SEC / a.speed
    tau = TAU_COOL / a.speed
    print(f"セッション {dur:.1f}s (実尺{SESSION_SEC:.0f}sの{a.speed}倍速) → 停止 → 残光τ={tau:.1f}s")

    print("  [待機] 消灯")
    s.set(0, 0, 0)
    time.sleep(1.5)

    print("  [消去] 呼吸")
    t0 = time.time()
    while (t := time.time() - t0) < dur:
        s.amber(_breath_level(t * a.speed, a), a.ratio)
        time.sleep(0.02)
        if a.dry and t > 1:
            break

    # 完了。スイッチングが止まるので変調成分は消える。閃光は置かない
    print("  [完了] 変調停止。残光へ")
    t0 = time.time()
    afterglow = a.level * a.low
    while (t := time.time() - t0) < tau * 5:
        s.amber(afterglow * math.exp(-t / tau), a.ratio)
        time.sleep(0.02)
        if a.dry and t > 1:
            break
    s.set(0, 0, 0)
    print("  [終了] 消灯")


MODES = {"hold": mode_hold, "steps": mode_steps, "ratio": mode_ratio,
         "breath": mode_breath, "session": mode_session,
         "off": lambda s, a: s.set(0, 0, 0)}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=sorted(MODES))
    p.add_argument("--level", type=float, default=0.10, help="マスター輝度 0-1 (既定0.10)")
    p.add_argument("--ratio", default=None, help="R,G,B の線形比 (既定は1900K計算値)")
    p.add_argument("--pins", default=",".join(map(str, DEFAULT_PINS)), help="R,G,BのGPIO番号")
    p.add_argument("--freq", type=int, default=2000, help="PWMキャリア周波数[Hz]")
    p.add_argument("--dwell", type=float, default=8.0, help="steps/ratioの各段の保持秒数")
    p.add_argument("--period", type=float, default=BREATH_PERIOD, help="呼吸の周期[s]")
    p.add_argument("--shape", choices=("square", "smooth"), default="square")
    p.add_argument("--low", type=float, default=0.15, help="呼吸の谷の相対輝度")
    p.add_argument("--speed", type=float, default=1.0, help="sessionの早回し倍率")
    p.add_argument("--dry", action="store_true", help="GPIOを触らず数値だけ出す")
    a = p.parse_args()

    a.ratio = tuple(float(x) for x in a.ratio.split(",")) if a.ratio else AMBER_1900K
    pins = tuple(int(x) for x in a.pins.split(","))

    s = Strip(pins=pins, freq=a.freq, dry=a.dry)
    try:
        MODES[a.mode](s, a)
    except KeyboardInterrupt:
        print("\n中断")
    finally:
        s.close()


if __name__ == "__main__":
    sys.exit(main())
