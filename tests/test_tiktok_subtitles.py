import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import app as clipapp
from tests.test_local_video import HAS_FFMPEG, make_video

WORDS = [[0.0, 0.4, " Waarom"], [0.4, 0.8, " doet"], [0.8, 1.2, " niemand"], [1.3, 1.8, " dit?"]]


class TikTokAssTests(unittest.TestCase):
    def test_one_line_per_word_with_highlight(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub.ass"
            clipapp.write_tiktok_ass(path, clipapp.group_words(WORDS), 1080, 1920, color="green")
            text = path.read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.startswith("Dialogue:")]
        self.assertGreaterEqual(len(lines), 4)
        self.assertIn("{\\c&H5AF254&\\fscx112\\fscy112}WAAROM{\\r}", lines[0])
        self.assertIn("Arial Black", text)

    def test_group_words_keeps_words_and_matches_make_cues(self):
        groups = clipapp.group_words(WORDS)
        self.assertEqual([c[2] for c in clipapp.make_cues(WORDS)],
                         ["".join(w[2] for w in g[2]).strip() for g in groups])


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is nodig voor deze test")
class TikTokRenderTests(unittest.TestCase):
    def test_render_with_tiktok_style(self):
        client = clipapp.app.test_client()
        tmp = Path(tempfile.mkdtemp())
        make_video(tmp / "v.mp4", seconds=5)
        r = client.post("/api/upload-video", data={
            "file": (io.BytesIO((tmp / "v.mp4").read_bytes()), "v.mp4")},
            content_type="multipart/form-data")
        shutil.rmtree(tmp)
        d = clipapp.WORK / r.json["job"]
        try:
            (d / "transcript.json").write_text(json.dumps({
                "energy": [0.1] * 5, "language": "", "model": clipapp.WHISPER_MODEL,
                "cues": [], "words": WORDS}))
            r = client.post("/api/render", json={
                "job": d.name, "segments": [{"start": 0, "end": 3}], "subtitles": True,
                "vertical": True, "blur": True, "sub_style": "tiktok", "sub_color": "pink"})
            self.assertEqual(r.status_code, 200, r.json)
            self.assertIn("B469FF", (d / "clip_01.ass").read_text(encoding="utf-8"))
            self.assertEqual(clipapp.video_size(d / "clip_01.mp4"), (1080, 1920))
            r = client.post("/api/render", json={
                "job": d.name, "segments": [{"start": 0, "end": 3}], "sub_style": "neon"})
            self.assertEqual(r.status_code, 400)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
