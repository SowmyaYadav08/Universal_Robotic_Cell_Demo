import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

from .engine import run_module_case
from .report import render_report


def run(module, cases, directory):
    parser = argparse.ArgumentParser(description=f"Run {module} synthetic cases in a separate output folder")
    parser.add_argument("--previews",action="store_true",help="Also extract approved real-video previews; does not classify faults")
    parser.add_argument("--output-dir",type=Path,default=directory/"outputs")
    args = parser.parse_args()
    results = [run_module_case(case) for case in cases]
    if any(result["module"] != module for result in results):
        raise ValueError("Another module's case entered this runner")
    output = args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=True)
    (output/"results.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    events = [event for result in results for event in result["events"]]
    with (output/"events.csv").open("w",newline="",encoding="utf-8") as stream:
        writer = csv.DictWriter(stream,fieldnames=list(events[0]))
        writer.writeheader()
        writer.writerows(events)
    (output/"dashboard.html").write_text(render_report(results).replace("Assembly Recovery Monitor", module+" Assembly Monitor"),encoding="utf-8")
    print(f"{module}: {len(results)} synthetic cases. Open {output/'dashboard.html'}")
    if args.previews:
        workspace = Path(__file__).resolve().parents[2]
        subprocess.run([sys.executable,str(workspace/"recovery_demo/module_video_library.py"),
                        "--module",module,"--output-dir",str(output/"video_library")],check=True)

