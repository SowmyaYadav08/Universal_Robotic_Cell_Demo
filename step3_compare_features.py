
import cv2
import torch
import torch.nn.functional as F

from pathlib import Path
from PIL import Image

from torchvision.models import (
    mobilenet_v3_small,
    MobileNet_V3_Small_Weights
)

# Video paths
NORMAL_VIDEO = Path("data/normal/normal_video.mp4")
FAILURE_VIDEO = Path("data/failure/failure_video.mp4")

# Corresponding assembly stage timestamps
NORMAL_TIME = 16.0
FAILURE_TIME = 15.0

# ROI coordinates from Step 3A
X1, Y1 = 1186, 704
X2, Y2 = 1362, 884

OUTPUT = Path("outputs/roi")
OUTPUT.mkdir(parents=True, exist_ok=True)


def extract_roi(video_path, timestamp, name):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video_path}")

    cap.set(
        cv2.CAP_PROP_POS_MSEC,
        timestamp * 1000
    )

    success, frame = cap.read()
    cap.release()

    if not success:
        raise RuntimeError("Frame extraction failed")

    height, width = frame.shape[:2]

    if not (0 <= X1 < X2 <= width and
            0 <= Y1 < Y2 <= height):
        raise ValueError("ROI outside video frame")

    roi = frame[Y1:Y2, X1:X2]

    cv2.imwrite(
        str(OUTPUT / f"{name}_roi.jpg"),
        roi
    )

    return roi


# Extract corresponding regions
normal_roi = extract_roi(
    NORMAL_VIDEO, NORMAL_TIME, "normal"
)

failure_roi = extract_roi(
    FAILURE_VIDEO, FAILURE_TIME, "failure"
)


# Load pretrained MobileNetV3-Small
weights = MobileNet_V3_Small_Weights.DEFAULT
model = mobilenet_v3_small(weights=weights)

model.classifier = torch.nn.Identity()
model.eval()

preprocess = weights.transforms()


def extract_features(roi):
    # OpenCV uses BGR; PIL expects RGB
    rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

    image = Image.fromarray(rgb)

    tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        features = model(tensor)

    return features


# Extract features
normal_features = extract_features(normal_roi)
failure_features = extract_features(failure_roi)

# Compare feature vectors using cosine similarity
similarity = F.cosine_similarity(
    normal_features,
    failure_features,
    dim=1
).item()

print("Normal ROI shape:", normal_roi.shape)
print("Failure ROI shape:", failure_roi.shape)
print(f"Cosine similarity: {similarity:.4f}")
print("Feature comparison completed!")
