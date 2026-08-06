---
domain: research
type: 調査
status: 要更新
description: "Neuralink・Synchron・Precision Neuroscience・Merge Labsを侵襲度別に整理し、電極方式ごとの信号解像度(bps)・長期安定性のトレードオフを比較した技術動向ノート"
tags:
  - BCI
  - 電脳化社会
topics:
  - "[[00_index]]"
---

# 主流BCI方式と企業比較 -- 侵襲度別の技術地図

2026年8月時点で臨床開発が進む主要BCI企業を、侵襲度の低い順に整理する。忘却炉プロジェクトが扱う「電脳化した人間とそうでない人間の出力格差」という予測軸のうち、どの方式が最初に一般に普及しうるかを判断する基礎資料。

## 現状

### 非侵襲型・超音波方式 -- Merge Labs
サム・アルトマン共同設立、OpenAIがリード投資。2025年設立、2026年1月にステルス解除し2.52億ドルを調達（評価額8.5億ドル）。超音波ベースの脳インターフェースを遺伝子治療と組み合わせるアプローチで、インプラントを伴わない。

### 血管内留置型（開頭手術なし）-- Synchron Stentrode
自己拡張型ニチノールステントに白金-イリジウム薄膜電極（16個）を組み込み、頸静脈からカテーテルで上矢状静脈洞（一次運動野に隣接）まで進めて留置する。脳卒中治療で確立済みの神経血管内治療の術式を転用しており、開頭手術・脳実質の貫通が不要。COMMAND試験（2024年9月発表）で6例全員が一次安全性エンドポイントを達成、Apple Vision Pro / Alexaの脳信号操作を実証。2026年、FDA PMA取得に向けたpivotal trial段階。

### 脳表面設置型（微小侵襲）-- Precision Neuroscience Layer 7
Neuralink元共同創業者が設立。頭蓋骨の裂隙開頭から脳表面に1,024電極のシートを滑り込ませる方式で、組織を貫通せず安全に除去可能。2025年にFDA 510(k)承認（新規商用BCIとして初の完全な規制承認）を取得し、最大30日間の植込みで38例の人体手術を実施済み。

### 侵襲型・皮質貫通電極アレイ -- Neuralink N1
ロボット手術で運動野に1,024本の極細電極線を刺入。2024年1月に初のヒト植込み（Noland Arbaugh氏）を実施し、思考のみでチェスを操作する実証で注目を集めた。PRIME試験で少なくとも21例に植込み済み。20,000 samples/sec、10bit分解能、チャンネルあたり約200kbps、全体で生データ約200Mbps。

## 論点・トレードオフ

### 信号の種類と解像度
NeuralinkとSynchronはそもそも捕捉している信号の階層が異なる。

| | Neuralink (N1) | Synchron (Stentrode) |
|---|---|---|
| 記録方式 | 皮質内穿通電極（intracortical） | 血管内留置電極（endovascular、ECoG類似） |
| 捕捉する信号 | 個々のニューロンの活動電位（spike） | 局所フィールド電位（LFP）、主にhigh-gamma帯域 |
| 空間分解能 | 単一ニューロン〜小集団レベル | 数千〜数万ニューロンの集団平均レベル |
| 電極数 | 1,024本超 | 16個（間隔3mm） |

Neuralinkは組織を直接貫通して個々のニューロンの発火を拾うため原理的に解像度が高い。Synchronは血管壁越しの間接記録でLFP/ECoG的な性質の信号しか得られない。

### 実効性能（情報伝達速度）
- Neuralink: 初期の被験者で4〜10bps、最高記録9.5bps（カーソル操作タスク）
- Synchron: 5bps未満。アイトラッカー併用でタイピング速度14〜20文字/分、クリック確定に300〜900msの持続的な運動意図が必要
- 一般整理: 侵襲型（皮質内電極）は50〜100bpsでフルタイピング速度に足る。低侵襲型（endovascular・表面電極）は10〜25bpsでコマンド/カーソル操作は可能だが文字単位のテキスト構成には力不足

