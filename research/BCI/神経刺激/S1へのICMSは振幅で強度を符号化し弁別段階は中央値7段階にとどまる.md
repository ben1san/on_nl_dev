---
domain: research
type: 調査
status: 進行中
description: "ヒトS1への皮質内微小電気刺激で弁別できる強度段階が単一電極で中央値7段階・多電極バイオミメティック符号化でも19.5段階にとどまり健常触覚の45〜50段階に届かないこと、および温度はS1に皮質表現がなく記号化と学習によってしか伝えられないことを一次資料で確認した"
tags:
  - BCI
  - 神経刺激
  - FR-11
topics:
  - "[[00_index]]"
---

# S1へのICMSは振幅で強度を符号化し弁別段階は中央値7段階にとどまる

## 要約

脳に電気で「強さ」を伝えるとき、人が確実に区別できる段階は7段くらいしかない。何本もの電極を凝った波形で同時に使っても20段には届かず、生身の指の45〜50段には遠く及ばない。しかも「温かい」という感覚は、狙って作れる場所が体の感覚をつかさどる領域には存在しない。

## 強度を運ぶパラメータは振幅だけである

[[電気刺激によるBCI書き込みと文字表示]]が視覚野への走査刺激で「形」を伝える話だったのに対し、本ノートは体性感覚野（S1）へのICMSで「量」を伝える話を扱う。忘却炉のFR-11が送ろうとしているのは消去量から合成した数値なので、必要なのは形ではなく量の解像度である。

ヒトS1へのICMSの基礎データはFlesher et al. (2016) が確立した。脊髄損傷から10年経過した男性1名のBrodmann area 1に32電極アレイを2枚留置し、カソード相先行の電荷平衡二相性パルス（カソード相200 µs、アノード相400 µs、相間100 µs、25〜300 Hz、最大100 µA）で刺激した結果、検出閾値は59電極で範囲15〜88 µA・中央値34.9 µA、100 µAまでで64電極中59電極が感覚を誘発し、術前MEGマッピングと一致するソマトトピーが6ヶ月間安定した。

**強度に効くパラメータの切り分けが設計上決定的である。** Hughes et al. (2021) は参加者2名で振幅・周波数・パルス列長を系統的に動かし、振幅とパルス列長は全電極で単調に知覚強度を上げるが、**周波数は電極によって強度を上げたり下げたりする**ことを示した。周波数が変えているのは強度ではなく質であり、20 Hzではpressure・tapping・sparkle、100 Hzではbuzzing・vibration・sharpと報告される。著者らの結論は明確で、強度を伝えるには振幅を使うべきで周波数を使ってはならない。**したがって数値を強度として書き込むなら、変調できる軸は実質的に振幅1本しかない。**

「知覚強度は総注入電荷で決まる」という素朴な理解は、多電極条件では成り立たない。Bjånes et al. (2025) は同じ総電荷をより多くの電極へ分散すると報告される強度が**下がる**ことを示し、支配量は総電荷ではなく電極あたりの電荷密度だと結論した。一方で多チャネル化は電極あたりの検出閾値を大きく下げ（1チャネル約12 nC/電極 → 2チャネル8 nC → 4チャネル4 nC）、「自然」と記述される割合を高めた（多チャネル100%対単一チャネル85%）。設計上の主変数は総量ではなく電極あたりの振幅である。

## 弁別できる段階数は一桁で頭打ちになる

最も規模の大きい実測はGreenspon et al. (2025) である。頸髄損傷3名で、ICMSの知覚強度は振幅にほぼ線形に増加し（相関中央値0.97）、これは自然な機械刺激がべき関数（減速指数0.2±0.08）に従うのと符号化則が異なる。振幅弁別閾（JND）の中央値は13.5 µA（四分位8.5〜22.9 µA）だった。

**そこから導かれる段階数が本ノートの中心的な数値である。**

| 条件 | 弁別可能な段階数 | ビット換算 |
| --- | --- | --- |
| 単一電極・線形（flat）符号化 | 中央値7（範囲2〜14） | 約2.8ビット |
| 単一電極・バイオミメティック符号化 | 8→11 | 約3.5ビット |
| 多電極＋バイオミメティック符号化 | 11→19.5 | 約4.3ビット |
| 健常な触覚（同一の力範囲） | 45〜50 | 約5.6ビット |

Flesher et al. (2016) も同じ趣旨の見積りを述べており、検出閾値（典型20〜50 µA）とJND（約15 µA）から「多くの電極は100 µAまでに4〜6段階の識別可能な強度勾配を作れる」と結論している。単一被験者の推定と3名の実測が2.0〜2.8ビットの範囲で一致していることになる。

