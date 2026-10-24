"""Generate artificial three-cycle assemblies; labels are evaluation-only."""
import argparse
import csv
from pathlib import Path
import cv2
import numpy as np

SCENARIOS = {"normal": (1.0, 20, 1.0), "drop": (1.0, 20, 1.0),
             "occlusion": (1.0, 20, 1.0), "incomplete": (1.0, 20, 1.0),
             "normal_fast_dim": (0.8, 15, 0.7), "drop_slow": (1.2, 24, 1.0)}

def generate(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    labels = []
    for scenario, (scale, fps, brightness) in SCENARIOS.items():
        path = output_dir / f"{scenario}.avi"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, (640, 360))
        if not writer.isOpened():
            raise RuntimeError(f"Cannot create {path}")
        mounted = []
        try:
            for cycle in range(1, 4):
                slot = 350 + (cycle - 1) * 60
                failing = cycle == 2 and scenario.startswith("drop")
                incomplete = cycle == 2 and scenario == "incomplete"
                start = (cycle - 1) * 6.2 * scale
                if failing:
                    labels.append([path.name, cycle, "suspected_plate_loss", start + 2 * scale])
                labels.append([path.name, cycle, "incomplete_placement" if failing or incomplete
                               else "placement_confirmed", start + 4 * scale])
                if cycle == 2 and scenario == "occlusion":
                    labels.append([path.name, cycle, "tracking_uncertain", start + 1.7 * scale])
                for index in range(round(6.2 * scale * fps)):
                    u = index / fps / scale
                    x = round(80 + (slot - 80) * np.clip((u - 0.5) / 3, 0, 1))
                    gy = round(140 - 75 * np.clip((u - 4) / 0.8, 0, 1))
                    if u >= 5:
                        x = round(slot + (80 - slot) * np.clip((u - 5) / 0.8, 0, 1))
                    px, py = x, gy + 35
                    if failing and u >= 2:
                        px = round(80 + (slot - 80) * 0.5)
                        py = round(min(320, 175 + 130 * (u - 2)))
                    elif u >= 4 and not incomplete:
                        px, py = slot, 175
                    frame = np.full((360, 640, 3), 35, dtype=np.uint8)
                    for target in (350, 410, 470):
                        cv2.rectangle(frame, (target - 24, 190), (target + 24, 215), (150, 150, 150), -1)
                    for target in mounted:
                        cv2.rectangle(frame, (target - 14, 170), (target + 14, 180), (255, 80, 0), -1)
                    cv2.rectangle(frame, (x - 20, gy - 20), (x + 20, gy + 20), (0, 220, 0), -1)
                    if not (cycle == 2 and scenario == "occlusion" and 1.7 <= u < 2.15):
                        cv2.rectangle(frame, (px - 14, py - 5), (px + 14, py + 5), (255, 80, 0), -1)
                    cv2.putText(frame, "SYNTHETIC DEMO", (12, 28), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (220, 220, 220), 1)
                    writer.write((frame * brightness).astype(np.uint8))
                if not failing and not incomplete:
                    mounted.append(slot)
        finally:
            writer.release()
    with (output_dir / "expected_events.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["video", "cycle", "event", "timestamp_sec"])
        writer.writerows(labels)
    print(f"Created {len(SCENARIOS)} synthetic videos in {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/synthetic_plate_demo_v2"))
    generate(parser.parse_args().output_dir)
