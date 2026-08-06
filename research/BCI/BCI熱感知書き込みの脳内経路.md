---
domain: research
type: 調査
status: 進行中
description: "温度感覚が識別的経路(S1)と情動的経路(VMpo→後部島皮質Ig2/Id2)に解剖学的に分岐する事実を一次資料(Duong 2023, Mazzola 2017)で検証し、全脳被覆型BCIが島皮質という埋没構造へ到達する手段として導電性ポリマーの可撓性が鍵になるという設計上の含意を整理"
tags:
  - BCI
  - 神経刺激
  - 島皮質
topics:
  - "[[00_index]]"
---

# BCI熱感知書き込みの脳内経路 -- 体性感覚野と島皮質の二経路

## 要約

温度を感じる仕組みは、脳の中で「どこがどれくらい熱いか」を伝える経路と「それがどう感じられるか」を伝える経路の二つに分かれている。後者が届く先は脳の表面ではなく奥深くの折れ込みの中にあるため、そこに電極を届けるにはやわらかい材料が要る。忘却炉から熱を電脳へ直接送る機能は、この二経路のどちらを狙うかで体験の質が変わる。

## わかったこと

[[電気刺激によるBCI書き込みと文字表示]]がV1のretinotopy（網膜部位対応）を利用した視覚情報の書き込みを扱ったのに対し、本ノートは同じ「書き込み」でも温度感覚を対象にする。忘却炉のFR-11（感覚のAPI化、義体化ユーザー対応）が前提とする「熱を電脳へ送る」機能の生理学的な着地点はどこかを一次資料で検証した。

**温度感覚は末梢から二経路に分岐している。** 温度感覚は単一の皮質部位に対応しない。末梢の脊髄後角lamina Iから始まり、視床で二つの経路に分岐する（Craigの内受容モデル。要検証: 用語としての枠組み自体は広く参照されるが本ノートでは概説レベルの再確認に留まる）。

| 経路 | 中継核 | 皮質終着点 | 運ぶ情報 |
|---|---|---|---|
| 識別的（discriminative） | 視床VPL/VPM | 一次体性感覚野(S1)、中心後回の体部位対応(homunculus) | どこが・どれくらいの温度か |
| 情動的・内受容的（interoceptive/affective） | 視床VMpo（後内側腹側核） | 背側後部島皮質（dorsal posterior insula） | それがどう「感じられるか」 |

VMpoが背側後部島皮質への主要な投射先であることは組織学的に同定されている（Blomqvist A, Zhang ET, Craig AD. "Cytoarchitectonic and immunohistochemical characterization of a specific pain and temperature relay, the posterior portion of the ventral medial nucleus, in the human thalamus." Brain. 2000;123(3):601-619）。ただしVMpoがヒトで独立した核として実在するか自体に批判的レビューが存在し、経路の解剖学的実体には論争が残る（Willis WD Jr, Zhang X, Honda CN, Giesler GJ Jr. "A critical review of the role of the proposed VMpo nucleus in pain." J Pain. 2002;3(2):79-94. PMID: 14622792）。

**島皮質への直接電気刺激で温感が誘発されることは一次資料で確認できている。** Duong et al. (Brain Stimulation, 2023, DOI: 10.1016/j.brs.2023.11.001, PMID: 37949296) はSEEG電極ペア57組への刺激（双極、1〜3秒、50Hz、2〜10mA、after-discharge閾値未満）を報告した。57組中30組（53%）が痛み/温度感覚を誘発し、うち22組が明確な温感（"warm bath"「温かい風呂」、"hot boiling sensation"「熱く煮えたぎる感覚」）を示した。誘発部位は細胞構築学的に後部島皮質のIg2・Id2領域に集中し、93%が右半球という強いラテラリティが見られた。電極位置が上方に移動するにつれ、四肢から体幹・肩へ「温かさが広がる」報告があり、局在感覚が空間的に連続変化することも確認された。

**島皮質は温度専用のチャンネルではなく多モーダルに混線する。** Mazzola L, Mauguière F, Isnard J. "Electrical Stimulations of the Human Insula: Their Contribution to the Ictal Semiology of Insular Seizures." J Clin Neurophysiol. 2017;34:307-314（PMID: 28644200）は1997〜2015年の222例・669回の刺激を総括し、550回に臨床反応（体性感覚・内臓感覚が75.9%）を確認した。痛み・喉頭痙攣・前庭・聴覚・嗅味覚症状が同一部位から混在して誘発されることが示されている。Duong et al. (2023)も「温感と痛みは同じ被験者報告としてまとめて分類した」と明記しており、「温かさだけ」を選択的に誘発するクリーンなチャンネルは島皮質に存在しない。

