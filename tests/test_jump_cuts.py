import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import app as clipapp
from tests.test_local_video import HAS_FFMPEG


class RemapTests(unittest.TestCase):
    KEEPS = [(0.0, 2.0), (4.0, 6.0)]

    def test_keep_ranges_leaves_a_little_padding(self):
        keeps = clipapp.keep_ranges([(2.0, 4.0)], 6.0)
        self.assertEqual(keeps, [(0.0, 2.12), (3.88, 6.0)])

    def test_short_pauses_are_kept(self):
        self.assertEqual(clipapp.keep_ranges([(2.0, 2.3)], 6.0), [(0.0, 6.0)])

    def test_remap_time(self):
        self.assertEqual(clipapp.remap_time(1.0, self.KEEPS), 1.0)
        self.assertIsNone(clipapp.remap_time(3.0, self.KEEPS))
        self.assertEqual(clipapp.remap_time(5.0, self.KEEPS), 3.0)

    def test_remap_words_drops_words_in_removed_parts(self):
        words = [[0.5, 1.0, " a"], [2.5, 3.0, " weg"], [4.5, 5.0, " b"]]
        self.assertEqual(clipapp.remap_words(words, self.KEEPS),
                         [[0.5, 1.0, " a"], [2.5, 3.0, " b"]])


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is nodig voor deze test")
class JumpCutRenderTests(unittest.TestCase):
    def test_silence_in_the_middle_is_removed(self):
        tmp = Path(tempfile.mkdtemp())
        src = tmp / "pauze.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc=size=320x240:rate=25:duration=6",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
            "-af", "volume='if(between(t,2,4),0,1)':eval=frame",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(src),
        ], check=True)
        client = clipapp.app.test_client()
        r = client.post("/api/upload-video", data={
            "file": (io.BytesIO(src.read_bytes()), "pauze.mp4")}, content_type="multipart/form-data")
        shutil.rmtree(tmp)
        d = clipapp.WORK / r.json["job"]
        try:
            r = client.post("/api/render", json={
                "job": d.name, "segments": [{"start": 0, "end": 6}], "jump_cuts": True})
            self.assertEqual(r.status_code, 200, r.json)
            length = clipapp.duration_of(d / "clip_01.mp4")
            self.assertAlmostEqual(length, 6 - 2 + 2 * clipapp.SILENCE_PAD, delta=0.35)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
