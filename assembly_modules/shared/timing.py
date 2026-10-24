"""Timing from simulated event timestamps, not physical robot measurements."""


def summarize_timing(result):
    events = result["events"]
    def first(kind):
        return next((float(e["time_sec"]) for e in events if e["event"] == kind), None)
    def difference(start, end):
        a, b = first(start), first(end)
        return round(b-a, 2) if a is not None and b is not None else None
    return {
        "source": "simulated_event_clock",
        "elapsed_process_sec": round(float(events[-1]["time_sec"])-float(events[0]["time_sec"]), 2) if events else 0,
        "pause_sec": difference("pause_started", "pause_finished"),
        "drop_to_recovery_sec": difference("defect_detected", "recovery_completed"),
        "after_pause_to_recovery_sec": difference("pause_finished", "recovery_completed"),
        "until_manual_hold_sec": difference("defect_detected", "manual_intervention"),
        "check_duration_sec": None,
        "note": "Checks have no modeled duration. Open holds exclude future operator time. This is not measured factory downtime."
    }
