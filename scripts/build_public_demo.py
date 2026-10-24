"""Build a self-contained public demo using synthetic scenarios only."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "public_demo"


def main():
    DEST.mkdir(exist_ok=True)
    commands = {
        "light_localizer": "recovery_demo/run_demo.py",
        "prefilter": "assembly_modules/prefilter/run_demo.py",
        "tube_interface": "assembly_modules/tube_interface/run_demo.py",
    }
    modules = []
    for module, entry in commands.items():
        output = DEST / module
        subprocess.run([sys.executable, str(ROOT / entry), "--output-dir", str(output)],
                       cwd=ROOT, check=True)
        for page in output.glob("*.html"):
            html = page.read_text(encoding="utf-8")
            # Public demo contains no manufacturing footage or reference photos.
            html = re.sub(r'<details><summary>Original assembly photos for reference</summary>.*?</details>',
                          '', html, flags=re.S)
            html = re.sub(r'<a href="(?:real_video_review/review.html|video_library/library.html)">.*?</a>',
                          '', html)
            page.write_text(html, encoding="utf-8")
        reports = [
            {"name": "Assembly Event Log (CSV)", "path": f"{module}/events.csv", "kind": "download", "available": True},
            {"name": "Scenario Results (JSON)", "path": f"{module}/results.json", "kind": "download", "available": True},
        ]
        if module == "light_localizer":
            reports.insert(0, {"name": "Plate Replacement Playback (Simulation)",
                               "path": f"{module}/recovery_playback.html", "kind": "page", "available": True})
        modules.append({"id": module, "name": module.replace("_", " ").title(),
                        "description": "Synthetic demonstration. No real robot or factory data.",
                        "dashboard": f"{module}/dashboard.html", "available": True, "reports": reports})
    template = (ROOT / "assembly_modules/hub_template.html").read_text(encoding="utf-8-sig")
    (DEST / "index.html").write_text(template.replace("__MODULES__", json.dumps(modules).replace('<', '\\u003c')),
                                     encoding="utf-8")
    (DEST / ".nojekyll").touch()
    # Check all literal local href/src references before publishing.
    for page in DEST.rglob("*.html"):
        for reference in re.findall(r'(?:href|src)=[\"\']([^\"\']+)', page.read_text(encoding="utf-8")):
            if reference.startswith(("#", "http:", "https:", "data:")):
                continue
            target = (page.parent / reference.split("?")[0].split("#")[0]).resolve()
            if not target.is_relative_to(DEST.resolve()) or not target.is_file():
                raise ValueError(f"Broken public demo link: {page}: {reference}")
    print(f"Public demo built and local links checked: {DEST}")


if __name__ == "__main__":
    main()
