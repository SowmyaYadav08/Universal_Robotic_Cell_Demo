"""Readable summaries for video findings and simulated recovery outcomes."""
import html
import re
from pathlib import Path
from timing import summarize_timing

TEMPLATES = Path(__file__).with_name("templates")


def fill_template(name, values):
    template = (TEMPLATES / name).read_text(encoding="utf-8")
    return re.sub(r"__[A-Z_]+__", lambda match: values[match.group(0)[2:-2]], template)


def render_review(summary):
    esc = lambda value: html.escape(str(value))
    events = summary["events"]
    cards = []
    for event in events:
        captions = (("before_image", "Before the alert", "Previous sampled frame: compare the plate and gripper."),
                    ("evidence_image", "At the alert", "The sampled frame that triggered the motion warning."),
                    ("after_image", "After the alert", "Next sampled frame: look for where the plate moved."))
        pictures = ''.join(f'<figure><a href="{esc(event[key])}"><img src="{esc(event[key])}" alt="{label} video frame"></a><figcaption><strong>{label}</strong>{text}</figcaption></figure>'
                           for key, label, text in captions if event.get(key))
        cards.append(f'<section><h2>Recorded evidence at {event["timestamp_sec"]:.2f} seconds</h2><p>The program saw unusual downward movement. It has not confirmed which object moved.</p><div class="pictures">{pictures}</div><p class="small">These are consecutive sampled frames, not three different defects. Click any picture to enlarge it. Compare whether the plate separates from the gripper before reaching the housing.</p></section>')
    return fill_template("video_review.html", {
        "STATUS": "Possible drop — video evidence available" if events else "No motion alerts",
        "HEADLINE": f'Unusual movement was flagged at {events[0]["timestamp_sec"]:.2f} seconds.' if events else "The current rules did not flag unusual movement.",
        "EXPLANATION": "The pictures below show the moment flagged in the actual recording. Recovery is shown separately as a simulation." if events else "No alerts does not prove that assembly was correct. The detector may still miss an event.",
        "COUNT": str(len(events)),
        "TIME": f'{events[0]["timestamp_sec"]:.2f} seconds' if len(events) == 1 else "See evidence below" if events else "No alert",
        "EVIDENCE": ''.join(cards),
        "NORMAL": esc(summary.get("normal_calibration_candidate_count", "unknown")),
        "SAMPLES": esc(summary.get("total_samples", 0)),
        "UNCERTAIN": esc(summary.get("uncertain_samples", 0)),
        "ANALYSIS_TIME": f'{float(summary["elapsed_processing_sec"]):.2f} seconds' if "elapsed_processing_sec" in summary else "Not recorded",
    })


def render_replay(result):
    esc = lambda value: html.escape(str(value))
    recovered = result["outcome"] == "recovered"
    timing = summarize_timing(result)
    def seconds(value):
        return f"{value:g} seconds" if value is not None else "Not completed"
    blockers = [event["message"] for event in result["events"] if event["event"] == "check_failed"]
    if not recovered and not blockers:
        blockers = [event["message"] for event in result["events"] if event["event"] == "manual_intervention"]
    return fill_template("replay_report.html", {
        "OUTCOME": "Replacement completed in simulation" if recovered else "Task held — a person is needed",
        "MEANING": "The simulated robot returned to the rack, picked a replacement, and stacked it on the first plate." if recovered else "The simulation did not finish the replacement task. The reasons below need attention.",
        "PLACEMENTS": esc(result["confirmed_placements"]),
        "PAUSE": esc(result["simulated_pause_sec"]),
        "RETRIES": esc(result["retries"]),
        "WATCH": '<a class="button" href="recovery_playback.html">Watch Plate Replacement (Simulation)</a>' if recovered else "No successful replacement animation is available for this held outcome.",
        "TIME": f'{float(result["trigger"]["timestamp_sec"]):.2f}',
        "CHECK_SUMMARY": "All required simulated checks passed, so one replacement attempt was allowed." if recovered else "At least one required check failed, was unknown, or the retry limit was reached.",
        "BLOCKERS": '<ul>' + ''.join(f'<li>{esc(reason)}</li>' for reason in blockers) + '</ul>' if blockers else '',
        "TOTAL_TIME": seconds(timing["elapsed_process_sec"]),
        "RECOVERY_TIME": seconds(timing["drop_to_recovery_sec"]),
        "REPLACEMENT_TIME": seconds(timing["after_pause_to_recovery_sec"]),
    })

