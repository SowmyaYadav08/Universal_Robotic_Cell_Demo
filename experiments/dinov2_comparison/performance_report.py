"""Summarize measured model costs without inventing classification metrics."""
import csv
import html
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def build_metrics(result):
    rows = []
    for model in result["models"]:
        mobile = model["model"] == "MobileNetV3-Small"
        weights = BASE / "models" / ("mobilenet_v3_small-047dcff4.pth" if mobile else "dinov2_vits14_pretrain.pth")
        ms = float(model["inference_ms_per_crop"])
        rows.append({"model":model["model"], "architecture":"Convolutional network" if mobile else "Vision transformer",
                     "f1":None,"precision":None,"recall":None,"accuracy":None,
                     "inference_ms_per_crop":ms,"inference_only_crops_per_sec":1000/ms if ms > 0 else None,
                     "model_loading_sec":float(model["loading_sec"]),
                     "embedding_values":int(model["feature_dimension"]),
                     "weight_file_mib":weights.stat().st_size/(1024**2) if weights.exists() else None,
                     "peak_memory_mib":None,
                     "classification_status":"Not evaluated: no verified test labels or model alarm predictions"})
    return rows


def metrics_table(result):
    rows = build_metrics(result)
    def value(number):
        return f"{number:.2f}" if number is not None else "Not measured"
    body = ''.join(f'<tr><td>{html.escape(r["model"])}</td><td>Not evaluated</td><td>Not evaluated</td><td>Not evaluated</td><td>{value(r["inference_ms_per_crop"])} ms</td><td>{value(r["inference_only_crops_per_sec"])}</td><td>{value(r["weight_file_mib"])} MiB</td><td>{r["embedding_values"]}</td></tr>' for r in rows)
    return '<section><h2>Model performance comparison</h2><div style="overflow:auto"><table><tr><th>Model</th><th>F1</th><th>Precision</th><th>Recall</th><th>Inference per crop</th><th>Inference-only crops/s</th><th>Weight file</th><th>Feature values</th></tr>'+body+'</table></div><p><strong>Why no F1 yet?</strong> F1 compares correct alarms, false alarms, and missed anomalies. We have similarity scores, not model predictions on independently labeled test examples. Not evaluated does not mean zero.</p><p class="small">Seven crops per model, CPU, four threads, batch size one, after warmup. Throughput is calculated as 1000 / milliseconds and excludes decoding, preprocessing and model loading. It is not end-to-end video FPS. Weight-file size is not peak RAM. Peak memory and robust latency percentiles have not been measured.</p><p>For accuracy: label independent normal/failure examples, choose each model’s threshold on calibration data, freeze it, and evaluate the same untouched test examples. Also measure false alarms per cycle, missed drops and event-detection delay.</p></section>'


def main():
    output = BASE / "outputs/matched_scenario"
    path = output / "matched_results.json"
    if not path.exists():
        print("Run run_matched_scenario.py first; no saved model measurements found.")
        return
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = build_metrics(result)
    with (output / "performance_metrics.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "performance_metrics.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
    from appearance_report import render_appearance
    (output / "matched_comparison.html").write_text(render_appearance(result),encoding="utf-8")
    print("Updated report. CPU costs are measured; F1/precision/recall remain not evaluated.")


if __name__ == "__main__":
    main()
