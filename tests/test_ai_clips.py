import json
import unittest
from types import SimpleNamespace

from ai_clips import AIClipError, build_transcript, clean_clips, suggest_clips


class FakeClient:
    """Neppe Anthropic-client: geeft een vast antwoord terug en onthoudt het verzoek."""

    def __init__(self, payload, stop_reason="end_turn"):
        self.request = None
        text = payload if isinstance(payload, str) else json.dumps(payload)
        response = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="text", text=text)],
        )

        def create(**kwargs):
            self.request = kwargs
            return response

        self.beta = SimpleNamespace(messages=SimpleNamespace(create=create))


def clip(start, end, score=50, **extra):
    return {"start": start, "end": end, "caption": "Hook", "description": "Kijk dit",
            "hashtags": ["#grappig", "fyp"], "reason": "Sterk moment", "score": score, **extra}


CUES = [[0.0, 1.5, "Hallo allemaal."], [1.6, 3.0, "Vandaag iets geks"], [3.1, 4.0, "gebeurd!"]]


class BuildTranscriptTests(unittest.TestCase):
    def test_merges_cues_into_sentences_with_times(self):
        self.assertEqual(
            build_transcript(CUES),
            "[0.0-1.5] Hallo allemaal.\n[1.6-4.0] Vandaag iets geks gebeurd!",
        )


class CleanClipsTests(unittest.TestCase):
    def test_drops_overlaps_keeps_best_and_sorts_by_start(self):
        result = clean_clips([clip(100, 130, 40), clip(110, 140, 90), clip(10, 40, 60)],
                             duration=300, count=5, min_len=20, max_len=60)
        self.assertEqual([(c["start"], c["score"]) for c in result], [(10, 60), (110, 90)])

    def test_clamps_to_video_and_max_length_and_normalises_hashtags(self):
        result = clean_clips([clip(250, 400)], duration=300, count=5, min_len=20, max_len=30)
        self.assertEqual((result[0]["start"], result[0]["end"]), (250, 280))
        self.assertEqual(result[0]["hashtags"], ["#grappig", "#fyp"])

    def test_skips_too_short_and_invalid_clips(self):
        result = clean_clips([clip(0, 3), {"start": "x", "end": 9}, "nope"],
                             duration=300, count=5, min_len=20, max_len=60)
        self.assertEqual(result, [])

    def test_respects_requested_count(self):
        clips = [clip(i * 50, i * 50 + 30, score=i) for i in range(5)]
        result = clean_clips(clips, duration=300, count=2, min_len=20, max_len=60)
        self.assertEqual([c["score"] for c in result], [3, 4])


class SuggestClipsTests(unittest.TestCase):
    def test_sends_transcript_and_signals_and_returns_clean_clips(self):
        client = FakeClient({"clips": [clip(0.0, 30.0, 80)]})
        bins = [{"start": 0, "end": 30, "comment_mentions": 4, "viewer_score": 0.9}]
        result = suggest_clips(CUES, 60, count=3, min_len=20, max_len=40, bins=bins, client=client)
        self.assertEqual(len(result), 1)
        prompt = client.request["messages"][0]["content"]
        self.assertIn("Hallo allemaal.", prompt)
        self.assertIn("4 comment-timestamps", prompt)
        self.assertEqual(client.request["output_config"]["format"]["type"], "json_schema")

    def test_errors_without_speech(self):
        with self.assertRaises(AIClipError):
            suggest_clips([], 60, client=FakeClient({"clips": []}))

    def test_errors_on_refusal_and_bad_json(self):
        with self.assertRaises(AIClipError):
            suggest_clips(CUES, 60, client=FakeClient({"clips": []}, stop_reason="refusal"))
        with self.assertRaises(AIClipError):
            suggest_clips(CUES, 60, client=FakeClient("geen json"))


if __name__ == "__main__":
    unittest.main()
