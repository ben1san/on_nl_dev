"""
忘却炉 聴覚演出プロトタイプ（実験用スタンドアロン版）

目的:
    classical_erasure/architecture.md・components.md が確定している回路の実クロック値
    （相補コンデンサ対の4相サイクル、~7.5kHz）から、捏造ではなく実測値の分周として
    可聴な音高・テンポを導出し、Play/Destroy（CHI PLAY 2026）の「再生する行為そのもの
    が破壊である」という設計思想を、audio_visual/聴覚演出はノーバッファの連続グライド
    楽器として記憶の中身相関を担う.md が既に定めた「ブロックをまたいでバッファを持ち
    越さない」という制約の範囲内で実装できるかを試す。

重要な注意（このプロトタイプの位置づけ）:
    - これは実機（Raspberry Pi / Pico / MQTT）とは接続していないスタンドアロンの
      音響実験である。ブロックごとの「元データ」は本物の消去対象データではなく、
      疑似乱数で生成したダミーバイト列で代替している（本物のQRNG出力rでも実データd
      でもない）。実装する場合は必ずPiからPicoへ流れる実ブロックに差し替えること。
    - 度数・オクターブ・ブロック長など、回路定数から一意に決まらないパラメータは
      このプロトタイプでの実験用の暫定値であり、確定仕様ではない。
    - 生成音源（グレイン波形）はコピーライトフリーな自前合成のみを使用している
      （technical_req.mdのFR-08既存曲不使用の方針に合わせた）。

出力:
    erasure_sonification_prototype.wav
        Section A (0-8s)   : グレインのみ, 劣化度 p=0.0（消去開始直後を想定）
        Section B (8-16s)  : グレインのみ, 劣化度 p=0.5（消去中盤を想定）
        Section C (16-24s) : グレインのみ, 劣化度 p=1.0（点火直前・完全劣化を想定）
        [1秒無音の区切り]
        Section D (25-49s) : ドローン(常時鳴る470Hz系トーン) + グレイン(実テンポ)
                              の合成、実際に鳴っているであろう質感の連続24秒抜粋
"""

import numpy as np
from scipy.io import wavfile

SR = 44100

# ---- 回路の実定数（components.md 0節、architecture.md 4.4節） ----
R = 117.0        # ohm : R_ext(110) + TC4427 R_on(~7)
C = 71e-9        # F   : セル容量
TAU = R * C                    # 1遷移の時定数 ≈ 8.307 us
PHASE_TIME = 4 * TAU           # 1相(4tau、フル充放電) ≈ 33.228 us
CYCLE_TIME = 16 * TAU          # 4相1サイクル ≈ 132.912 us
F_CYCLE = 1.0 / CYCLE_TIME     # ≈ 7523.78 Hz。8bit並列なので「1サイクル=1バイト処理」

# クロック分周（実在するPIOのクロックディバイダの考え方をそのまま流用。
# 捏造ではなくF_CYCLEの整数分周であることを崩さない）
DRONE_DIVISOR = 16
F_DRONE = F_CYCLE / DRONE_DIVISOR   # ≈ 470.24 Hz (平均律A#4+15cent相当)

# ブロック周期（ノーバッファ制約下でPi→Picoへ実際にストリーミングされる単位。
# 具体的なバイト数は既存ドキュメントに数値がないため、このプロトタイプでは
# 儀式的なテンポ感を優先して4096byteを暫定値として置く）
BLOCK_BYTES = 4096
BLOCK_TIME = BLOCK_BYTES / F_CYCLE  # ≈ 0.5444 s ( ≈1.84 Hz )

rng = np.random.default_rng(20260817)


