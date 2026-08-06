---
domain: classical_erasure
type: 仕様
status: 進行中
description: "architectureのブロック図を部品・ピン番号レベルまで展開したASCII回路図。TC4427の実ピン配置と入力しきい値をMicrochipデータシートで確認した上で、1ビット詳細回路・全体結線・電源安全系統・案B試作の物理対応を示す"
tags:
  - 回路図
  - TC4427
topics:
  - "[[00_index]]"
---

# 回路図（TC4427駆動 8bit・16ハーフセル構成）

**位置づけ**: [[architecture]] 2節のシステムブロック図（情報層／熱破壊セル層／計測・安全層）を、部品・ピン番号レベルまで展開したもの。定数・採用値は[[components]]、ドライバ選定の経緯は[[cell_driver_choice]]を参照。

真の画像（KiCad等のベクター図）は生成できないため、以下はASCII回路図。テキストのみで完結し、Obsidian上でそのまま読める。

---

## 0. TC4427ピン配置（Microchipデータシート DS20001422G で確認済み）

8-Pin PDIP/SOIC/MSOP、両チャンネルnon-inverting：

```
        ┌─────∪─────┐
  NC  1 │            │ 8  NC
 IN A 2 │            │ 7  OUT A
  GND 3 │  TC4427    │ 6  VDD
 IN B 4 │            │ 5  OUT B
        └────────────┘
```

**入力しきい値**（4.5–18V全動作範囲で共通、VDD比ではなく絶対値）: $V_{IH}$（Logic '1' 最小）= 2.4V、$V_{IL}$（Logic '0' 最大）= 0.8V。Pico GPIO（3.3V/0V）はレベルシフタなしで直接IN A/IN Bを駆動できる（[[cell_driver_choice]] 4.5節で確認済み、旧「未確認事項」を解消）。

---

## 1. 1ビット詳細回路図（TC4427 1個 = 2ハーフセル）

```
                                  +12V_cell（5節「電源・安全系統図」経由）
                                    │
                        ┌───────────┼───────────┐
                        │  NC(1)          NC(8) │
                        │          VDD(6)       │
 Pico GPIO(2n)  ────────┤IN A(2)                │
 （bitn の「1」側）      │            OUT A(7)  ├──[R_ext 110Ω]──●──[C 71nF]──● GND  … Cb（ビット=1側）
                        │      TC4427           │
 Pico GPIO(2n+1)────────┤IN B(4)                │
 （bitn の「0」側）      │            OUT B(5)  ├──[R_ext 110Ω]──●──[C 71nF]──● GND  … C̄b（ビット=0側／相補）
                        │                        │
                        │          GND(3)        │
                        └───────────┬────────────┘
                                    │
                                   GND
```

$R_{ext}$（110Ω）とTC4427出力段の$R_{on}$（≈7Ω）が直列で$R\approx117\Omega$（[[components]] 0節）。$C$（71nF）の充放電エネルギー$\frac12CV^2$が$R$でほぼ全て熱に変わる（3節「抵抗＝熱が生まれる唯一の場所」、[[回路解説_初学者向け]]参照）。

---

## 2. 全体結線図（8bit・16ハーフセル、シフトレジスタなし）

```
Raspberry Pi Pico 2                TC4427 ×8                  セル ×16
 GP0 ──IN A┐
 GP1 ──IN B┴─ #1（bit0）─OUT A/OUT B─→ R-Cペア×2（Cb0 / C̄b0）
 GP2 ──IN A┐
 GP3 ──IN B┴─ #2（bit1）─OUT A/OUT B─→ R-Cペア×2（Cb1 / C̄b1）
 GP4 ──IN A┐
 GP5 ──IN B┴─ #3（bit2）─OUT A/OUT B─→ R-Cペア×2（Cb2 / C̄b2）
  :            :                              :
 GP14──IN A┐
 GP15──IN B┴─ #8（bit7）─OUT A/OUT B─→ R-Cペア×2（Cb7 / C̄b7）
```

16本のGPIOをTC4427×8個のIN A/IN Bへ直結（[[cell_driver_choice]] 3節：この規模なら概算9〜10bitまでシフトレジスタ不要）。GND・VDD（12V）は8個のTC4427で共通バス。

---

## 3. 電源・安全系統図

```
12V ACアダプタ
   │
   ▼
[DCジャック＋ヒューズ]（components.md 6節）
   │
   ├──────────────→ 降圧コンバータ(12V→5V) → Pi / Pico（常時給電、下記の遮断の影響を受けない）
   │
   ▼
[Pch MOSFET]（IRF9540等）── ゲート ←── [LM393コンパレータ + ヒステリシス抵抗]
   │                                              ▲
   │（NTCが42℃検知でOFF、ソフトウェア非経由）        │
   ▼                                       NTC（プレート温度）
[INA260]（∫VIdt計測）
   │
   ▼
+12V_cell（セル電源バス）── TC4427 #1〜#8 の VDD(6) へ分配
                            （デカップリング100nF×8、バルク10µF×3、[[components]] 2節）
```

安全系はPicoのハング時にも効くよう、NTC→LM393→Pch MOSFETのゲートというハードウェアのみのループで構成する（[[components]] 5節）。Pi/Pico用の5V系統は12V_cellの遮断より上流から分岐するため、遮断中も制御・監視は継続する。

---

## 4. 試作（案B）との物理対応

3節・4節の直列RCペアが、試作段階でどこに実装されるかの対応表（[[components]] 3〜4節、案Bの決定を参照）。

| 回路図上の記号 | 実装場所（試作・案B） |
|---|---|
| $R_{ext}$（110Ω）×16 | アルミ板に熱伝導両面テープで直付け（発熱源本体） |
| $C$（71nF）×16 | ユニバーサル基板側、アルミには接触させない |
| TC4427×8、Pico、デカップリング／バルクC | ユニバーサル基板 |
| R⇔TC4427間、R⇔C間の配線 | リボンケーブルで橋渡し（16〜17本、[[components]] 4節） |

量産時はIMS基板上に$R$・$C$とも銅パッドとして実装し直す（[[components]] 4節「量産時のレイアウト」）。

---

## 5. 未確認・関連事項

- RC遷移波形の実測、抵抗ワット数の最終確認は引き続き[[cell_driver_choice]] 4節を参照
- 出典：Microchip TC4426/TC4427/TC4428 datasheet DS20001422G（https://ww1.microchip.com/downloads/en/DeviceDoc/20001422G.pdf）

---

Relevant Notes:
- [[architecture]] -- このノートが展開する元のシステムブロック図（2節）
- [[components]] -- 定数・部品表・試作/量産の構成分岐
- [[cell_driver_choice]] -- TC4427採用の経緯、ピン配置・入力しきい値の確認記録（4.5節）
- [[回路解説_初学者向け]] -- 本図で使う部品の役割を高校物理レベルで補足する付録

Topics:
- [[00_index]]
