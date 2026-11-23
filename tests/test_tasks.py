import io
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import app as clipapp
from tests.test_local_video import HAS_FFMPEG, make_video


def wait(client, task_id, timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        state = client.get(f"/api/tasks/{task_id}").json
        if state["status"] != "running":
            return state
        time.sleep(0.2)
    raise AssertionError("taak bleef te lang lopen")


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is nodig voor deze test")
class BackgroundTaskTests(unittest.TestCase):
    def setUp(self):
        self.client = clipapp.app.test_client()
        tmp = Path(tempfile.mkdtemp())
        src = tmp / "video.mp4"
        make_video(src, seconds=20)
        r = self.client.post("/api/upload-video", data={
            "file": (io.BytesIO(src.read_bytes()), "video.mp4")}, content_type="multipart/form-data")
        shutil.rmtree(tmp)
        self.job = r.json["job"]

    def tearDown(self):
        shutil.rmtree(clipapp.WORK / self.job, ignore_errors=True)

    def test_background_render_reports_result(self):
        r = self.client.post("/api/render", json={
            "job": self.job, "segments": [{"start": 0, "end": 3}], "background": True})
        self.assertEqual(r.status_code, 202)
        state = wait(self.client, r.json["task"])
        self.assertEqual(state["status"], "done", state)
        self.assertEqual(state["result"]["clips"][0]["name"], "clip_01.mp4")
        self.assertIn("Clip 1", state["title"])

    def test_job_is_busy_while_task_runs_and_can_be_cancelled(self):
        r = self.client.post("/api/render", json={
            "job": self.job, "background": True, "vertical": True, "blur": True,
            "segments": [{"start": 0, "end": 19}, {"start": 0, "end": 19}, {"start": 0, "end": 19}]})
        task_id = r.json["task"]
        busy = self.client.post("/api/render", json={"job": self.job, "segments": []})
        self.assertEqual(busy.status_code, 409)
        self.assertEqual(self.client.post(f"/api/tasks/{task_id}/cancel").status_code, 200)
        state = wait(self.client, task_id)
        self.assertEqual(state["status"], "cancelled", state)
        free = self.client.post("/api/render", json={"job": self.job, "segments": []})
        self.assertEqual(free.status_code, 200)

    def test_unknown_task(self):
        self.assertEqual(self.client.get("/api/tasks/doesnotexist").status_code, 404)


if __name__ == "__main__":
    unittest.main()
