"""Offline CPU appearance comparison; no detector accuracy or robot-control claims."""
import argparse
import csv
import hashlib
import html
import json
import math
import os
from pathlib import Path
import sys
import time

os.environ["XFORMERS_DISABLED"] = "1"
import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import mobilenet_v3_small

BASE = Path(__file__).resolve().parent
ROIS = {"transport": (1146, 514, 1478, 776), "mounting": (1186, 704, 1362, 884)}


def nearest_distances(query, references, exclude_self=False):
    if len(references) < 2 or query.ndim != 2 or references.ndim != 2:
        raise ValueError("Need at least two reference frames and two-dimensional embeddings")
    similarity = np.clip(query @ references.T, -1, 1)
    if exclude_self:
        if query.shape != references.shape:
            raise ValueError("Self-exclusion requires matching arrays")
        np.fill_diagonal(similarity, -np.inf)
    closest = similarity.argmax(axis=1)
    return 1-similarity[np.arange(len(query)), closest], closest


def load_model(name):
    if name == "MobileNetV3-Small":
        path = BASE / "models/mobilenet_v3_small-047dcff4.pth"
        model = mobilenet_v3_small(weights=None)
    else:
        path = BASE / "models/dinov2_vits14_pretrain.pth"
        repo = BASE / "models/dinov2-main"
        if not (repo / "dinov2/hub/backbones.py").is_file():
            raise FileNotFoundError("Official DINOv2 source is missing from models/dinov2-main")
        sys.path.insert(0, str(repo))
        # Import only backbone code, avoiding unrelated Hub entry points.
        from dinov2.hub.backbones import dinov2_vits14
        model = dinov2_vits14(pretrained=False)
    if not path.is_file():
        raise FileNotFoundError(f"Local weights missing: {path}. This runner never downloads files.")
    model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True), strict=True)
    if name == "MobileNetV3-Small":
        model.classifier = torch.nn.Identity()
    return model.eval().cpu(), path


def extract(model, video, roi, sample_fps, limit):
    preprocess = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                                     transforms.Normalize((0.485,0.456,0.406), (0.229,0.224,0.225))])
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot read copied approved video: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps) or fps <= 0:
        cap.release()
        raise ValueError("Invalid video FPS")
    stride = max(1, round(fps/sample_fps))
    x1,y1,x2,y2 = roi
    times, embeddings = [], []
    index = 0
    start = time.perf_counter()
    try:
        with torch.inference_mode():
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                frame_index = index
                index += 1
                if frame_index % stride:
                    continue
                height,width = frame.shape[:2]
                if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                    raise ValueError("Configured ROI does not fit this recording")
                image = Image.fromarray(cv2.cvtColor(frame[y1:y2,x1:x2], cv2.COLOR_BGR2RGB))
                embedding = model(preprocess(image).unsqueeze(0))
                if embedding.ndim != 2 or not torch.isfinite(embedding).all():
                    raise ValueError("Unexpected model output")
                embedding = torch.nn.functional.normalize(embedding, dim=1)
                embeddings.append(embedding[0].numpy())
                times.append(frame_index/fps)
                if limit and len(times) >= limit:
                    break
    finally:
        cap.release()
    if len(times) < 2:
        raise ValueError("Not enough decoded samples")
    return np.array(times), np.stack(embeddings), time.perf_counter()-start


