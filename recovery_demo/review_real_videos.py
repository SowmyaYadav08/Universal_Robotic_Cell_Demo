"""Offline motion-candidate reviewer for the two explicitly approved videos only."""
import argparse
import csv
import html
import json
import math
import time
from pathlib import Path

import cv2
import numpy as np
from motion_policy import MotionPolicy

ROOT = Path(__file__).resolve().parents[1]
APPROVED = { (ROOT / "Data/normal/normal_video.mp4").resolve(),
             (ROOT / "Data/failure/failure_video.mp4").resolve() }
TRACE_FIELDS = ["timestamp_sec", "interval_start_sec", "relative_downward_speed_px_sec",
                "valid_points", "downward_support_points", "downward_support_fraction", "status"]


def scan(video, config):
    """Yield motion evidence; does not infer identity, stage, or safe restart."""
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open approved video: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or fps <= 0:
        cap.release()
        raise ValueError("Video has no usable FPS")
    stride = max(1, round(fps / config["sample_fps"]))
    x1, y1, x2, y2 = config["transport_roi_xyxy"]
    previous = None
    previous_t = None
    index = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_index = index
            index += 1
            if frame_index % stride:
                continue
            height, width = frame.shape[:2]
            if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                raise ValueError("Transport ROI outside frame; configure for this camera")
            t = frame_index / fps
            gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
            score, count, status = None, 0, "initializing"
            support = 0
            support_fraction = 0.0
            if previous is not None:
                points = cv2.goodFeaturesToTrack(previous, maxCorners=160, qualityLevel=0.01, minDistance=5)
                status = "tracking_uncertain"
                if points is not None:
                    forward, good, _ = cv2.calcOpticalFlowPyrLK(previous, gray, points, None)
                    if forward is not None:
                        backward, back_good, _ = cv2.calcOpticalFlowPyrLK(gray, previous, forward, None)
                        if backward is not None:
                            old = points.reshape(-1, 2)
                            new = forward.reshape(-1, 2)
                            valid = ((good.ravel() == 1) & (back_good.ravel() == 1)
                                     & (np.linalg.norm(backward.reshape(-1, 2) - old, axis=1) < 1.5)
                                     & np.isfinite(new).all(axis=1))
                            count = int(valid.sum())
                            if count >= 12:
                                displacement = new[valid] - old[valid]
                                reference_dy = np.median(displacement[:, 1])
                                # Ignore points already at the mounting zone when looking
                                # for downward separation; this is a geometric heuristic.
                                above_mount = (old[valid, 1] + y1 < config["mounting_top_y"])
                                if int(above_mount.sum()) >= 6:
                                    residual = displacement[above_mount, 1] - reference_dy
                                    score = float(max(0, np.percentile(residual, 90)) / (t - previous_t))
                                    speeds = residual / (t - previous_t)
                                    support = int((speeds >= config.get("support_speed_px_sec", config["minimum_relative_speed_px_sec"])).sum())
                                    support_fraction = support / len(speeds)
                                    status = "observed"
            yield {"timestamp_sec": round(t, 4),
                   "interval_start_sec": round(previous_t if previous_t is not None else t, 4),
                   "relative_downward_speed_px_sec": round(score, 4) if score is not None else "",
                   "valid_points": count, "downward_support_points": support,
                   "downward_support_fraction": round(support_fraction, 4), "status": status}, frame
            previous, previous_t = gray, t
    finally:
        cap.release()
    if index == 0:
        raise RuntimeError("No decodable frames")


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("review_config.json"))
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).with_name("outputs") / "real_video_review")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    videos = [(ROOT / config[key]).resolve() for key in ("normal_video", "review_video")]
    if any(video not in APPROVED for video in videos):
        raise ValueError("Only the two explicitly approved workspace videos may be opened")
    if config["sample_fps"] <= 0 or config["persistence_sec"] <= 0 or config["cooldown_sec"] < 0:
        raise ValueError("Invalid timing configuration")
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    baseline = [row for row, _ in scan(videos[0], config)]
    scores = [row["relative_downward_speed_px_sec"] for row in baseline if row["status"] == "observed"]
    if len(scores) < 20:
        raise RuntimeError("Insufficient reliable normal observations to calibrate; no result claimed")
    threshold = max(config["minimum_relative_speed_px_sec"],
                    float(np.percentile(scores, config["baseline_percentile"])) * config["baseline_margin"])
    write_csv(output / "normal_motion.csv", baseline, TRACE_FIELDS)
    burst_threshold = max(threshold * config.get("burst_threshold_factor", 2.0),
                          max(scores) * config.get("normal_peak_margin", 1.5))
    def make_policy():
        return MotionPolicy(threshold, burst_threshold, config["persistence_sec"], config["cooldown_sec"],
                            config.get("minimum_burst_support_points", 6),
                            config.get("minimum_burst_support_fraction", 0.08))
    normal_policy = make_policy()
    normal_candidates = sum(normal_policy.observe(row) is not None for row in baseline)
    review_config = dict(config, support_speed_px_sec=burst_threshold)
    policy = make_policy()
    events, trace = [], []
    previous_frame = None
    awaiting_after = []
    for row, frame in scan(videos[1], review_config):
        for pending in awaiting_after:
            if not cv2.imwrite(str(output / pending["after_image"]), frame):
                raise RuntimeError("Could not write after frame")
        awaiting_after.clear()
        trace.append(row)
        t = row["timestamp_sec"]
        decision = policy.observe(row)
        if decision:
            image = f"candidate_{len(events)+1:03d}.jpg"
            if not cv2.imwrite(str(output / image), frame):
                raise RuntimeError("Could not write candidate evidence frame")
            events.append({"module": config["module"], "video": videos[1].name,
                           "timestamp_sec": t, "candidate_onset_sec": decision["candidate_onset_sec"],
                           "rule": decision["rule"],
                           "event": "unusual_downward_relative_motion", "priority": "review_required",
                           "confirmed_drop": False, "recovery_authorized": False,
                           "speed_px_sec": row["relative_downward_speed_px_sec"],
                           "threshold_px_sec": round(threshold, 4),
                           "burst_threshold_px_sec": round(burst_threshold, 4),
                           "downward_support_points": row["downward_support_points"],
                           "evidence_image": image,
                           "before_image": image.replace('.jpg', '_before.jpg'),
                           "after_image": image.replace('.jpg', '_after.jpg')})
            if not cv2.imwrite(str(output / events[-1]["before_image"]), previous_frame if previous_frame is not None else frame):
                raise RuntimeError("Could not write before frame")
            awaiting_after.append(events[-1])
        previous_frame = frame.copy()
    for pending in awaiting_after:
        pending["after_image"] = ""
    write_csv(output / "failure_motion.csv", trace, TRACE_FIELDS)
    fields = ["module", "video", "timestamp_sec", "candidate_onset_sec", "rule", "event", "priority",
              "confirmed_drop", "recovery_authorized", "speed_px_sec", "threshold_px_sec",
              "burst_threshold_px_sec", "downward_support_points", "evidence_image", "before_image", "after_image"]
    write_csv(output / "review_events.csv", events, fields)
    summary = {"source": "approved_real_video", "validated": False,
               "baseline_used_for_calibration": videos[0].name,
               "review_video": videos[1].name, "candidate_count": len(events),
               "threshold_px_sec": threshold, "elapsed_processing_sec": time.perf_counter()-started,
               "burst_threshold_px_sec": burst_threshold,
               "normal_calibration_candidate_count": normal_candidates,
               "normal_comparison_note": "In-sample calibration check only, not independent false-alarm validation. Burst threshold exceeds every calibration score by construction.",
               "uncertain_samples": sum(r["status"] == "tracking_uncertain" for r in trace),
               "observed_samples": sum(r["status"] == "observed" for r in trace),
               "total_samples": len(trace), "events": events,
               "limitations": "Motion clusters are not identified gripper/plate objects. Stages, placement and workspace clearance remain unknown. No candidate does not establish normal assembly. Normal baseline is calibration, not independent validation."}
    (output / "review_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    from review_report import render_review
    (output / "review.html").write_text(render_review(summary), encoding="utf-8")
    print(f"Finished checking the recording. {len(events)} moment(s) need review.")
    for event in events:
        print(f'  Check the video at {event["timestamp_sec"]:.2f} seconds. Before/after pictures are saved.')
    print(f"Normal video used for setup: {normal_candidates} alerts. This is not an independent accuracy test.")
    print("Next: inspect the pictures, then record verified event times before evaluating accuracy.")
    print(f"Open {output / 'review.html'}")


if __name__ == "__main__":
    main()

