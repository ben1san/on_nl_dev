// =====================================================================
//  M1: 連続体層 — 砂嵐から共鳴で音程を彫る
// =====================================================================
//
//  この層が担う目標指標は2つだけ。既定値での実測は次のとおり:
//
//      指標                  目標帯        M1既定値   参照(dimtakt)   v5(旧)
//      2-8kHz エネルギー [%]   0.9 〜 5.6      3.99        1.28        0.19
//      LTAS平坦度 100-2000    ≥ 0.024      0.0596      0.1060      0.0103
//
//  ついでに目標帯へ入った(M3で詰める予定だった)もの:
//      LR相関                0.78 〜 0.94    0.825       0.765       0.223
//      低音ピーク幅 [cent]     11 〜 33         25          13          10
//
//  この層では未達のまま残るもの(いずれもM2=出来事層の担当):
//      重心 p10-p90幅・スペクトル変化率のSD・減衰イベント数・RT60
//
//  同じ設定でも励起がノイズなので毎回わずかに違う音になる。3回レンダリング
//  した際のばらつきは 2-8kHz が ±5%、平坦度が ±4%、低音ピーク幅が ±20%
//  だった。**この幅より小さい差は改善ではなく偶然なので、比較の際は注意する。**
//
//  正弦波を並べる加算合成では原理的に届かない部分をここで作る。dimtaktの
//  スペクトルは「倍音の線」と「線と線の間を埋める連続体」の二層でできており、
//  v5には後者が無かった(平坦度 0.011 = 目標の1/2.2)。
//
//  作り方は加算ではなく減算に近い。広帯域のノイズを共鳴体に通し、共鳴の山
//  として音程を浮かび上がらせる。山と山の間には励起音そのものが残るので、
//  連続体は「足す」のではなく最初からそこにある。
//
//  ---- 使い方(ライブ) ----
//      s.boot;
//      "audio_visual/m1_continuum.scd".loadRelative;   // 定義を読む
//      ~continuum = Synth(\continuum);
//      ~continuum.set(\ringMax, 2.0);                  // 鳴らしたまま変える
//      ~continuum.set(\bedLevel, -30.dbamp);
//      ~continuum.free;
//
//  ---- 使い方(測定) ----
//      sclang audio_visual/m1_render.scd
//      uv run audio_visual/dimtakt_compare.py /tmp/m1_take.wav
//
//  パラメータと指標の対応(実測で確かめた効き方):
//      ringMin/ringMax  共鳴の減衰時間。長い=山が鋭い=平坦度が下がる
//      ringTilt         減衰時間を部分音ごとに落とす率。低音の鋭さと谷埋めの分担
//      ringComp         減衰時間によるゲイン増を打ち消す量。1で完全補正
//      bedLevel         共鳴を通さない素の励起音。上げると平坦度が直に上がる
//      tilt             全体の明るさ。2-8kHzを動かす主力のつまみ
//      driftHz/driftAmt 各共鳴が独立にゆらぐ速さと深さ
//      width            左右の混ぜ戻し量。LR相関を直接動かす
//
//  残響はこの層に持たせない。M2の出来事層と共有する空間段(space.scd)が持つ。
//  持続音だけに残響をかけても知覚されないことが試聴で確認されている
//  (A_基準とE_残響ありが聞き分けられなかった)。残響は立ち上がりを必要とする。
//
//  共鳴の本数(nLo/nHi)だけはSynthDefの構造を決めるため実行時には変えられない。
//  変えたい場合はコードを直して読み直す。
//

