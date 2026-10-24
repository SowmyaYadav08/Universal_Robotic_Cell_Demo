"""Build the one-entry dashboard with availability checked against local files."""
import json
from pathlib import Path


def build_hub():
    base = Path(__file__).resolve().parent
    workspace = base.parent
    modules = json.loads((base/"module_navigation.json").read_text(encoding="utf-8-sig"))
    def exists(relative):
        path = (base/relative).resolve()
        if not path.is_relative_to(workspace):
            raise ValueError("Module navigation path leaves workspace")
        return path.is_file()
    for module in modules:
        module["available"] = exists(module["dashboard"])
        for report in module["reports"]:
            report["available"] = bool(report["path"] and exists(report["path"]))
    template = (base/"hub_template.html").read_text(encoding="utf-8-sig")
    payload = json.dumps(modules).replace('<','\\u003c')
    (base/"index.html").write_text(template.replace('__MODULES__',payload),encoding="utf-8")
    return base/"index.html"


if __name__ == "__main__":
    print(f"Open {build_hub()}")
