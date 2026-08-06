---
domain: quantum
type: 決定
status: 進行中
description: "量子測定と古典セル鎮静を共通契約commit/disposeで包むCollapseTransaction案の設計と限界。焼却側133µs周期に対しどのQRNG経路も追いつかないため、速度最適化はトレードオフを解消せずバッチサイズNへ押し込むだけという結論"
tags:
  - QRNG
  - スループット
  - 情報漏洩対策
topics:
  - "[[00_index]]"
---

# CollapseTransactionによる乱数露出窓とスループットのトレードオフ

[[02_technical/decisions/量子測定リセットとランダウア4相サイクルの同型性|量子測定リセットとランダウア4相サイクルの同型性]]を出発点に、**FR-13（量子情報破壊）を意図的にスコープ外とし**、FR-03（QRNG）とFR-05/FR-12（ランダウアプロトコルの電気回路実装）の2者間だけで同型性を活かすアーキテクチャを検討した記録。

## 提案：共通の抽象契約で結合する

QuantumCollapse（FR-03側、Qiskitでの測定）とClassicalCollapse（FR-05/FR-12側、セルの鎮静）を、共通の抽象契約を持つ2つの実装として結合する。

- `commit()` — 不確定状態を単一値に圧縮する
- `dispose()` — 確定前の状態への参照を即時破棄する

現状は `r = QuantumCollapse.commit()` → `ClassicalCollapse.commit(r)` という別々の呼び出しであり、乱数 $r$ がPython変数として呼び出し側スコープに一度露出する。これを1つの `CollapseTransaction`（コンテキストマネージャ）に包み、$r$ 専用のmlock済みバッファをトランザクション自身が所有し、`__exit__` で例外の有無に関わらず即座にゼロ化する設計とする。これにより「$r$ を扱ってよい場所は1つのオブジェクトのライフサイクルの中だけ」という制約をPythonのスコープレベルで強制できる。FR-05がレジスタ $d$ に既に課している規律（bytearray/numpy.ndarray限定・mlock・swapoff）を $r$ にも同一適用する形になる。

**限界**: この案はPi↔Pico間のUART/SPI伝送（[[02_technical/spec/architecture|architecture]] 5節）そのものは消せない。Pi側の $r$ 保持時間を最小化・確定化するに留まり、Pico側ファームウェアにも対になる即時ゼロ化の実装が別途必要になる。

**粒度**: トランザクションを「1ビット」ではなく「1トランザクション」単位で考えるべきという指摘に沿って [[02_technical/spec/components|components]] を確認したところ、ビット数はすでに8bit並列（16ハーフセル、TC4427直接駆動）で確定済みだった。したがって8ビット単位に合わせることは新しい制約ではなく既存設計への追従に過ぎない。

## 定量検証：QRNG供給が焼却速度に追いつかない

components記載の値（$\tau = RC \approx 8.3\,\mu\mathrm{s}$、1サイクル $= 16\tau \approx 133\,\mu\mathrm{s}$、$f \approx 7.5\,\mathrm{kHz}$、スループット $\approx 60\,\mathrm{kbit/s}$、1MB≈140秒）に対し、「1トランザクション＝1物理サイクル」を厳密運用した場合にQuantumCollapseが133µsごとに新しい8ビット分の $r$ を供給できるかを検証した。

- Qiskit Aerの単発ショット実行: 約11.8ms±3.5ms/回（[arXiv:2110.03137](https://arxiv.org/pdf/2110.03137)、条件が正確に一致するベンチマークではなく参考値）
- IBM Quantum実機: キューイングが秒〜分オーダー
- ANU QRNG API: ネットワーク往復が数十〜数百ms

いずれも7.5kHzに到底届かない。**ローカルQRNGチップまたはPico内蔵ROSC以外の経路では、厳密な1サイクル1トランザクションを守ると焼却速度がQRNG供給速度まで低下し、会場での通し実演という時間要件を崩す。** デプロイ先がRaspberry Pi（ARM、technical_req記載の中枢）である点も一般的なベンチマーク値より悪化する要因になる。

## トレードオフとして残る2案

1. **厳密な1サイクル1トランザクション** — $r$ の露出窓は最小だが焼却速度が大きく低下する
2. **事前バッチ生成** — 60kbit/sを維持できるが、バッチ分の $r$ がPi側にまとまって存在する時間が生まれ、architecture 8節の「$r$ をバッファに溜めない」不変条件と緊張する。architecture 6節の動作シーケンス②が暗黙に前提としている方式

どちらを採用するかは未決定。

## 速度最適化はトレードオフを解消しない

8量子ビットの状態ベクトル計算自体（$2^8 = 256$次元）は数値計算として軽く、レイテンシの支配要因はQiskitのPython層オーバーヘッド（回路構築・トランスパイル・バックエンド呼び出し）と推定される。対策は3つ。

1. 回路の事前トランスパイルと使い回し
2. `shots=N` によるバッチ実行でPython呼び出しオーバーヘッドをN回分償却する（最有力）
3. Qiskitの高レベルAPIを迂回しnumpyで直接状態ベクトルを計算する自前実装（最速だが「実機IBM Quantumに接続可能なQiskit経由」という説明可能性を犠牲にする）

ただし2はNを大きくするほど案2の露出窓を広げる。したがって**速度を上げること自体はトレードオフを解消せず、Nの選び方へ押し込むだけ**である。$N$ は速度と露出窓のトレードオフパラメータとして明示的に設計すべき対象になる。

## 思想面の留保

CH（controlled-Hadamard）ゲートによるエンタングルメントはFR-03の思想的根拠（「観測量は事前に存在するのではなく観測によって創発する」というベルの不等式の破れの読み）と直結している。速度目的でH単体に単純化する選択は、技術判断ではなく思想的トレードオフとして扱うべきである。

---

Relevant Notes:
- [[02_technical/decisions/量子測定リセットとランダウア4相サイクルの同型性|量子測定リセットとランダウア4相サイクルの同型性]] -- 本検討の理論的出発点
- [[02_technical/decisions/ベル対self-testによるQRNG方式選定|ベル対self-testによるQRNG方式選定]] -- 供給側の回路構成
- [[02_technical/spec/components|components]] -- 133µs・7.5kHz・60kbit/sの根拠となる設計パラメータ
- [[02_technical/spec/architecture|architecture]] -- 5節のPi↔Pico伝送、8節の設計不変条件表（量子側の行追加が保留中）
- [[02_technical/implementation_risks|implementation_risks]] -- 実装上の手戻りリスク一覧

Topics:
- [[00_index]]
