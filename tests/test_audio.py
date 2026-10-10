import numpy as np

from jarvis.audio import BLOCK_MS, Segmenter

SR = 16000
N = SR * BLOCK_MS // 1000
rng = np.random.default_rng(0)


def silence(blocks):
    return [rng.normal(0, 0.002, N).astype(np.float32) for _ in range(blocks)]


def speech(blocks):
    return [rng.normal(0, 0.1, N).astype(np.float32) for _ in range(blocks)]


def run(seg, blocks):
    return [p for b in blocks if (p := seg.feed(b)) is not None]


def test_silence_returns_nothing():
    assert run(Segmenter(SR), silence(200)) == []


def test_phrase_is_returned_after_trailing_silence():
    phrases = run(Segmenter(SR), silence(20) + speech(20) + silence(40))
    assert len(phrases) == 1
    assert len(phrases[0]) >= 20 * N  # parole + pré-roll + silence final


def test_short_noise_is_ignored():
    assert run(Segmenter(SR, min_speech_ms=250), silence(20) + speech(2) + silence(40)) == []


def test_two_phrases_are_separated():
    audio = silence(10) + speech(15) + silence(40) + speech(15) + silence(40)
    assert len(run(Segmenter(SR), audio)) == 2


def test_long_speech_is_cut_at_max_length():
    seg = Segmenter(SR, max_phrase_s=1.0)
    phrases = run(seg, speech(100))
    assert phrases and len(phrases[0]) <= 1.1 * SR


def test_noise_floor_adapts_to_loud_room():
    seg = Segmenter(SR)
    for b in [rng.normal(0, 0.03, N).astype(np.float32) for _ in range(1200)]:
        seg.feed(b)
    assert seg.threshold > 0.05
    # La parole, nettement plus forte que ce bruit, est de nouveau détectée.
    assert len(run(seg, speech(20) + silence(40))) == 1
