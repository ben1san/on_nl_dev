/*
============================================================
忘却炉 聴覚演出 ライブ試作 (SuperCollider)
============================================================

位置づけ:
  audio_visual/erasure_sonification_v5.py が固めた仕様
  ([[audio_visual/聴覚演出は回路クロック分周の純正律ドローンと連続グライドする記憶の声で構成する]])
  ―― 離散的な発音を持たない・常時鳴り続ける・ブロック単位の統計量を
  「発音トリガー」ではなく「鳴り続けている音のパラメータ目標値」として
  使う ―― という設計を、オフラインのバッチ生成(numpyで全体を計算して
  wavに書き出す)から、SuperColliderのライブ環境(1つのSynthを鳴らし
  っぱなしにして.setで値を送り込み続ける)へ移植したもの。

  開発手法としての狙い:
    シンセサイザのように「今の音を鳴らしたまま」パラメータを触って
    音色を探れる環境が欲しい、という要求に対する回答。numpyバッチ版は
    コードを直すたびに全体を再計算してwavを書き出す必要があり、
    「触ってすぐ変わる」体験ができなかった。

v5.pyとの対応:
  7層の整数分周純正律ドローン        → \bed (SynthDef内)
  エントロピー駆動の記憶の声(連続グライド) → \voice
  きらめき層                          → \shimmer
  乱数rの連続テクスチャ                → \rtex
  劣化(ビットクラッシュのみ、ドロップアウトなし) → Decimator.ar
  ブロック周期由来のディレイ            → DelayC.ar(~blockTime)

v5.pyとの意図的な違い(探索環境としての簡略化。まだ「結論」ではない):
  - ブロック統計量は実ファイルのバイト列からではなく、まずは
    シミュレートしたランダムウォークで与える(~feedSimulated)。
    実データ駆動(実ボールトファイル・実QRNG)への配線は次段階。
  - ユニゾンデチューンは正規分布ではなく一様分布で近似。
  - リバーブ・ディレイはv5.pyの畳み込みIR/マルチタップではなく
    FreeVerb2/DelayCで簡略化。
  これらの差は「ライブで触って探る」ことを優先した結果で、
  Piへの実装移植時にv5.pyの数値と再照合が必要。

使い方:
  1. このファイルをSuperCollider IDE(scide)で開き、上から順に
     ブロック単位(丸括弧で囲まれた各セクション)をCmd+Returnで評価する
  2. ~startVoice.value; でSynthを1つだけ起動する。以後は鳴らし直さず
     .setで操作し続ける(離散トリガーを持たない設計そのものの体現)
  3. ~gui.value; でスライダーパネルを開き、手でh/meanByte/bt/progress/
     rAmtを動かして音色を探る(いつでも上書きできる = 手動操作が勝つ)
  4. ~feedSimulated.play; でブロック周期(~0.544s)ごとに疑似データを
     ランダムウォークさせて自動的に.setし続ける(v5.pyの「実データが
     鳴らす」体験に近い状態を、実配線前に確認するためのスタンドイン)
  5. ~stopVoice.value; で終了(ASRのリリースで自然にフェードアウト)
============================================================
*/

s.boot;

(
// ---- 回路定数 (classical_erasure/components.md 確定値 R=117Ω, C=71nF) ----
// 注意: 単一の大文字(~R, ~C等)を環境変数名に使うとこの環境のsclang 3.14.1が
// コンパイル時にハングする既知の問題を確認したため、必ず複数文字の変数名にする
~resistorOhm = 117.0;
~capFarad = 71e-9;
~tau = ~resistorOhm * ~capFarad;      // ~8.307 µs
~fCycle = 1 / (16 * ~tau);            // ~7523.8 Hz (4相・16τ=1サイクル)
~blockBytes = 4096;
~blockTime = ~blockBytes / ~fCycle;   // ~0.5444 s。発音間隔ではなく目標値更新間隔
~divisors = [64, 48, 32, 24, 16, 12, 8];   // 互いに2:1・3:2・4:3の純正律
~layerGain = [0.85, 0.45, 0.80, 0.40, 0.70, 0.28, 0.16];

// 16ハーフセルぶんのユニゾンデチューン(コンデンサ公差の可聴化。一様分布で近似)
~detune16 = Array.fill(16, { 1.0 / (1.0 + rrand(-0.0075, 0.0075)) });

("f_cycle = " ++ ~fCycle ++ " Hz,  block_time = " ++ ~blockTime ++ " s").postln;
)

