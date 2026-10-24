import unittest
from module_scenarios import module_cases, run_module_case
from report import render_report


class ModuleScenarioTests(unittest.TestCase):
    def test_module_stages_and_holds_are_distinct_from_plate_recovery(self):
        cases = [run_module_case(c) for c in module_cases()]
        self.assertEqual(len(cases),10)
        for result in cases:
            self.assertEqual(result["confirmed_placements"],0)
            self.assertFalse(any(e["event"] == "replacement_picked" for e in result["events"]))
            if result["priority"] == "high":
                self.assertEqual(result["outcome"],"intervention_required")
                self.assertEqual(result["confirmed_operations"],0)
            else:
                self.assertEqual(result["confirmed_operations"],1)
        page = render_report(cases)
        self.assertIn("Prefilter",page)
        self.assertIn("Tube Interface",page)
        self.assertIn("Bearing press incomplete",page)
        self.assertIn("Screwing not completed",page)
