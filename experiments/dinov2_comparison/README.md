# MobileNet and DINOv2 comparison — separate experiment

The matched report is now **Assembly Appearance Comparison**. It focuses only
on the visual test: mounting-area picture pairs, normal similarity range, and
transport pictures with readable timestamps. CPU timings and full measurements
are optional details. Similarity scores are not accuracy percentages. Recovery
animation behavior is unchanged and remains available separately in recovery_reference/.

## Start here: reproduce the same scenario before comparing

```powershell
python experiments/dinov2_comparison/run_matched_scenario.py
```

This first reproduces the frozen recovery demo from snapshot/, with outputs in
this experiment only. Then it repeats the original MobileNet mounting-frame
experiment and the existing three-frame transport inspection with both encoders.
It uses identical crops and the original MobileNet weights.transforms()
preprocessing for both, including resize and center crop. No weights are downloaded.

Open `outputs/matched_scenario/matched_comparison.html` inside this experiment.
It links the reproduced stacked-plate recovery playback, displays all seven shared
input pictures, compares normal-to-normal and normal-to-failure similarity, and
reports warmed CPU inference cost. Results and input tensor hashes are saved.
The settings are in matched_scenario.json. Existing manually chosen timestamps
are reproduced, not supplied as validated event labels.

The original recovery flow did not depend on MobileNet: it used synthetic checks,
and real motion alerts came from optical flow. This matched experiment changes
only the appearance encoder. Recovery policy therefore stays shared, and no
model-dependent recovery-success claim is made. Run the full-recording experiment
below only after this reproduction works. Neither experiment has yet been executed
by this assistant because its shell cannot launch the workspace interpreter.

Your original project is unchanged. `snapshot/` contains a copy of the Python
scripts, documentation, reports, and the two approved videos. The virtual
environment, IDE settings, and interpreter caches were not copied. Use your
existing working Python environment to run the experiment.

## 1. Check both models load

From the original workspace terminal:

```powershell
python experiments/dinov2_comparison/compare_models.py --limit 3
```

This checks only three frames per recording, not detection performance.
If it fails, retain the error message and do not interpret the partial run.

## 2. Run the full transport-region experiment

```powershell
python experiments/dinov2_comparison/compare_models.py
```

Open `outputs/transport/full_recordings/comparison.html` under this experiment
folder. Results include appearance-distance curves, actual extraction runtime,
sampled-frame throughput, the most visually different sampled timestamp, and
the score near the user-reported approximate 11–12 second drop interval.

The normal video becomes a bank of reference embeddings. Each failure sample
is compared with its closest normal reference using cosine distance. Normal
samples are also compared against the other normal frames, excluding themselves.
Adjacent normal frames remain correlated, so this is not independent validation.

For a separate mounting-area experiment:

```powershell
python experiments/dinov2_comparison/compare_models.py --roi mounting
```

Results are kept in separate ROI folders. Smoke-test results are also separate.
Rerunning the same experiment overwrites only that experiment's result files.

## 3. Run the distance checks

```powershell
python -m unittest discover -s experiments/dinov2_comparison -p "test_*.py" -v
```

## What is kept the same?

Both models process the same approved recordings, sampled timestamps, ROI and
shared 224x224 RGB preprocessing with ImageNet normalization. Inference uses CPU,
float32, one frame per batch, and four CPU threads by default. Both output vectors
are normalized. Default sampling is two frames per second. DINOv2 is a larger
model and may be slower; the report measures the local tradeoff rather than
assuming an improvement. The shared resize changes the ROI aspect ratio.

## What does this not prove?

These models extract appearance features; neither is a trained plate-drop
classifier here. Raw distances have model-specific scales. The normal recording
only shows the first placement, while later failure frames may show different
process states and additional plates. Novelty can therefore reflect stage,
occlusion, or assembly-state differences rather than a defect. The report does
not calculate accuracy, confirmed detection delay, or pick a winning model.
The 11–12 second interval is exploratory, not a precise independently verified
event label. We need stage-aligned references and independent annotated runs for
a reliable evaluation. Motion/recovery code in the snapshot is not changed or
automatically connected to the new appearance experiment.

## Downloads and privacy

The user authorized public model downloads only. Official DINOv2 code and
ViT-S/14 weights were downloaded locally; the existing cached MobileNet weights
were copied. The runner does not call remote inference, download weights, or upload
images. Dependencies are the existing PyTorch, torchvision, NumPy, Pillow and
OpenCV packages; no package installation was performed. Official source and
license files remain in `models/dinov2-main`.

- Source: https://github.com/facebookresearch/dinov2
- Archive: https://github.com/facebookresearch/dinov2/archive/refs/heads/main.zip
- Weights: https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth

The archive is a snapshot of the public main branch at download time. Local
SHA-256 hashes are recorded in the manifest for reproducibility; they are not
independent publisher-signed checksums.

## Execution status

Model files and the runner are prepared. This assistant's shell still cannot
launch the workspace interpreter; actual model loading, tests, runtime, and
comparison results remain unverified until executed in the working terminal.
