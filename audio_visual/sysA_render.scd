// =====================================================================
//  系統A をオーディオ機器なしでレンダリングする(NRT)
// =====================================================================
//
//      OUT=/tmp/a.wav DUR=60 sclang audio_visual/sysA_render.scd
//      BANK_ARGS="rotHz 0.14 detune 22" SPACE_ARGS="mix 0.4" \
//        OUT=/tmp/a.wav sclang audio_visual/sysA_render.scd
//      LAYERS=bank ... // 空間段を外して素の音を見る
//
//  測るときは60秒以上にする。発音がポアソン過程なので、30秒では同一設定でも
//  2-8kHzが±13%・重心が±14%動く。再現性の幅より小さい差を読んではいけない。
//
(
var dur, outPath, layers, dir, score, opts, bus, parse, bArgs, sArgs, msgs;

dur     = "DUR".getenv !? (_.asFloat) ?? { 60.0 };
outPath = "OUT".getenv ?? { "/tmp/sysA.wav" };
// **Symbolへ変換してから比較する。** Array:includes は String を同一性で
// 比較するため、内容が同じでも別インスタンスなら false を返す。症状は
// 「無音のwavが書き出される」だけで、エラーも警告も出ない。
layers  = ("LAYERS".getenv ?? { "bank space" }).split($ ).reject(_.isEmpty)
	.collect(_.asSymbol);

dir = thisProcess.nowExecutingPath.dirname;
File.readAllString(dir +/+ "sysA_bank.scd").interpret;
File.readAllString(dir +/+ "sysA_space.scd").interpret;

parse = { |str|
	var a = (str ?? { "" }).split($ ).reject(_.isEmpty);
	a.clump(2).collect({ |p| [p[0].asSymbol, p[1].asFloat] }).flatten
};
bArgs = parse.("BANK_ARGS".getenv);
sArgs = parse.("SPACE_ARGS".getenv);

bus = 16;

// **SynthDefは1つずつ別の時刻に送る。** scsynthのOSC受信バッファは32KBで、
// 同時刻のメッセージは1つのバンドルにまとめられる。定義を全部0.0秒に置くと
// 合計が超えることがあり、超えたバンドルはエラーも警告もなく丸ごと捨てられる。
msgs = [
	[0.000, ['/d_recv', ~makeSysABankDef.().asBytes]],
	[0.005, ['/d_recv', ~makeSysASpaceDef.().asBytes]]
];

if (layers.includes(\bank)) {
	msgs = msgs.add([0.01, ['/s_new', \sysABank, 1000, 0, 0, \out, bus] ++ bArgs]);
};
// 音源はルートグループの先頭(addAction 0)、空間段は末尾(addAction 1)。
// これだけで「音源が書く → 空間段が読む」の実行順が固定される。
if (layers.includes(\space)) {
	msgs = msgs.add([0.01, ['/s_new', \sysASpace, 1001, 1, 0, \in, bus, \out, 0] ++ sArgs]);
} {
	// 空間段を外すときは素の音をそのまま出力へ回す
	msgs = msgs.add([0.01, ['/s_new', \sysASpace, 1001, 1, 0,
		\in, bus, \out, 0, \mix, 0] ++ sArgs]);
};
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
