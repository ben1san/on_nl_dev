---
domain: concept
type: "MOC"
status: "進行中"
description: "ランダウアの忘却炉チーム開発の状態ボード兼索引。全ノートは1行でここに載る"
tags: []
topics: []
---

# 00_index — 状態ボード

このファイルは統合担当のみが編集する。他の団員はPR本文に「索引へ載せる1行」を書き、
統合担当がmerge後に反映する。索引に載らないファイルは存在させない。

## 領域とオーナー

| 領域 | オーナー | ブランチ | 状態 |
|---|---|---|---|
| concept | 統合担当 | main | - |
| quantum | 未定 | feature/quantum | - |
| quantum_erasure | 未定 | feature/quantum_erasure | - |
| classical_erasure | 未定 | feature/classical_erasure | - |
| audio_visual | 未定 | feature/audio_visual | - |
| enclosure | 未定 | feature/enclosure | - |
| accessibility | 未定 | feature/accessibility | - |
| research | 未定 | main直 | - |
| foresight | 未定 | main直 | - |

## concept

- [[idea]] -- AI氾濫・電脳化が進む未来で実在が揺らぐことへの応答として、実在の証明ではなく執着の放棄を提案する初期コンセプトメモ
- [[summary]] -- 記憶データを量子乱数で不可逆上書きし熱を手に伝える忘却炉を「記憶を弔うデジタル葬儀」として要約
- [[functional_req]] -- 情報エントロピーを熱エントロピーへ不可逆変換するというコンセプトをFR番号ごとに機能要件へ翻訳
- [[technical_req]] -- 熱破壊回路以外のFRの実現手段とシステム全体アーキテクチャ・BOM・リスク

## quantum

- [[ベル対self-testによるQRNG方式選定]] -- 単一チップ上のCHSH違反観測（Tier 1 self-test）採用の判断根拠
- [[CollapseTransactionによる乱数露出窓とスループットのトレードオフ]] -- 焼却側133µs周期にどのQRNG経路も追いつかず、速度最適化はトレードオフをバッチサイズNへ押し込むだけという結論
- [[量子測定リセットとランダウア4相サイクルの同型性]] -- 量子回路の初期化→ゲート→測定→リセットと古典4相サイクルの構造的対応。QRNGを装置全体の主張の縮小実演へ格上げする根拠

## quantum_erasure

（まだノートがありません）

## classical_erasure

- [[architecture]] -- FR-12熱破壊回路をビットごとの相補コンデンサ対の充放電として実装するアーキテクチャ仕様
- [[components]] -- 相補容量セル+TC4427直接駆動を前提とした部品表と設計パラメータ
- [[circuit_schematic]] -- architectureのブロック図を部品・ピン番号レベルまで展開した回路図
- [[cell_driver_choice]] -- 駆動段を74HCT595からTC4427へ変更した設計判断の記録
- [[erasure_cell_capacitor_choice]] -- 発熱効率で劣るコンデンサをあえて選ぶ理由
- [[erasure_protocol_choice]] -- Bennettの二重井戸プロトコルの矩形波駆動を採用した理由
- [[pi_pico_role_separation]] -- Raspberry PiとPicoの役割分離の設計根拠
- [[implementation_risks]] -- 手はんだ・単層ルーティング・GPIO制約など手戻りが大きい実装リスク
- [[info_layer_components]] -- Pi・Pico・TC4427など情報層の部品の役割を整理する補足解説
- [[回路解説_初学者向け]] -- 電子部品の役割を高校物理レベルの比喩で説明する初学者向け付録
- [[熱破壊再考察]]（`status: 要更新` -- 初期案からの設計変遷全体が未記入）
- [[忘却ステップの熱力学的正当化]]（`status: 要更新` -- スタブ、相互情報量による導出が未記入）

## audio_visual

（まだノートがありません）

## enclosure

