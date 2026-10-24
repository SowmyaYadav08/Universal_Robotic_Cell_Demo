
import cv2
from pathlib import Path

VIDEO_PATH = Path("data/normal/normal_video.mp4")
TIMESTAMP = 16.0

OUTPUT_DIR = Path("outputs/roi")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(str(VIDEO_PATH))

if not cap.isOpened():
    raise RuntimeError("Could not open normal video")

# Seek to the selected post-placement timestamp
cap.set(cv2.CAP_PROP_POS_MSEC, TIMESTAMP * 1000)

success, frame = cap.read()
cap.release()

if not success:
    raise RuntimeError("Could not read selected frame")

# Show a half-size preview for easier ROI selection
scale = 0.5
preview = cv2.resize(
    frame, None,
    fx=scale, fy=scale,
    interpolation=cv2.INTER_AREA
)

print("Select the mounting area.")
print("Drag a rectangle, press ENTER to confirm.")
print("Press C to cancel.")

roi = cv2.selectROI(
    "Select mounting region",
    preview,
    showCrosshair=True,
    fromCenter=False
)

cv2.destroyAllWindows()

x, y, w, h = map(int, roi)

if w == 0 or h == 0:
    raise RuntimeError("No ROI selected")

# Convert preview coordinates back to original resolution
x1 = round(x / scale)
y1 = round(y / scale)
x2 = round((x + w) / scale)
y2 = round((y + h) / scale)

crop = frame[y1:y2, x1:x2]

cv2.imwrite(
    str(OUTPUT_DIR / "normal_roi.jpg"),
    crop
)

print("Original-resolution ROI:",
      x1, y1, x2, y2)
print("ROI saved locally")
