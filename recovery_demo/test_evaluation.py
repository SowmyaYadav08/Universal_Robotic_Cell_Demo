import unittest
from evaluate_real_review import evaluate


class EvaluationTests(unittest.TestCase):
    def test_hits_misses_false_alarms_and_unreviewed(self):
        events = [{"video": "failure_video.mp4", "timestamp_sec": t} for t in (2.1, 2.2, 5, 9)]
        intervals = [{"video": "failure_video.mp4", "start_sec": a, "end_sec": b,
                      "label": label, "verified": "yes"}
                     for a,b,label in ((2,3,"drop"), (4,6,"no_drop"), (6,7,"drop"))]
        result = evaluate(events, intervals)
        self.assertEqual(result["drop_intervals_found"], 1)
        self.assertEqual(result["drop_intervals_missed"], 1)
        self.assertEqual(result["candidates_in_no_drop_intervals"], 1)
        self.assertEqual(result["duplicate_candidates_in_drop_intervals"], 1)
        self.assertEqual(result["candidates_outside_reviewed_intervals"], 1)

    def test_missing_or_unverified_annotations_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([], [])
        with self.assertRaises(ValueError):
            evaluate([], [{"video":"x", "start_sec":0, "end_sec":1, "label":"drop", "verified":"no"}])
