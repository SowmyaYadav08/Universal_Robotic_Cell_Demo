
import cv2
from pathlib import Path

VIDEO = Path("data/failure/failure_video.mp4")
TIME = 11.30

OUTPUT = Path("outputs/templates")
OUTPUT.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    raise RuntimeError("Cannot open video")

cap.set(cv2.CAP_PROP_POS_MSEC, TIME * 1000)

success, frame = cap.read()
cap.release()

if not success:
    raise RuntimeError("Cannot read selected frame")

# Display full-size frame for precise selection
print("Select ONLY the visible plate.")
print("Avoid including gripper or background.")
print("Press Enter to confirm.")

x, y, w, h = cv2.selectROI(
    "Select Plate Template",
    frame,
    showCrosshair=True,
    fromCenter=False
)

cv2.destroyAllWindows()

if w <= 0 or h <= 0:
    raise RuntimeError("No plate selected")

plate = frame[y:y+h, x:x+w]

cv2.imwrite(
    str(OUTPUT / "plate_template.png"),
    plate
)

print("Template size:", plate.shape)
print("Template coordinates:", x, y, w, h)
print("Template saved locally.")
