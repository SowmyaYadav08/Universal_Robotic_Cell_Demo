
import cv2
import numpy as np
from pathlib import Path

VIDEO_PATH = Path("data/failure/failure_video.mp4")

TIMESTAMPS = [11.30, 11.40, 11.50]

OUTPUT = Path("outputs/motion_analysis")
OUTPUT.mkdir(parents=True, exist_ok=True)


def get_frame(timestamp):
    cap = cv2.VideoCapture(str(VIDEO_PATH))

    if not cap.isOpened():
        raise RuntimeError("Cannot open failure video")

    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    success, frame = cap.read()
    cap.release()

    if not success:
        raise RuntimeError(f"Frame unavailable: {timestamp}")

    return frame


frames = [get_frame(t) for t in TIMESTAMPS]

# Convert to grayscale
gray = [
    cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    for frame in frames
]

for i in range(len(gray) - 1):
    # Calculate absolute pixel differences
    difference = cv2.absdiff(gray[i], gray[i + 1])

    # Smooth minor pixel noise
    difference = cv2.GaussianBlur(
        difference, (5, 5), 0
    )

    # Highlight significant changes
    _, motion_mask = cv2.threshold(
        difference, 30, 255, cv2.THRESH_BINARY
    )

    # Calculate percentage of changing pixels
    motion_percentage = (
        np.count_nonzero(motion_mask) /
        motion_mask.size
    ) * 100

    filename = OUTPUT / (
        f"motion_{TIMESTAMPS[i]:.2f}_"
        f"to_{TIMESTAMPS[i + 1]:.2f}.png"
    )

    cv2.imwrite(str(filename), motion_mask)

    print(
        f"{TIMESTAMPS[i]:.2f}s → "
        f"{TIMESTAMPS[i + 1]:.2f}s: "
        f"{motion_percentage:.2f}% pixels changed"
    )

print("Motion analysis completed.")
