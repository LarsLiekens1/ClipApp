import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import app as clipapp
import batch
from tests.test_local_video import HAS_FFMPEG, make_video


class BatchCliTests(unittest.TestCase):
    def test_options_from_arguments(self):
        args = batch.parse_args(["x.mp4", "--count", "3", "--length", "15-30", "--subs", "--face"])
        options = batch.options_from(args)
        self.assertEqual((options["count"], options["min_len"], options["max_len"]), (3, 15, 30))
        self.assertTrue(options["subtitles"] and options["vertical"] and options["blur"])
        self.assertTrue(options["face_crop"])

    def test_invalid_length_is_rejected(self):
        with self.assertRaises(SystemExit):
            batch.parse_args(["x.mp4", "--length", "lang"])

    def test_expand_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.mp4").write_bytes(b"x")
            (tmp / "notes.doc").write_bytes(b"x")
            (tmp / "links.txt").write_text("# lijst\nhttps://youtu.be/1\n\nhttps://youtu.be/2\n")
            sources = batch.expand_sources([str(tmp), str(tmp / "links.txt"), "https://x.test/v"])
        self.assertEqual([Path(s).name if not s.startswith("http") else s for s in sources],
                         ["a.mp4", "https://youtu.be/1", "https://youtu.be/2", "https://x.test/v"])


class BatchApiTests(unittest.TestCase):
    def test_batch_runs_every_link_and_keeps_going_after_errors(self):
        client = clipapp.app.test_client()
        calls = []

        def fake(source, options):
            calls.append(source)
            if source.endswith("kapot"):
                raise RuntimeError("stuk")
            return {"source": source, "job": "abcdefabcdef", "clips": [{"name": "clip_01.mp4"}]}

        with patch.object(clipapp, "process_video", fake):
            r = client.post("/api/batch", json={
                "sources": ["https://a.test/1", "https://a.test/kapot", "https://a.test/3"],
                "options": {"count": 1}})
            self.assertEqual(r.status_code, 202)
            task_id = r.json["task"]
            for _ in range(100):
                state = client.get(f"/api/tasks/{task_id}").json
                if state["status"] != "running":
                    break
                time.sleep(0.05)
        self.assertEqual(state["status"], "done", state)
        self.assertEqual(calls, ["https://a.test/1", "https://a.test/kapot", "https://a.test/3"])
        self.assertEqual(state["result"]["results"][1]["error"], "stuk")

    def test_batch_needs_links(self):
        client = clipapp.app.test_client()
        self.assertEqual(client.post("/api/batch", json={"sources": []}).status_code, 400)
        self.assertEqual(client.post("/api/batch", json={"sources": ["C:/video.mp4"]}).status_code, 400)


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is nodig voor deze test")
class BatchEndToEndTests(unittest.TestCase):
    def test_folder_of_videos_becomes_tiktoks(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            inbox, out = tmp / "inbox", tmp / "out"
            inbox.mkdir()
            make_video(inbox / "Mijn opname.mp4", seconds=12)
            code = batch.main([str(inbox), "--out", str(out), "--count", "1", "--length", "5-8"])
            self.assertEqual(code, 0)
            clips = sorted(out.glob("*.mp4"))
            self.assertEqual([c.name for c in clips], ["Mijn_opname_clip_01.mp4"])
            self.assertEqual(clipapp.video_size(clips[0]), (1080, 1920))
            self.assertTrue((out / "Mijn_opname_clip_01.txt").exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            for d in clipapp.WORK.iterdir():          # taakmappen van deze test opruimen
                meta = d / "meta.json"
                if meta.exists() and "Mijn opname.mp4" in meta.read_text(encoding="utf-8"):
                    shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
