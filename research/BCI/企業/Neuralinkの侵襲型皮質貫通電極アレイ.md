---
domain: research
type: 調査
status: 進行中
description: "運動野に1,024本の極細電極線を刺入するNeuralink N1の2026年8月時点の臨床進捗と電極スレッド後退の課題を整理し、同社が刺激すなわち脳への書き込みをヒトでも動物でも一度も実証しておらずBlindsightのヒト植込みが未実施であることを一次資料で確認した"
tags:
  - BCI
  - Neuralink
topics:
  - "[[00_index]]"
---

# Neuralinkの侵襲型皮質貫通電極アレイ（N1）

## 要約

Neuralinkは脳に直接、極細の電極を刺す方式で、他社より細かく信号を読める。ただし脳という柔らかい組織に硬い電極を刺すため、時間が経つと電極がずれて信号が弱くなる問題を抱えている。そしてこの会社がやっているのは今のところ脳を読むことだけで、脳へ書き込む側は一度も実演されていない。

## 読み取り側の構成と実績

ロボット手術で運動野に1,024本の極細電極線を刺入する。2024年1月に初のヒト植込み（Noland Arbaugh氏）を実施し、思考のみでチェスを操作する実証で注目を集めた。20,000 samples/sec、10bit分解能、チャンネルあたり約200kbps、全体で生データ約200Mbps。

記録方式は皮質内穿通電極（intracortical）で、個々のニューロンの活動電位（spike）を直接拾う。空間分解能は単一ニューロン〜小集団レベルであり、[[主流BCI方式と企業比較]]で対比したSynchronの血管内留置電極（LFP・集団平均レベル）より原理的に解像度が高い。同社公表のWebgrid指標では8例目の被験者が10.39 BPSに到達しており、健常者のマウス操作（8〜10 BPS）と同等だとしている。ただしこれは企業公表値であって査読を経た数値ではない。査読論文で確認できる皮質内BCIのタイピング性能は毎分110字・単語誤り率1.6%（Jude et al. 2026, *Nature Neuroscience*）である。

**公表されている最新の症例数は21例で、その出典は2026年1月28日時点のものである。** 同社公式アップデート "Two Years of Telepathy"（同日付）によれば、手術は2024年上半期に1件、2024年下半期に2件、2025年上半期に4件、2025年下半期に13件と加速しており、重篤なデバイス関連有害事象ゼロの記録を維持している。2026年8月時点でこれを更新する公式発表は確認できていないため、実際の症例数はこれより多い可能性が高い。Reutersも同日に21名という数字を報じた。登録されている臨床試験はPRIME（NCT06429735）、CAN-PRIME（NCT06700304）、CONVOY（NCT06710626、ロボットアーム）、UAE-PRIME（NCT06992596）、GB-PRIME（NCT07127172）、VOICE（NCT07224256、発話復元）の6本である。2026年6月30日には初の経硬膜手技、7月23日には車椅子の思考制御が公式に公開された。今後の改良として電極数を1,000から3,000へ増やす計画が示されている。

## 長期安定性の課題

最初の被験者で術後約3ヶ月の時点で電極スレッドの約85%が脳組織から後退（retraction）し、信号捕捉能力が急激に低下した。追加手術なしに記録・デコードアルゴリズムの改良で対処し性能は回復したが、これはソフトウェア側の代償でありハードウェアの位置ズレ自体は未解決である。原因は組織の拍動・呼吸による機械的マイクロモーションと、異物反応としてのグリオーシス（電極周囲の瘢痕組織形成によるSN比の年単位劣化）——慢性神経インプラント全般に共通する既知の失敗モードである。この劣化パターンは[[導電性ポリマー電極材料]]で整理した金属電極の機械的ミスマッチ問題そのものであり、材料面での代替アプローチが検討される背景になっている。

同社は2026年1月のアップデートで、スレッド後退への対策実施後に続く20名中18名でより高い信号品質を観測したと述べている。ただしこれも企業公表値であり、**Neuralinkはヒト臨床結果の査読論文を一本も公表していない**。同社名義の実質的な査読論文は2019年のMusk E, Neuralink, *Journal of Medical Internet Research* 21(10):e16194 のみである。

## 書き込み側は一度も実証されていない

忘却炉のFR-11が必要とするのは脳への書き込み（刺激）だが、**この点でNeuralinkは参照先にならない**。2026年8月時点で確認できる事実は次の通りである。

**登録6試験はすべて記録のみである。** ロボットアーム試験CONVOYの介入記述も「N1 Implantを用いて神経信号でアシスト用ロボットアームを制御する」であり、感覚フィードバックへの言及は一切ない。主要評価項目は参加者がデバイス制御のために脳活動を変調できる能力である。

**チップは刺激能力を設計上持つが、実演されたことがない。** 2019年の論文本文には「全チャネルで電気刺激が可能なようにNeuralink ASICを設計したが、本稿ではその能力を実証していない」と明記されている。それから7年を経た2026年8月時点でも、ヒトでも動物でも刺激の実証結果は査読論文として公表されていない。

