import unittest
from recovery import run_scenario
from simulator import Scenario
from timing import summarize_timing


class TimingTests(unittest.TestCase):
    def test_recovery_timing_excludes_prefault_work(self):
        timing = summarize_timing(run_scenario(Scenario("drop", defect="component_drop")))
        self.assertEqual(timing["pause_sec"], 2)
        self.assertEqual(timing["drop_to_recovery_sec"], 9.5)
        self.assertEqual(timing["after_pause_to_recovery_sec"], 7.5)
        self.assertEqual(timing["elapsed_process_sec"], 15.5)
        self.assertIsNone(timing["check_duration_sec"])

    def test_open_hold_is_not_counted_as_completed_recovery(self):
        timing = summarize_timing(run_scenario(Scenario("blocked", defect="component_drop", workspace_clear=False)))
        self.assertIsNone(timing["drop_to_recovery_sec"])
        self.assertEqual(timing["until_manual_hold_sec"], 2)
