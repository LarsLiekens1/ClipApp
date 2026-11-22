import unittest

from auto_clips import (
    AutoClipError,
    build_sentences,
    build_transcript,
    hook_score,
    loudness_per_second,
    suggest_clips,
)


def sentence_cues(sentences):
    """Maak cues van (start, end, tekst)-zinnen, zoals Whisper ze per paar woorden geeft."""
    cues = []
    for start, end, text in sentences:
        words = text.split()
        step = (end - start) / len(words)
        for k, w in enumerate(words):
            cues.append([start + k * step, start + (k + 1) * step, w])
    return cues


FILLER = "we gaan hier rustig verder met het verhaal van vandaag."


def video(n=24, special=None):
    """n zinnen van 5 s; special = {index: tekst} voor afwijkende zinnen."""
    special = special or {}
    return sentence_cues([(i * 5.0, i * 5.0 + 4.8, special.get(i, FILLER)) for i in range(n)])


class SentenceTests(unittest.TestCase):
    def test_builds_sentences_on_punctuation_and_pauses(self):
        cues = [[0.0, 1.0, "Hallo"], [1.0, 1.5, "allemaal."], [1.6, 2.0, "Kijk"], [4.0, 5.0, "hier"]]
        self.assertEqual([s["text"] for s in build_sentences(cues)],
                         ["Hallo allemaal.", "Kijk", "hier"])
        self.assertTrue(build_transcript(cues).startswith("[0.0-1.5] Hallo allemaal."))

    def test_hook_score_prefers_questions_and_hook_words_over_weak_starts(self):
        self.assertGreater(hook_score("Waarom doet niemand dit?"), 0.6)
        self.assertLess(hook_score("en toen gingen we verder"), 0.2)


class SuggestClipsTests(unittest.TestCase):
    def test_clips_start_and_end_on_sentence_boundaries(self):
        clips = suggest_clips(video(), 120, count=3, min_len=20, max_len=30)
        self.assertTrue(clips)
        for c in clips:
            self.assertAlmostEqual((c["start"] + 0.15) % 5.0, 0.0, places=1)
            self.assertTrue(20 <= c["end"] - c["start"] <= 31)

    def test_picks_the_moment_with_a_hook_and_loud_audio(self):
        energy = [0.1] * 120
        for sec in range(60, 85):
            energy[sec] = 0.5
        cues = video(special={12: "Waarom zegt niemand je dit geheim? Echt niet normaal!"})
        clips = suggest_clips(cues, 120, count=1, min_len=20, max_len=30, energy=energy)
        self.assertEqual(len(clips), 1)
        self.assertLessEqual(clips[0]["start"], 60)
        self.assertGreater(clips[0]["end"], 60)
        self.assertIn("geheim", clips[0]["caption"])
        self.assertIn("#fyp", clips[0]["hashtags"])
        self.assertTrue(clips[0]["reason"])

    def test_uses_comment_timestamps_and_popular_comment_caption(self):
        bins = [{"start": s, "end": s + 30, "comment_mentions": 20 if s == 90 else 0,
                 "viewer_score": None} for s in range(0, 120, 30)]
        comments = [{"timestamps": [95], "text": "1:35 hier ging het helemaal mis", "like_count": 40}]
        clips = suggest_clips(video(), 120, count=1, min_len=20, max_len=30,
                              bins=bins, comments=comments)
        self.assertGreaterEqual(clips[0]["end"], 95)
        self.assertEqual(clips[0]["caption"], "Hier ging het helemaal mis")

    def test_clips_do_not_overlap_and_respect_count(self):
        clips = suggest_clips(video(), 120, count=10, min_len=20, max_len=30)
        self.assertLessEqual(len(clips), 10)
        for a, b in zip(clips, clips[1:]):
            self.assertLessEqual(a["end"], b["start"])

    def test_works_without_speech_using_audio_energy(self):
        energy = [0.1] * 100
        energy[70:80] = [0.9] * 10
        clips = suggest_clips([], 100, count=1, min_len=20, max_len=30, energy=energy)
        self.assertTrue(clips[0]["start"] <= 70 < clips[0]["end"])

    def test_errors_without_any_signal(self):
        with self.assertRaises(AutoClipError):
            suggest_clips([], 60)

    def test_loudness_per_second(self):
        self.assertEqual(loudness_per_second([0.5] * 32000 + [0.0] * 100), [0.5, 0.5])


if __name__ == "__main__":
    unittest.main()
