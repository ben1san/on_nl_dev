---
domain: research
type: 調査
status: 進行中
description: "自己拡張型ステント電極を頸静脈から血管経由で留置するSynchron Stentrodeの臨床進捗(COMMAND試験)と、血管壁越し記録による安定性と情報密度のトレードオフを整理"
tags:
  - BCI
  - Synchron
  - Stentrode
topics:
  - "[[00_index]]"
---

# Synchronの血管内留置型BCI（Stentrode）

## 要約

Synchronは血管の中から脳に電極を届けるので、頭を開ける手術が要らない。信号は粗いが、電極が組織を傷つけない分、長持ちしやすい方式である。

## わかったこと

自己拡張型ニチノールステントに白金-イリジウム薄膜電極（16個）を組み込み、頸静脈からカテーテルで上矢状静脈洞（一次運動野に隣接）まで進めて留置する。脳卒中治療で確立済みの神経血管内治療の術式を転用しており、開頭手術・脳実質の貫通が不要。COMMAND試験（2024年9月発表）で6例全員が一次安全性エンドポイントを達成、Apple Vision Pro / Alexaの脳信号操作を実証。2026年、FDA PMA取得に向けたpivotal trial段階にある。

記録方式は血管内留置電極（endovascular、ECoG類似）で、捕捉する信号は局所フィールド電位（LFP、主にhigh-gamma帯域）。空間分解能は数千〜数万ニューロンの集団平均レベルにとどまる（電極数16個・間隔3mm）。血管壁越しの間接記録でLFP/ECoG的な性質の信号しか得られないため、[[主流BCI方式と企業比較]]で対比したNeuralinkの皮質内穿通電極ほどの解像度は出ない。

実効性能は5bps未満で、アイトラッカー併用でタイピング速度14〜20文字/分、クリック確定に300〜900msの持続的な運動意図が必要になる。低侵襲型（endovascular・表面電極）は一般に10〜25bpsでコマンド/カーソル操作は可能だが文字単位のテキスト構成には力不足とされる。ただし血管壁・硬膜を介した信号減衰は致命的ではないという知見もある。血管内電極のSNRは硬膜下・硬膜外センサーと有意差がないとする比較研究があり、埋込み後の血管内皮化がむしろ信号安定性を向上させる報告もある。Synchronの制約は「信号が弱い」ことよりも「電極数が少なくニューロン単位の発火を拾えない」という構造的な情報密度の低さに起因する。

長期安定性では、血管を貫通しないためグリオーシス駆動の電極後退メカニズムが起きにくく、むしろステントが血管内皮に取り込まれる（endothelialization）ことで信号がより安定化するという報告がある。これは[[主流BCI方式と企業比較]]で対比したNeuralinkの電極後退問題とは対照的な劣化パターンである。

## 出典

- [The Stentrode System by Synchron: Architectural Design and Clinical Translation (ResearchGate)](https://www.researchgate.net/publication/395700531_The_Stentrode_System_by_Synchron_Architectural_Design_and_Clinical_Translation_of_a_Minimally_Invasive_Brain-Computer_Interface)
- [Synchron Announces Positive Results from U.S. COMMAND Study (BioSpace)](https://www.biospace.com/news/synchron-announces-positive-results-from-u-s-command-study-of-endovascular-brain-computer-interface)
- [Signal quality of simultaneously recorded endovascular, subdural and epidural signals are comparable (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5976775/)

## 未検証

FDA PMA取得の実際の時期、pivotal trialの規模・結果は2026年8月時点で未確定。血管内皮化による長期安定化の主張は今回参照した文献の範囲での整理であり、より長期（数年単位）の追跡データは確認できていない。

---

Relevant Notes:
- [[主流BCI方式と企業比較]] -- Neuralinkとの解像度・安定性の比較先
- [[導電性ポリマー電極材料]] -- 金属電極の機械的ミスマッチ問題への材料面での代替アプローチ

Topics:
- [[00_index]]
