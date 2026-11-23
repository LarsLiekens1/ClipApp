import unittest

import app as clipapp


class Json3Tests(unittest.TestCase):
    def test_auto_captions_have_a_time_per_word(self):
        data = {"events": [
            {"tStartMs": 1000, "dDurationMs": 2000, "segs": [
                {"utf8": "hallo"}, {"utf8": " allemaal", "tOffsetMs": 600}, {"utf8": " vandaag", "tOffsetMs": 1200}]},
            {"tStartMs": 2900, "dDurationMs": 10, "aAppend": 1, "segs": [{"utf8": "\n"}]},
            {"tStartMs": 3200, "dDurationMs": 800, "segs": [{"utf8": "joepie"}]},
        ]}
        words = clipapp.parse_json3_words(data)
        self.assertEqual([w[2] for w in words], [" hallo", " allemaal", " vandaag", " joepie"])
        self.assertEqual([w[0] for w in words], [1.0, 1.6, 2.2, 3.2])
        self.assertEqual(words[0][1], 1.6)
        self.assertEqual(words[2][1], 3.0)

    def test_manual_subtitles_are_spread_over_the_line(self):
        data = {"events": [{"tStartMs": 0, "dDurationMs": 2000, "segs": [{"utf8": "Dit is een test."}]}]}
        words = clipapp.parse_json3_words(data)
        self.assertEqual([w[0] for w in words], [0.0, 0.5, 1.0, 1.5])
        self.assertEqual(words[-1], [1.5, 2.0, " test."])

    def test_empty_or_broken_data(self):
        self.assertEqual(clipapp.parse_json3_words({}), [])
        self.assertEqual(clipapp.parse_json3_words({"events": [{"segs": [{"utf8": " "}]}]}), [])

    def test_unknown_language_skips_youtube_subtitles(self):
        self.assertIsNone(clipapp.youtube_words(clipapp.WORK, "https://youtu.be/x", None))


if __name__ == "__main__":
    unittest.main()
