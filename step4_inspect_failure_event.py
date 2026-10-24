
import cv2
from pathlib import Path

VIDEO = Path("data/failure/failure_video.mp4")
OUTPUT = Path("outputs/failure_event")

START_TIME = 10.0
END_TIME = 14.0
SAMPLE_FPS = 10

OUTPUT.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    raise RuntimeError("Cannot open failure video")

video_fps = cap.get(cv2.CAP_PROP_FPS)

if video_fps <= 0:
    cap.release()
    raise RuntimeError("Invalid FPS")

print(f"Video FPS: {video_fps:.2f}")
print("Extracting frames around 12-second event...")

saved = 0

for i in range(
    int((END_TIME - START_TIME) * SAMPLE_FPS) + 1
):
    timestamp = START_TIME + i / SAMPLE_FPS

    frame_number = round(timestamp * video_fps)

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        frame_number
    )

    success, frame = cap.read()

    if not success:
        continue

    filename = OUTPUT / (
        f"failure_{timestamp:.2f}s.jpg"
    )

    if cv2.imwrite(str(filename), frame):
        saved += 1

cap.release()

print(f"Frames saved: {saved}")
print(f"Output folder: {OUTPUT}")
print("Event-frame extraction completed!")