- [[enclosure_design]] -- 黒フィラメント3Dプリントによる手のひら大10cm立方体への素材・サイズ方針転換
- [[enclosure_fit_review]] -- 部品点数削減不可能な設計の必然性と、熱層レイアウトの寸法計算矛盾の指摘

## accessibility

（まだノートがありません。具体的な設計〈決定・仕様〉のみをここに置く。調査はresearchへ）

## research

- [[references]] -- FR裏付け出典（ANU QRNG・NIST SP800-22）と未収集の出典領域を残した参考文献の残余整理
- [[主流BCI方式と企業比較]] -- Neuralink・Synchron・Precision Neuroscience・Merge Labsを侵襲度別に比較する合成ノート。企業別詳細は個社ノートを参照
- [[Neuralinkの侵襲型皮質貫通電極アレイ]] -- N1の臨床進捗と電極スレッド後退・グリオーシスによる長期安定性の課題
- [[Synchronの血管内留置型BCI]] -- StentrodeのCOMMAND試験進捗と血管壁越し記録による安定性と情報密度のトレードオフ
- [[Precision Neuroscienceの脳表面設置型BCI]] -- Layer 7によるFDA 510(k)承認取得済みの微小侵襲BCIの現状
- [[Merge Labsの非侵襲超音波方式]] -- サム・アルトマン共同設立の超音波+遺伝子治療BCIの設立初期段階の状況
- [[導電性ポリマー電極材料]] -- PEDOT:PSS系材料の電荷注入容量・インピーダンス等の刺激特性と未解決課題。企業別詳細は個社ノートを参照
- [[Axoft Fleuronの導電性ハイドロゲル電極]] -- ポリイミド電極比で最大1万倍柔らかいFleuronの商用化状況
- [[INBRAIN Neuroelectronicsのグラフェン電極]] -- グラフェンベースBCI-TxでFDA Breakthrough Device Designationを取得した商用化状況
- [[電気刺激によるBCI書き込みと文字表示]] -- 動的走査刺激によるphosphene文字表示と読字速度の理論的下限
- [[BCI熱感知書き込みの脳内経路]] -- 温度感覚の識別的経路(S1)と情動的経路(島皮質)への分岐と義体化書き込み先候補
- [[脳オルガノイド計算基盤]] -- BCIとは別パラダイムの生体計算基盤の位置づけと忘却炉プロジェクトとの接続。企業別詳細は個社ノートを参照
- [[Cortical LabsのCL1商用生体コンピュータ]] -- DishBrainを起点に2025年商用化したCL1の消費電力・価格
- [[FinalSparkのNeuroplatform]] -- 脳オルガノイドへのリモートアクセスをクラウド提供するNeuroplatformの現状
- [[仏教的概念と量子自然の対応関係]] -- 堀田昌寛を起点に、空・縁起・テトラレンマと量子測定の対応、量子神秘主義への批判的視座
- [[null²における仏教哲学の参照と空間化]] -- 落合陽一のnull²が仏教哲学を鏡膜/デジタルツインに空間化した経緯の整理
- [[色即是空・空即是色と量子自然の相互創発]] -- 計算を空、出力を色と見る自説を学術的対応論で補強
- [[無所得と神秀の漸進修行による忘却炉の幸福論]] -- 般若心経の無所得・少欲知足を神秀の漸進的修行で統合した幸福論
- [[東洋哲学の教義と忘却炉の解釈の相違点]] -- 無我・断見の否定・神道の祖霊観との食い違いを特定し独自の混成として位置づけ
- [[消去儀礼の候補としての護摩と修験道]] -- UX構造を軸に護摩・火の行・荼毘・坐禅を比較し護摩を第一候補と判定

## foresight

- [[trends]] -- BCI・電脳化・量子コンピューティングの技術的現状（`status: 要更新`）
- [[forecast]] -- trendsを起点にした未来予測

## 関連

- 未決の論点は [[open_questions]] を参照
- 用語は [[glossary]] を参照
