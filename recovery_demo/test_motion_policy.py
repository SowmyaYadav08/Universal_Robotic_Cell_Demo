import unittest
from motion_policy import MotionPolicy


def sample(t, speed, support=12, fraction=0.2, status="observed"):
    return {"timestamp_sec": t, "interval_start_sec": t-0.1,
            "relative_downward_speed_px_sec": speed, "status": status,
            "downward_support_points": support, "downward_support_fraction": fraction}


class MotionPolicyTests(unittest.TestCase):
    def test_brief_supported_motion_is_not_discarded(self):
        policy = MotionPolicy(80, 160)
        self.assertEqual(policy.observe(sample(1, 188))["rule"], "brief_supported_burst")
        self.assertIsNone(policy.observe(sample(1.1, 30)))

    def test_unsupported_spike_does_not_trigger(self):
        self.assertIsNone(MotionPolicy(80,160).observe(sample(1,188,support=2)))
        self.assertIsNone(MotionPolicy(80,160).observe(sample(1,188,fraction=0.01)))

    def test_sustained_motion_and_episode_deduplication(self):
        policy = MotionPolicy(80,160)
        self.assertIsNone(policy.observe(sample(0,100)))
        self.assertEqual(policy.observe(sample(0.3,100))["rule"], "sustained_motion")
        self.assertIsNone(policy.observe(sample(3,100)))
        policy.observe(sample(3.1,0))
        self.assertIsNotNone(policy.observe(sample(4,180)))

    def test_uncertainty_resets_persistence(self):
        policy = MotionPolicy(80,160)
        policy.observe(sample(0,100))
        policy.observe(sample(0.1,100,status="tracking_uncertain"))
        self.assertIsNone(policy.observe(sample(0.3,100)))
