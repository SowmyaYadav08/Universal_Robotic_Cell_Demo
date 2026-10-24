"""Generate six local scenarios and evaluate events by cycle against separate labels."""
import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path
import cv2
from detect_plate_loss import FIELDS, detect
from generate_synthetic_video import generate

def validate(output_dir):
    generate(output_dir)
    with (output_dir / "expected_events.csv").open(newline="", encoding="utf-8") as stream:
        labels = list(csv.DictReader(stream))
    detections, checks = [], []
    evaluated = {"suspected_plate_loss", "placement_confirmed", "incomplete_placement", "tracking_uncertain"}
    for name in sorted({row["video"] for row in labels}):
        video = output_dir / name
        started = time.perf_counter()
        events = detect(video)
        elapsed = time.perf_counter() - started
        detections.extend(events)
        truth = [row for row in labels if row["video"] == name]
        observed = [row for row in events if row["event"] in evaluated]
        expected_counts = Counter((int(row["cycle"]), row["event"]) for row in truth)
        actual_counts = Counter((row["cycle"], row["event"]) for row in observed)
        delays = []
        timing_ok = True
        for row in truth:
            match = [e for e in observed if e["cycle"] == int(row["cycle"]) and e["event"] == row["event"]]
            delay = round(float(match[0]["timestamp_sec"]) - float(row["timestamp_sec"]), 3) if len(match) == 1 else None
            # Placement ground truth is release time, followed by withdrawal and verification.
            limit = 1.5 if row["event"] in {"placement_confirmed", "incomplete_placement"} else 1.0
            timing_ok = timing_ok and delay is not None and -0.1 <= delay <= limit
            delays.append({"cycle": int(row["cycle"]), "event": row["event"], "delay_sec": delay})
        starts = [e["cycle"] for e in events if e["event"] == "cycle_started"]
        confirmed = sum(row["event"] == "placement_confirmed" for row in truth)
        count_ok = bool(events) and events[-1]["confirmed_placements"] == confirmed
        passed = (expected_counts == actual_counts and starts == [1, 2, 3] and timing_ok
                  and count_ok and not any(e["event"] == "cycle_unresolved" for e in events))
        cap = cv2.VideoCapture(str(video))
        try:
            count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        finally:
            cap.release()
        checks.append({"video": name, "passed": bool(passed), "cycles": starts,
                       "confirmed_placements": events[-1]["confirmed_placements"] if events else 0,
                       "expected_placements": confirmed, "event_counts_match": expected_counts == actual_counts,
                       "event_delays": delays, "processing_sec": round(elapsed, 4),
                       "processing_fps": round(count / elapsed, 2) if elapsed else None})
    with (output_dir / "events.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(detections)
    report = {"scope": "colored synthetic three-cycle demo only",
              "passed": all(c["passed"] for c in checks), "checks": checks}
    (output_dir / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report["passed"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/synthetic_plate_demo_v2"))
    raise SystemExit(0 if validate(parser.parse_args().output_dir) else 1)
