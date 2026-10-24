
import cv2
from pathlib import Path

VIDEO = Path("data/failure/failure_video.mp4")
TIMESTAMP = 11.40

cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    raise RuntimeError("Cannot open failure video")

cap.set(cv2.CAP_PROP_POS_MSEC, TIMESTAMP * 1000)

success, frame = cap.read()
cap.release()

if not success:
    raise RuntimeError("Cannot read frame")

# Display half-size preview
scale = 0.5

preview = cv2.resize(
    frame, None,
    fx=scale,
    fy=scale,
    interpolation=cv2.INTER_AREA
)

print("Select the region containing the gripper")
print("and the falling component.")
print("Press ENTER to confirm.")

x, y, w, h = cv2.selectROI(
    "Failure event ROI",
    preview,
    showCrosshair=True,
    fromCenter=False
)

cv2.destroyAllWindows()

if w <= 0 or h <= 0:
    raise RuntimeError("No ROI selected")

# Convert to original-resolution coordinates
x1 = round(x / scale)
y1 = round(y / scale)
x2 = round((x + w) / scale)
y2 = round((y + h) / scale)

print("Failure event ROI:", x1, y1, x2, y2)
print("ROI selection completed!")
