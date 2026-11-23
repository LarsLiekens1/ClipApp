import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import app as clipapp
import delivery


class UploadFunctionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.video = Path(self.tmp.name) / "clip_01.mp4"
        self.video.write_bytes(b"\x00" * 1024)

    def tearDown(self):
        self.tmp.cleanup()

    def fake_service(self):
        insert = MagicMock()
        insert.next_chunk.return_value = (None, {"id": "abc123", "status": {"privacyStatus": "private"}})
        service = MagicMock()
        service.videos.return_value.insert.return_value = insert
        return service

    def test_upload_is_private_by_default_and_tagged_as_short(self):
        service = self.fake_service()
        with patch.object(delivery, "_google_credentials", return_value=object()), \
                patch("googleapiclient.discovery.build", return_value=service):
            result = delivery.upload_youtube_short(self.video, "Niemand vertelt je dit", "#fyp")
        self.assertEqual(result["url"], "https://youtube.com/shorts/abc123")
        body = service.videos.return_value.insert.call_args.kwargs["body"]
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertEqual(body["snippet"]["title"], "Niemand vertelt je dit #Shorts")
        self.assertEqual(body["snippet"]["description"], "#fyp")

    def test_invalid_privacy_and_missing_file(self):
        with self.assertRaises(delivery.DeliveryError):
            delivery.upload_youtube_short(self.video, "x", privacy="iedereen")
        with self.assertRaises(delivery.DeliveryError):
            delivery.upload_youtube_short(Path(self.tmp.name) / "weg.mp4", "x")


class UploadEndpointTests(unittest.TestCase):
    def test_only_available_in_local_app(self):
        client = clipapp.app.test_client()
        with patch.dict(os.environ, {"CLIPAPP_LOCAL_MODE": ""}):
            r = client.post("/api/upload-youtube", json={"job": "abcdefabcdef", "name": "clip_01.mp4"})
        self.assertEqual(r.status_code, 403)

    def test_uploads_exported_clip_with_its_post_text(self):
        client = clipapp.app.test_client()
        d = clipapp.WORK / "fedcbafedcba"
        d.mkdir(exist_ok=True)
        (d / "clip_01.mp4").write_bytes(b"x")
        (d / "clip_01.txt").write_text("Kijk dit\n\n#fyp", encoding="utf-8")
        try:
            with patch.dict(os.environ, {"CLIPAPP_LOCAL_MODE": "1"}), \
                    patch.object(clipapp, "upload_youtube_short",
                                 return_value={"id": "1", "url": "u", "privacy": "private"}) as up:
                r = client.post("/api/upload-youtube", json={
                    "job": d.name, "name": "clip_01.mp4", "title": "Hook"})
            self.assertEqual(r.status_code, 200, r.json)
            self.assertEqual(up.call_args.args[1:], ("Hook", "Kijk dit\n\n#fyp", "private"))
            with patch.dict(os.environ, {"CLIPAPP_LOCAL_MODE": "1"}):
                r = client.post("/api/upload-youtube", json={
                    "job": d.name, "name": "clip_01.mp4", "privacy": "iedereen"})
            self.assertEqual(r.status_code, 400)
        finally:
            for f in d.iterdir():
                f.unlink()
            d.rmdir()


if __name__ == "__main__":
    unittest.main()
