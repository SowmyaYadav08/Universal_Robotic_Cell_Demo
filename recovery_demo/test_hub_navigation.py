import json
from pathlib import Path
import unittest


class HubNavigationTests(unittest.TestCase):
    def test_reports_stay_with_selected_module_and_missing_demos_are_explicit(self):
        base = Path(__file__).resolve().parents[1]/"assembly_modules"
        modules = json.loads((base/"module_navigation.json").read_text(encoding="utf-8-sig"))
        self.assertEqual({m["id"] for m in modules},{"light_localizer","prefilter","tube_interface"})
        for module in modules:
            self.assertTrue(module["dashboard"].startswith(module["id"]+"/"))
            if module["id"] != "light_localizer":
                self.assertTrue(all(r["path"].startswith(module["id"]+"/") for r in module["reports"] if r["path"]))
                self.assertTrue(any(r["path"] is None and "not implemented" in r["name"] for r in module["reports"]))