def rc_shape(n, tau_ratio=0.28):
    """RC充放電カーブ(1相=charge, 1相=discharge)を1周期ぶんの波形として返す。
    正弦波ではなく実回路の充放電式 (1-exp)/(exp) をそのまま波形の形に使うことで、
    音色そのものが実回路の物理過程の相似形になるようにする。"""
    t = np.linspace(0, 1, n, endpoint=False)
    half = n // 2
    tau = tau_ratio
    charge = 1 - np.exp(-t[:half] / (tau * 0.5))
    discharge = np.exp(-(t[:n - half] - 0) / (tau * 0.5))
    charge = charge / charge.max()
    discharge = discharge / discharge.max()
    shape = np.concatenate([charge, -discharge])  # 充電=正、放電=負の半サイクル
    return shape


def render_drone(duration_s, f=F_DRONE, amp=0.18):
    n_total = int(duration_s * SR)
    period_n = max(4, int(round(SR / f)))
    one_cycle = rc_shape(period_n)
    reps = int(np.ceil(n_total / period_n))
    wave = np.tile(one_cycle, reps)[:n_total]
    # わずかな高調波を足して単調な電子音を避ける(実回路のRC波形は基音以外に
    # 高次の充放電残留成分を持つはずなので、2倍音を小さく足すのは物理的にも自然)
    wave2 = np.tile(rc_shape(max(4, period_n // 2)), reps * 2)[:n_total]
    return amp * (0.85 * wave + 0.15 * wave2)


def degrade(signal, p, seed_offset=0):
    """Play/Destroy的な不可逆劣化。ビットクラッシュ(量子化ノイズ)を主体にし、
    連続ホワイトノイズは使わない
    （audio_visual/聴覚演出はノーバッファ...md が試聴で「耳障りな“サー”」と判定済み）。
    ドロップアウト(サンプル&ホールド)は控えめな確率にとどめる。"""
    if p <= 0:
        return signal.copy()
    g = np.random.default_rng(1000 + seed_offset)
    bits = 16 - round(13 * p)          # 16bit -> 3bitまで劣化
    bits = max(2, bits)
    levels = 2 ** bits
    crushed = np.round(signal * (levels / 2)) / (levels / 2)
    # サンプル&ホールドのドロップアウト（確率は劣化度に比例、上限を抑える）
    drop_prob = 0.22 * p
    mask = g.random(len(signal)) < drop_prob
    held = crushed.copy()
    last = 0.0
    out = np.empty_like(crushed)
    for i in range(len(crushed)):
        if mask[i]:
            out[i] = last
        else:
            out[i] = held[i]
            last = held[i]
    return out


def render_grain(duration_s, pitch_hz, p, seed_offset):
    """1ブロック分だけ生きるグレイン。既存決定ノートに合わせ、ブロックの
    バイト列から導いた制御値(ここではダミーデータの平均・分散)だけを使い、
    生成後は他ブロックへ持ち越さない。"""
    n = int(duration_s * SR)
    t = np.linspace(0, duration_s, n, endpoint=False)
    # RC放電カーブをアタック/ディケイのエンベロープとして使う
    tau_env = duration_s * 0.22
    env = np.exp(-t / tau_env)
    tone = np.sin(2 * np.pi * pitch_hz * t) * env
    tone += 0.35 * np.sin(2 * np.pi * pitch_hz * 2.0 * t) * env  # 倍音
    tone = tone / (np.max(np.abs(tone)) + 1e-9)
    tone = degrade(tone, p, seed_offset=seed_offset)
    return 0.5 * tone * env  # エンベロープを再度掛け直し、劣化後も末尾のプチノイズを抑える


def simulate_block_byte_stats(seed):
    """実装では本物のブロックデータから導出する値。ここではダミー。"""
    g = np.random.default_rng(seed)
    b = g.integers(0, 256, size=BLOCK_BYTES)
    return b.mean(), b.std()


def render_grain_section(n_blocks, p, label):
    chunks = []
    for i in range(n_blocks):
        mean_b, std_b = simulate_block_byte_stats(seed=42_000 + i)
        # バイト平均をF_DRONE周辺の音程オフセットにマッピング(既存ノートのポルタメント
        # 追従先の考え方を単純化した簡易版)
        pitch = F_DRONE * (1.0 + (mean_b - 128) / 128 * 0.5)
        grain_len = BLOCK_TIME * 0.85  # ブロック周期のうち鳴る割合
        grain = render_grain(grain_len, pitch, p, seed_offset=i)
        gap = np.zeros(int((BLOCK_TIME - grain_len) * SR))
        chunks.append(grain)
        chunks.append(gap)
    sig = np.concatenate(chunks)
    print(f"[{label}] p={p:.2f} blocks={n_blocks} duration={len(sig)/SR:.2f}s "
          f"block_time={BLOCK_TIME*1000:.1f}ms tempo={1/BLOCK_TIME:.2f}Hz")
    return sig


def analyze(sig, sr, label):
    rms = float(np.sqrt(np.mean(sig ** 2)))
    peak = float(np.max(np.abs(sig)) + 1e-12)
    crest_db = 20 * np.log10(peak / (rms + 1e-12))
    spec = np.abs(np.fft.rfft(sig * np.hanning(len(sig))))
    freqs = np.fft.rfftfreq(len(sig), d=1 / sr)
    centroid = float(np.sum(freqs * spec) / (np.sum(spec) + 1e-12))
    print(f"  -> RMS={rms:.4f}  peak={peak:.4f}  crest={crest_db:.1f}dB  "
          f"spectral_centroid={centroid:.1f}Hz")
    return dict(rms=rms, peak=peak, crest_db=crest_db, centroid=centroid)


def main():
    print("=== 回路定数 ===")
    print(f"tau={TAU*1e6:.3f}us  1phase={PHASE_TIME*1e6:.3f}us  "
          f"1cycle={CYCLE_TIME*1e6:.3f}us  f_cycle={F_CYCLE:.2f}Hz")
    print(f"f_drone(f_cycle/{DRONE_DIVISOR})={F_DRONE:.2f}Hz")
    print(f"block={BLOCK_BYTES}B  block_time={BLOCK_TIME*1000:.2f}ms  "
          f"tempo={1/BLOCK_TIME:.2f}Hz")
    print()

    print("=== Section A/B/C: グレイン劣化のアーク(グレインのみ) ===")
    n_blocks_per_section = int(round(8.0 / BLOCK_TIME))
    secA = render_grain_section(n_blocks_per_section, 0.0, "A p=0.0")
    secB = render_grain_section(n_blocks_per_section, 0.5, "B p=0.5")
    secC = render_grain_section(n_blocks_per_section, 1.0, "C p=1.0")

    silence = np.zeros(int(1.0 * SR))

    print()
    print("=== Section D: ドローン + グレイン(実テンポ)の24秒リアルタイム抜粋 ===")
    dur_d = 24.0
    drone = render_drone(dur_d, amp=0.16)
    n_blocks_d = int(round(dur_d / BLOCK_TIME))
    grains_d = render_grain_section(n_blocks_d, 0.32, "D excerpt p~=0.32")[: len(drone)]
    if len(grains_d) < len(drone):
        grains_d = np.pad(grains_d, (0, len(drone) - len(grains_d)))
    secD = drone + grains_d

    full = np.concatenate([secA, secB, secC, silence, secD])
    full = full / (np.max(np.abs(full)) + 1e-9) * 0.92

    print()
    print("=== 音響解析(セクション別) ===")
    analyze(secA, SR, "A")
    analyze(secB, SR, "B")
    analyze(secC, SR, "C")
    analyze(secD, SR, "D(drone+grain)")
    analyze(drone, SR, "drone単体")

    out_path = "erasure_sonification_prototype.wav"
    wavfile.write(out_path, SR, (full * 32767).astype(np.int16))
    print()
    print(f"書き出し完了: {out_path}  総尺={len(full)/SR:.2f}s")


if __name__ == "__main__":
    main()