**この天井はダイナミックレンジの狭さから来ている。** 上限100 µAはシャノン基準に基づく安全限界であり（[[神経刺激の安全限界とシャノン基準]]参照）、検出閾値からの倍率はFlesher 2016で約2.9倍、Greenspon et al. (2026) の5名長期データ（中央値14.5〜22.5 µAが4名）でも約4.4〜6.9倍にすぎない。JNDが13〜15 µAと粗く、レンジが3〜7倍しかないため、段階数は構造的に一桁に留まる。Greenspon et al. (2025) 自身も、単一電極では弱い感覚（0.25 N相当未満）しか出せない電極があり、良い電極でも0.5 N相当、物体操作で必要な1 Nには届かないと記している。

**多電極化は線形には効かない。** 同論文は四重刺激の知覚強度が構成要素の和より小さい（劣加算）と明記しており、段階数の増加も11→19.5、すなわちビットでは3.5→4.3の0.8ビット分にしかならない。サルでの直接的な証拠としてOverstreet et al. (2016) があり、2電極では22セッション中7セッションで有意だったのに対し3電極では9セッション中2セッションのみで、符号化方向を4から8へ増やすと精度が大幅に低下した。電極数を増やせば情報量が比例して増えるという想定は、書き込み側では読み取り側（[[電極数を増やしても出力帯域は毎秒10ビットを超えない]]）と別の理由で崩れる。

**Weber分率を単一の値として仮定してはならない。** Flesher et al. (2016) はJNDが基準振幅（20 µAと70 µA）に依存しなかったと報告しており（P=0.86）、これはWeberの法則が成立していないことを意味する。対してGreenspon et al. (2025) は「JNDはWeberの法則に従うが、その傾向は電極間で大きくばらつく」とする。両者は食い違っており、電極ごとの実測なしに段階の刻みを決められない。

**時間方向の制約も強い。** Hughes, Flesher & Gaunt (2022) は、高周波の連続刺激では全プロトコルで1分以内に感覚が完全消失し、数秒の間隔を空けた間欠刺激なら3分以上持続すると示した。**連続的な高レート書き込みは物理的に不可能で、「短い刺激列＋数秒の回復間隔」が実用パターンになる。** 単一電極の2.8ビットをこの周期で送ると毎秒0.5〜3ビット程度が上限という推定になるが（本ノートでの導出、原著記載値ではない）、ICMSによる感覚フィードバックの情報伝達レートを直接測定した研究は見つけられなかった。

強度以外の軸に情報を載せる方向のほうが有望に見える。Valle et al. (2025) は空間的にパターン化された投射野を持つ電極群の同時刺激でエッジ（線分）の感覚を誘発し、時空間パターン化により皮膚上の運動感覚を速度・方向まで制御して誘発した。段階数を増やすより空間・時間パターンを使うほうが帯域拡張の余地がある。

## 温度はS1に書き込めない

[[BCI熱感知書き込みの脳内経路]]はヒトの島皮質刺激で温感が誘発されることを扱ったが、S1側の事情はさらに厳しい。

**皮質表現そのものが存在しない。** Vestergaard et al. (2023) はマウス前肢系の広視野・2光子カルシウムイメージングで、一次体性感覚野には**冷覚の表現はあるが温覚の表現はなく**、温覚と冷覚の両方を持ちしかも体部位対応的に配列されているのは**後部島皮質**であると示した。可逆的な操作実験で島皮質が温度知覚に決定的な影響を持つことも確認されている。S1のハンドエリアに電極を刺しても、そこに狙って刺激すべき温度地図は無い。

**ただし「S1では温感が出ない」と言い切るのも誤りである。** Flesher et al. (2016) のTable 1は報告された感覚質の内訳（総数190）を載せており、Pressure 128、Tingle 79、Electrical 29に対して**Warm 30、Cool 0**が記録されている。温感の報告は実在し、しかも冷感はゼロという非対称がある。これはVestergaardのマウス知見（S1は冷覚のみ）と逆方向であり、興味深い食い違いとして残る。とはいえこれは選択肢リストからの複数選択回答であって温度を制御変数として符号化した実験ではなく、後続の大規模研究（Greenspon et al. 2026の5名・最長10年、Greenspon et al. 2025の3名）では温度が主要な感覚質カテゴリとして現れない。**再現性のある温度チャネルとして使える証拠はない。**

**実効的な道は記号化と学習である。** これは複数の系で実証されている。Dadarlat, O'Doherty & Sabes (2015) はサルが8電極の多チャネルICMSによる当初まったく未知の符号（電極間の相対パルスレートで方向、全電極の線形スケーリングで距離）を学習し、視覚とベイズ最適に統合することを示した（ICMS単独の方向推定 $R^2=0.900$／0.948）。ただし学習コストは20,000〜40,000試行と大きい。Senneka & Dadarlat (2026) はマウスで約1,000試行・多感覚試行75%精度に到達し、ICMSでの成績が自然視覚と同等以上だったと報告している。古典的にはRomo et al. (1998) が、area 3bへのICMSによる周波数弁別が自然な機械振動による弁別と行動的に区別できないことを示している。

