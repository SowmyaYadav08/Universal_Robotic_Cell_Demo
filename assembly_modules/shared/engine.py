"""Module-specific synthetic examples; not inferred from recordings or real sensors."""
from dataclasses import dataclass

from .timing import summarize_timing


@dataclass(frozen=True)
class ModuleCase:
    name: str
    module: str
    defect: str
    priority: str
    issue: str
    action: str
    stages: tuple


def run_module_case(case):
    held = case.priority == "high"
    failed_stage = {"pickup_failure":"pickup", "component_drop":"transport",
                    "press_incomplete":"bearing_press", "screwing_incomplete":"screwing"}.get(case.defect)
    events = []
    clock = 0.0
    confirmed = 0
    def emit(event, stage, message):
        events.append({"scenario":case.name, "time_sec":clock, "module":case.module, "cycle":1,
                       "event":event, "stage":stage, "message":message,
                       "confirmed_placements":0, "confirmed_operations":confirmed,
                       "source":"synthetic_module_observations", "case_priority":case.priority,
                       "case_status":"open" if case.defect != "none" else "completed"})
    emit("cycle_started", "pickup", "Begin synthetic module cycle; no physical robot command")
    for stage in case.stages:
        clock += 1.0
        emit("stage_observed", stage, f"Simulated stage: {stage.replace('_',' ')}")
        if held and stage == failed_stage:
            emit("defect_detected", stage, case.issue)
            emit("pause_started", "paused", "Pause synthetic motion")
            clock += 2.0
            emit("pause_finished", "hold", "A pause does not authorize an undefined recovery")
            emit("manual_intervention", "hold", case.action)
            break
    if not held:
        confirmed = 1
        emit("operation_confirmed", "verification", "One module operation confirmed in simulation, not two stacked plates")
        if case.defect != "none":
            emit("advisory", "completion", case.action)
        emit("assembly_completed", "completion", "Synthetic module operation completed")
    result = {"scenario":case.name,"module":case.module,"defect":case.defect,"priority":case.priority,
              "status":"open" if case.defect != "none" else "completed",
              "outcome":"intervention_required" if held else "completed_with_warning" if case.defect != "none" else "completed",
              "issue_label":case.issue,"confirmed_placements":0,"confirmed_operations":confirmed,
              "expected_operations":1,"retries":0,"simulated_pause_sec":2 if held else 0,
              "simulated_duration_sec":clock,"events":events,
              "observations":{"mode":"scripted_synthetic", "stages":case.stages,
                              "real_sensor_assignments_verified":False,"automatic_recovery_implemented":False}}
    result["timing"] = summarize_timing(result)
    return result

