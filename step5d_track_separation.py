
import cv2
import numpy as np
from pathlib import Path

VIDEO = Path("data/failure/failure_video.mp4")
TIMES = [11.30, 11.40, 11.50]
SCALE = 0.5


def read_frame(cap, seconds):
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"Cannot read {seconds}s")
    return cv2.resize(
        frame, None, fx=SCALE, fy=SCALE
    )


cap = cv2.VideoCapture(str(VIDEO))
if not cap.isOpened():
    raise RuntimeError("Cannot open video")

frames = [read_frame(cap, t) for t in TIMES]
cap.release()

first = frames[0]

print("Select GRIPPER region and press Enter")
gripper_roi = cv2.selectROI(
    "Select Gripper", first, False, False
)

print("Select PLATE region and press Enter")
plate_roi = cv2.selectROI(
    "Select Plate", first, False, False
)

cv2.destroyAllWindows()


def get_points(frame, roi):
    x, y, w, h = map(int, roi)
    if w <= 0 or h <= 0:
        raise RuntimeError("Invalid ROI selection")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    mask[y:y+h, x:x+w] = 255

    points = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=40,
        qualityLevel=0.01,
        minDistance=5,
        mask=mask
    )
    return points


gripper_points = get_points(first, gripper_roi)
plate_points = get_points(first, plate_roi)

if gripper_points is None or plate_points is None:
    raise RuntimeError(
        "Not enough visual features in selected regions"
    )


def track(points, gray_a, gray_b):
    next_points, status, _ = cv2.calcOpticalFlowPyrLK(
        gray_a, gray_b, points, None
    )

    if next_points is None:
        return None, None

    valid = status.reshape(-1) == 1
    old = points[valid].reshape(-1, 2)
    new = next_points[valid].reshape(-1, 2)

    if len(old) < 3:
        return None, None

    motion = np.median(new - old, axis=0)
    return next_points[valid].reshape(-1, 1, 2), motion


OUTPUT = Path("outputs/tracking_check")
OUTPUT.mkdir(parents=True, exist_ok=True)


for i in range(2):
    gray_a = cv2.cvtColor(
        frames[i], cv2.COLOR_BGR2GRAY
    )
    gray_b = cv2.cvtColor(
        frames[i+1], cv2.COLOR_BGR2GRAY
    )

    gripper_points, gm = track(
        gripper_points, gray_a, gray_b
    )
    plate_points, pm = track(
        plate_points, gray_a, gray_b
    )

    if gm is None or pm is None:
        print("Tracking uncertain: insufficient points")
        break

    relative = pm - gm


    # Draw tracked points on the next frame
    display = frames[i + 1].copy()

    for point in gripper_points.reshape(-1, 2):
        x, y = point.astype(int)
        cv2.circle(display, (x, y), 3, (0, 255, 0), -1)

    for point in plate_points.reshape(-1, 2):
        x, y = point.astype(int)
        cv2.circle(display, (x, y), 3, (0, 0, 255), -1)

    filename = OUTPUT / f"tracking_{TIMES[i+1]:.2f}.jpg"

    cv2.imwrite(str(filename), display)


    print(f"\n{TIMES[i]:.2f}s -> {TIMES[i+1]:.2f}s")
    print("Gripper motion:", np.round(gm, 2))
    print("Plate motion:", np.round(pm, 2))
    print(
        "Relative motion magnitude:",
        round(float(np.linalg.norm(relative)), 2),
        "preview pixels"
    )

print("\nTracking experiment completed.")
