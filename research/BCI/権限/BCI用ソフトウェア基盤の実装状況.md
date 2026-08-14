---
domain: research
type: 調査
status: 進行中
description: "BCI2000・CorTec Brain Interchange・Medtronic Summit RC+Sにアプリ層とデバイス層の分離が既に実装されている一方、自称BCI OSは権限・安全・プライバシーを扱わず、既存基盤がすべて単一アプリ前提で複数アプリ調停の設計例が存在しないことを確認した調査"
tags:
  - BCI
  - ソフトウェアアーキテクチャ
topics:
  - "[[00_index]]"
---

# BCI用ソフトウェア基盤の実装状況

## 要約

脳とつなぐ機器のソフトウェアは、すでに「何をするかを決める部分」と「機器を安全に動かす部分」が別々に作られており、研究用にも人体に埋め込む医療用にも実例がある。ただし今あるものはどれも一度に一つのアプリしか動かない前提で作られており、複数のアプリが同時に脳を使う世界を想定した設計は見当たらない。

## アプリケーション層の分離は研究用プラットフォームで確立している

2000年から開発され110以上の研究室で使われているBCI2000は、Operator・Source・Signal Processing・Applicationの4モジュールで構成される。うち後ろ3つをcore moduleと呼び、その間の通信はSource→Signal Processing→Applicationの単方向に固定されている。Operatorだけが全モジュールと双方向に通信し、「core moduleからパラメータメッセージを受け取り、設定ダイアログに表示し、パラメータファイルへ保存・読み出しする」中央の設定権威として振る舞う。

構成として重要なのは、Applicationが信号処理から独立したモジュールとして最初から切られている点である。何を提示しどうフィードバックするかという体験設計と、信号をどう処理するかという変換は、20年以上前から別の担当として設計されていた。ただしBCI2000は研究用であり、権限・同意・プライバシー・複数アプリの調停はいずれも扱わない。

## 埋込み型の双方向デバイスでもアプリ層とデバイス層は分かれている

CorTecのBrain Interchangeは32接点で記録と皮質刺激の双方を行う完全埋込み型の閉ループシステムで、FDAのIDEを取得し500日以上の連続安定動作を報告している。ここでは研究者がカスタムアプリケーションを書いて「どの刺激プロトコルを適用するか」を決め、CorTec側が刺激の実行と安全制約を担う。刺激は電流制御方式で、コンプライアンス電圧は−11V〜+5V、最大電流は±6mAという上限がデバイス層に置かれている。Jeffrey Ojemann・Jeffrey HerronとCorTecが共同開発したOMNI-BICは、この上で実験・研究室・プログラミング言語をまたいだコードの再利用と可搬性を狙う枠組みである。

Medtronic Summit RC+SとOpenMind consortiumにも同型の構造がある。デバイス側に検出器（Ld0・Ld1）が組み込まれ、研究者はAPI経由で適応的刺激のロジックを実装する。

つまり「アプリケーションが何をするかを決め、デバイス層が安全域を強制する」という分業は、仮説ではなく既に人体に埋め込まれて動いている製品の構造である。

## 自称「BCIのOS」が担っているのは読み取り側の利便性だけである

NeuroOSは「iOSとAndroidがスマートフォンにとってそうであるように、BCIの標準OSになる」と明示的に掲げるスタートアップで、同種のものにAxonOSがある。掲げている機能は、各社が独自SDKと独自信号形式を持つ断片化への対処としてのハードウェア抽象化（「1つのAPIが全BCIデバイスで動く」）と、雑多な信号をクリーンなコマンドへ変換するintent recognitionの2つである。

一方でこれらの説明には、権限システム・安全制御・プライバシー保護・データガバナンス・認証認可の記述が見当たらない。市場が現在「BCIのOS」と呼んでいるものは、読み取り方向の、開発者向け利便性レイヤーに留まっている。

## 既存基盤はすべて単一アプリ前提であり、調停の設計例が存在しない

調べた範囲のすべて――BCI2000もCorTecもSummit RC+Sも――は「一つの実験」「一つの治療」しか走らせない前提で作られている。複数のアプリケーションが同時に同一の脳を使おうとしたときの優先度・排他制御・フォーカス管理・累積負荷の配分といった、通常のOSが資源に対して行う調停に相当する機能は、どの基盤にも見当たらなかった。

これは[[FR-11感覚配信における忘却炉と電脳側の処理境界]]が想定する構図と直接ぶつかる。忘却炉は「その人の電脳で走っている多数のアプリのうちの1つ」として感覚を届ける前提に立っており、この前提を支える層は現時点でどこにも実装されていない。[[電脳OSが担う責務の範囲]]で整理した調停・摩耗分散・身体マップの割り当ては、既存機能の説明ではなく未発明の機能である。

## 出典

- [BCI2000: a general-purpose brain-computer interface (BCI) system (PubMed 15188875)](https://pubmed.ncbi.nlm.nih.gov/15188875/)
- [BCI2000 Technical Reference: System Design](https://www.bci2000.org/mediawiki/index.php/Technical_Reference:System_Design)
- [CorTec: A Software Interface for Developing Next Generation Neurotherapies](https://cortec-neuro.com/story/a-software-interface-for-developing-next-generation-neurotherapies/)
- [CorTec's Brain Interchange BCI System Enables Stroke Patient to Control Computer with his Mind](https://cortec-neuro.com/brain-interchange-stroke-patient-computer-mind-control/)
- [Analysis-rcs-data: Open-Source Toolbox for Medtronic Summit RC+S (PMC8312257)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8312257/)
- [NeuroOS - The Operating System for Brain-Computer Interfaces](https://www.neuroos.xyz/)
- [AxonOS: The Global BCI Hardware Landscape and What It Means for the Software Layer](https://medium.com/@AxonOS/axonos-article-25-57f438f0bc73)

## 未検証

CorTec・Medtronicいずれについても、参照したのは公開の紹介ページと二次情報であり、SDK文書やAPI仕様書といった一次資料は取得していない。デバイス層が安全制約をどの粒度で強制するのか、研究者アプリがどこまでのパラメータを直接指定できるのかは確認できていない。NeuroOS・AxonOSは稼働実績を確認していない設立初期のスタートアップであり、掲げている機能が実装されているかも未確認。「複数アプリの調停機構が存在しない」という結論は、調べた範囲に存在しなかったという消極的な確認に留まり、非公開の実装や本調査で辿らなかった基盤にある可能性は残る。

---

Relevant Notes:
- [[電脳OSが担う責務の範囲]] -- 本調査で確認した空白を埋める形で、電脳OSが担うべき責務を整理した先
- [[神経刺激の安全限界とシャノン基準]] -- デバイス層が強制する安全制約の実体
- [[神経データのプライバシー保護の現状]] -- 本調査で扱わなかった権限・プライバシー側の現状
- [[非侵襲BCI車椅子における処理分担と低帯域幅コマンド設計]] -- ヘッドセットと外部計算機の処理分担という、同じ分業を読み取り側で扱った先行ノート
- [[FR-11感覚配信における忘却炉と電脳側の処理境界]] -- 本調査が前提の妥当性を検証した対象

Topics:
- [[00_index]]
