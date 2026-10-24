
import torch
import numpy as np
from PIL import Image
from torchvision.models import (
    mobilenet_v3_small,
    MobileNet_V3_Small_Weights
)

# 1. Select CPU
device = torch.device("cpu")

# 2. Load pretrained MobileNetV3-Small
weights = MobileNet_V3_Small_Weights.DEFAULT
model = mobilenet_v3_small(weights=weights)

# Remove the classification layers
model.classifier = torch.nn.Identity()

# Set evaluation mode
model.eval()
model.to(device)

print("Model loaded successfully!")

# 3. Get the correct image preprocessing
preprocess = weights.transforms()

# 4. Generate a synthetic image
image_array = np.zeros(
    (224, 224, 3),
    dtype=np.uint8
)

# Add a white rectangle
image_array[60:160, 70:150] = 255

image = Image.fromarray(image_array)

# 5. Prepare model input
input_tensor = preprocess(image)
input_batch = input_tensor.unsqueeze(0).to(device)

# 6. Extract visual features
with torch.no_grad():
    features = model(input_batch)

print("Input shape:", input_batch.shape)
print("Feature shape:", features.shape)

assert features.shape == (1, 576)
assert torch.isfinite(features).all()

print("SUCCESS: Feature extraction works!")
