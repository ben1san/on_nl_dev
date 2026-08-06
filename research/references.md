---
domain: research
type: 調査
status: 進行中
description: "ANU QRNG APIやNIST SP 800-22等の技術的FR裏付け出典に加え、色即是空・無我・少欲知足・本覚思想・神秀慧能・禊祓等、東洋哲学/神道に不慣れなユーザー向けの入門記事をトピック別に整理した参考文献集"
tags:
  - 参考文献
  - 量子乱数
  - 東洋哲学
  - 神道
topics:
  - "[[00_index]]"
---

# Web参考文献

トピック別に出典をまとめる。各エントリは「出典 → 一言要約 → どのFR/主張を裏付けるか」の形式で統一する。
機能要件側からは `[[references#トピック見出し]]` の形でリンクする。

## 量子乱数・量子コンピューティング

- **ANU QRNG API** — https://qrng.anu.edu.au/API/
  - 真空の量子ゆらぎを測定して真の乱数を公開APIで配信している物理乱数源。IBM Quantum実機のキューイング遅延を避けるフォールバックとして利用可能。
  - 裏付けるFR: [[functional_req#FR-03 物理乱数生成（Must・Tier1）|FR-03]]

- **NIST SP 800-22**（乱数統計検定スイート）
  - 出典URL: (未記入)
  - 頻度検定・連検定など、乱数列が統計的にランダムであることを検証する標準スイート。
  - 裏付けるFR: [[functional_req#FR-04 乱数の真性証明（Could）|FR-04]]

## 熱力学・ランダウアの原理

- (未記入 — 熱破壊再考察.md の内容から出典を抽出予定)

## ストレージ技術（SSD／ウェアレベリング）

- (未記入 — technical_req.md FR-05の技術的限界の記述に対応する一次情報を追加予定)

## 忘れられる権利・デジタル終活

- (未記入 — GDPR「忘れられる権利」の一次情報、デジタル遺品供養サービスの事例など)

## BCI・電脳化社会

- **BCI Clinical Trials 2026: Neuralink, Synchron, Precision** — https://nextwavesinsight.com/bci-neuralink-synchron-clinical-trials-2026/
  - 2026年時点の主要3社の臨床試験段階を比較。Synchronは16電極でNeuralinkの1000本超に対し解像度は低いが開頭手術不要、Precisionは1,024電極のシート型でFDA 510(k)取得済み。
  - 裏付ける主張: [[03_research/bci/主流BCI方式と企業比較|主流BCI方式と企業比較]]の侵襲度別比較
- **Synchron Announces Positive Results from U.S. COMMAND Study** — https://www.biospace.com/news/synchron-announces-positive-results-from-u-s-command-study-of-endovascular-brain-computer-interface
  - COMMAND試験6例全員が一次安全性エンドポイントを達成（2024年9月発表）。Apple Vision Pro/Alexaの脳信号操作を実証。
  - 裏付ける主張: [[03_research/bci/主流BCI方式と企業比較|主流BCI方式と企業比較]]のSynchron臨床進捗
- **Neuralink PRIME Study Progress Update**（Neuralink公式） — https://neuralink.com/updates/prime-study-progress-update/
  - 最初の被験者で電極スレッドの約85%が術後3ヶ月で後退し信号低下、ソフトウェア側の対処で回復した経緯を報告。
  - 裏付ける主張: [[03_research/bci/主流BCI方式と企業比較|主流BCI方式と企業比較]]の長期安定性比較
- **Axoft Announces Commercialization of Fleuron**（Stanford独占ライセンス） — https://www.businesswire.com/news/home/20250514024008/en/Axoft-Announces-Commercialization-of-Fleuron-Covered-by-an-Exclusive-License-Agreement-with-Stanford-University
  - 現行ポリイミド電極比で最大1万倍柔らかい全有機導電性ハイドロゲル。2026年First-in-human試験実施。
  - 裏付ける主張: [[03_research/bci/導電性ポリマー電極材料|導電性ポリマー電極材料]]のAxoft節
- **PEDOT:PSS-based bioelectronics for brain monitoring and modulation**（Nature） — https://www.nature.com/articles/s41378-025-00948-w
  - 導電性ポリマーPEDOT:PSSの神経工学応用と生体適合性のメカニズムを整理した総説。
  - 裏付ける主張: [[03_research/bci/導電性ポリマー電極材料|導電性ポリマー電極材料]]のPEDOT:PSS節
- **Living brain-cell biocomputers are now training on dopamine**（New Atlas） — https://newatlas.com/computers/finalspark-bio-computers-brain-organoids/
  - FinalSparkのNeuroplatform、ドーパミン報酬による神経細胞の学習、シリコン比100万倍効率という未検証の主張。
  - 裏付ける主張: [[03_research/bci/脳オルガノイド計算基盤|脳オルガノイド計算基盤]]のFinalSpark節
- **Biological Computing: The First Commercial Brain-on-a-Chip Arrives** — https://publicmarkets.substack.com/p/biological-computing-the-first-commercial
  - Cortical LabsのCL1（2025年3月発売、数十万個のヒト由来神経細胞、消費電力850〜1,000W）の商用仕様。
  - 裏付ける主張: [[03_research/bci/脳オルガノイド計算基盤|脳オルガノイド計算基盤]]のCortical Labs節

## 宇宙・エントロピー

- (未記入 — space.md の内容から出典を抽出予定)

## 東洋哲学・神道 入門（幸福論・存在論関連）

ユーザーから「東洋哲学・神道に詳しくない」との申告を受け、[[00_concept/色即是空・空即是色と量子自然の相互創発|色即是空ノート]]・[[00_concept/無所得と神秀の漸進修行による忘却炉の幸福論|幸福論ノート]]・[[03_research/philosophy/仏教的概念と量子自然の対応関係|仏教的概念ノート]]で扱った各概念について、一般向けの入門記事を選定した。学術論文ではなく、初学者が読める解説記事・公式サイトを優先している。

**色即是空・空即是色（般若心経）**
- 色即是空 - Wikipedia — https://ja.wikipedia.org/wiki/色即是空
  - 「色（物質的現象）には固定的実体がない」という基本定義と成立の経緯を中立的に整理。
- 色即是空とは？般若心経に説かれた恐ろしい意味を分かりやすく解説（true-buddhism.com） — https://true-buddhism.com/teachings/shikisokuzeku/
  - 色（ルーパ）・空（シューニャ）の語義から、色即是空・空即是色が「不二法門」を説く構図までを平易に解説。
  - 関連ノート: [[00_concept/色即是空・空即是色と量子自然の相互創発|色即是空ノート]]

**無我・縁起**
- 諸法無我——「わたし」とは何かを見つめる智慧（東京国際仏教塾） — https://tibs.jp/20250613_10219/
  - 「わたし」は体・心・記憶・関係という無数の縁の集まりであり、揺るがない固定的な核はないという無我の定義を実感に即して解説。
- 縁起とは？仏教の縁起思想をわかりやすく解説（全国坐禅会マップ） — https://zazenmap.jp/articles/engi-toha/
  - すべての「もの」は原因と条件（縁）によって生じるという縁起の道理を解説。
  - 関連ノート: [[03_research/philosophy/仏教的概念と量子自然の対応関係|仏教的概念ノート]]（無我と観測値の緊張の議論）

**少欲知足**
- 少欲知足（大谷大学「生活の中の仏教用語」） — https://www.otani.ac.jp/yomu_page/b_yougo/nab3mq000001phvn.html
  - 「少欲」は得ていないものを欲しないこと、「知足」はすでに得たものに満足すること、という定義を仏教用語解説として整理。
- バランスと少欲知足（浄土真宗本願寺派） — https://www.hongwanji.or.jp/mioshie/story/000580.html
  - 欲望を否定するのでも野放しにするのでもない「制御」としての少欲知足の実践的位置づけを説く法話。
  - 関連ノート: [[00_concept/無所得と神秀の漸進修行による忘却炉の幸福論|幸福論ノート]]

**本覚思想**
- 本覚 - Wikipedia — https://ja.wikipedia.org/wiki/本覚
  - 「一切の衆生に本来的に悟りが具わっている」という本覚の定義と天台宗での展開を整理。
- 本覚思想 - 新纂浄土宗大辞典 — https://jodoshuzensho.jp/daijiten/index.php/本覚思想
  - 迷いと悟りを峻別しない、現実肯定的な本覚思想の特徴を仏教学の辞典項目として解説。
  - 関連ノート: [[00_concept/無所得と神秀の漸進修行による忘却炉の幸福論|幸福論ノート]]

**涅槃**
- 涅槃（ニルヴァーナ）の意味と涅槃に達する方法を分かりやすく解説（true-buddhism.com） — https://true-buddhism.com/teachings/nirvana/
  - ニルヴァーナの語源が「（煩悩の火を）吹き消す」であること、涅槃が死後の世界ではなく「涅槃寂静」という安らぎの境地を指すことを解説。
  - 関連ノート: [[00_concept/無所得と神秀の漸進修行による忘却炉の幸福論|幸福論ノート]]

**神秀・慧能（漸悟と頓悟）**
- 禅の二つの立場（臨済宗大本山 円覚寺） — https://www.engakuji.or.jp/blog/34342/
  - 神秀「時時に勤めて払拭せよ」（漸悟・北宗）と慧能「本来無一物」（頓悟・南宗）の偈を原文つきで対比し、その後の禅宗史への影響を解説。
- 六祖壇経 - Wikipedia — https://ja.wikipedia.org/wiki/六祖壇経
  - 神秀・慧能の偈が記録された経典の成立背景を整理。
  - 関連ノート: [[00_concept/無所得と神秀の漸進修行による忘却炉の幸福論|幸福論ノート]]（コギトvs無我の緊張の解消に使用）

**神道の祖霊信仰・禊祓**
- 禊とは（神社本庁公式サイト） — https://www.jinjahoncho.or.jp/omatsuri/misogi/
  - 神道の中心儀礼である禊の定義を、神社を統括する公式機関の解説として提供。
- 禊（みそぎ）と祓（はらえ）の違い（神社チャンネル） — https://zinja-omairi.com/misogi-harae/
  - 禊は自ら穢れを清める自力的行為、祓は神職・祓戸の神に委ねる他力的行為、という違いを整理。
- 神道とは｜「神葬祭と祖霊祭」（遠江國一宮 小國神社） — https://okunijinja.or.jp/shinsousai/shinto.html
  - 死後の御霊が祖先神（氏神）の仲間入りをするという神道の祖霊信仰・氏神の考え方を神社公式サイトとして解説。
  - 関連ノート: [[東洋哲学の教義と忘却炉の解釈の相違点]]（神道の祖霊観との相違点の議論）

**初心（禅マインド・ビギナーズマインド）**
- 禅マインド ビギナーズ・マインド 要約（flier） — https://www.flierinc.com/summary/2100
  - 鈴木俊隆の「初心（ビギナーズ・マインド）」の核心——「初めての心をそのまま保つ」という修行の目的——を要約。
- ［新訳］禅マインド ビギナーズ・マインド（PHP研究所、書籍情報） — https://www.php.co.jp/books/detail.php?isbn=978-4-569-85293-5
  - 原著の書誌情報。通読する場合の一次資料。
  - 関連ノート: [[00_concept/無所得と神秀の漸進修行による忘却炉の幸福論|幸福論ノート]]

---

## 運用ルール

- 新しい記事・論文を読んだら、まずここに1行追加してからidea.md / [[04_foresight/trends|trends.md]] / [[04_foresight/forecast|forecast.md]] 等の本文に反映する（順序を逆にしない）。電脳技術系の記事は原則ここへの1行要約＋trends/forecastへの直接統合で完結させ、記事単位の個別ノートは作らない。
- URLだけの追加は禁止。必ず「一言要約」と「裏付けるFR」をセットで書く。
- 出典が本文中に散在しているのを見つけたら、ここに集約してリンクに置き換える。
