import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as clipapp
from tests.test_local_video import HAS_FFMPEG, make_video


class WordHelpersTests(unittest.TestCase):
    def test_words_between_shifts_times_to_clip_start(self):
        words = [[0.5, 1.0, " a"], [10.2, 10.8, " Hallo"], [11.0, 11.6, " daar."], [30, 31, " b"]]
        result = clipapp.words_between(words, 10, 12)
        self.assertEqual([w[2] for w in result], [" Hallo", " daar."])
        for (start, end, _), expected in zip(result, [(0.2, 0.8), (1.0, 1.6)]):
            self.assertAlmostEqual(start, expected[0])
            self.assertAlmostEqual(end, expected[1])

    def test_make_cues_from_word_lists(self):
        cues = clipapp.make_cues([[0, 0.4, " Hallo"], [0.5, 0.9, " allemaal."], [1.0, 1.4, " Kijk"]])
        self.assertEqual([c[2] for c in cues], ["Hallo allemaal.", "Kijk"])


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is nodig voor deze test")
class ReuseTranscriptTests(unittest.TestCase):
    def test_render_uses_saved_transcript_instead_of_whisper(self):
        client = clipapp.app.test_client()
        tmp = Path(tempfile.mkdtemp())
        make_video(tmp / "v.mp4", seconds=8)
        r = client.post("/api/upload-video", data={
            "file": (io.BytesIO((tmp / "v.mp4").read_bytes()), "v.mp4")},
            content_type="multipart/form-data")
        shutil.rmtree(tmp)
        job = r.json["job"]
        d = clipapp.WORK / job
        try:
            (d / "transcript.json").write_text(json.dumps({
                "energy": [0.1] * 8, "language": "", "model": clipapp.WHISPER_MODEL,
                "cues": [[2.1, 3.0, "Dit is een test."]],
                "words": [[2.1, 2.4, " Dit"], [2.4, 2.6, " is"], [2.6, 2.8, " een"], [2.8, 3.0, " test."]],
            }))

            def no_whisper(*a, **k):
                raise AssertionError("Whisper mag niet opnieuw draaien")

            with patch.object(clipapp, "transcribe", no_whisper):
                r = client.post("/api/render", json={
                    "job": job, "segments": [{"start": 2, "end": 5}], "subtitles": True})
            self.assertEqual(r.status_code, 200, r.json)
            srt = (d / "clip_01.srt").read_text(encoding="utf-8")
            self.assertIn("00:00:00,100 -->", srt)
            self.assertIn("Dit is een", srt)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