補足: 血管壁・硬膜を介した信号減衰は致命的ではないという知見がある。血管内電極のSNRは硬膜下・硬膜外センサーと有意差がないとする比較研究があり、埋込み後の血管内皮化がむしろ信号安定性を向上させる報告もある。Synchronの制約は「信号が弱い」ことよりも「電極数が少なくニューロン単位の発火を拾えない」という構造的な情報密度の低さに起因する。

### 長期安定性 -- 対照的な劣化パターン
- **Neuralink**: 最初の被験者で術後約3ヶ月の時点で電極スレッドの約85%が脳組織から後退（retraction）し、信号捕捉能力が急激に低下。追加手術なしに記録・デコードアルゴリズムの改良で対処し性能は回復したが、これはソフトウェア側の代償でありハードウェアの位置ズレ自体は未解決。原因は組織の拍動・呼吸による機械的マイクロモーションと、異物反応としてのグリオーシス（電極周囲の瘢痕組織形成によるSN比の年単位劣化）——慢性神経インプラント全般に共通する既知の失敗モード
- **Synchron**: 血管を貫通しないためグリオーシス駆動の後退メカニズムが起きにくい。むしろステントが血管内皮に取り込まれる（endothelialization）ことで信号がより安定化するという報告がある

「解像度で勝るNeuralink」「安定性で勝るSynchron」という構図は、両者が選んだ侵襲方式の根本設計思想の違いから必然的に生じている。

## 参照
- [BCI Clinical Trials 2026: Neuralink, Synchron, Precision (NWI)](https://nextwavesinsight.com/bci-neuralink-synchron-clinical-trials-2026/)
- [Brain-Computer Interfaces in 2026: Neuralink, Synchron, and the Patient Pathway](https://pdpspectra.com/blog/brain-computer-interfaces-neuralink-2026/)
- [Precision Neuroscience vs Neuralink: Which Is Better? (2026)](https://www.biology.digital/compare/neuralink-vs-precision-neuroscience)
- [The Past, Present And Future Of Brain-Computer Interfaces (Forbes, 2025)](https://www.forbes.com/sites/robtoews/2025/10/05/these-are-the-startups-merging-your-brain-with-ai/)
- [The Stentrode System by Synchron: Architectural Design and Clinical Translation (ResearchGate)](https://www.researchgate.net/publication/395700531_The_Stentrode_System_by_Synchron_Architectural_Design_and_Clinical_Translation_of_a_Minimally_Invasive_Brain-Computer_Interface)
- [Synchron Announces Positive Results from U.S. COMMAND Study (BioSpace)](https://www.biospace.com/news/synchron-announces-positive-results-from-u-s-command-study-of-endovascular-brain-computer-interface)
- [Signal quality of simultaneously recorded endovascular, subdural and epidural signals are comparable (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5976775/)
- [Neuralink Beyond First Human 2026: Updates](https://axis-intelligence.com/neuralink-beyond-first-human-updates/)
- [PRIME Study Progress Update (Neuralink公式)](https://neuralink.com/updates/prime-study-progress-update/)
- [How Fast Can Neuralink Read the Brain? Speed Breakdown](https://www.neurapod.com/blog/neuralink-brain-read-speed)
- [But do we need high bandwidth? (IOPscience)](https://iopscience.iop.org/article/10.1088/1741-2552/ae6dfd)

---

Relevant Notes:
- [[00_concept/idea|idea]] -- 忘却炉の電脳社会像という企画初期の直感的アイデアが、本ノートの技術的検証の起点になっている
- [[04_foresight/trends|trends.md]] -- 本ノートの要約が統合される技術動向の親ノート
- [[04_foresight/forecast|forecast.md]] -- 本ノートのエビデンス（各社の規制承認・臨床進捗）に基づき電脳社会の普及タイムライン予測を更新する土台
- [[導電性ポリマー電極材料]] -- ここで比較した金属電極の機械的ミスマッチ・グリオーシス問題に対する材料面での代替アプローチ

Topics:
- [[00_index]]
