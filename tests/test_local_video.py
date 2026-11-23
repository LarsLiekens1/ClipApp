import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import app as clipapp

HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def make_video(path, seconds=6, size="640x360"):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"testsrc=size={size}:rate=25:duration={seconds}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path),
    ], check=True)


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is nodig voor deze test")
class LocalVideoTests(unittest.TestCase):
    def setUp(self):
        self.client = clipapp.app.test_client()
        self.tmp = Path(tempfile.mkdtemp())
        self.jobs = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for job in self.jobs:
            shutil.rmtree(clipapp.WORK / job, ignore_errors=True)

    def upload(self, name):
        src = self.tmp / name
        make_video(src)
        r = self.client.post("/api/upload-video", data={
            "file": (io.BytesIO(src.read_bytes()), name)}, content_type="multipart/form-data")
        if r.status_code == 200:
            self.jobs.append(r.json["job"])
        return r

    def test_upload_and_render_vertical_clip(self):
        r = self.upload("mijn video.mp4")
        self.assertEqual(r.status_code, 200, r.json)
        self.assertAlmostEqual(r.json["duration"], 6, delta=0.3)
        job = r.json["job"]
        r = self.client.post("/api/render", json={
            "job": job, "segments": [{"start": 1, "end": 4}],
            "vertical": True, "blur": True,
        })
        self.assertEqual(r.status_code, 200, r.json)
        out = clipapp.WORK / job / r.json["clips"][0]["name"]
        self.assertEqual(clipapp.video_size(out), (1080, 1920))
        self.assertAlmostEqual(clipapp.duration_of(out), 3, delta=0.3)

    def test_mov_gets_browser_preview(self):
        r = self.upload("clip.mov")
        self.assertEqual(r.status_code, 200, r.json)
        self.assertTrue(r.json["video"].endswith("/preview.mp4"))

    def test_rejects_non_video(self):
        r = self.client.post("/api/upload-video", data={
            "file": (io.BytesIO(b"hallo"), "notes.txt")}, content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
