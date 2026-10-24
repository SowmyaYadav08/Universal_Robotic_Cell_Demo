"""Compare review candidates with manually verified, non-overlapping intervals."""
import argparse
import csv
import json
import math
from pathlib import Path


def evaluate(events, intervals):
    if not intervals:
        raise ValueError("No reviewed intervals: fill reference_intervals.csv first")
    clean = []
    for row in intervals:
        start, end = float(row["start_sec"]), float(row["end_sec"])
        if not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end:
            raise ValueError("Intervals require finite 0 <= start < end")
        if row["label"] not in {"drop", "no_drop"} or row["verified"].lower() != "yes":
            raise ValueError("Each interval needs label drop/no_drop and verified=yes")
        clean.append((row["video"], start, end, row["label"]))
    clean.sort()
    for a, b in zip(clean, clean[1:]):
        if a[0] == b[0] and a[2] > b[1]:
            raise ValueError("Reviewed intervals must not overlap")
    hits = misses = false_alarms = duplicates = unreviewed = 0
    used = set()
    delays = []
    for video, start, end, label in clean:
        matching = [(i, float(e["timestamp_sec"])) for i, e in enumerate(events)
                    if e["video"] == video and start <= float(e["timestamp_sec"]) < end]
        used.update(i for i, _ in matching)
        if label == "drop":
            if matching:
                hits += 1
                duplicates += len(matching)-1
                delays.append(min(t for _, t in matching)-start)
            else:
                misses += 1
        else:
            false_alarms += len(matching)
    unreviewed = len(events)-len(used)
    return {"scope": "manually reviewed intervals only; motion candidates are not confirmed classifications",
            "drop_intervals_found": hits, "drop_intervals_missed": misses,
            "candidates_in_no_drop_intervals": false_alarms,
            "duplicate_candidates_in_drop_intervals": duplicates,
            "candidates_outside_reviewed_intervals": unreviewed,
            "delay_from_interval_start_sec": delays,
            "interval_recall": hits/(hits+misses) if hits+misses else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).with_name("outputs") / "real_video_review"
    parser.add_argument("--events", type=Path, default=base / "review_events.csv")
    parser.add_argument("--reference", type=Path, default=Path(__file__).with_name("reference_intervals.csv"))
    args = parser.parse_args()
    try:
        with args.events.open(newline="", encoding="utf-8-sig") as stream:
            events = list(csv.DictReader(stream))
        with args.reference.open(newline="", encoding="utf-8-sig") as stream:
            intervals = list(csv.DictReader(stream))
    except OSError as error:
        print(f"Could not open an input file: {error.filename}")
        print("First run: python recovery_demo/review_real_videos.py")
        print("Then check that recovery_demo/reference_intervals.csv exists.")
        return 1
    print(f"The video reviewer found {len(events)} moment(s) to check.")
    for event in events:
        print(f'  {event["video"]}: {float(event["timestamp_sec"]):.2f} seconds')
    if not intervals:
        report = {"status": "waiting_for_human_review", "accuracy_checked": False,
                  "message": "No confirmed event times have been entered. This is not a detector failure or a passing accuracy result."}
        (args.events.parent / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("\nAccuracy has NOT been checked yet. Nothing is broken.")
        print("The reference file is empty. It needs times that someone has checked in the original video.")
        print("1. Open recovery_demo/outputs/real_video_review/review.html.")
        print("2. Inspect the pictures and replay that part of the original recording.")
        print("3. Record checked time ranges in recovery_demo/reference_intervals.csv.")
        print("   Columns: video, start_sec, end_sec, label, verified")
        print("   label: drop or no_drop. verified: yes only after checking the recording.")
        print("4. Run this command again. Do not guess the times or copy an alert as proof.")
        return 0
    try:
        report = evaluate(events, intervals)
    except (ValueError, KeyError) as error:
        print(f"Please correct the reference file: {error}")
        print("Use start/end times in seconds, label drop or no_drop, and verified=yes.")
        return 1
    report["status"] = "evaluated_reviewed_intervals_only"
    (args.events.parent / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f'Checked drop intervals found: {report["drop_intervals_found"]}')
    print(f'Checked drop intervals missed: {report["drop_intervals_missed"]}')
    print(f'Alerts during checked no-drop intervals: {report["candidates_in_no_drop_intervals"]}')
    print(f'Alerts outside checked intervals (still unknown): {report["candidates_outside_reviewed_intervals"]}')
    print("These results apply only to the time ranges you checked. Details: evaluation.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
