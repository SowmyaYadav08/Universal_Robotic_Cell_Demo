
import csv
from pathlib import Path

import cv2
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision.models import (
    mobilenet_v3_small,
    MobileNet_V3_Small_Weights
)

VIDEO = Path("data/normal/normal_video.mp4")
OUTPUT = Path("outputs/normal_timeline.csv")

SAMPLE_FPS = 2

# Load pretrained model
weights = MobileNet_V3_Small_Weights.DEFAULT
model = mobilenet_v3_small(weights=weights)

# Extract features instead of classifications
model.classifier = torch.nn.Identity()
model.eval()

preprocess = weights.transforms()


def extract_features(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)

    tensor = preprocess(image).unsqueeze(0)

    with torch.inference_mode():
        features = model(tensor)

    return F.normalize(features, dim=1)


cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    raise RuntimeError("Cannot open normal video")

fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

if fps <= 0:
    cap.release()
    raise RuntimeError("Invalid video FPS")

duration = total_frames / fps

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

results = []
previous_features = None

sample_count = int(duration * SAMPLE_FPS)

print(f"Video duration: {duration:.2f}s")
print("Extracting normal visual features...")

for i in range(sample_count):
    timestamp = i / SAMPLE_FPS

    cap.set(
        cv2.CAP_PROP_POS_MSEC,
        timestamp * 1000
    )

    success, frame = cap.read()

    if not success:
        continue

    features = extract_features(frame)

    similarity = None

    if previous_features is not None:
        similarity = F.cosine_similarity(
            previous_features,
            features,
            dim=1
        ).item()

    results.append({
        "timestamp_sec": round(timestamp, 2),
        "similarity_to_previous": (
            round(similarity, 4)
            if similarity is not None else ""
        )
    })

    previous_features = features

cap.release()

with OUTPUT.open(
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "timestamp_sec",
            "similarity_to_previous"
        ]
    )

    writer.writeheader()
    writer.writerows(results)

print("Frames processed:", len(results))
print("Results saved:", OUTPUT)
print("Normal timeline analysis completed!")
