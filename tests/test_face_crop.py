import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as clipapp
import face_crop
from tests.test_local_video import HAS_FFMPEG, make_video


class CropMathTests(unittest.TestCase):
    def test_smoothing_fills_gaps_and_ignores_small_moves(self):
        self.assertEqual(face_crop.smooth_centers([None, 0.5, 0.52, None, 0.8]),
                         [0.5, 0.5, 0.5, 0.5, 0.8])
        self.assertEqual(face_crop.smooth_centers([None, None]), [])

    def test_expression_switches_position_per_window(self):
        # 1280x720 -> geschaald 3414x1920; midden 0.5 -> x = 1707 - 540 = 1167
        expr = face_crop.crop_x_expression([0.5, 0.5, 0.9], 1280, 720)
        self.assertEqual(expr, "if(lt(t\\,4)\\,1167\\,2334)")
        self.assertEqual(face_crop.crop_x_expression([0.0], 1280, 720), "0")

    def test_portrait_video_needs_no_crop(self):
        self.assertIsNone(face_crop.face_crop_filter("x.mp4", 10, 1080, 1920))

    def test_no_faces_means_no_crop(self):
        with patch.object(face_crop, "face_centers", return_value=([None, None], 0.0)):
            self.assertIsNone(face_crop.face_crop_filter("x.mp4", 4, 1280, 720))


@unittest.skipUnless(HAS_FFMPEG, "FFmpeg is nodig voor deze test")
class FaceCropRenderTests(unittest.TestCase):
    def setUp(self):
        self.client = clipapp.app.test_client()
        tmp = Path(tempfile.mkdtemp())
        make_video(tmp / "v.mp4", seconds=6, size="1280x720")
        r = self.client.post("/api/upload-video", data={
            "file": (io.BytesIO((tmp / "v.mp4").read_bytes()), "v.mp4")},
            content_type="multipart/form-data")
        shutil.rmtree(tmp)
        self.d = clipapp.WORK / r.json["job"]

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def render(self):
        return self.client.post("/api/render", json={
            "job": self.d.name, "segments": [{"start": 0, "end": 5}],
            "vertical": True, "face_crop": True, "blur": True,
            "caption_position": "above"})

    def test_moving_crop_is_accepted_by_ffmpeg(self):
        with patch.object(face_crop, "face_centers", return_value=([0.2, 0.8, 0.8], 1.0)):
            r = self.render()
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(clipapp.video_size(self.d / "clip_01.mp4"), (1080, 1920))

    def test_test_pattern_without_faces_falls_back_to_blur(self):
        r = self.render()                      # echte detectie: testbeeld heeft geen gezicht
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(clipapp.video_size(self.d / "clip_01.mp4"), (1080, 1920))


if __name__ == "__main__":
    unittest.main()