**Blindsightのヒト植込みは実施されていない。** 視覚野刺激による人工視覚プロジェクトBlindsightは2024年9月17日にFDA Breakthrough Device Designationを取得したが、同社公式サイトの試験一覧は視覚補綴を「Upcoming trial（今後の試験）」と表示し、個別ページは「米国で試験を開始したときに通知を受け取るため登録を」と案内している。ClinicalTrials.govにNeuralinkがスポンサーの視覚関連試験は存在しない。Musk自身も2026年1月28日に「規制当局の承認待ちで（Pending regulatory approval）最初のBlindsight augmentを行う準備ができている」と述べており、この時点で承認前であることを認めている。植込み時期の予告は2025年3月に「今年中」、2025年6月に「今後6〜12か月」、2026年8月にも「今後6〜12か月」と繰り返されている。Blindsightのサル前臨床データについても査読論文は存在しない。

**流通している誤情報に注意が要る。** Breakthrough Device Designationは優先審査の枠組みであって販売承認でも治験開始許可でもないが、「FDAがBlindsightを承認」と報じた記事が存在する。「Blindsightは視覚野に3,072電極を置く」という記述も公式には確認できず、3,000という数字は次世代Telepathy実装の目標値（1,000→3,000）である。「2026年初頭のテストで数十年盲目だった患者が閃光や幾何学的輪郭を見たと報告」という記述も一次ソースで裏付けられない。植込み自体が行われていない。

書き込み側で実際に成果を出しているのは別の主体である。詳細は[[脳への書き込みは毎秒数イベントで頭打ちであり電極数の増加では超えられない]]を参照。

## 出典

- Musk E, Neuralink. "An Integrated Brain-Machine Interface Platform With Thousands of Channels." *Journal of Medical Internet Research*. 2019;21(10):e16194. DOI: 10.2196/16194, PMID: 31642810, PMCID: PMC6914248（刺激能力の未実証を明記した本文）
- Neuralink公式アップデート "Two Years of Telepathy". 2026-01-28. https://neuralink.com/updates/two-years-of-telepathy/ （21名、手術タイムライン、電極1,000→3,000）
- Neuralink公式 試験一覧. https://neuralink.com/trials/ （視覚補綴を "Upcoming trial" と表示、2026-08-18取得）
- Neuralink公式 "Neuralink Receives Breakthrough Device Designation for Blindsight". 2024-09-17. https://neuralink.com/updates/neuralink-receives-breakthrough-device-designation-for-blindsight/
- Neuralink公式 Webgrid. https://neuralink.com/webgrid/ （8例目の被験者が10.39 BPS）
- ClinicalTrials.gov: NCT06429735（PRIME）, NCT06700304（CAN-PRIME）, NCT06710626（CONVOY）, NCT06992596（UAE-PRIME）, NCT07127172（GB-PRIME）, NCT07224256（VOICE）。いずれも記録のみで刺激の登録なし（2026-08-18時点）
- Reuters. "Elon Musk's Neuralink says it has 21 participants enrolled in trials". 2026-01-28
- CNBCTV18. 2026-01-29. https://www.cnbctv18.com/technology/elon-musk-neuralink-to-implant-blindsight-vision-chip-in-humans-by-end-of-2026-what-it-means-ws-l-19835492.htm （Muskの2026-01-28投稿 "Pending regulatory approval" の全文引用）
- IEEE Spectrum. "Neuralink's Blindsight Implant". 2024-09-27. https://spectrum.ieee.org/neuralink-blindsight （Ione Fine・Philip Troyk・Gislin Dagnelieによる批判）
- Jude JJ, et al. *Nature Neuroscience*. 2026 Mar 16. DOI: 10.1038/s41593-026-02218-y, PMID: 41840138（皮質内BCIタイピング毎分110字、比較用の査読値）

## 未検証

電極スレッド後退問題がソフトウェア側の対処以外でハードウェア的に解決される見込みは未確認である。2026年1月以降の症例数の更新は確認できておらず、一部の記事が挙げる26例という数字は一次ソースで裏付けられない。「CANAAN試験」という名称の試験は存在せず、CAN-PRIME（NCT06700304）との混同と考えられるが、断定はできない。

Blindsightについては、規制当局の承認取得・植込み実施のいずれも2026年8月18日時点で確認できないという不在の確認に留まる。UAEで実施するという報道もあるが一次ソースでの裏付けは取れていない。同社が刺激機能を将来どの試験で実証するかも未確認である。

本ノートの症例数・信号品質・BPSに関する数値は同社の公表値であり、査読を経ていない。Neuralinkのヒト臨床結果に第三者検証が入っていないという事実自体が、他社との比較を難しくしている。

---

Relevant Notes:
- [[主流BCI方式と企業比較]] -- Synchron・Precision Neuroscienceとの解像度・安定性の比較先
- [[導電性ポリマー電極材料]] -- 本ノートのグリオーシス問題に対する材料面での代替アプローチ
- [[脳への書き込みは毎秒数イベントで頭打ちであり電極数の増加では超えられない]] -- Neuralinkが不在である書き込み側で実際に何が起きているか
- [[電極数を増やしても出力帯域は毎秒10ビットを超えない]] -- 電極数の増加が出力に効かないという、電極1,000→3,000計画への対抗論点

Topics:
- [[00_index]]
