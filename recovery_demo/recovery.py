"""Conservative recovery policy evaluated on synthetic observations only."""
from dataclasses import asdict
import json
from timing import summarize_timing


DEFECT_GUIDANCE = {
    "component_drop": "Inspect retention, contact surfaces, release timing and trajectory; cause unconfirmed.",
    "incorrect_position": "Inspect fixture alignment and placement pose; cause unconfirmed.",
    "incomplete_placement": "Inspect component, fixture and placement sequence; cause unconfirmed.",
    "unexpected_delay": "Inspect endpoint feedback and process interruptions; cause unconfirmed.",
}

ADVISORIES = {
    "short_delay_cleared": ("medium", "Brief delay cleared; both placements confirmed. Investigate repeated delays."),
    "sensor_feedback_restored": ("medium", "Earlier feedback interruption cleared before the task completed; inspect connection history."),
    "rack_stock_low": ("low", "Enough plates for this task; replenish the rack before future tasks."),
    "minor_cycle_variation": ("low", "Cycle timing varied slightly within this synthetic example; both placements confirmed."),
}


def run_scenario(scenario, max_retries=1, pause_seconds=2.0):
    if max_retries < 0 or pause_seconds < 0:
        raise ValueError("Retry limit and pause must be nonnegative")
    if scenario.advisory and scenario.advisory not in ADVISORIES:
        raise ValueError("Unknown advisory")
    events = []
    clock = 0.0
    placements = retries = 0

    def log(event, stage, message, cycle=2, advance=0.0):
        nonlocal clock
        clock += advance
        events.append({"scenario": scenario.name, "time_sec": round(clock, 2),
                       "module": scenario.module,
                       "cycle": cycle, "event": event, "stage": stage,
                       "message": message, "confirmed_placements": placements,
                       "source": "synthetic_observations_and_PLC"})

    def finish(outcome):
        priority = "high" if outcome == "intervention_required" or scenario.defect != "none" else ADVISORIES[scenario.advisory][0] if scenario.advisory else "none"
        status = "resolved" if outcome == "recovered" else "open" if scenario.advisory or outcome == "intervention_required" else "completed"
        for event in events:
            event["case_priority"] = priority
            event["case_status"] = status
        result = {"scenario": scenario.name, "defect": scenario.advisory or scenario.defect, "outcome": outcome,
                "priority": priority,
                "status": status,
                "module": scenario.module,
                "confirmed_placements": placements, "retries": retries,
                "simulated_pause_sec": pause_seconds if scenario.defect != "none" else 0,
                "simulated_duration_sec": round(clock, 2),
                "observations": asdict(scenario), "events": events}
        result["timing"] = summarize_timing(result)
        return result

    log("cycle_started", "pickup", "Pick first plate (simulated)", cycle=1)
    placements = 1
    log("placement_confirmed", "placement_check", "First plate initially observed at target", cycle=1, advance=4)
    log("cycle_started", "transport", "Transport second plate (simulated)", advance=1)
    if scenario.defect == "none":
        placements = 2
        log("placement_confirmed", "placement_check", "Second plate observed after withdrawal", advance=3)
        log("assembly_completed", "completion", "Two visible placements confirmed")
        if scenario.advisory:
            log("advisory", "completion", ADVISORIES[scenario.advisory][1])
            return finish("completed_with_warning")
        return finish("completed")
    log("defect_detected", "transport" if scenario.defect == "component_drop" else "placement_check",
        scenario.defect + ": " + DEFECT_GUIDANCE[scenario.defect], advance=1)
    log("pause_started", "paused", "Pause simulated motion; no physical stop command")
    log("pause_finished", "recovery_check", "Elapsed pause alone does not authorize retry", advance=pause_seconds)
    log("observation_snapshot", "recovery_check", json.dumps(asdict(scenario), sort_keys=True))
    if scenario.defect != "component_drop":
        log("manual_intervention", "hold", "No validated automatic policy for this defect; inspect before continuing")
        return finish("intervention_required")
    checks = [
        (scenario.first_plate_correct is True, "First plate remains correctly positioned (synthetic vision)"),
        (scenario.gripper_empty is True, "Gripper empty (synthetic vision; not inferred from reed contacts)"),
        (scenario.workspace_clear is True, "Dropped plate clear of workspace (synthetic vision)"),
        (scenario.correct_tool is True, "Expected tool attached (synthetic RFID)"),
        (scenario.cylinder_position == "fully_in", "Recovery cylinder at configured fully_in endpoint (synthetic reed contacts)"),
        (scenario.fixture_present is True, "First fixture occupied (explicitly simulated Hall-equipped fixture)"),
        (0 <= scenario.sensor_age_sec <= 1.0, "Required feedback no older than 1 second"),
        (scenario.replacement_available is True, "Replacement plate available"),
    ]
    failed = []
    for passed, description in checks:
        log("check_passed" if passed else "check_failed", "recovery_check", description)
        if not passed:
            failed.append(description)
    if failed:
        log("manual_intervention", "hold", "Recovery blocked: " + "; ".join(failed))
        return finish("intervention_required")
    while retries < max_retries:
        retries += 1
        log("retry_started", "recovery", f"Retry {retries}: recover position 2; preserve position 1")
        log("return_to_supply", "return", "Simulated gripper returns empty to the plate supply", advance=1)
        log("replacement_picked", "pickup", "Simulated replacement plate attached to gripper", advance=1)
        log("replacement_transported", "transport", "Simulated replacement transported to position 2", advance=1)
        log("replacement_released", "placement", "Simulated gripper releases replacement at position 2", advance=1)
        log("gripper_withdrawn", "placement_check", "Simulated gripper withdraws for visual verification", advance=0.5)
        if scenario.retry_succeeds:
            placements = 2
            log("placement_confirmed", "placement_check", "Replacement visible at position 2 after withdrawal", advance=3)
            log("recovery_completed", "completion", "Both positions confirmed in simulation")
            return finish("recovered")
        log("retry_failed", "placement_check", "Replacement placement not confirmed", advance=3)
    log("manual_intervention", "hold", "Retry limit reached; automatic retry disabled")
    return finish("intervention_required")