def curve(times, scores, name):
    esc = html.escape
    maximum = max(float(max(scores)), 0.001)
    duration = max(float(max(times)), 1)
    points = ' '.join(f'{50+t/duration*740:.1f},{165-s/maximum*130:.1f}' for t,s in zip(times,scores))
    return f'<svg viewBox="0 0 850 205" role="img" aria-label="{esc(name)} appearance distance over recording time"><rect x="{50+11/duration*740:.1f}" y="30" width="{740/duration:.1f}" height="135" fill="#fff0c2"/><path d="M50 30V165H790" fill="none" stroke="#9baec0"/><polyline points="{points}" fill="none" stroke="#007b89" stroke-width="2"/><text x="50" y="20">Cosine distance (scale 0 to {maximum:.3f})</text><text x="50" y="190">0 seconds</text><text x="700" y="190">{duration:.1f} seconds</text></svg>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roi", choices=ROIS, default="transport")
    parser.add_argument("--sample-fps", type=float, default=2)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--limit", type=int, help="Smoke test only: maximum samples per recording")
    args = parser.parse_args()
    if not math.isfinite(args.sample_fps) or args.sample_fps <= 0 or args.threads <= 0 or (args.limit is not None and args.limit < 2):
        parser.error("Use positive FPS/threads and a limit of at least 2")
    torch.set_num_threads(args.threads)
    output = BASE / "outputs" / args.roi / ("smoke_test" if args.limit else "full_recordings")
    output.mkdir(parents=True, exist_ok=True)
    videos = [BASE / "snapshot/Data/normal/normal_video.mp4", BASE / "snapshot/Data/failure/failure_video.mp4"]
    results, all_rows, chart_sections = [], [], []
    for name in ("MobileNetV3-Small", "DINOv2 ViT-S/14"):
        print(f"Loading {name} on CPU...", flush=True)
        load_start = time.perf_counter()
        model, weights = load_model(name)
        load_seconds = time.perf_counter()-load_start
        normal_t, normal_f, normal_sec = extract(model, videos[0], ROIS[args.roi], args.sample_fps, args.limit)
        print(f"{name}: {len(normal_t)} normal samples processed. Scanning failure recording...", flush=True)
        failure_t, failure_f, failure_sec = extract(model, videos[1], ROIS[args.roi], args.sample_fps, args.limit)
        normal_scores, normal_nearest = nearest_distances(normal_f, normal_f, exclude_self=True)
        failure_scores, failure_nearest = nearest_distances(failure_f, normal_f)
        for category, times, scores, nearest in (("normal_leave_one_out",normal_t,normal_scores,normal_nearest),
                                                  ("failure",failure_t,failure_scores,failure_nearest)):
            for t,score,neighbor in zip(times,scores,nearest):
                all_rows.append({"model":name,"recording":category,"timestamp_sec":round(float(t),4),
                                 "appearance_distance":round(float(score),6),
                                 "closest_normal_timestamp_sec":round(float(normal_t[neighbor]),4)})
        window = (failure_t >= 11) & (failure_t <= 12)
        event_score = float(max(failure_scores[window])) if window.any() else None
        peak = int(failure_scores.argmax())
        result = {"model":name,"embedding_dimension":normal_f.shape[1],
                  "parameter_count":sum(p.numel() for p in model.parameters()),
                  "weight_sha256":hashlib.sha256(weights.read_bytes()).hexdigest(),
                  "model_loading_sec":round(load_seconds,3),
                  "normal_samples":len(normal_t),"failure_samples":len(failure_t),
                  "extraction_sec_including_video_decode":round(normal_sec+failure_sec,3),
                  "sampled_frames_per_sec":round((len(normal_t)+len(failure_t))/(normal_sec+failure_sec),3),
                  "normal_leave_one_out_distance_median":float(np.median(normal_scores)),
                  "largest_failure_distance":float(failure_scores[peak]),
                  "largest_failure_distance_time_sec":float(failure_t[peak]),
                  "user_reported_window_sec":[11,12],"window_distance_max":event_score,
                  "window_peak_percentile_within_failure":float(100*np.mean(failure_scores <= event_score)) if event_score is not None else None}
        results.append(result)
        chart_sections.append(f'<section><h2>{html.escape(name)}</h2>{curve(failure_t,failure_scores,name)}<p>Most different sampled frame: {failure_t[peak]:.2f}s. Shaded region: user-reported approximate drop window (11–12s), not an exact verified label.</p></section>')
        print(f"{name} complete: {result['sampled_frames_per_sec']} sampled frames/sec", flush=True)
        del model
    with (output / "appearance_scores.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    summary = {"mode":"offline_cpu_appearance_experiment", "roi":args.roi,"roi_xyxy":ROIS[args.roi],
               "sample_fps_requested":args.sample_fps,"threads":args.threads,"smoke_test":bool(args.limit),
               "preprocessing":"Shared RGB resize to 224x224 and ImageNet normalization; ROI aspect ratio is resized.",
               "models":results,"validated_drop_detector":False,
               "limitations":"No stage alignment; multiple-plate state mismatch can dominate scores. Normal leave-one-out samples are temporally correlated. User-reported 11–12s interval is exploratory, not ground truth. No detection accuracy, delay, recovery permission or superiority conclusion is calculated."}
    (output / "comparison.json").write_text(json.dumps(summary,indent=2), encoding="utf-8")
    rows = ''.join(f'<tr><td>{html.escape(r["model"])}</td><td>{r["embedding_dimension"]}</td><td>{r["extraction_sec_including_video_decode"]:.2f}s</td><td>{r["sampled_frames_per_sec"]:.2f}</td><td>{r["largest_failure_distance_time_sec"]:.2f}s</td><td>{r["window_peak_percentile_within_failure"] if r["window_peak_percentile_within_failure"] is not None else "Not sampled"}</td></tr>' for r in results)
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MobileNet vs DINOv2 — appearance experiment</title><style>body{font:17px system-ui;max-width:1150px;margin:30px auto;padding:20px;background:#f2f6fa;color:#20354b}section{background:white;padding:20px;border-radius:12px;margin:20px 0}svg{width:100%}td,th{padding:12px;text-align:left;border-bottom:1px solid #ddd}table{border-collapse:collapse;width:100%;background:white}.note{padding:20px;background:#fff1ce}</style><h1>MobileNet vs DINOv2</h1><p class="note">Appearance experiment on copied approved recordings. This does not confirm plate drops or control a robot.</p>'
    if args.limit:
        page += f'<p class="note"><strong>LOAD CHECK ONLY:</strong> limited to {args.limit} samples per recording. The drop interval may not be included. Run without --limit for the full experiment.</p>'
    page += f'<p>ROI: {args.roi}. Both models use the same sampled frames and preprocessing. Higher distance means less resemblance to the closest normal reference frame. Each graph has its own scale: larger raw scores do not mean a better model.</p><table><tr><th>Model</th><th>Feature size</th><th>Extraction time</th><th>Sampled frames/s</th><th>Largest difference at</th><th>Drop-window peak percentile*</th></tr>{rows}</table><p>*Ranks the largest score in 11–12s against that model’s scores over the failure recording. This is neither confidence nor accuracy. Extraction time includes decoding, preprocessing and inference, excludes model loading, and is not full-frame inference throughput.</p>'
    page += ''.join(chart_sections) + f'<section><h2>What can we conclude?</h2><p>{html.escape(summary["limitations"])}</p><p>Next: verify annotations, align process stages and assembly state, and test independent recordings before choosing a detector.</p><a href="appearance_scores.csv">Per-frame appearance measurements</a> | <a href="comparison.json">Experiment configuration and results</a></section></html>'
    (output / "comparison.html").write_text(page, encoding="utf-8")
    print(f"Open {output / 'comparison.html'}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Comparison did not finish: {error}", file=sys.stderr)
        print("No complete comparison result is claimed. Keep earlier reports separate from this attempted run.", file=sys.stderr)
        raise SystemExit(1)
