import json
import unittest
from unittest.mock import patch

import app as clipapp
from auto_clips import suggest_clips
from video_analysis import add_chat_counts, analyze_video_info, chat_offsets


def chat_line(ms, n=1):
    return json.dumps({"replayChatItemAction": {
        "videoOffsetTimeMsec": str(ms),
        "actions": [{"addChatItemAction": {}} for _ in range(n)]}})


class ChatParsingTests(unittest.TestCase):
    def test_reads_offsets_and_ignores_noise(self):
        lines = [chat_line(1500), chat_line(61000, 2), "", "geen json",
                 json.dumps({"replayChatItemAction": {"videoOffsetTimeMsec": "-5", "actions": [
                     {"addChatItemAction": {}}]}}),
                 json.dumps({"other": 1})]
        self.assertEqual(chat_offsets(lines), [1.5, 61.0, 61.0])

    def test_counts_per_bin(self):
        result = analyze_video_info({"duration": 90, "comments": []})
        add_chat_counts(result, [1, 2, 45, 89, 500])
        self.assertEqual([b["chat_messages"] for b in result["bins"]], [2, 1, 1])
        self.assertEqual(result["chat_messages"], 4)


class ChatScoringTests(unittest.TestCase):
    def test_busy_chat_moment_is_chosen(self):
        bins = [{"start": s, "end": s + 30, "comment_mentions": 0, "viewer_score": None,
                 "chat_messages": 300 if s == 60 else 5} for s in range(0, 120, 30)]
        clips = suggest_clips([], 120, count=1, min_len=20, max_len=30, bins=bins)
        self.assertTrue(clips[0]["start"] >= 55 and clips[0]["end"] <= 95, clips[0])
        self.assertIn("live-chat", clips[0]["reason"])


class ChatEndpointTests(unittest.TestCase):
    def test_chat_is_added_for_finished_streams_only(self):
        client = clipapp.app.test_client()
        info = {"duration": 60, "comments": [], "live_status": "was_live"}
        with patch.object(clipapp, "ytdlp", return_value=json.dumps(info)), \
                patch.object(clipapp, "fetch_chat_offsets", return_value=[5, 6, 50]) as fetch:
            r = client.post("/api/analyze-comments", json={
                "url": "https://www.youtube.com/watch?v=x", "live_chat": True})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json["chat_messages"], 3)
            self.assertTrue(r.json["was_live"])
            info["live_status"] = "not_live"
            with patch.object(clipapp, "ytdlp", return_value=json.dumps(info)):
                r = client.post("/api/analyze-comments", json={
                    "url": "https://www.youtube.com/watch?v=x", "live_chat": True})
            self.assertFalse(r.json["was_live"])
            self.assertNotIn("chat_messages", r.json)
            self.assertEqual(fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
