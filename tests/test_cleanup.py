import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import app as clipapp


class CleanupTests(unittest.TestCase):
    def test_removes_only_old_job_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            old, new, other = work / "aaaaaaaaaaaa", work / "bbbbbbbbbbbb", work / "keep-me"
            for d in (old, new, other):
                d.mkdir()
                (d / "clip.mp4").write_bytes(b"x")
            past = time.time() - 10 * 86400
            for path in (old, old / "clip.mp4", other, other / "clip.mp4"):
                os.utime(path, (past, past))
            with patch.object(clipapp, "WORK", work):
                self.assertEqual(clipapp.cleanup_work(7), 1)
            self.assertFalse(old.exists())
            self.assertTrue(new.exists())
            self.assertTrue(other.exists())

    def test_zero_days_disables_cleanup(self):
        with patch.dict(os.environ, {"CLIPAPP_KEEP_DAYS": "0"}):
            self.assertEqual(clipapp.cleanup_work(), 0)


if __name__ == "__main__":
    unittest.main()
