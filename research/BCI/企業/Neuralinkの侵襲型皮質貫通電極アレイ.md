---
domain: research
type: 調査
status: 要更新
description: "運動野に1,024本の極細電極線を刺入するNeuralink N1の臨床進捗(PRIME試験)と、電極スレッド後退・グリオーシスによる長期安定性の課題を整理"
tags:
  - BCI
  - Neuralink
topics:
  - "[[00_index]]"
---

# Neuralinkの侵襲型皮質貫通電極アレイ（N1）

## 要約

Neuralinkは脳に直接、極細の電極を刺す方式で、他社より細かく信号を読める。ただし脳という柔らかい組織に硬い電極を刺すため、時間が経つと電極がずれて信号が弱くなる問題を抱えている。

## わかったこと

ロボット手術で運動野に1,024本の極細電極線を刺入。2024年1月に初のヒト植込み（Noland Arbaugh氏）を実施し、思考のみでチェスを操作する実証で注目を集めた。PRIME試験で少なくとも21例に植込み済み。20,000 samples/sec、10bit分解能、チャンネルあたり約200kbps、全体で生データ約200Mbps。

記録方式は皮質内穿通電極（intracortical）で、個々のニューロンの活動電位（spike）を直接拾う。空間分解能は単一ニューロン〜小集団レベルであり、[[主流BCI方式と企業比較]]で対比したSynchronの血管内留置電極（LFP・集団平均レベル）より原理的に解像度が高い。実効性能は初期の被験者で4〜10bps、最高記録9.5bps（カーソル操作タスク）。一般整理では侵襲型（皮質内電極）は50〜100bpsでフルタイピング速度に足るとされる。

長期安定性には課題がある。最初の被験者で術後約3ヶ月の時点で電極スレッドの約85%が脳組織から後退（retraction）し、信号捕捉能力が急激に低下した。追加手術なしに記録・デコードアルゴリズムの改良で対処し性能は回復したが、これはソフトウェア側の代償でありハードウェアの位置ズレ自体は未解決。原因は組織の拍動・呼吸による機械的マイクロモーションと、異物反応としてのグリオーシス（電極周囲の瘢痕組織形成によるSN比の年単位劣化）——慢性神経インプラント全般に共通する既知の失敗モードである。この劣化パターンは[[導電性ポリマー電極材料]]で整理した金属電極の機械的ミスマッチ問題そのものであり、材料面での代替アプローチが検討される背景になっている。

## 出典

- [Neuralink Beyond First Human 2026: Updates](https://axis-intelligence.com/neuralink-beyond-first-human-updates/)
- [PRIME Study Progress Update (Neuralink公式)](https://neuralink.com/updates/prime-study-progress-update/)
- [How Fast Can Neuralink Read the Brain? Speed Breakdown](https://www.neurapod.com/blog/neuralink-brain-read-speed)

## 未検証

電極スレッド後退問題がソフトウェア側の対処以外で（ハードウェア的に）解決される見込みは未確認。21例以降の追加植込みの安定性データ、2026年8月以降の規制承認進捗も要更新のまま残る。

---

Relevant Notes:
- [[主流BCI方式と企業比較]] -- Synchron・Precision Neuroscienceとの解像度・安定性の比較先
- [[導電性ポリマー電極材料]] -- 本ノートのグリオーシス問題に対する材料面での代替アプローチ

Topics:
- [[00_index]]