ヒトで最も設計に近いのはVerbaarschot et al. (2025) である。四肢麻痺の3名が各3電極で盲検下に刺激パラメータ（振幅10〜100 µA、周波数20〜150 Hzの10段階、バイオミメティック係数0〜10、ドラッグ0〜2）を自分で調整し、5つの仮想物体に対応する感覚を作った。参加者は猫について「それにはある種の温かさすらある」、りんごについて「少し冷たくて湿っている」と述べ、統計上も温度次元が観測された分散の大半を説明し、刺激パラメータとの粗い対応も見出された。ただし著者ら自身が視覚情報の寄与を認めており、直接的な温覚誘発ではなく連想的・解釈的なものである。5物体の分類成績もチャンス20%に対し22〜37%と絶対値は低い。

**忘却炉の設計への含意は明快である。** 温度を「温かさそのもの」として書き込む経路はS1には無く、島皮質を狙う経路も慢性ICMSでの実証例が存在しない。したがって義体化ユーザーへ温度を届けるとは、温度を温度として再現することではなく、**装置が算出した量を数段階の記号へ量子化し、その記号の意味を利用者に学習させること**である。この結論は[[FR-11感覚配信における忘却炉と電脳側の処理境界]]が「単一スキーマへの優雅な劣化という発想自体が効かない」と述べた判断を、書き込み側の生理から裏付ける。

## 出典

- Flesher SN, Collinger JL, Foldes ST, Weiss JM, Downey JE, Tyler-Kabara EC, Bensmaia SJ, Schwartz AB, Boninger ML, Gaunt RA. "Intracortical microstimulation of human somatosensory cortex." *Science Translational Medicine*. 2016;8(361):361ra141. DOI: 10.1126/scitranslmed.aaf8083, PMID: 27738096
- Flesher SN, Downey JE, Weiss JM, Hughes CL, Herrera AJ, Tyler-Kabara EC, Boninger ML, Collinger JL, Gaunt RA. "A brain-computer interface that evokes tactile sensations improves robotic arm control." *Science*. 2021;372(6544):831-836. DOI: 10.1126/science.abd0380, PMID: 34016775, PMCID: PMC8715714
- Greenspon CM, Valle G, Shelchkova ND, et al. "Evoking stable and precise tactile sensations via multi-electrode intracortical microstimulation of the somatosensory cortex." *Nature Biomedical Engineering*. 2025;9(6):935-951. DOI: 10.1038/s41551-024-01299-z, PMID: 39643730, PMCID: PMC12176618
- Greenspon CM, Hobbs TG, Verbaarschot C, et al. "Long-term safety and efficacy of intracortical microstimulation in humans." *Science Translational Medicine*. 2026;18(858):eaec3728. DOI: 10.1126/scitranslmed.aec3728, PMID: 42455900（プレプリント: medRxiv 2025.08.11.25332271, PMCID: PMC12363726）
- Hughes CL, Flesher SN, Weiss JM, Boninger M, Collinger JL, Gaunt RA. "Perception of microstimulation frequency in human somatosensory cortex." *eLife*. 2021;10:e65128. DOI: 10.7554/eLife.65128, PMID: 34313221, PMCID: PMC8376245
- Hughes CL, Flesher SN, Gaunt RA. "Effects of stimulus pulse rate on somatosensory adaptation in the human cortex." *Brain Stimulation*. 2022;15(4):987-995. DOI: 10.1016/j.brs.2022.05.021, PMID: 35671947, PMCID: PMC10308851
- Hobbs TG, Greenspon CM, Verbaarschot C, Valle G, Hughes CL, Boninger ML, Bensmaia SJ, Gaunt RA. "Biomimetic stimulation patterns drive natural artificial touch percepts using intracortical microstimulation in humans." *Journal of Neural Engineering*. 2025;22(3). DOI: 10.1088/1741-2552/adc2d4, PMID: 40106898
- Bjånes DA, Bashford L, Pejsa K, Lee B, Liu CY, Andersen RA. "Charge density of multi-channel intra-cortical micro-stimulation modulates intensity and naturalness of evoked somatosensations." *Journal of Neural Engineering*. 2025;22(6):066025. DOI: 10.1088/1741-2552/ae1bd8, PMID: 41191971
- Valle G, Alamri AH, Downey JE, et al. "Tactile edges and motion via patterned microstimulation of the human somatosensory cortex." *Science*. 2025;387(6731):315-322. DOI: 10.1126/science.adq5978, PMID: 39818881, PMCID: PMC11994950
- Overstreet CK, Hellman RB, Ponce Wong RD, Santos VJ, Helms Tillery SI. "Discriminability of Single and Multichannel Intracortical Microstimulation within Somatosensory Cortex." *Frontiers in Bioengineering and Biotechnology*. 2016;4:91. DOI: 10.3389/fbioe.2016.00091, PMID: 27995126, PMCID: PMC5133427
- Vestergaard M, Carta M, Güney G, Poulet JFA. "The cellular coding of temperature in the mammalian cortex." *Nature*. 2023;614(7949):725-731. DOI: 10.1038/s41586-023-05705-5, PMID: 36755097, PMCID: PMC9946826
- Verbaarschot C, Karapetyan V, Greenspon CM, Boninger ML, Bensmaia SJ, Sorger B, Gaunt RA. "Conveying tactile object characteristics through customized intracortical microstimulation of the human somatosensory cortex." *Nature Communications*. 2025;16(1):4017. DOI: 10.1038/s41467-025-58616-6, PMID: 40312384, PMCID: PMC12046030
- Dadarlat MC, O'Doherty JE, Sabes PN. "A learning-based approach to artificial sensory feedback leads to optimal integration." *Nature Neuroscience*. 2015;18(1):138-144. DOI: 10.1038/nn.3883, PMID: 25420067, PMCID: PMC4282864
- Senneka SJ, Dadarlat MC. "Integration of learned artificial sensation with vision during freely moving navigation." *PNAS*. 2026;123(9):e2521769123. DOI: 10.1073/pnas.2521769123, PMID: 41758662
- Romo R, Hernández A, Zainos A, Salinas E. "Somatosensory discrimination based on cortical microstimulation." *Nature*. 1998;392(6674):387-390. DOI: 10.1038/32891, PMID: 9537321
- Osborn LE, Christie BP, McMullen DP, et al. "Intracortical microstimulation of somatosensory cortex enables object identification through perceived sensations." *Annual International Conference of the IEEE EMBS*. 2021;2021:6259-6262. DOI: 10.1109/EMBC46164.2021.9630450, PMID: 34892544
- Duong A, Quabs J, Kucyi A, Lusk Z, Buch V, Caspers S, Parvizi J. "Subjective states induced by intracranial electrical stimulation matches the cytoarchitectonic organization of the human insula." *Brain Stimulation*. 2023;16(6):1653-1665. DOI: 10.1016/j.brs.2023.11.001, PMID: 37949296, PMCID: PMC10893903