~makeContinuumDef = {
	SynthDef(\continuum, { |out = 0,
		amp = 0.2,
		baseFreq = 142.7,      // 参照録音の低音とだいたい同じ高さから始める
		stretch = 1.0,         // 1.0=倍音列 / 1.0より大きい=非調和に開く
		// 以下の既定値は測定で詰めたもの。この状態で M1 の2指標は合格する。
		ringMin = 0.08, ringMax = 9.0, ringTilt = 0.45, ringComp = 1.0,
		bedLevel = 0.06,       // 素の励起音の混ぜ量
		tilt = 1.2,            // 明るさ。上げると2-8kHzが増える
		driftHz = 0.07, driftAmt = 0.004,
		noiseLevel = 0.5,      // 連続ノイズ励起の量。下げると共鳴が「叩かれる」音になる
		dustRate = 9.0, dustAmt = 0.5,
		width = 0.7,           // 左右の非相関の量。0=完全モノ
		lag = 0.3|

		var nLo = 14, nHi = 10;   // 低中域の共鳴数 / 高域の共鳴数
		var exc, bed, res, sig, freqs, amps, rings, drift;
		var mkChannel;

		ringMin = Lag.kr(ringMin, lag); ringMax = Lag.kr(ringMax, lag);
		ringTilt = Lag.kr(ringTilt, lag); ringComp = Lag.kr(ringComp, lag);
		bedLevel = Lag.kr(bedLevel, lag); tilt = Lag.kr(tilt, lag);
		driftAmt = Lag.kr(driftAmt, lag); baseFreq = Lag.kr(baseFreq, lag);

		// ---- 励起: 連続のピンクノイズ + ポアソン的な粒 ----
		// Dustは非周期なので、これ自体が後段(M2)の出来事層の種にもなる。
		exc = PinkNoise.ar(Lag.kr(noiseLevel, lag))
		    + (Dust.ar(dustRate) * dustAmt * 6);

		// 明るさの傾き。tiltが0なら素通りに近い
		exc = exc + (HPF.ar(exc, 900) * tilt);

		// ---- 共鳴体を1チャンネル分作る関数 ----
		// seedをずらして左右で別の共鳴体にすると相関が下がる。widthで混ぜる。
		mkChannel = { |seed|
			var f, a, r, d;
			f = Array.fill(nLo + nHi, { |i|
				var n = i + 1;
				if (i < nLo) {
					// 低中域: 非調和に開いた部分音列。stretch>1で金属寄りになる
					baseFreq * pow(n, stretch) * (1 + (0.011 * ((seed * 7 + i * 13) % 5 - 2)))
				} {
					// 高域: 2-8kHzを埋めるための、音程に紐づかない共鳴
					2000 * pow(1.29, i - nLo) * (1 + (0.03 * ((seed * 3 + i * 11) % 7 - 3)))
				}
			});
			// 各共鳴に独立したゆらぎ。周波数が互いに無理数比なので位相が揃わない
			d = Array.fill(nLo + nHi, { |i|
				LFDNoise3.kr(driftHz * (1 + (i * 0.37)), driftAmt)
			});
			f = f * (1 + d);
			a = Array.fill(nLo + nHi, { |i|
				if (i < nLo) { 1 / pow(i + 1, 0.85) } { 0.16 / pow(1.22, i - nLo) }
			});
			// 減衰時間は部分音ごとに変える。ここが M1 で一番効いた設計判断:
			//   全部を長くすると低音の山は鋭くなる(低音ピーク幅が目標帯に入る)が、
			//   山という山が細くなって谷が開き、平坦度が落ちる。
			//   全部を短くすると逆になる。両立しないので周波数で分担させる。
			//   低い部分音ほど長く(音程を担う)、高い部分音ほど短く(谷を埋める)。
			r = Array.fill(nLo + nHi, { |i|
				var jitter = 0.75 + (0.5 * ((seed + (i * 0.41)) % 1.0));
				(ringMin + ((ringMax - ringMin) * pow(ringTilt, i))) * jitter
			});
			// 共鳴のゲインは減衰時間に比例して上がる。補正しないと、減衰を伸ばした
			// 瞬間に低い部分音だけが巨大になり、全エネルギーを占めて2-8kHzの比率も
			// 平坦度も一緒に落ちる(実測: ringMaxを0.9→4.0にしただけで平坦度が
			// 0.061→0.013へ崩れた)。白色励起に対する定常パワーは減衰時間に比例
			// するので、振幅を sqrt(減衰時間) で割って打ち消す。これで減衰時間は
			// 「山の鋭さ」だけを動かすつまみになる。
			a = a / (r.sqrt * ringComp + (1 - ringComp));
			DynKlank.ar(`[f, a, r], exc * 0.28)
		};

		res = [mkChannel.(0.13), mkChannel.(0.71)];

		// ---- 素の励起音(bed) ----
		// 共鳴の山と山の間を埋めるのはこれ。平坦度を直接動かすつまみになる。
		bed = BPF.ar(exc, 700, 2.2) * bedLevel;
		bed = [bed, DelayN.ar(bed, 0.02, 0.011)];   // 左右をわずかにずらす

		sig = res + bed;

		// widthで左右をどれだけ混ぜ戻すか= LR相関の制御
		sig = [
			(sig[0] * (1 - (width * 0.5))) + (sig[1] * (width * 0.5)),
			(sig[1] * (1 - (width * 0.5))) + (sig[0] * (width * 0.5))
		];

		sig = LeakDC.ar(sig);

		sig = Limiter.ar(sig, 0.9);
		Out.ar(out, sig * amp);
	})
};

// ライブで読んだときは、その場でサーバへ送る
if (thisProcess.nowExecutingPath.isNil.not and: { Server.default.serverRunning }) {
	~makeContinuumDef.().add;
	"m1_continuum: SynthDef \\continuum を登録した。Synth(\\continuum) で鳴る".postln;
};
