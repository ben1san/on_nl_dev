---
domain: research
type: 調査
status: 進行中
description: "非侵襲EEG車椅子BCIの文献調査から、ヘッドセットは信号取得のみを担い外部コンピュータが前処理・特徴抽出・分類を一手に引き受ける分担と、低ビットレート制約が連続軌道デコードでなく離散コマンド設計へ導く構図を整理"
tags:
  - BCI
  - インタラクション設計
topics:
  - "[[00_index]]"
---

# 非侵襲BCI車椅子における処理分担と低帯域幅コマンド設計

## 要約

電動車椅子を脳波で動かす仕組みを調べると、頭に着ける装置はほとんど何もしておらず、信号を整理して「進む・止まる」を判断する処理は全部スマホやパソコン側で行われていた。脳から読み取れる情報量が少ないので、細かい操作をそのまま再現するのではなく、少ない選択肢から選ぶ形に割り切って設計されていた。

BCIシステムは一般に信号取得・前処理・特徴抽出・分類・動作という5段階のパイプラインで構成される。非侵襲EEG方式の車椅子デモを調べた範囲では、この5段階のうち最初の1段階（信号取得）だけがヘッドセット側で行われ、残り全部が外部コンピュータ側に集約されている。

## ヘッドセットは実質センサーに徹する

16chのOpenBCI Ultracortex Mark-4のようなヘッドセットは、脳波を増幅・AD変換してBluetoothで送信するだけで、フィルタリングすら行わない。前処理（バンドパス・ノッチフィルタ、アーティファクト除去）・特徴抽出（運動想起ならCSP: Common Spatial Pattern、SSVEPならFBCCA: Filter Bank Canonical Correlation Analysis）・分類（k-NN、SVM、近年はTFormerEEGのようなTransformerベースdeep learning）は、Odroid XU-4等のSBCやノートPC側が一手に引き受ける。

[[Neuralinkの侵襲型皮質貫通電極アレイ]]のような侵襲型が、無線伝送帯域の物理制約からインプラント上でスパイク検出をせざるを得ないのとは対照的に、非侵襲EEG（16〜64ch、数百Hz〜1kHz程度）はBluetooth帯域に余裕で収まるため、演算をヘッドセット側に持つ理由が構造的にない。

## 低ビットレート制約は連続デコードでなく離散コマンド設計に倒される

[[主流BCI方式と企業比較]]で確認した通り低侵襲・非侵襲方式の実効性能は10〜25bps程度に留まる。この制約に対し、車椅子BCI研究は連続的な軌道をリアルタイムでデコードする方向ではなく、コマンド語彙自体を極小の離散選択に絞る方向で解決している。SSVEP方式では前進/後退/右/左をそれぞれ7Hz/8Hz/9Hz/10Hzの注視という4値の選択問題に落とし込み、スキャン式メニューから選ぶ「Switch」パラダイムと「Continuous」パラダイムを比較評価する研究もある。BCI側は高レベルの意図(どちらへ進むか、どこへ行きたいか)だけを出し、障害物回避・経路計画のような低レベル操縦はロボット側の自律性(shared autonomy)に委ねる構成が一般的である。

## 出典

- [Controlling a Wheelchair using a Brain Computer Interface (thesai.org)](https://thesai.org/Downloads/Volume12No6/Paper_7-Controlling_a_Wheelchair_using_a_Brain_Computer.pdf)
- [EEG-based AI-BCI wheelchair advancement: Transformer-based learning with motor imagery (Oxford Academic)](https://academic.oup.com/biomethods/article/11/1/bpag039/8728793)
- [EEG Control of a Robotic Wheelchair (IntechOpen)](https://www.intechopen.com/chapters/86899)
- [Evaluation of Switch and Continuous Navigation Paradigms to Command a Brain-Controlled Wheelchair (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6031925/)
- [A Hybrid BCI System Integrating Motor Imagery and SSVEP for Wheelchair Control (ACM)](https://dl.acm.org/doi/10.1145/3704323.3704343)
- [An Electric Wheelchair Manipulating System Using SSVEP-Based BCI System (PubMed)](https://pubmed.ncbi.nlm.nih.gov/36290910/)

## 未検証

侵襲型BCI（Neuralink等）側のオンチップ処理の詳細（スパイク検出がASIC上で行われる、デコードアルゴリズム本体は外部コンピュータ側で走る等）は、本ノートでは一次資料での確認をしておらず、想起に基づく記述に留まる。本ノートで確認した文献は車椅子制御に特化しており、タイピング等の他アプリケーションでも同じ処理分担構造が成り立つかは未検証。

---

Relevant Notes:
- [[主流BCI方式と企業比較]] -- 侵襲度別のbps・安定性比較との対比先
- [[Neuralinkの侵襲型皮質貫通電極アレイ]] -- 侵襲型における帯域幅制約起因のオンチップ処理という対照構図
- [[電気刺激によるBCI書き込みと文字表示]] -- 書き込み側の帯域幅制約と対をなす、読み取り側の帯域幅制約

Topics:
- [[00_index]]
