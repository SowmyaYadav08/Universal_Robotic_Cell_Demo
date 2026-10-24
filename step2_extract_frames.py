
import cv2
from pathlib import Path

VIDEOS = {
    "normal": Path("data/normal/normal_video.mp4"),
    "failure": Path("data/failure/failure_video.mp4")
}

OUTPUT = Path("outputs/frames")
SAMPLE_INTERVAL = 1.0  # seconds


def extract_frames(video_path, category):
    if not video_path.exists():
        print(f"Missing file: {video_path}")
        return

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"Cannot open: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    if fps <= 0:
        print("Invalid video FPS")
        cap.release()
        return

    duration = total / fps

    print(f"\nVideo: {category}")
    print(f"FPS: {fps:.2f}")
    print(f"Duration: {duration:.2f} seconds")

    folder = OUTPUT / category
    folder.mkdir(parents=True, exist_ok=True)

    saved = 0
    second = 0.0

    while second < duration:
        frame_number = round(second * fps)

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = cap.read()

        if not success:
            break

        # Smaller copy for inspection only
        preview = cv2.resize(
            frame, (960, 540),
            interpolation=cv2.INTER_AREA
        )

        timestamp_ms = round(second * 1000)
        filename = folder / f"frame_{timestamp_ms:06d}ms.jpg"

        if cv2.imwrite(str(filename), preview):
            saved += 1

        second += SAMPLE_INTERVAL

    cap.release()

    print(f"Extracted frames: {saved}")
    print(f"Saved locally in: {folder}")


for category, path in VIDEOS.items():
    extract_frames(path, category)

print("\nStep 2 completed.")
