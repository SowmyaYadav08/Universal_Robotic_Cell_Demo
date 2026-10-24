
import cv2
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision.models import (
    mobilenet_v3_small,
    MobileNet_V3_Small_Weights
)

VIDEO = "data/normal/normal_video.mp4"

# Use only times when placement is already complete
TIMESTAMPS = [14.0, 15.0, 16.0]

X1, Y1, X2, Y2 = 1186, 704, 1362, 884

weights = MobileNet_V3_Small_Weights.DEFAULT
model = mobilenet_v3_small(weights=weights)
model.classifier = torch.nn.Identity()
model.eval()

preprocess = weights.transforms()


def get_features(timestamp):
    cap = cv2.VideoCapture(VIDEO)

    cap.set(
        cv2.CAP_PROP_POS_MSEC,
        timestamp * 1000
    )

    success, frame = cap.read()
    cap.release()

    if not success:
        raise RuntimeError(
            f"Could not read frame at {timestamp}s"
        )

    roi = frame[Y1:Y2, X1:X2]
    rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)

    image = Image.fromarray(rgb)
    tensor = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        features = model(tensor)

    return features


features = {
    t: get_features(t) for t in TIMESTAMPS
}

print("\nNormal-to-normal similarity:")

for i, t1 in enumerate(TIMESTAMPS):
    for t2 in TIMESTAMPS[i + 1:]:
        similarity = F.cosine_similarity(
            features[t1],
            features[t2],
            dim=1
        ).item()

        print(
            f"{t1:.1f}s vs {t2:.1f}s: "
            f"{similarity:.4f}"
        )
