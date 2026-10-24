"""Run with Python standard library only; creates logs and an offline HTML report."""
import argparse
import csv
import json
from pathlib import Path

from recovery import run_scenario
from simulator import scenarios


from report import render_report, render_playback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "outputs")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = [run_scenario(s) for s in scenarios()]
    (args.output_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    timing_rows = [{"scenario": r["scenario"], "module": r["module"], "outcome": r["outcome"],
                    **r["timing"]} for r in results]
    with (args.output_dir / "timings.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(timing_rows[0]))
        writer.writeheader()
        writer.writerows(timing_rows)
    events = [e for r in results for e in r["events"]]
    with (args.output_dir / "events.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(dict.fromkeys(key for event in events for key in event)))
        writer.writeheader()
        writer.writerows(events)
    (args.output_dir / "dashboard.html").write_text(render_report(results), encoding="utf-8")
    (args.output_dir / "recovery_playback.html").write_text(render_playback(results), encoding="utf-8")
    for r in results:
        count = r.get("confirmed_operations", r["confirmed_placements"])
        total = r.get("expected_operations", 2)
        print(f'{r["module"]} | {r["scenario"]}: {r["outcome"]}; verified={count}/{total}; retries={r["retries"]}')
    print(f'Open report: {args.output_dir / "dashboard.html"}')


if __name__ == "__main__":
    main()