## 未検証

ICMSによる感覚フィードバックの情報伝達レート（bits/second）を直接測定した一次研究は見つけられなかった。本ノートの毎秒0.5〜3ビットという値は、段階数と適応の時間定数から導いた推定であって原著記載値ではない。上限100 µAの根拠であるシャノン基準の原著（Shannon 1992, IEEE Trans Biomed Eng）は直接取得しておらず、無次元数kの閾値（安全域 $k\le1.5$、損傷観察 $k\ge1.85$）は二次資料経由の確認に留まる。

島皮質へのICMSで制御された温度感覚を書き込んだ実証例は見つからなかった。Duong et al. (2023) はてんかん評価用の頭蓋内電極による刺激であり、慢性留置の感覚義肢ではない。ヒトS1における温度の体部位対応地図の不在も、Vestergaard et al. (2023) がマウスでの結果であるためヒトでの直接検証は未確認である。多電極ICMSで弁別可能な空間位置数（空間方向のビット数）についても明示的な数値を見つけられなかった。

Flesher et al. (2016) のWarm 30件・Cool 0件という非対称が何に由来するのか、単一被験者の特異性なのか報告形式の偏りなのかは未検証である。この点はマウスの知見と逆方向であるため、ヒトS1の温度応答は再調査に値する。

---

Relevant Notes:
- [[BCI熱感知書き込みの脳内経路]] -- 温度感覚がS1と島皮質へ分岐する解剖学的経路。本ノートはその島皮質側の対としてS1側の限界を定量した
- [[電気刺激によるBCI書き込みと文字表示]] -- 同じ書き込み側で「形」を扱う姉妹ノート。本ノートは「量」を扱う
- [[電極数を増やしても出力帯域は毎秒10ビットを超えない]] -- 読み取り側の帯域天井。書き込み側の天井が別の理由（安全限界とJND）で生じることの対比先
- [[神経刺激の安全限界とシャノン基準]] -- 上限100 µAという天井の定量的根拠
- [[FR-11感覚配信における忘却炉と電脳側の処理境界]] -- 本ノートの段階数が、送るべき演出値の粒度を決める先
- [[接触プレートの42℃上限と体感を決める接触条件]] -- 生身の掌で温度を感じる側の閾値。書き込み側と対比する基準

Topics:
- [[00_index]]
