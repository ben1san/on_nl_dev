/*
============================================================
忘却炉 聴覚演出 ゼロから音づくり用スケッチ (v4)
============================================================

【使い方】丸括弧で囲まれたブロックの中にカーソルを置き、Cmd+Return。
下の4つを上から順に1回ずつ評価するだけ。

  ブロック1  s.boot;              サーバー起動(最初の1回だけ)
  ブロック2  全SynthDef           音とエフェクトの「作り方」を登録
  ブロック3  ヘルパー関数         操作用の関数とエフェクトチェイン
  ブロック4  GUI                  評価すると操作パネルが自動で開く

順番を飛ばした場合はpost windowに日本語で「先に○番を評価してください」と
出るので、それに従えばよい。

【中身】
  - 波形は wave パラメータ(0〜4)で選ぶ:
      0=サイン波(澄んだ音) 1=ノコギリ波 2=パルス波 3=三角波 4=ノイズ
  - 同時に鳴らせる数は ~numVoices で決める(今は6)。増やせばGUIのタブも増える
  - 全ボイスの音はマスターエフェクト(歪み→エコー→リバーブ)を通ってから出る
  - パネル上部のタブでvoiceを切り替える。切り替えても鳴っている音は止まらない

【v3からの変更】
  ブロックが7つあり、1つでも評価し忘れると意味の分からないエラーが出ていた。
  SynthDefを1ブロックに統合し、シーケンスをヘルパーに畳み込み、~makeRowを
  GUIの内部に取り込んで、4ブロックに減らした。
============================================================
*/

// ============ ブロック1: サーバー起動(最初の1回だけ) ============
s.boot;


