import unittest
from replay_video_alert import build_replay


class VideoReplayTests(unittest.TestCase):
    def test_preserves_real_trigger_and_marks_simulated_actions(self):
        candidate = {"timestamp_sec":11.5, "confirmed_drop":False, "video":"failure_video.mp4"}
        result = build_replay(candidate)
        self.assertEqual(result["outcome"], "recovered")
        self.assertFalse(result["trigger_confirmed_as_drop"])
        self.assertFalse(result["physical_robot_commands_sent"])
        self.assertEqual(result["trigger"], candidate)
        self.assertTrue(all(e["video_alert_time_sec"] == 11.5 for e in result["events"]))

    def test_blocked_and_unknown_checks_never_pick_replacement(self):
        for checks in ("blocked", "unknown"):
            result = build_replay({"timestamp_sec":11.5}, checks)
            self.assertEqual(result["outcome"], "intervention_required")
            self.assertNotIn("replacement_picked", [e["event"] for e in result["events"]])
