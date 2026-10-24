"""Readable appearance-only report, separate from simulated robot recovery."""
import html
from pathlib import Path
import re
from performance_report import metrics_table


def render_appearance(result):
    names = ["MobileNetV3-Small", "DINOv2 ViT-S/14"]
    rows = result["scores"]
    mount_rows, inside = [], []
    for name in names:
        normal = [r["cosine_similarity"] for r in rows if r["model"] == name and r["comparison"] == "normal_variation"]
        cross = next(r["cosine_similarity"] for r in rows if r["model"] == name and r["comparison"] == "original_mounting_comparison")
        inside.append(min(normal) <= cross <= max(normal))
        mount_rows.append(f'<tr><td>{html.escape(name)}</td><td>{cross:.3f}</td><td>{min(normal):.3f} to {max(normal):.3f}</td></tr>')
    def pairs(category, region):
        keys = list(dict.fromkeys((r["frame_a"], r["frame_b"]) for r in rows if r["comparison"] == category))
        output = []
        for a,b in keys:
            values = [next(r["cosine_similarity"] for r in rows if r["model"] == name and r["frame_a"] == a and r["frame_b"] == b) for name in names]
            label = a.removeprefix(region).removesuffix("s") + " → " + b.removeprefix(region).removesuffix("s") + " seconds"
            output.append(f'<tr><td>{html.escape(label)}</td><td>{values[0]:.3f}</td><td>{values[1]:.3f}</td></tr>')
        return ''.join(output)
    timing = ''.join(f'<tr><td>{html.escape(m["model"])}</td><td>{m["inference_ms_per_crop"]:.2f} milliseconds</td></tr>' for m in result["models"])
    conclusion = ("For both models, the normal-vs-failure score falls inside the range seen between normal pictures. This small mounting test does not show clear separation between normal and failure appearance."
                  if all(inside) else "At least one normal-vs-failure score lies outside its small normal reference range. This is an exploratory difference, not proof of reliable anomaly detection.")
    values = {"PERFORMANCE":metrics_table(result),"MOUNT_ROWS":''.join(mount_rows),"CONCLUSION":conclusion,
              "TRANSPORT_ROWS":pairs("transport_visual_change", "failure_transport_"),
              "BASELINE_ROWS":pairs("normal_variation", "normal_mounting_"),"TIMING_ROWS":timing}
    template = Path(__file__).with_name("appearance_report.html").read_text(encoding="utf-8-sig")
    return re.sub(r"__[A-Z_]+__", lambda m: values[m.group(0)[2:-2]], template)
