
import cv2
import numpy as np
from pathlib import Path

VIDEO = Path("data/failure/failure_video.mp4")

TIMESTAMPS = [11.30, 11.40, 11.50]

# Failure-event ROI
X1, Y1 = 1146, 514
X2, Y2 = 1478, 776

OUTPUT = Path("outputs/roi_motion")
OUTPUT.mkdir(parents=True, exist_ok=True)


def read_roi(cap, timestamp):
    cap.set(
        cv2.CAP_PROP_POS_MSEC,
        timestamp * 1000
    )

    success, frame = cap.read()

    if not success:
        raise RuntimeError(
            f"Cannot read video at {timestamp}s"
        )

    roi = frame[Y1:Y2, X1:X2]

    if roi.size == 0:
        raise RuntimeError("ROI is empty")

    return roi


cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    raise RuntimeError("Cannot open video")

frames = [
    read_roi(cap, t)
    for t in TIMESTAMPS
]

cap.release()

for i in range(len(frames) - 1):

    gray_a = cv2.cvtColor(
        frames[i], cv2.COLOR_BGR2GRAY
    )

    gray_b = cv2.cvtColor(
        frames[i + 1], cv2.COLOR_BGR2GRAY
    )

    difference = cv2.absdiff(
        gray_a, gray_b
    )

    difference = cv2.GaussianBlur(
        difference, (5, 5), 0
    )

    _, motion_mask = cv2.threshold(
        difference,
        30,
        255,
        cv2.THRESH_BINARY
    )

    motion_percentage = (
        np.count_nonzero(motion_mask)
        / motion_mask.size
    ) * 100

    filename = OUTPUT / (
        f"roi_motion_{TIMESTAMPS[i]:.2f}_"
        f"to_{TIMESTAMPS[i + 1]:.2f}.png"
    )

    cv2.imwrite(
        str(filename),
        motion_mask
    )

    print(
        f"{TIMESTAMPS[i]:.2f}s → "
        f"{TIMESTAMPS[i + 1]:.2f}s: "
        f"{motion_percentage:.2f}% "
        f"ROI pixels changed"
    )

print("ROI motion analysis completed!")