// ============ ブロック2: 全SynthDef(音とエフェクトの作り方) ============
(
// ---- 汎用ボイス: wave で波形を選べる ----
SynthDef(\voice, {
    |freq = 220, amp = 0.2, gate = 1, wave = 0, grit = 0.3, cutoff = 3000,
     lfoRate = 0.3, lfoDepth = 0.3, out = 0|
    var sigs, sig, env, dist, cutoffMod;

    // wave(0〜4)で選ばれる5種類の波形の候補
    sigs = [
        SinOsc.ar(freq),                                      // 0: サイン波(澄んだ音)
        Saw.ar(freq),                                         // 1: ノコギリ波(ざらざら)
        Pulse.ar(freq, 0.3 + (0.15 * SinOsc.kr(0.07))),       // 2: パルス波
        LFTri.ar(freq),                                       // 3: 三角波(中間的な柔らかさ)
        PinkNoise.ar() * 0.6,                                 // 4: ノイズ(音程を持たない砂嵐)
    ];
    sig = Select.ar(wave, sigs);

    // cutoffを中心にサイン波で自動的に揺らす(「波のように」変化するauto-filter)。
    // lfoDepth=0なら揺れずcutoffは一定のまま
    cutoffMod = (cutoff * (1 + (lfoDepth * SinOsc.kr(lfoRate)))).clip(60, 14000);
    sig = RLPF.ar(sig, cutoffMod, 0.5);

    // grit: 歪ませる前に信号を増幅してから潰す(ドライブ)ことで、
    // 同じgrit値でもはっきり荒くなる
    dist = (sig * (1 + (grit * 6))).distort;
    sig = sig + (grit * (dist - sig));

    env = EnvGen.kr(Env.asr(0.5, 1, 1.5), gate, doneAction: 2);
    Out.ar(out, (sig * amp * env) ! 2);
}).add;

// ---- レーザー(ピロピロ): 単発トリガー音 ----
SynthDef(\laser, {
    |freq = 1800, amp = 0.3, out = 0|
    var sig, env, freqEnv;
    // 周波数がfreqからfreq*0.12まで0.18秒で駆け下りる(古典的なレーザー音の作り方)
    freqEnv = EnvGen.kr(Env([freq, freq * 0.12], [0.18], curve: -6));
    env = EnvGen.kr(Env.perc(0.001, 0.22), doneAction: 2);
    sig = Pulse.ar(freqEnv, 0.3) + (0.4 * Saw.ar(freqEnv));
    Out.ar(out, (sig * amp * env) ! 2);
}).add;

// ---- マスターエフェクト。全voice/レーザーの音をまとめて通す。
//      それぞれ on(0/1)を持ち、on=0のときは音を一切変えず素通りする ----
SynthDef(\fxDistort, {
    |in = 0, out = 0, on = 0, amount = 0.3|
    var dry, wet, onLag, sig;
    dry = In.ar(in, 2);
    // amountが大きいほど信号を強く増幅してから潰す = 歪みが激しくなる
    wet = (dry * (1 + (amount * 10))).distort;
    onLag = Lag.kr(on, 0.05);  // on切替時のプチッというクリックを避ける
    sig = XFade2.ar(dry, wet, (onLag * 2) - 1);
    ReplaceOut.ar(out, sig);
}).add;

SynthDef(\fxEcho, {
    |in = 0, out = 0, on = 0, amount = 0.3, delayTime = 0.35|
    var dry, wet, onLag, sig, decayTime;
    dry = In.ar(in, 2);
    decayTime = amount.linlin(0, 1, 0.3, 4.0);
    wet = CombL.ar(dry, 1.0, delayTime, decayTime);
    wet = dry + (wet * amount);
    onLag = Lag.kr(on, 0.05);
    sig = XFade2.ar(dry, wet, (onLag * 2) - 1);
    ReplaceOut.ar(out, sig);
}).add;

// 大空間リバーブ。以前はFreeVerb2だったが、部屋の大きさがコードに直書きで
// 固定され尾も2〜3秒しか伸びず「反響が足りない」と判断されたためGVerbへ差し替えた。
// GVerbは部屋の広さをメートル、残響長を秒で直接指定でき、GUIから変えられる。
// 実測: roomsize=60m, revtime=7.5s でRT60=6.5秒(滑らかな指数減衰)。
//
// エコー(コムディレイ)との違い: エコーは「1つの反射を等間隔で繰り返す」ため、
// 持続音にかけると周期的な脈動(ヘリコプターのような音)になる。リバーブは
// 無数の不規則な反射が密に重なるので、規則性が耳につかない。
SynthDef(\fxReverb, {
    |in = 0, out = 0, on = 0, amount = 0.5, roomsize = 60, revtime = 7.5, damping = 0.4|
    var dry, mono, wet, onLag, sig;
    dry = In.ar(in, 2);
    // GVerbはモノラル入力・ステレオ出力なので、左右を混ぜて1本にして渡す
    mono = (dry[0] + dry[1]) * 0.5;
    wet = GVerb.ar(mono,
        roomsize: roomsize.clip(1, 290),  // maxroomsizeを超えると破綻するのでclip
        revtime: revtime.clip(0.1, 30),
        damping: damping,                 // 大きいほど尾が暗く、小さいほど明るい
        inputbw: 0.5,
        spread: 15,                       // 残響の左右の広がり
        drylevel: 0,                      // 素の音はGVerbから出さず下で自分で混ぜる
        earlyreflevel: 0.7,
        taillevel: 0.5,
        maxroomsize: 300                  // SynthDef作成時に固定される上限
    );
    onLag = Lag.kr(on, 0.08);
    // 素の音は常に残し、そこに残響成分を足す(リバーブは元の音を消すものではない)
    sig = dry + (wet * amount * onLag);
    ReplaceOut.ar(out, sig);
}).add;

"ブロック2 OK: SynthDef 5つ登録(voice / laser / fxDistort / fxEcho / fxReverb)".postln;
)


