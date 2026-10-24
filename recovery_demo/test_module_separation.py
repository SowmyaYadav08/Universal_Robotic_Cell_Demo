import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from assembly_modules.prefilter.scenarios import scenarios as prefilter_cases
from assembly_modules.tube_interface.scenarios import scenarios as tube_cases
from assembly_modules.shared.engine import run_module_case
from assembly_modules.shared.report import render_report as module_report
from simulator import scenarios as light_cases


class ModuleSeparationTests(unittest.TestCase):
    def test_module_datasets_remain_separate(self):
        self.assertEqual(len(light_cases()),20)
        self.assertEqual({case.module for case in light_cases()},{"Light Localizer"})
        for name,factory in (("Prefilter",prefilter_cases),("Tube Interface",tube_cases)):
            cases = factory()
            self.assertEqual(len(cases),5)
            self.assertEqual({case.module for case in cases},{name})
            results = [run_module_case(case) for case in cases]
            self.assertTrue(all(event["module"] == name for result in results for event in result["events"]))
            page = module_report(results)
            self.assertNotIn('href="recovery_playback.html"',page)
            self.assertIn('video_library/library.html',page)
