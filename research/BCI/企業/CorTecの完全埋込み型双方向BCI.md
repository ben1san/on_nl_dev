---
domain: research
type: 調査
status: 進行中
description: "2010年創業のCorTecが手がける完全埋込み型双方向BCI Brain Interchangeの技術構成と、2025年初のヒト植込み・2026年FDA脳卒中リハビリ向けブレークスルー指定などの臨床進捗を整理"
tags:
  - BCI
  - CorTec
  - Brain Interchange
topics:
  - "[[00_index]]"
---

# CorTecの完全埋込み型双方向BCI（Brain Interchange）

## 要約

CorTecはドイツの会社で、脳に電極を埋め込んで信号を読み取りながら同時に刺激もできる機器を作っている。2025年に世界初のドイツ製埋込み型BCIの人体植込みを実施し、2026年には脳卒中のリハビリ用途でアメリカの承認が優先的に進む指定を得た。

## 会社の位置づけ

CorTec GmbHは2010年、Martin SchuettlerとJoern Rickertがドイツ・Freiburgで創業したニューロテクノロジー企業。自社BCIプラットフォーム「Brain Interchange」の開発と、埋込み型医療機器の受託開発・製造（CDMO）を事業の2本柱とする。資金調達は累計約$21.6M（6ラウンド、9投資家）で、Mangold Invest・K & SW Consult・Santo Venture Capitalなどが出資している。

## Brain Interchangeの技術構成

Brain Interchangeは32接点で記録と皮質刺激の双方を行う完全埋込み型の閉ループシステムである。閉ループとは、脳から信号を記録し→解析し→結果に応じて刺激を決めて与え→その効果をまた記録する、という制御ループが機器内で自動的に回っている構成を指す（開発者が逐一操作しなくても機器が脳の状態を見ながら刺激の要否・強さを調整し続けられる）。刺激は電流制御方式で、コンプライアンス電圧（狙った電流を維持するために機器が出せる電圧の上限。ノート[[BCI用ソフトウェア基盤の実装状況]]参照）は−11V〜+5V、最大電流は±6mAという安全上限がデバイス層に組み込まれている。研究者はカスタムアプリケーションで「どの刺激プロトコルを適用するか」を決め、刺激の実行と安全制約の強制はCorTec側が担うという分業になっている。この分業構造は[[BCI用ソフトウェア基盤の実装状況]]で確認したアプリ層/デバイス層分離の具体例の一つ。

Jeffrey Ojemann・Jeffrey HerronとCorTecが共同開発したOMNI-BICは、Brain Interchangeの上で実験・研究室・プログラミング言語をまたいだコードの再利用と可搬性を狙う枠組みである。FDAのIDE（治験機器適用免除）を取得しており、500日以上の連続安定動作が報告されている。

## 臨床進捗

2025年7月、シアトルのHarborview Medical Centerで、ドイツ製の完全埋込み型BCIとして史上初のヒト植込みを実施した（FDA承認済み臨床試験の一環）。2026年4月には、脳卒中後の運動機能回復を狙った皮質電気刺激の用途でFDAブレークスルーデバイス指定を取得した。これはBCIとして世界初の脳卒中リハビリ向け指定である。同月、脳卒中患者がBrain Interchangeでコンピュータをマインドコントロールする臨床成果も発表されている。

臨床戦略は4本柱で構成される：脳卒中リハビリ（UW Medicineと進行中）、てんかん管理（Mayo Clinicと進行中）、麻痺・重度コミュニケーション障害向けBCI、うつ病治療（University Hospital Freiburgと計画中）。CorTecは、完全埋込み型・双方向のBCIシステムを米国でFDA承認の臨床評価に持ち込んだ欧州発の企業として位置づけられている。

## 出典

- [CorTec's Brain Interchange™ BCI System Enables Stroke Patient to Control Computer with his Mind (GlobeNewswire)](https://www.globenewswire.com/news-release/2026/04/29/3283689/0/en/cortec-s-brain-interchange-bci-system-enables-stroke-patient-to-control-computer-with-his-mind.html)
- [CorTec Receives FDA Breakthrough Device Designation for Its Brain Interchange System in Stroke Rehabilitation (GlobeNewswire)](https://www.globenewswire.com/news-release/2026/04/08/3270076/0/en/CorTec-Receives-FDA-Breakthrough-Device-Designation-for-Its-Brain-Interchange-System-in-Stroke-Rehabilitation-the-First-BCI-Worldwide-Designated-for-Stroke-Motor-Rehabilitation.html)
- [CorTec wins FDA breakthrough nod for BCI system (MassDevice)](https://www.massdevice.com/cortec-wins-fda-breakthrough-nod-bci/)
- [CorTec Announces Neurotech Milestone: First Human Implantation of a Brain-Computer Interface made in Germany](https://cortec-neuro.com/first-human-implantation-of-a-bci-made-in-germany/)
- [CorTec - Company Profile (Tracxn)](https://tracxn.com/d/companies/cortec/__OZRSTJXAPix1rgRSaSrVLabWnpGr5XZoPeL0UdcQ51Q)
- [Investor Relations - CorTec Neuro](https://cortec-neuro.com/investor-relations/)
- [CorTec: A Software Interface for Developing Next Generation Neurotherapies](https://cortec-neuro.com/story/a-software-interface-for-developing-next-generation-neurotherapies/)

## 未検証

参照したのは公開の紹介ページ・プレスリリース・二次情報（Tracxn等）であり、SDK文書やAPI仕様書といった一次資料は未取得。資金調達額$21.6Mの内訳・直近ラウンドの詳細条件は確認できていない。デバイス層が安全制約をどの粒度で強制するのか、研究者アプリがどこまでのパラメータを直接指定できるのかも未確認（[[BCI用ソフトウェア基盤の実装状況]]と同じ限界）。うつ病治療研究の実施時期・脳卒中リハビリpivotal trialの規模は2026年8月時点で未確定。

---

Relevant Notes:
- [[BCI用ソフトウェア基盤の実装状況]] -- Brain Interchangeのアプリ層/デバイス層分離を含む、BCIソフトウェア基盤全般の調査
- [[神経刺激の安全限界とシャノン基準]] -- コンプライアンス電圧などデバイス層が強制する安全制約の理論的背景
- [[主流BCI方式と企業比較]] -- Neuralink・Synchron等との侵襲度比較の中でのBrain Interchangeの位置づけ

Topics:
- [[00_index]]