(
SynthDef(\forgettingFurnace, {
    |out = 0, h = 6.0, meanByte = 128, bt = 4.0, progress = 0.0,
     rAmt = 0.03, gate = 1, amp = 0.85|

    var glideT = 0.544;                 // ブロック周期そのもの = 追従の時定数
    var hL        = Lag.kr(h, glideT);
    var meanL     = Lag.kr(meanByte, glideT);
    var btL       = Lag.kr(bt, glideT);
    var progL     = Lag.kr(progress, glideT * 4);
    var rAmtL     = Lag.kr(rAmt, glideT);
    var purity    = ((hL - 5.0) / 1.6).clip(0, 1);   // 記憶の「純度」

    var vib, bed, voiceF, voice, shimmer, rtex, wet, l, r, env, degradeBits;

    // 装置自身の身体の微細な呼吸(全レイヤー共通のビブラート)
    vib = 1
        + (0.0030 * SinOsc.kr(0.043))
        + (0.0018 * SinOsc.kr(0.017, 2.1));

    // ---- 1. 純正律ドローン床(回路クロックの整数分周。中身に依存しない) ----
    bed = Mix.fill(7, { |i|
        var dv     = ~divisors[i];
        var gain   = ~layerGain[i];
        var f0     = (~fCycle / dv) * vib;
        // 上位の軽い分周(/8,/12,/16)は常にフル。低い分周は純度が開くほど輝く
        var lift   = if(dv >= 24, 1.0, 0.35 + (0.65 * purity));
        var nVoice = if(dv >= 24, 4, 3);
        var layer  = Mix.fill(nVoice, { |k|
            SinOsc.ar(f0 * ~detune16[(i * 4 + k) % 16])
        }) / nVoice;
        layer * gain * lift
    }) * 0.5;

    // ---- 2. 記憶の声(H(d)に連続グライド。発音トリガーではない) ----
    voiceF = (~fCycle / 16)
        * (2 ** ((hL - 6.0) / 4.0))
        * (2 ** (((meanL - 128) / 128) * 0.03));
    voice = SinOsc.ar(voiceF * vib)
        + (0.30 * SinOsc.ar(voiceF * 2 * vib))
        + (0.12 * SinOsc.ar(voiceF * 3 * vib));
    // フォルマント2バンド(620Hz/1450Hz)を高めに置き、籠らせない
    voice = (0.45 * voice)
        + (0.55 * ((0.6 * BPF.ar(voice, 620, 0.35))
                 + (0.4 * BPF.ar(voice, 1450, 0.35))));
    voice = voice * (0.35 + (0.45 * purity));

    // ---- 3. きらめき(安らかさのための空気感。純度に連動) ----
    shimmer = SinOsc.ar((~fCycle / 4) * vib) * (0.10 + (0.16 * purity));
    shimmer = shimmer * (0.55 + (0.45 * SinOsc.kr(0.021)));

    // ---- 4. 乱数rの連続テクスチャ(ひとつづきの息。旋律を持たない) ----
    rtex = BPF.ar(WhiteNoise.ar(1), 1700, 2.0) * rAmtL
         * (0.7 + (0.3 * SinOsc.kr(0.013)));

    // ---- ミックス・劣化・空間処理 ----
    wet = (0.55 * bed) + (0.42 * voice) + shimmer;

    // 劣化はビットクラッシュ(音色変化)のみ。ドロップアウトは使わない
    // v5.pyのbitcrush()と同じ手動量子化(Decimator.arはこの環境のSC 3.14.1で
    // グラフ構築中にハングする既知の問題を確認したため使わない)
    degradeBits = (16 - (10 * progL * 0.55)).clip(4, 16);
    wet = {
        var lv = 2.0.pow(degradeBits);
        (wet * (lv / 2)).round / (lv / 2);
    }.value;

    // ブロック周期由来のディレイ(演出値を持ち込まない)
    wet = wet + (0.26 * DelayC.ar(wet, 2.0, ~blockTime));

    # l, r = FreeVerb2.ar(wet, wet, 0.62, 0.85, 0.5);
    l = HPF.ar(l, 120);
    r = HPF.ar(r, 120);

    // 鎮静相=rの放電こそ真のランダウアー消去。rはドライに近く聞こえて正しい
    l = l + rtex;
    r = r + (rtex * 0.92);

    env = EnvGen.kr(Env.asr(3.5, 1, 9.0, curve: \sine), gate, doneAction: 2);

    Out.ar(out, [l, r] * env * amp);
}).add;

"SynthDef \\forgettingFurnace 登録完了".postln;
)

