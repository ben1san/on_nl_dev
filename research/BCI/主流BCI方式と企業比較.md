---
domain: research
type: 調査
status: 進行中
description: "Neuralink・Synchron・Precision Neuroscience・Merge Labsを侵襲度別に並べ、電極方式ごとの信号解像度(bps)・長期安定性のトレードオフを比較した合成ノート。各社の詳細は個社ノートを参照"
tags:
  - BCI
  - 電脳化社会
topics:
  - "[[00_index]]"
---

# 主流BCI方式と企業比較 -- 侵襲度別の技術地図

## 要約

脳とコンピュータをつなぐ技術には、頭を開けずに済む方式から脳に直接電極を刺す方式まで侵襲度に幅がある。侵襲度が低いほど安全だが得られる情報は粗く、侵襲度が高いほど情報は精密だが劣化も早い。どちらが先に普及するかで、忘却炉が想定する電脳社会の姿が変わる。

## わかったこと

2026年8月時点で臨床開発が進む主要BCI企業を、侵襲度の低い順に並べる。各社固有の技術詳細・臨床進捗・出典は個別ノートに分離した——[[Merge Labsの非侵襲超音波方式]]、[[Synchronの血管内留置型BCI]]、[[Precision Neuroscienceの脳表面設置型BCI]]、[[Neuralinkの侵襲型皮質貫通電極アレイ]]。本ノートは4社を横断する比較表と、忘却炉プロジェクトが扱う「電脳化した人間とそうでない人間の出力格差」という予測軸への含意だけを保持する。

| | 侵襲度 | 記録方式 | 電極数 | 実効bps | 長期安定性 |
|---|---|---|---|---|---|
| Merge Labs | 非侵襲（超音波） | 未確立 | — | 未検証 | 未検証 |
| Synchron (Stentrode) | 血管内留置（開頭なし） | 血管内留置電極、LFP | 16 | 5bps未満 | 血管内皮化でむしろ安定化 |
| Precision Neuroscience (Layer 7) | 脳表面設置（微小侵襲） | ECoG類似 | 1,024 | 未検証 | 貫通しないため除去容易 |
| Neuralink (N1) | 侵襲（皮質貫通） | 皮質内穿通電極、spike | 1,024超 | 4〜10bps（最高9.5） | 3ヶ月で電極85%後退 |

### 信号の種類と解像度は記録方式の違いで根本的に決まる

NeuralinkとSynchronはそもそも捕捉している信号の階層が異なる。Neuralinkは組織を直接貫通して個々のニューロンの発火を拾うため原理的に解像度が高く、Synchronは血管壁越しの間接記録でLFP/ECoG的な性質の信号しか得られない。一般整理では、侵襲型（皮質内電極）は50〜100bpsでフルタイピング速度に足り、低侵襲型（endovascular・表面電極）は10〜25bpsでコマンド/カーソル操作は可能だが文字単位のテキスト構成には力不足とされる。

### 「解像度で勝るNeuralink」「安定性で勝るSynchron」という構図

両者が選んだ侵襲方式の根本設計思想の違いから必然的に生じている。Neuralinkは機械的ミスマッチに由来するグリオーシス・電極後退という金属電極特有の劣化を抱え（[[導電性ポリマー電極材料]]が材料面での対抗策を扱う）、Synchronは血管を貫通しないためこの劣化メカニズムが起きにくい。侵襲度と解像度・安定性がトレードオフの関係にあるという構図そのものが、忘却炉が想定する電脳社会像のうちどの方式が先に一般に普及するかを左右する。

## 出典

- [BCI Clinical Trials 2026: Neuralink, Synchron, Precision (NWI)](https://nextwavesinsight.com/bci-neuralink-synchron-clinical-trials-2026/)
- [Brain-Computer Interfaces in 2026: Neuralink, Synchron, and the Patient Pathway](https://pdpspectra.com/blog/brain-computer-interfaces-neuralink-2026/)
- [The Past, Present And Future Of Brain-Computer Interfaces (Forbes, 2025)](https://www.forbes.com/sites/robtoews/2025/10/05/these-are-the-startups-merging-your-brain-with-ai/)
- [But do we need high bandwidth? (IOPscience)](https://iopscience.iop.org/article/10.1088/1741-2552/ae6dfd)

## 未検証

Merge Labsの実効bps・長期安定性は資料がなく未検証。Precision NeuroscienceのbpsデータもLayer 7の性能公開が限られており未確認。4社を跨いだ比較表そのものは今後各社の進捗更新に応じて要更新になる可能性が高いが、個社ごとの事実は分離済みなので、更新は該当する個社ノートの方で先に反映し、本表への統合は後追いでよい。

---

Relevant Notes:
- [[00_concept/idea|idea]] -- 忘却炉の電脳社会像という企画初期の直感的アイデアが、本ノートの技術的検証の起点になっている
- [[04_foresight/trends|trends.md]] -- 本ノートの要約が統合される技術動向の親ノート
- [[04_foresight/forecast|forecast.md]] -- 本ノートのエビデンス（各社の規制承認・臨床進捗）に基づき電脳社会の普及タイムライン予測を更新する土台
- [[導電性ポリマー電極材料]] -- ここで比較した金属電極の機械的ミスマッチ・グリオーシス問題に対する材料面での代替アプローチ

Topics:
- [[00_index]]
