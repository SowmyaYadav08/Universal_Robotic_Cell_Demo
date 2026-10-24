"""Scripted synthetic observations and PLC feedback; no camera or robot connection."""
from dataclasses import dataclass, replace
from typing import Optional


@dataclass(frozen=True)
class Scenario:
    name: str
    defect: str = "none"
    first_plate_correct: Optional[bool] = True
    gripper_empty: Optional[bool] = True
    workspace_clear: Optional[bool] = True
    correct_tool: Optional[bool] = True
    cylinder_position: str = "fully_in"
    fixture_present: Optional[bool] = True
    sensor_age_sec: float = 0.1
    replacement_available: bool = True
    retry_succeeds: bool = True
    module: str = "Light Localizer"
    advisory: str = ""


def scenarios():
    drop = Scenario("drop_recovered", defect="component_drop")
    return [
        Scenario("normal"), drop,
        replace(drop, name="first_plate_displaced", first_plate_correct=False),
        replace(drop, name="workspace_obstructed", workspace_clear=False),
        replace(drop, name="visibility_uncertain", gripper_empty=None),
        replace(drop, name="wrong_tool", correct_tool=False),
        replace(drop, name="stale_sensor", sensor_age_sec=5.0),
        replace(drop, name="contradictory_cylinder", cylinder_position="contradictory"),
        replace(drop, name="fixture_presence_unknown", fixture_present=None),
        replace(drop, name="replacement_unavailable", replacement_available=False),
        replace(drop, name="retry_exhausted", retry_succeeds=False),
        Scenario("incorrect_position", defect="incorrect_position"),
        Scenario("incomplete_placement", defect="incomplete_placement"),
        Scenario("unexpected_delay", defect="unexpected_delay"),
        replace(drop, name="gripper_not_empty", gripper_empty=False),
        replace(drop, name="tool_identity_unknown", correct_tool=None),
        Scenario("short_delay_cleared", advisory="short_delay_cleared"),
        Scenario("sensor_feedback_restored", advisory="sensor_feedback_restored"),
        Scenario("rack_stock_low", advisory="rack_stock_low"),
        Scenario("minor_cycle_variation", advisory="minor_cycle_variation"),
    ]
