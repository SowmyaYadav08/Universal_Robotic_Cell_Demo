"""Acceptance checks for recovery decisions, independent of camera detection."""
import unittest
from dataclasses import replace
from recovery import run_scenario
from simulator import Scenario, scenarios
from report import render_report, render_playback


class RecoveryTests(unittest.TestCase):
    def test_normal_and_drop_recovery(self):
        normal = run_scenario(Scenario("normal"))
        self.assertEqual((normal["outcome"], normal["retries"], normal["confirmed_placements"]), ("completed", 0, 2))
        result = run_scenario(Scenario("drop", defect="component_drop"))
        self.assertEqual((result["outcome"], result["retries"], result["confirmed_placements"]), ("recovered", 1, 2))
        kinds = [e["event"] for e in result["events"]]
        self.assertLess(kinds.index("pause_finished"), kinds.index("retry_started"))
        self.assertLess(kinds.index("check_passed"), kinds.index("retry_started"))
        actions = ["return_to_supply", "replacement_picked", "replacement_transported",
                   "replacement_released", "gripper_withdrawn"]
        positions = [kinds.index(action) for action in actions]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(positions[-1], kinds.index("recovery_completed"))

    def test_each_required_signal_blocks_retry_when_unknown_or_false(self):
        base = Scenario("drop", defect="component_drop")
        for field in ("first_plate_correct", "gripper_empty", "workspace_clear", "correct_tool", "fixture_present"):
            for value in (False, None):
                with self.subTest(field=field, value=value):
                    result = run_scenario(replace(base, **{field: value}))
                    self.assertEqual(result["outcome"], "intervention_required")
                    self.assertEqual(result["retries"], 0)

    def test_suite_expectations_and_retry_bound(self):
        for scenario in scenarios():
            expected = "completed_with_warning" if scenario.advisory else "completed" if scenario.name == "normal" else "recovered" if scenario.name == "drop_recovered" else "intervention_required"
            with self.subTest(scenario=scenario.name):
                result = run_scenario(scenario)
                self.assertEqual(result["outcome"], expected)
                self.assertLessEqual(result["retries"], 1)
        failed = run_scenario(Scenario("drop", defect="component_drop", retry_succeeds=False), max_retries=2)
        self.assertEqual((failed["retries"], failed["outcome"]), (2, "intervention_required"))

    def test_disabled_retry_and_invalid_configuration(self):
        scenario = Scenario("drop", defect="component_drop")
        result = run_scenario(scenario, max_retries=0)
        self.assertEqual((result["outcome"], result["retries"]), ("intervention_required", 0))
        with self.assertRaises(ValueError):
            run_scenario(scenario, max_retries=-1)
        with self.assertRaises(ValueError):
            run_scenario(scenario, pause_seconds=-1)

    def test_dashboard_shows_only_interventions_and_playback_includes_recovery(self):
        results = [run_scenario(s) for s in scenarios()]
        dashboard = render_report(results)
        self.assertNotIn('drop recovered</td>', dashboard)
        self.assertNotIn('>normal</td>', dashboard)
        self.assertIn('workspace obstructed', dashboard)
        self.assertIn('events.csv', dashboard)
        self.assertIn('Manual intervention cases by defect', dashboard)
        self.assertIn('Manual intervention cases by scenario', dashboard)
        self.assertIn('value="module">Assembly module', dashboard)
        self.assertIn('<svg', dashboard)
        self.assertIn('Light Localizer', dashboard)
        playback = render_playback(results)
        self.assertIn('return_to_supply', playback)
        self.assertIn('replacement_picked', playback)
        self.assertIn('Plate 2 (upper)', playback)
        self.assertIn('Plate 1 (lower)', playback)
        self.assertIn('Robot gripper', playback)
        self.assertIn('normal_scene_16s.jpg', playback)
        self.assertIn('x="475" y="180"', playback)
        self.assertIn('x="475" y="166"', playback)

    def test_module_chart_uses_result_modules(self):
        result = run_scenario(Scenario("blocked", defect="component_drop", workspace_clear=False,
                                       module="Test Module"))
        dashboard = render_report([result])
        self.assertIn('Test Module', dashboard)
        self.assertIn('1 scenarios require operator attention', dashboard)
        self.assertEqual(result["events"][0]["module"], "Test Module")

    def test_filter_controls_and_embedded_data(self):
        results = [run_scenario(s) for s in scenarios()]
        dashboard = render_report(results)
        self.assertIn('id="module"', dashboard)
        self.assertIn('id="priority"', dashboard)
        self.assertIn('id="scenario"', dashboard)
        self.assertIn('Dropped plate blocks the work area', dashboard)
        self.assertIn('Wrong tool attached', dashboard)
        self.assertIn('Plate placed in the wrong position', dashboard)
        self.assertIn('value="high" selected', dashboard)
        self.assertIn('Medium - investigate', dashboard)
        self.assertIn('Low - routine attention', dashboard)
        self.assertIn('id="status"', dashboard)
        self.assertIn('"scenario": "drop recovered"', dashboard)
        self.assertNotIn('__DATA__', dashboard)
        unusual = run_scenario(Scenario('blocked', defect='component_drop', workspace_clear=False,
                                        module='</script><script>alert(1)</script>'))
        self.assertNotIn('</script><script>alert(1)</script>', render_report([unusual]))

    def test_priority_levels_do_not_downgrade_blocked_recovery(self):
        results = [run_scenario(s) for s in scenarios()]
        self.assertEqual({r["priority"] for r in results if r["defect"] != "none"}, {"high", "medium", "low"})
        self.assertTrue(all(r["priority"] == "high" for r in results if r["outcome"] == "intervention_required"))
        self.assertTrue(all(r["confirmed_placements"] == 2 for r in results if r["priority"] == "medium"))

    def test_priority_is_separate_from_resolution(self):
        recovered = run_scenario(Scenario("drop", defect="component_drop"))
        self.assertEqual((recovered["priority"], recovered["status"]), ("high", "resolved"))
        low = run_scenario(Scenario("stock", advisory="rack_stock_low"))
        self.assertEqual((low["priority"], low["status"]), ("low", "open"))


if __name__ == "__main__":
    unittest.main()
