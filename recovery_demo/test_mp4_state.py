import unittest
from export_recovery_mp4 import target_after


class PlaybackStateTests(unittest.TestCase):
    def test_replacement_preserves_lower_layer_and_releases_upper_layer(self):
        state = {"x":350,"y":110,"p1":True,"p2":False,"carry":True,"dropped":False}
        dropped = target_after(state,{"event":"defect_detected"})
        self.assertTrue(dropped["p1"])
        self.assertTrue(dropped["dropped"])
        self.assertFalse(dropped["p2"])
        self.assertFalse(dropped["carry"])
        picked = target_after(dropped,{"event":"replacement_picked"})
        self.assertTrue(picked["carry"])
        released = target_after(picked,{"event":"replacement_released"})
        self.assertTrue(released["p1"] and released["p2"])
        self.assertFalse(released["carry"])
        self.assertTrue(released["dropped"])
