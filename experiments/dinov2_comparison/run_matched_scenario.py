"""Reproduce the existing recovery demo, then compare two models on fixed inputs."""
import csv
import hashlib
import html
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image
import torch
from torchvision.models import MobileNet_V3_Small_Weights

from compare_models import BASE, load_model


def read_roi(video, timestamp, roi):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video}")
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp*1000)
        ok, frame = cap.read()
    finally:
        cap.release()
    if not ok:
        raise RuntimeError(f"Cannot read {timestamp}s from {video}")
    x1,y1,x2,y2 = roi
    height,width = frame.shape[:2]
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError("ROI outside recording")
    return frame[y1:y2,x1:x2].copy()


def main():
    config = json.loads((BASE / "matched_scenario.json").read_text(encoding="utf-8-sig"))
    output = BASE / "outputs/matched_scenario"
    output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    # Reproduce the frozen scenario rather than editing the current project.
    print("1/3 Reproducing the existing synthetic recovery scenarios...", flush=True)
    run = subprocess.run([sys.executable, str(BASE / "snapshot/recovery_demo/run_demo.py"),
                          "--output-dir", str(output / "recovery_reference")],
                         capture_output=True, text=True)
    (output / "recovery_reference_run.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise RuntimeError("Copied recovery scenario did not run. See recovery_reference_run.txt")
    playback_path = output / "recovery_reference/recovery_playback.html"
    playback_path.write_text(playback_path.read_text(encoding="utf-8-sig").replace(
        '../../outputs/approved_visual_references/', '../../../snapshot/outputs/approved_visual_references/'), encoding="utf-8")
    inputs = {}
    normal = BASE / config["normal_video"]
    failure = BASE / config["failure_video"]
    for t in config["normal_mounting_times_sec"]:
        inputs[f"normal_mounting_{t:g}s"] = read_roi(normal,t,config["mounting_roi_xyxy"])
    failure_key = f'failure_mounting_{config["failure_mounting_time_sec"]:g}s'
    inputs[failure_key] = read_roi(failure,config["failure_mounting_time_sec"],config["mounting_roi_xyxy"])
    for t in config["failure_transport_times_sec"]:
        inputs[f"failure_transport_{t:g}s"] = read_roi(failure,t,config["transport_roi_xyxy"])
    for name,image in inputs.items():
        if not cv2.imwrite(str(output / f"{name}.png"),image):
            raise RuntimeError("Could not save input evidence")
    # This is exactly the original MobileNet preprocessing. Both models receive
    # identical tensors here. It does not download weights.
    preprocess = MobileNet_V3_Small_Weights.DEFAULT.transforms()
    tensors = {name:preprocess(Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))).unsqueeze(0)
               for name,image in inputs.items()}
    input_hashes = {name:hashlib.sha256(tensor.numpy().tobytes()).hexdigest() for name,tensor in tensors.items()}
    normal_keys = [f"normal_mounting_{t:g}s" for t in config["normal_mounting_times_sec"]]
    transport_keys = [f"failure_transport_{t:g}s" for t in config["failure_transport_times_sec"]]
    comparisons = [("normal_variation",a,b) for a,b in itertools.combinations(normal_keys,2)]
    comparisons += [("original_mounting_comparison",f'normal_mounting_{config["normal_comparison_time_sec"]:g}s',failure_key)]
    comparisons += [("transport_visual_change",a,b) for a,b in zip(transport_keys,transport_keys[1:])]
    rows, model_summaries = [], []
    for number,name in enumerate(("MobileNetV3-Small","DINOv2 ViT-S/14"), start=2):
        print(f"{number}/3 Comparing {name} on the same seven crops...", flush=True)
        start = time.perf_counter()
        model,weights = load_model(name)
        loading = time.perf_counter()-start
        features = {}
        with torch.inference_mode():
            model(next(iter(tensors.values())))  # untimed warmup
            start = time.perf_counter()
            for key,tensor in tensors.items():
                feature = model(tensor)
                if feature.ndim != 2 or not torch.isfinite(feature).all():
                    raise ValueError("Invalid embedding")
                features[key] = torch.nn.functional.normalize(feature,dim=1)
            inference_sec = time.perf_counter()-start
        for category,a,b in comparisons:
            similarity = float((features[a]*features[b]).sum().clamp(-1,1))
            rows.append({"model":name,"comparison":category,"frame_a":a,"frame_b":b,
                         "cosine_similarity":similarity,"cosine_distance":1-similarity})
        model_summaries.append({"model":name,"feature_dimension":features[normal_keys[0]].shape[1],
                                "loading_sec":loading,"warmed_inference_sec":inference_sec,
                                "inference_ms_per_crop":inference_sec/len(tensors)*1000,
                                "weights_sha256":hashlib.sha256(weights.read_bytes()).hexdigest()})
        np.savez(output / ("mobilenet_features.npz" if number == 2 else "dinov2_features.npz"),
                 **{key:value.numpy() for key,value in features.items()})
        del model
    with (output / "matched_scores.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = {"protocol":config,"input_tensor_sha256":input_hashes,"models":model_summaries,
              "scores":rows,"drop_detection_accuracy":None,"models_control_recovery":False,
              "scope":"Same fixed inputs and original MobileNet preprocessing, CPU, four threads. No fine-tuning or model-specific threshold. Recovery policy is shared and synthetic."}
    (output / "matched_results.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    from appearance_report import render_appearance
    (output / "matched_comparison.html").write_text(render_appearance(result), encoding="utf-8")
    print(f"Open: {output / 'matched_comparison.html'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError,RuntimeError,ValueError) as error:
        print(f"Matched comparison did not finish: {error}",file=sys.stderr)
        raise SystemExit(1)

