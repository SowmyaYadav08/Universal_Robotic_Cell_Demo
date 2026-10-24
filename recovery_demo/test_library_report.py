import unittest
from library_report import render_library


class LibraryCaptionTests(unittest.TestCase):
    def test_captions_include_context_time_and_uncertainty(self):
        record = {"module":"Prefilter", "operation":"Bearing pickup", "filename_label":"Failure-labeled",
                  "video":"prefilter_bad_bearingpick.mp4", "duration_sec":20, "sheet":"sheet.jpg",
                  "frames":[{"image":"frame.jpg", "requested_time_sec":2.5}]}
        page = render_library({"records":[record]})
        self.assertIn("2.50s",page)
        self.assertIn("What the sequence shows",page)
        self.assertIn("What to look for",page)
        self.assertIn("label from filename",page)
        self.assertIn("not verified fault labels",page)
