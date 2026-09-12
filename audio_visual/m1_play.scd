// =====================================================================
//  M1 連続体層 — 鳴らしたまま触るための操作パネル
// =====================================================================
//
//  手順:
//      s.boot;
//      このファイル全体を選択して評価(cmd+enter)
//
//  ウィンドウの「鳴らす」で音が出る。スライダーは鳴らしたまま効く。
//
//  耳で決めた設定を測定へ渡すには「設定を出力」を押す。ポストウィンドウに
//  そのまま貼れるコマンドが出るので、ターミナルで実行すれば8指標が出る:
//
//      M1_ARGS="tilt 1.2 ringMax 9.0 ..." sclang audio_visual/m1_render.scd
//      uv run audio_visual/dimtakt_compare.py /tmp/m1_take.wav
//
//  「30秒録音」はライブの音をそのまま録る。NRTレンダリングと違って実際に
//  聴いている音そのものなので、耳と数値がずれたときはこちらで確かめる。
//
//  この操作パネルは既知のSuperCollider固有の罠を避けて書いてある:
//    - EZSliderは使わない(VLayoutでラベルも数値も潰れるため素の部品で行を自作)
//    - Synthの在否は .isPlaying ではなく言語側の変数で管理する(多重起動防止)
//    - ScrollViewは使わない(ホイールがスライダーの値変更と競合するため1画面に収める)
//    - 環境変数名に単一の大文字を使わない
//

s.waitForBoot({

	var win, layout, mkRow, specs, controls, isOn, synth, presets, mkPreset, argString;

	// ---- 定義を読む(m1_continuum.scd が唯一の定義元) ----
	File.readAllString(
		thisProcess.nowExecutingPath.dirname +/+ "m1_continuum.scd"
	).interpret;
	~makeContinuumDef.().add;
	s.sync;

	isOn = false;
	synth = nil;
	controls = IdentityDictionary.new;

	// 名前 -> [最小, 最大, 初期値, カーブ]
	specs = [
		[\amp,       0.0,  0.6,  0.2,  \lin],
		[\baseFreq,  40,   500,  142.7, \exp],
		[\stretch,   0.94, 1.12, 1.0,  \lin],
		[\ringMin,   0.01, 0.5,  0.08, \exp],
		[\ringMax,   0.2,  12.0, 9.0,  \exp],
		[\ringTilt,  0.2,  0.95, 0.45, \lin],
		[\ringComp,  0.0,  1.0,  1.0,  \lin],
		[\bedLevel,  0.0,  0.4,  0.06, \lin],
		[\tilt,      0.0,  3.0,  1.2,  \lin],
		[\driftHz,   0.01, 1.0,  0.07, \exp],
		[\driftAmt,  0.0,  0.05, 0.004, \lin],
		[\dustRate,  0.5,  80.0, 9.0,  \exp],
		[\dustAmt,   0.0,  2.0,  0.5,  \lin],
		[\width,     0.0,  1.0,  0.7,  \lin]
	];

	// 現在の設定を M1_ARGS 用の1行にする
	argString = {
		specs.collect({ |sp|
			var name = sp[0];
			name.asString ++ " " ++ controls[name][\value].round(0.001)
		}).join(" ")
	};

	win = Window("M1 連続体層", Rect(120, 120, 560, 560)).front;
	layout = VLayout();
	win.layout = layout;

	// ---- スライダー1行を素の部品で自作する ----
	mkRow = { |name, lo, hi, init, curve|
		var spec = ControlSpec(lo, hi, curve);
		var label = StaticText().string_(name.asString).minWidth_(90);
		var slider = Slider().orientation_(\horizontal).value_(spec.unmap(init));
		var num = NumberBox().value_(init).maxWidth_(80).decimals_(3);
		var state = IdentityDictionary[\value -> init];

		var apply = { |v|
			state[\value] = v;
			num.value = v;
			if (isOn and: { synth.notNil }) { synth.set(name, v) };
		};

		slider.action = { |sl| apply.(spec.map(sl.value)) };
		num.action    = { |nb| var v = spec.constrain(nb.value);
			slider.value = spec.unmap(v); apply.(v) };

		state[\reset] = { |v| slider.value = spec.unmap(v); apply.(v) };
		controls[name] = state;
		layout.add(HLayout(label, [slider, stretch: 1], num));
	};

	specs.do({ |sp| mkRow.(sp[0], sp[1], sp[2], sp[3], sp[4]) });

	// ---- プリセット(いずれも実測でM1の2指標に合格している) ----
	presets = [
		["A 基準",   (tilt: 1.2,  ringMin: 0.08, ringMax: 9.0, ringTilt: 0.45,
			stretch: 1.0,  dustRate: 9.0,  dustAmt: 0.5)],
		["B 暗い",   (tilt: 0.85, ringMin: 0.10, ringMax: 6.0, ringTilt: 0.60,
			stretch: 1.0,  dustRate: 9.0,  dustAmt: 0.5)],
		["C 金属質", (tilt: 1.1,  ringMin: 0.05, ringMax: 4.0, ringTilt: 0.55,
			stretch: 1.06, dustRate: 9.0,  dustAmt: 0.5)],
		["D 砂質",   (tilt: 1.5,  ringMin: 0.04, ringMax: 2.0, ringTilt: 0.70,
			stretch: 1.0,  dustRate: 30.0, dustAmt: 1.2)]
	];

	mkPreset = { |pair|
		Button().states_([[pair[0]]]).action_({
			pair[1].keysValuesDo({ |k, v|
				if (controls[k].notNil) { controls[k][\reset].(v) };
			});
			("preset: " ++ pair[0]).postln;
		});
	};

	layout.add(HLayout(*presets.collect(mkPreset)));

	// ---- 操作ボタン ----
	layout.add(HLayout(
		Button().states_([["鳴らす", Color.black, Color.green(0.7)],
			              ["止める", Color.white, Color.grey(0.4)]])
			.action_({ |b|
				// .isPlaying は取りこぼすので言語側の変数で在否を管理する
				if (isOn.not) {
					synth = Synth(\continuum,
						specs.collect({ |sp| [sp[0], controls[sp[0]][\value]] }).flatten);
					isOn = true;
				} {
					synth.free; synth = nil; isOn = false;
				};
			}),

		Button().states_([["30秒録音"]]).action_({
			var path = "/tmp/m1_live_" ++ Date.getDate.stamp ++ ".wav";
			if (isOn.not) {
				"先に「鳴らす」を押す".postln;
			} {
				s.record(path: path, duration: 30);
				("録音開始(30秒) -> " ++ path).postln;
				("  測る: uv run audio_visual/dimtakt_compare.py " ++ path).postln;
			};
		}),

		Button().states_([["設定を出力"]]).action_({
			"".postln;
			"---- いまの設定 ----".postln;
			("M1_ARGS=\"" ++ argString.() ++ "\" sclang audio_visual/m1_render.scd").postln;
			"uv run audio_visual/dimtakt_compare.py /tmp/m1_take.wav".postln;
		}),

		Button().states_([["緊急停止", Color.white, Color.red]]).action_({
			s.freeAll; synth = nil; isOn = false;
			"全部止めた".postln;
		})
	));

	win.onClose = { if (synth.notNil) { synth.free }; synth = nil; isOn = false; };

	"M1操作パネルを開いた。「鳴らす」で音が出る。".postln;
});
