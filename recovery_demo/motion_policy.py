"""Temporal candidate rules; pure Python so behavior can be tested without OpenCV."""
import math


class MotionPolicy:
    def __init__(self, threshold, burst_threshold, persistence=0.2, cooldown=2.0,
                 minimum_support=6, minimum_fraction=0.08):
        self.threshold = threshold
        self.burst_threshold = burst_threshold
        self.persistence = persistence
        self.cooldown = cooldown
        self.minimum_support = minimum_support
        self.minimum_fraction = minimum_fraction
        self.onset = None
        self.last_alarm = -math.inf
        self.in_episode = False

    def observe(self, row):
        t = float(row["timestamp_sec"])
        if row["status"] != "observed":
            self.onset = None
            self.in_episode = False
            return None
        speed = float(row["relative_downward_speed_px_sec"])
        if speed <= self.threshold:
            self.onset = None
            self.in_episode = False
            return None
        if self.onset is None:
            self.onset = t
        burst = (speed >= self.burst_threshold
                 and row.get("downward_support_points", 0) >= self.minimum_support
                 and row.get("downward_support_fraction", 0) >= self.minimum_fraction)
        sustained = t - self.onset >= self.persistence
        if not self.in_episode and t-self.last_alarm >= self.cooldown and (burst or sustained):
            self.in_episode = True
            self.last_alarm = t
            return {"rule": "brief_supported_burst" if burst else "sustained_motion",
                    "candidate_onset_sec": row.get("interval_start_sec", t) if burst else self.onset}
        return None
