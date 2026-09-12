// =====================================================================
//  連続体層 + 出来事層 + 空間段 をオーディオ機器なしでレンダリングする(NRT)
// =====================================================================
//
//      sclang audio_visual/render.scd
//      uv run audio_visual/dimtakt_compare.py /tmp/take.wav
//
//  層ごとに引数を渡す。層を外すこともできる:
//      LAYERS="events drone" \
//      CONTINUUM_ARGS="tilt 1.2 ringMax 9.0" \
//      EVENTS_ARGS="rate 1.2 pitchHi 18" \
//      SPACE_ARGS="time 2.1 mix 0.33" \
//      OUT=/tmp/take.wav DUR=30 sclang audio_visual/render.scd
//
//  LAYERS の既定は "events drone"。連続体層(continuum)は羽音に聞こえるため既定から外した。"continuum" だけにすればM1単体、
//  "events" だけにすれば出来事層だけが鳴る(切り分けに使う)。
//  SPACE_ARGS に "mix 0" を渡せば残響を無効にできる。
//
//  ライブ演奏と同じSynthDefを使う。定義元は m1_continuum.scd /
//  m2_events.scd / space.scd の3つで、ここには音の定義を持たない。
//
(
var dur, outPath, layers, dir, score, opts, bus, parse, cArgs, eArgs, dArgs, gArgs, roArgs, sArgs, msgs;

dur     = "DUR".getenv !? (_.asFloat) ?? { 30.0 };
outPath = "OUT".getenv ?? { "/tmp/take.wav" };
// Symbolへ変換してから比較する。**ArrayのincludesはStringを同一性で比較する**
// ため、内容が同じでも別インスタンスなら false になる。Symbolはinternされる
// ので同一性比較が効く。これも症状は「無音のwavが書き出される」だけだった。
layers  = ("LAYERS".getenv ?? { "glide" }).split($ ).reject(_.isEmpty)
	.collect(_.asSymbol);

dir = thisProcess.nowExecutingPath.dirname;
File.readAllString(dir +/+ "m1_continuum.scd").interpret;
File.readAllString(dir +/+ "m2_events.scd").interpret;
File.readAllString(dir +/+ "m3_drone.scd").interpret;
File.readAllString(dir +/+ "m4_glide.scd").interpret;
File.readAllString(dir +/+ "m5_rotor.scd").interpret;
File.readAllString(dir +/+ "space.scd").interpret;

// "名前 値 名前 値" を s_new の引数列へ
parse = { |str|
	var a = (str ?? { "" }).split($ ).reject(_.isEmpty);
	a.clump(2).collect({ |p| [p[0].asSymbol, p[1].asFloat] }).flatten
};
cArgs = parse.("CONTINUUM_ARGS".getenv);
eArgs = parse.("EVENTS_ARGS".getenv);
dArgs = parse.("DRONE_ARGS".getenv);
gArgs = parse.("GLIDE_ARGS".getenv);
roArgs = parse.("ROTOR_ARGS".getenv);
sArgs = parse.("SPACE_ARGS".getenv);

// 音源は私設バス16へ書き、空間段がそれを読んで出力0へ出す。
// 実行順は g_new の addAction で固定する(音源グループ10 -> 空間グループ11)。
bus = 16;

// 音源はルートグループの先頭へ、空間段は末尾へ足す。これだけで実行順が
// 「音源が書く -> 空間段が読む」に固定される(グループを別に作る必要はない)。
//
// **SynthDefは1つずつ別の時刻に送る。** scsynthのOSC受信バッファは32KBで、
// 同じ時刻の複数メッセージは1つのバンドルにまとめられるため、定義を全部
// 0.0秒に置くと合計がこれを超える。超えたバンドルはエラーも警告も出さずに
// 丸ごと捨てられ、症状は「無音のwavが書き出される」だけになる。連続体層の
// 定義だけで31KBあるので、2つ以上を同時刻に置くと即座に踏む。
msgs = [
	[0.000, ['/d_recv', ~makeContinuumDef.().asBytes]],
	[0.005, ['/d_recv', ~makeEventsDef.().asBytes]],
	[0.010, ['/d_recv', ~makeDroneDef.().asBytes]],
	[0.015, ['/d_recv', ~makeGlideDef.().asBytes]],
	[0.020, ['/d_recv', ~makeRotorDef.().asBytes]],
	[0.025, ['/d_recv', ~makeSpaceDef.().asBytes]]
];

if (layers.includes(\continuum)) {
	msgs = msgs.add([0.03, ['/s_new', \continuum, 1000, 0, 0, \out, bus] ++ cArgs]);
};
if (layers.includes(\events)) {
	msgs = msgs.add([0.03, ['/s_new', \events, 1001, 0, 0, \out, bus] ++ eArgs]);
};
if (layers.includes(\rotor)) {
	msgs = msgs.add([0.03, ['/s_new', \rotor, 1005, 0, 0, \out, bus] ++ roArgs]);
};
if (layers.includes(\glide)) {
	msgs = msgs.add([0.03, ['/s_new', \glide, 1004, 0, 0, \out, bus] ++ gArgs]);
};
if (layers.includes(\drone)) {
	msgs = msgs.add([0.03, ['/s_new', \drone, 1003, 0, 0, \out, bus] ++ dArgs]);
};
msgs = msgs.add([0.03, ['/s_new', \space, 1002, 1, 0, \in, bus, \out, 0] ++ sArgs]);
msgs = msgs.add([dur, ['/c_set', 0, 0]]);

score = Score(msgs);

opts = ServerOptions.new
	.numOutputBusChannels_(2)
	.numInputBusChannels_(0)
	.sampleRate_(44100);

("render: " ++ dur ++ "s [" ++ layers.join(" ") ++ "] -> " ++ outPath).postln;

score.recordNRT(
	outputFilePath: outPath,
	headerFormat: "WAV",
	sampleFormat: "int24",
	options: opts,
	duration: dur,
	action: { "done".postln; 0.exit }
);
)
