import unittest
from review_report import render_review, render_replay
from replay_video_alert import build_replay


class ReviewReportTests(unittest.TestCase):
    def test_empty_result_is_not_presented_as_success(self):
        page = render_review({"events": [], "total_samples": 10})
        self.assertIn("No alerts does not prove", page)
        self.assertIn("What should I do?", page)
        self.assertIn('../video_alert_replay/replay.html', page)

    def test_alert_has_plain_language_and_escaped_filenames(self):
        page = render_review({"events": [{"timestamp_sec":11.5, "evidence_image":"x\".jpg"}],
                              "normal_calibration_candidate_count":0})
        self.assertIn("11.50 seconds", page)
        self.assertIn("x&quot;.jpg", page)
        self.assertIn("It has not confirmed which object moved", page)

    def test_replay_summary_distinguishes_video_and_simulation(self):
        result = build_replay({"timestamp_sec":11.5})
        page = render_replay(result)
        self.assertIn("Replacement completed in simulation", page)
        self.assertIn("2/2", page)
        self.assertIn("11.50", page)
        self.assertIn('href="recovery_playback.html"', page)
        self.assertNotIn('__OUTCOME__', page)
        blocked = render_replay(build_replay({"timestamp_sec":11.5}, "blocked"))
        self.assertIn("Task held", blocked)
        self.assertNotIn('href="recovery_playback.html"', blocked)
