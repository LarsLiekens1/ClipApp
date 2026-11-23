import json
import unittest
from unittest.mock import patch

import app as clipapp


class WhisperOptionTests(unittest.TestCase):
    def test_model_choice_is_validated(self):
        self.assertEqual(clipapp.whisper_model_from({"whisper_model": "tiny"}), "tiny")
        self.assertEqual(clipapp.whisper_model_from({}), clipapp.WHISPER_MODEL)
        with self.assertRaises(ValueError):
            clipapp.whisper_model_from({"whisper_model": "large-v9"})

    def test_cpu_is_used_when_forced(self):
        with patch.object(clipapp, "WHISPER_DEVICE", "cpu"):
            self.assertEqual(clipapp.whisper_device(), "cpu")

    def test_second_job_on_same_task_is_refused_while_busy(self):
        d = clipapp.WORK / "abcabcabcabc"
        d.mkdir(exist_ok=True)
        (d / "meta.json").write_text(json.dumps({"url": "https://x.test", "duration": 60}))
        client = clipapp.app.test_client()
        try:
            with clipapp.job_busy(d) as ok:
                self.assertTrue(ok)
                r = client.post("/api/render", json={"job": d.name, "segments": []})
                self.assertEqual(r.status_code, 409)
                r = client.post("/api/auto-clips", json={"job": d.name})
                self.assertEqual(r.status_code, 409)
            r = client.post("/api/render", json={"job": d.name, "segments": []})
            self.assertEqual(r.status_code, 200)
        finally:
            for f in d.iterdir():
                f.unlink()
            d.rmdir()


if __name__ == "__main__":
    unittest.main()
