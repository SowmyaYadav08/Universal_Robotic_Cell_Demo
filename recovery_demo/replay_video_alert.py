"""Replay a real-video motion candidate through a separately simulated recovery."""
import argparse
import csv
import html
import json
from pathlib import Path

from recovery import run_scenario
from report import render_playback
from simulator import Scenario


def build_replay(candidate, checks="pass"):
    if checks not in {"pass", "blocked", "unknown"}:
        raise ValueError("Choose pass, blocked, or unknown simulated checks")
    scenario = Scenario("drop_recovered", defect="component_drop",
                        workspace_clear=False if checks == "blocked" else None if checks == "unknown" else True)
    result = run_scenario(scenario)
    for event in result["events"]:
        event["source"] = "simulated_recovery_after_unconfirmed_video_alert"
        event["video_alert_time_sec"] = float(candidate["timestamp_sec"])
    result["trigger"] = dict(candidate)
    result["trigger_confirmed_as_drop"] = False
    result["checks_source"] = "synthetic_preset_" + checks
    result["physical_robot_commands_sent"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent / "outputs"
    parser.add_argument("--summary", type=Path, default=base / "real_video_review" / "review_summary.json")
    parser.add_argument("--event-number", type=int, default=1, help="Which saved alert to replay, starting at 1")
    parser.add_argument("--checks", choices=("pass", "blocked", "unknown"), default="pass",
                        help="Synthetic recovery-check preset; these are not measured sensor readings")
    parser.add_argument("--output-dir", type=Path, default=base / "video_alert_replay")
    args = parser.parse_args()
    try:
        summary = json.loads(args.summary.read_text(encoding="utf-8-sig"))
        candidates = summary["events"]
        if not candidates:
            print("No video alerts are available to replay. No recovery was simulated.")
            print("First run: python recovery_demo/review_real_videos.py")
            return 0
        if not 1 <= args.event_number <= len(candidates):
            print(f"Choose an alert number from 1 to {len(candidates)}.")
            return 1
        candidate = candidates[args.event_number - 1]
        result = build_replay(candidate, args.checks)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Could not read a usable video alert: {error}")
        print("First run: python recovery_demo/review_real_videos.py")
        return 1
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "replay_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    trigger = {key: "" for key in result["events"][0]}
    trigger.update(scenario="video_alert", time_sec="", module=result["module"], cycle="unknown",
                   event="unconfirmed_video_motion_alert", stage="unknown",
                   message="Recorded motion candidate; not a confirmed plate drop or restart permission",
                   confirmed_placements="unknown", source="approved_real_video",
                   case_priority="review_required",
                   case_status="unconfirmed",
                   video_alert_time_sec=float(candidate["timestamp_sec"]))
    with (output / "events.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(trigger))
        writer.writeheader()
        writer.writerows([trigger] + result["events"])
    if result["outcome"] == "recovered":
        playback = (render_playback([result])
                    .replace('href="dashboard.html"', 'href="replay.html"')
                    .replace('Back to Assembly Recovery Monitor', 'Back to Recovery Decision Report')
                    .replace('../../outputs/approved_visual_references/', '../../../outputs/approved_visual_references/'))
        (output / "recovery_playback.html").write_text(playback, encoding="utf-8")
        outcome = "The simulation picked a replacement and finished both plate layers."
        playback_link = '<p><a href="recovery_playback.html">Watch replacement pickup and stacked mounting</a></p>'
    else:
        outcome = "The simulation stayed on hold because a required recovery check failed or was unknown."
        playback_link = ""
    from review_report import render_replay
    (output / "replay.html").write_text(render_replay(result), encoding="utf-8")
    print(f"Video alert: {float(candidate['timestamp_sec']):.2f} seconds (unconfirmed).")
    print(f"Recovery checks: synthetic '{args.checks}' preset.")
    print(outcome)
    print(f"Open: {output / 'replay.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


