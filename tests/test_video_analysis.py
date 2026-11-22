import json
import unittest
from unittest.mock import patch

import app as clipapp
from video_analysis import analyze_video_info


class VideoAnalysisTests(unittest.TestCase):
    def test_counts_comment_timestamps_and_aligns_heatmap_to_video_bins(self):
        result = analyze_video_info({
            "duration": 60,
            "comments": [
                {"text": "Great at 00:30 and again 0:30"},
                {"text": "Watch 1:02"},
                {"text": "This timestamp 2:00 is beyond the video"},
            ],
            "heatmap": [
                {"start_time": 0, "end_time": 30, "value": 0.2},
                {"start_time": 30, "end_time": 60, "value": 0.8},
            ],
        })

        self.assertEqual(result["comment_count"], 3)
        self.assertEqual(result["timestamp_mentions"], 2)
        self.assertEqual(
            [item["comment_mentions"] for item in result["bins"]],
            [0, 2],
        )
        self.assertEqual(
            [item["viewer_score"] for item in result["bins"]],
            [0.2, 0.8],
        )

    def test_accepts_hour_timestamps_and_ignores_invalid_comment_data(self):
        result = analyze_video_info({
            "duration": 4000,
            "comments": [
                {"text": "At 1:02:03 the scene changes"},
                {"text": "Malformed 1:90:10 should not count"},
                None,
            ],
            "heatmap": [],
        })

        self.assertEqual(result["timestamp_mentions"], 1)
        self.assertEqual(result["bins"][124]["comment_mentions"], 1)
        self.assertTrue(all(item["viewer_score"] is None for item in result["bins"]))

    def test_analysis_route_fetches_youtube_comments_and_rejects_other_hosts(self):
        client = clipapp.app.test_client()
        output = json.dumps({
            "duration": 60,
            "comments": [{"text": "Look at 0:30"}],
            "heatmap": [],
        })

        with patch.object(clipapp, "ytdlp", return_value=output) as fetch:
            response = client.post(
                "/api/analyze-comments",
                json={"url": "https://www.youtube.com/watch?v=example"},
            )
            rejected = client.post(
                "/api/analyze-comments",
                json={"url": "https://example.com/video"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["timestamp_mentions"], 1)
        self.assertEqual(rejected.status_code, 400)
        fetch.assert_called_once_with(
            "--dump-single-json",
            "--write-comments",
            "--extractor-args", "youtube:max_comments=1000",
            "https://www.youtube.com/watch?v=example",
        )


if __name__ == "__main__":
    unittest.main()