// ============ ブロック3: ヘルパー関数とエフェクトチェイン ============
(
~numVoices = 6;  // ← ここを増やせば同時に鳴らせるボイス数が増える
~voices = Array.newClear(~numVoices);
~voiceIsOn = Array.fill(~numVoices, false);

// ---- マスターエフェクトチェインの初期化 ----
// 全voice/レーザーは直接スピーカーに出さず、いったん~busAという専用バスに
// 書き込む。そのバスを fxDistort → fxEcho → fxReverb の順で処理し、
// 最後にスピーカー(バス0)へ出す。~sourceGroupが必ず~fxGroupより先に
// 実行されるようGroup.afterで順序を固定している。
// s.waitForBootで包んでいるので、サーバー起動が終わっていなくても安全。
~initFx = {
    s.waitForBoot({
        ~busA = Bus.audio(s, 2);
        ~busB = Bus.audio(s, 2);
        ~busC = Bus.audio(s, 2);
        ~sourceGroup = Group.new;
        ~fxGroup = Group.after(~sourceGroup);
        ~fxDistortOn = false; ~fxEchoOn = false; ~fxReverbOn = false;
        ~fxDistortAmt = 0.3; ~fxEchoAmt = 0.3; ~fxReverbAmt = 0.5;
        ~fxReverbRoom = 60; ~fxReverbTime = 7.5; ~fxReverbDamp = 0.4;
        ~fxDistortSynth = Synth(\fxDistort,
            [\in, ~busA.index, \out, ~busB.index, \on, 0, \amount, ~fxDistortAmt],
            ~fxGroup, \addToTail);
        ~fxEchoSynth = Synth(\fxEcho,
            [\in, ~busB.index, \out, ~busC.index, \on, 0, \amount, ~fxEchoAmt],
            ~fxGroup, \addToTail);
        ~fxReverbSynth = Synth(\fxReverb,
            [\in, ~busC.index, \out, 0, \on, 0, \amount, ~fxReverbAmt,
             \roomsize, ~fxReverbRoom, \revtime, ~fxReverbTime, \damping, ~fxReverbDamp],
            ~fxGroup, \addToTail);
        "エフェクトチェイン初期化".postln;
    });
};

// ON/OFFは.isPlayingに頼らず自分の配列(~voiceIsOn)で管理する
// (理由: サーバーからの通知タイミングに頼ると、まだ鳴っているのに気づかず
//  重ねて作ってしまい、古いSynthが誰にも止められなくなる事故が起きるため)
~voiceOn = { |i, wave = 0, freq = 220, amp = 0.2, grit = 0.3, cutoff = 3000, lfoRate = 0.3, lfoDepth = 0.3|
    if(~sourceGroup.isNil, {
        "エフェクトチェインの準備がまだ。少し待ってからもう一度押してください".postln;
    }, {
        if(~voiceIsOn[i].not, {
            ~voices[i] = Synth(\voice, [
                \wave, wave, \freq, freq, \amp, amp, \grit, grit, \cutoff, cutoff,
                \lfoRate, lfoRate, \lfoDepth, lfoDepth, \out, ~busA.index
            ], ~sourceGroup);
            ~voiceIsOn[i] = true;
            ("voice " ++ i ++ " ON").postln;
        });
    });
};
~voiceOff = { |i|
    if(~voiceIsOn[i], {
        ~voices[i].set(\gate, 0);
        ~voiceIsOn[i] = false;
        ("voice " ++ i ++ " OFF").postln;
    });
};
~voiceSet = { |i, key, val|
    if(~voiceIsOn[i], { ~voices[i].set(key, val); });
};
~voiceToggle = { |i, wave = 0, freq = 220, amp = 0.2, grit = 0.3, cutoff = 3000, lfoRate = 0.3, lfoDepth = 0.3|
    if(~voiceIsOn[i], { ~voiceOff.value(i) }, { ~voiceOn.value(i, wave, freq, amp, grit, cutoff, lfoRate, lfoDepth) });
};

~fireLaser = {
    if(~sourceGroup.isNil, {
        "エフェクトチェインの準備がまだ。少し待ってからもう一度押してください".postln;
    }, {
        Synth(\laser, [\freq, ~laserFreq ? 1800, \out, ~busA.index], ~sourceGroup);
        "レーザー発射".postln;
    });
};

// エフェクトのON/OFF切り替え(強さamountの値はそのまま保持される)
~fxDistortToggle = {
    ~fxDistortOn = ~fxDistortOn.not;
    ~fxDistortSynth.set(\on, ~fxDistortOn.asInteger);
    ("歪み強化 " ++ (if(~fxDistortOn, "ON", "OFF"))).postln;
};
~fxEchoToggle = {
    ~fxEchoOn = ~fxEchoOn.not;
    ~fxEchoSynth.set(\on, ~fxEchoOn.asInteger);
    ("エコー " ++ (if(~fxEchoOn, "ON", "OFF"))).postln;
};
~fxReverbToggle = {
    ~fxReverbOn = ~fxReverbOn.not;
    ~fxReverbSynth.set(\on, ~fxReverbOn.asInteger);
    ("リバーブ " ++ (if(~fxReverbOn, "ON", "OFF"))).postln;
};

// 緊急停止: 今鳴っている音を全部即座に止める(パニックボタン)。
// s.freeAllはエフェクトチェインも一緒に消してしまうため、直後に作り直す
~panicStop = {
    s.freeAll;
    ~voiceIsOn = Array.fill(~numVoices, false);
    ~initFx.value;
    "全部停止した(エフェクトチェインは再構築済み)".postln;
};

// ---- 音色の自動シーケンス(叩き台)。voice 0 をONにした状態で
//      ~voiceSeq.play; すると音色が自動で切り替わり続ける。
//      ~voiceSeq.stop; で停止。中の配列は自由に書き換えてよい ----
~voiceSeqTarget = 0;  // このシーケンスがどのvoice番号を動かすか
~voiceSteps = [
    (wave: 1, cutoff: 500,  grit: 0.1),
    (wave: 1, cutoff: 900,  grit: 0.3),
    (wave: 2, cutoff: 300,  grit: 0.5),
    (wave: 3, cutoff: 1200, grit: 0.15),
    (wave: 4, cutoff: 650,  grit: 0.4),
];
~voiceSeq = Routine({
    loop {
        ~voiceSteps.do { |step|
            ~voiceSet.value(~voiceSeqTarget, \wave, step[\wave]);
            ~voiceSet.value(~voiceSeqTarget, \cutoff, step[\cutoff]);
            ~voiceSet.value(~voiceSeqTarget, \grit, step[\grit]);
            2.0.wait;
        };
    };
});

~initFx.value;
"ブロック3 OK: ヘルパー関数を定義".postln;
)