// ---- 起動・停止(1つのSynthを鳴らしっぱなしにする。鳴らし直さない) ----
(
~startVoice = {
    if(~synth.isNil or: { ~synth.isPlaying.not }, {
        ~synth = Synth(\forgettingFurnace);
        "開始: 以後は ~synth.set(...) でのみ操作すること".postln;
    }, {
        "既に鳴っている。多重起動しない(離散トリガーを持たない設計)".postln;
    });
};

~stopVoice = {
    ~synth.set(\gate, 0);
    "リリース開始(9秒。NTC冷却時定数に相当)".postln;
};
)

// ---- 疑似データ供給ルーチン(実ファイル/実QRNGへの配線は次段階) ----
(
~feedSimulated = Routine({
    var h = 6.0, meanByte = 128.0, bt = 4.0, progress = 0.0;
    inf.do {
        // 実データのH(d)分布(5.34-6.41)を模したランダムウォーク。
        // ときどき大きく振って「乱数に置き換わった領域」(H→7.95付近)も模擬する
        h = (h + rrand(-0.25, 0.25)).clip(5.0, 7.95);
        meanByte = (meanByte + rrand(-8.0, 8.0)).clip(0, 255);
        bt = (bt + rrand(-0.3, 0.3)).clip(0, 8);
        progress = (progress + (~blockTime / 140.0)).min(1.0); // 1MB≈140sを想定

        if(~synth.notNil and: { ~synth.isPlaying }, {
            ~synth.set(
                \h, h,
                \meanByte, meanByte,
                \bt, bt,
                \progress, progress,
                \rAmt, 0.03 + (0.045 * progress)
            );
        });
        ~blockTime.wait;
    };
});
)

// ---- 手動探索用GUIパネル ----
(
~gui = {
    var win = Window("忘却炉 聴覚演出 ライブ試作", Rect(100, 100, 420, 340)).front;
    var layout = VLayout();

    layout.add(EZSlider(win, 380@40, "H(d) エントロピー",
        ControlSpec(5.0, 7.95, \lin, 0, 6.0),
        { |sl| ~synth.set(\h, sl.value) }));
    layout.add(EZSlider(win, 380@40, "平均バイト値",
        ControlSpec(0, 255, \lin, 0, 128),
        { |sl| ~synth.set(\meanByte, sl.value) }));
    layout.add(EZSlider(win, 380@40, "ビット遷移密度",
        ControlSpec(0, 8, \lin, 0, 4.0),
        { |sl| ~synth.set(\bt, sl.value) }));
    layout.add(EZSlider(win, 380@40, "消去進行 progress",
        ControlSpec(0, 1, \lin, 0, 0.0),
        { |sl| ~synth.set(\progress, sl.value) }));
    layout.add(EZSlider(win, 380@40, "乱数テクスチャ量 rAmt",
        ControlSpec(0, 0.2, \lin, 0, 0.03),
        { |sl| ~synth.set(\rAmt, sl.value) }));
    layout.add(EZSlider(win, 380@40, "amp",
        ControlSpec(0, 1, \lin, 0, 0.85),
        { |sl| ~synth.set(\amp, sl.value) }));

    win.layout = layout;
    win.onClose = { "GUI閉じた(Synthは鳴り続ける)".postln };
    win;
};
)

/*
次にやること(未検証):
  - ~feedSimulatedを実ファイル(research/**/*.md 等)のバイト列読み取りに
    差し替え、v5.pyと同じエントロピー計算で駆動する
  - 疑似乱数ではなく実QRNG出力をrtexの元データにする
  - Raspberry Piへの移植時、Pi→Picoの実ストリーミングに便乗して
    ブロック統計量を~feedSimulatedと同じ形でOSC等から.setする経路を作る
  - v5.pyのdelay_fx(4タップ・フィードバック)・畳み込みIRとの音の違いを
    比較試聴し、どちらの手触りを採用するか判断する
  - detune16の一様分布近似をrrand(正規分布ではない)からPythonのrng.normal
    相当に寄せる必要があるかは未検証
*/