**全脳を導電性ポリマーで覆っても島皮質には届かないという幾何学的制約がある。** ヒト大脳皮質の表面積の大部分は脳溝(sulcus)の中に埋もれ、露出しているのは脳回(gyrus)の頂上のみである（比率は目安、厳密な出典未確認）。島皮質はシルビウス裂の奥に完全に埋没しており、脳表を這う単純なシート型電極（Precision Neuroscience Layer 7のような設計）では到達できない。到達するには脳溝への折り込みか貫通型深部電極が必要になる。一方S1（中心後回）は脳回の凸面にあり、シート型電極でも比較的到達しやすい。「全脳被覆」の技術的難度は部位によって非対称であり、S1書き込み（局在化した温感の再現）と島皮質書き込み（情動的・内受容的な温感の再現）とでは要求される電極形態が異なる。

**導電性ポリマーの可撓性が島皮質到達の技術的な鍵になりうる。** [[導電性ポリマー電極材料]]で整理した通りPEDOT系・Axoft Fleuronの最大の特長は電気特性だけでなく機械的柔軟性（ポリイミド電極比で最大1万倍柔らかい）である。この柔軟性は、剛体アレイでは不可能な「脳溝の起伏に自己コンフォーマルに密着し折り畳まれる」という経路を理論上可能にする。これが成立すれば、貫通せずに島皮質へ到達する手段になりうる（本セッションでの一次資料確認は未実施 — 要検証）。

**書き込み先の選択が体験の質を分ける。** S1（手のひら領域相当）に書けば、局在化した「掌が温かい」感覚になり、忘却炉の実体験（接触プレート）に最も忠実な再現になる。一方、島皮質・ACCに直接書けば、身体上のどこにも定位しない全身的・情動的な「温かさに包まれる」感覚になる。身体部位を経由しない分、[[00_concept/idea|idea]]が志向する自己の境界の融解・宇宙への溶け込みに、生身の体験より近づく可能性がある。ただし島皮質は痛みとの混線が構造的にあるため、狙って「温かさだけ」を誘発できる保証がなく、S1より設計難度が高い。

## 出典

- Duong A, Quabs J, Kucyi A, Lusk Z, Buch V, Caspers S, Parvizi J. "Subjective states induced by intracranial electrical stimulation matches the cytoarchitectonic organization of the human insula." Brain Stimulation. 2023. DOI: 10.1016/j.brs.2023.11.001, PMID: 37949296
- Mazzola L, Mauguière F, Isnard J. "Electrical Stimulations of the Human Insula: Their Contribution to the Ictal Semiology of Insular Seizures." J Clin Neurophysiol. 2017;34:307-314. PMID: 28644200
- Blomqvist A, Zhang ET, Craig AD. "Cytoarchitectonic and immunohistochemical characterization of a specific pain and temperature relay, the posterior portion of the ventral medial nucleus, in the human thalamus." Brain. 2000;123(3):601-619
- Willis WD Jr, Zhang X, Honda CN, Giesler GJ Jr. "A critical review of the role of the proposed VMpo nucleus in pain." J Pain. 2002;3(2):79-94. PMID: 14622792

## 未検証

Craigの内受容モデルという枠組み自体の妥当性は概説レベルの再確認に留まり、一次資料での検証はしていない。VMpoがヒトで独立した核として実在するかは解剖学的に論争が残っている。導電性ポリマーの可撓性が実際に脳溝への折り込みを介して島皮質へ到達できるかは、本ノートでは理論的な推論であり一次資料での確認は未実施。S1と島皮質それぞれへの書き込みが実際にどの程度の設計難度・安全性の差になるかも未検証。

---

Relevant Notes:
- [[電気刺激によるBCI書き込みと文字表示]] -- 同じ「脳への書き込み」を視覚野retinotopyで扱った対をなすノード。走査刺激の方法論が本ノートの出発点
- [[導電性ポリマー電極材料]] -- 島皮質到達の鍵として言及した機械的柔軟性のデータ元
- [[00_concept/idea|idea]] -- 「熱感知センサーが自分の体に搭載されていないかもしれないので、忘却炉から温度情報を送ってあげる」という義体化バリアフリーの発想源。書き込み先の選択（S1 vs 島皮質）が同ノートの自己の境界融解というテーマとどう接続するかの論点はここに由来する

Topics:
- [[00_index]]