// ============ ブロック4: GUI(評価するとパネルが自動で開く) ============
// EZSliderは内部に独自レイアウトを持つ複合ウィジェットで、外側のVLayoutに
// 埋め込むと内部が潰れてラベルも数値も見えなくなるため使わない。ラベル
// (StaticText)・スライダー(Slider)・数値ボックス(NumberBox)を個別の
// プリミティブな部品として手動で組み立てている。
//
// ScrollViewも、マウスホイールでのスクロールがカーソル下のSliderの値変更と
// 競合する(スクロールするとバーも動いてしまう)ため使わない。代わりに一度に
// 1つのパネルだけを表示するタブ方式にしている。タブを切り替えても、既にONに
// したvoiceの音は裏で鳴り続ける(表示・非表示と再生状態は無関係)。
(
~gui = {
    var win, mainLayout, tabBar, panels, fxTabIndex, showPanel;
    var laserRow, getLaserFreq, makeRow;

    // ラベル+スライダー+数値ボックスを1行にまとめるヘルパー。
    // [横並びの行(HLayout), 現在値を返す関数] を返す。
    // v3では外部の別ブロックに置いていたが、評価し忘れると意味の分からない
    // エラー(nil does not understand 'at')になるため、GUIの内部に取り込んだ。
    makeRow = { |label, spec, initVal, onChange|
        var row = HLayout();
        var lbl = StaticText().string_(label).fixedWidth_(190);
        var nb = NumberBox().fixedWidth_(60).value_(initVal);
        var sl = Slider().orientation_(\horizontal).fixedHeight_(22)
            .value_(spec.unmap(initVal));
        // wave等、整数刻み(spec.step)を持つパラメータはその刻みに丸める
        var quantize = { |v| if(spec.step != 0, { (v / spec.step).round * spec.step }, { v }) };
        var getter;

        sl.action_({ |s|
            var v = quantize.value(spec.map(s.value));
            nb.value_(v);
            onChange.value(v);
        });
        nb.action_({ |n|
            var v = quantize.value(spec.constrain(n.value));
            sl.value_(spec.unmap(v));
            nb.value_(v);
            onChange.value(v);
        });

        row.add(lbl);
        row.add(sl);
        row.add(nb);

        getter = { quantize.value(spec.map(sl.value)) };
        [row, getter];
    };

    // 再評価したときに古いウィンドウが残らないよう閉じる
    if(~guiWindow.notNil, { ~guiWindow.close; });

    win = Window("ゼロから音づくり v4 - 複数ボイス+エフェクト", Rect(80, 60, 540, 620)).front;
    ~guiWindow = win;
    mainLayout = VLayout();
    tabBar = HLayout();
    // タブはvoice 0..N-1 に加え、最後の1枠を「FX」パネルとして使う
    panels = Array.newClear(~numVoices + 1);
    fxTabIndex = ~numVoices;

    showPanel = { |sel| (~numVoices + 1).do { |j| panels[j].visible_(j == sel) } };

    mainLayout.add(StaticText().string_("wave: 0=サイン 1=ノコギリ 2=パルス 3=三角 4=ノイズ"));
    mainLayout.add(tabBar);

    ~numVoices.do { |i|
        var panel = View();
        var innerLayout = VLayout();
        var row, getWave, getFreq, getAmp, getGrit, getCutoff, getLfoRate, getLfoDepth, onBtn, tabBtn;

        #row, getWave = makeRow.value("wave", ControlSpec(0, 4, \lin, 1, 0), 0,
            { |v| ~voiceSet.value(i, \wave, v) });
        innerLayout.add(row);
        #row, getFreq = makeRow.value("freq", ControlSpec(30, 4000, \exp, 0, 220), 220,
            { |v| ~voiceSet.value(i, \freq, v) });
        innerLayout.add(row);
        #row, getAmp = makeRow.value("amp", ControlSpec(0, 1, \lin, 0, 0.2), 0.2,
            { |v| ~voiceSet.value(i, \amp, v) });
        innerLayout.add(row);
        #row, getGrit = makeRow.value("grit (荒さ)", ControlSpec(0, 1, \lin, 0, 0.3), 0.3,
            { |v| ~voiceSet.value(i, \grit, v) });
        innerLayout.add(row);
        #row, getCutoff = makeRow.value("cutoff", ControlSpec(100, 8000, \exp, 0, 3000), 3000,
            { |v| ~voiceSet.value(i, \cutoff, v) });
        innerLayout.add(row);
        #row, getLfoRate = makeRow.value("cutoff LFO rate", ControlSpec(0.02, 8, \exp, 0, 0.3), 0.3,
            { |v| ~voiceSet.value(i, \lfoRate, v) });
        innerLayout.add(row);
        #row, getLfoDepth = makeRow.value("cutoff LFO depth", ControlSpec(0, 1, \lin, 0, 0.3), 0.3,
            { |v| ~voiceSet.value(i, \lfoDepth, v) });
        innerLayout.add(row);

        // ONを押した瞬間の各行の現在値でそのボイスを鳴らす
        onBtn = Button(win, 480@28).states_([["voice " ++ i ++ " ON/OFF"]])
            .action_({
                ~voiceToggle.value(
                    i, getWave.value, getFreq.value, getAmp.value, getGrit.value,
                    getCutoff.value, getLfoRate.value, getLfoDepth.value
                );
            });
        innerLayout.add(onBtn);

        panel.layout = innerLayout;
        panels[i] = panel;
        mainLayout.add(panel);

        tabBtn = Button(win, 78@26).states_([["voice " ++ i]])
            .action_({ showPanel.value(i) });
        tabBar.add(tabBtn);
    };

    // ---- FXパネル(全voice共通のマスターエフェクト) ----
    {
        var fxPanel = View();
        var fxLayout = VLayout();
        var row, getVal, fxTabBtn;

        fxLayout.add(StaticText().string_("-- 歪み強化(distort) --"));
        fxLayout.add(Button(win, 480@26).states_([["歪み強化 ON/OFF"]])
            .action_({ ~fxDistortToggle.value }));
        #row, getVal = makeRow.value("amount", ControlSpec(0, 1, \lin, 0, 0.3), 0.3,
            { |v| ~fxDistortSynth.set(\amount, v) });
        fxLayout.add(row);

        // エコーは等間隔の繰り返しなので、持続音にかけると周期的な脈動
        // (ヘリコプターのような音)になりやすい。広がりが欲しい場合は下のリバーブを使う
        fxLayout.add(StaticText().string_("-- エコー(等間隔の繰り返し。持続音だと機械的になりやすい) --"));
        fxLayout.add(Button(win, 480@26).states_([["エコー ON/OFF"]])
            .action_({ ~fxEchoToggle.value }));
        #row, getVal = makeRow.value("amount", ControlSpec(0, 1, \lin, 0, 0.3), 0.3,
            { |v| ~fxEchoSynth.set(\amount, v) });
        fxLayout.add(row);
        #row, getVal = makeRow.value("delay time", ControlSpec(0.03, 1.0, \exp, 0, 0.35), 0.35,
            { |v| ~fxEchoSynth.set(\delayTime, v) });
        fxLayout.add(row);

        fxLayout.add(StaticText().string_("-- リバーブ(大空間の反響。広がりはこちら) --"));
        fxLayout.add(Button(win, 480@26).states_([["リバーブ ON/OFF"]])
            .action_({ ~fxReverbToggle.value }));
        #row, getVal = makeRow.value("amount (混ぜる量)", ControlSpec(0, 1, \lin, 0, 0.5), 0.5,
            { |v| ~fxReverbSynth.set(\amount, v) });
        fxLayout.add(row);
        #row, getVal = makeRow.value("roomsize (部屋の広さ m)", ControlSpec(5, 290, \exp, 0, 60), 60,
            { |v| ~fxReverbSynth.set(\roomsize, v) });
        fxLayout.add(row);
        #row, getVal = makeRow.value("revtime (残響長 秒)", ControlSpec(0.3, 30, \exp, 0, 7.5), 7.5,
            { |v| ~fxReverbSynth.set(\revtime, v) });
        fxLayout.add(row);
        #row, getVal = makeRow.value("damping (尾の暗さ)", ControlSpec(0, 1, \lin, 0, 0.4), 0.4,
            { |v| ~fxReverbSynth.set(\damping, v) });
        fxLayout.add(row);

        fxPanel.layout = fxLayout;
        panels[fxTabIndex] = fxPanel;
        mainLayout.add(fxPanel);

        fxTabBtn = Button(win, 78@26).states_([["FX"]])
            .action_({ showPanel.value(fxTabIndex) });
        tabBar.add(fxTabBtn);
    }.value;

    showPanel.value(0); // 最初はvoice 0のパネルだけ見えている状態にする

    mainLayout.add(StaticText().string_("-- レーザー(単発) --"));
    #laserRow, getLaserFreq = makeRow.value("laser freq", ControlSpec(600, 4000, \exp, 0, 1800), 1800,
        { |v| ~laserFreq = v; });
    mainLayout.add(laserRow);
    mainLayout.add(Button(win, 480@28).states_([["レーザー発射!"]])
        .action_({ ~fireLaser.value }));

    mainLayout.add(StaticText().string_("-- 緊急停止 --"));
    mainLayout.add(Button(win, 480@30).states_([["全部止める(パニックボタン)", Color.white, Color.red]])
        .action_({ ~panicStop.value }));

    win.layout = mainLayout;
    win;
};

// 前のブロックを評価し忘れていないか確認してから開く。
// 忘れていた場合は日本語で何をすればよいか出す(意味の分からないエラーを防ぐ)
~openGui = {
    if(SynthDescLib.global.at(\voice).isNil, {
        "【手順】先に「ブロック2: 全SynthDef」を評価してください".postln;
    }, {
        if(~numVoices.isNil or: { ~voiceOn.isNil }, {
            "【手順】先に「ブロック3: ヘルパー関数」を評価してください".postln;
        }, {
            ~gui.value;
            "ブロック4 OK: パネルを開いた".postln;
        });
    });
};

~openGui.value;
)


/*
次の一歩の候補:
  - ~numVoicesを増やしてみる(6→12など。GUIのタブも自動でその数だけ増える)
  - 波形の候補(sigs配列)にさらに種類を足す
  - ~voiceStepsを書き換えてシーケンスを作り込む
  - wave切り替え時のプチッというクリック音が気になる場合、Select.arではなく
    クロスフェードで滑らかに波形を混ぜる方式に変える
  - 各voiceを左右別々の位置に配置する(pan)。今は全voiceが真ん中に定位して
    いるため、左右の広がりはリバーブのspreadだけに依存している
*/
