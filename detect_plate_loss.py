"""Process-aware reviewer for colored synthetic scenes, without event-label inputs."""
import argparse
import csv
import math
from pathlib import Path
import cv2
import numpy as np

FIELDS = ["video", "cycle", "timestamp_sec", "event", "stage", "evidence", "confirmed_placements"]

def centers(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    result = []
    for contour in contours:
        m = cv2.moments(contour)
        if cv2.contourArea(contour) >= 50 and m["m00"]:
            result.append(np.array([m["m10"] / m["m00"], m["m01"] / m["m00"]]))
    return result

def detect(video):
    video = Path(video)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or fps <= 0:
        cap.release()
        raise RuntimeError(f"Invalid FPS in {video}")
    events = []
    cycle = confirmed = index = pickup_frames = 0
    active = alarmed = unknown = False
    offset = last_plate = target = None
    separation_start = withdrawn_since = None
    state = "pickup"

    def emit(event, stage, evidence, timestamp):
        events.append(dict(zip(FIELDS, [video.name, cycle, round(timestamp, 3), event,
                                       stage, evidence, confirmed])))
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            t = index / fps
            index += 1
            if frame.shape[:2] != (360, 640):
                raise ValueError("Synthetic adapter requires 640x360 demo frames")
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            grips = centers(cv2.inRange(hsv, (45, 120, 70), (85, 255, 255)))
            plates = centers(cv2.inRange(hsv, (95, 120, 70), (125, 255, 255)))
            gripper = grips[0] if len(grips) == 1 else None
            if not active:
                candidate = min(plates, key=lambda p: np.linalg.norm(p - gripper - (0, 35))) if plates and gripper is not None else None
                ready = (gripper is not None and candidate is not None and gripper[0] < 115
                         and abs(gripper[1] - 140) < 10
                         and np.linalg.norm(candidate - gripper - (0, 35)) < 12)
                pickup_frames = pickup_frames + 1 if ready else 0
                if pickup_frames >= 3:
                    cycle += 1
                    active = True
                    alarmed = unknown = False
                    offset = candidate - gripper
                    last_plate = candidate
                    target = separation_start = withdrawn_since = None
                    state = "pickup"
                    emit("cycle_started", state, "attached plate observed at pickup", t)
                continue
            if gripper is None:
                if not unknown:
                    emit("tracking_uncertain", state, "gripper not visible", t)
                unknown = True
                separation_start = withdrawn_since = None
                continue
            if gripper[0] >= 320 and abs(gripper[1] - 140) < 12:
                target = float(gripper[0])
                state = "positioning"
            elif target is None and gripper[0] >= 115:
                state = "transport"
            candidates = [p for p in plates if not (p[0] >= 320 and abs(p[1] - 175) < 12)
                          or (target is not None and abs(p[0] - target) < 20)]
            plate = min(candidates, key=lambda p: np.linalg.norm(p - last_plate)) if candidates else None
            if plate is None:
                if not unknown:
                    emit("tracking_uncertain", state, "plate temporarily not visible", t)
                unknown = True
                separation_start = None
            else:
                unknown = False
                last_plate = plate
                distance = float(np.linalg.norm(plate - gripper - offset))
                if state == "transport" and distance > 25:
                    if separation_start is None:
                        separation_start = t
                    if t - separation_start >= 0.15 and not alarmed:
                        emit("suspected_plate_loss", state,
                             f"relative separation {distance:.1f}px persisted since {separation_start:.3f}s", t)
                        alarmed = True
                else:
                    separation_start = None
            if target is not None and gripper[1] < 100:
                state = "placement_check"
                if withdrawn_since is None:
                    withdrawn_since = t
                if t - withdrawn_since >= 0.25:
                    present = any(abs(p[0] - target) < 20 and abs(p[1] - 175) < 12 for p in plates)
                    if present and not alarmed:
                        confirmed += 1
                        emit("placement_confirmed", state, "plate visible at target after gripper withdrawal", t)
                    else:
                        emit("incomplete_placement", state,
                             "no confirmed plate at target after withdrawal; inspect mounting and prior loss evidence", t)
                    active = False
                    pickup_frames = 0
        if active:
            emit("cycle_unresolved", state, "recording ended before placement could be verified", index / fps)
    finally:
        cap.release()
    if index == 0:
        raise RuntimeError(f"No decodable frames in {video}")
    return events

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("videos", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/synthetic_plate_demo_v2/events.csv"))
    args = parser.parse_args()
    events = []
    for video in args.videos:
        found = detect(video)
        events.extend(found)
        print(f"{video.name}: {len(found)} logged event(s)")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(events)
    print(f"Event log: {args.output}")

if __name__ == "__main__":
    main()
