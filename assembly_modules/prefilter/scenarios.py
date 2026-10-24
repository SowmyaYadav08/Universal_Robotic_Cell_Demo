from assembly_modules.shared.engine import ModuleCase


def scenarios():
    stages = ("pickup", "transport", "positioning", "bearing_press", "verification")
    definitions = [
        ("prefilter_normal", "none", "none", "Normal bearing assembly", "All simulated checks passed."),
        ("prefilter_pick_failed", "pickup_failure", "high", "Bearing pickup failed", "Hold. Check bearing supply and gripper retention before pressing."),
        ("prefilter_press_incomplete", "press_incomplete", "high", "Bearing press incomplete", "Hold. Inspect seating and press feedback; no force/displacement measurements are available."),
        ("prefilter_delay_cleared", "short_delay_cleared", "medium", "Bearing cycle delay cleared", "Cycle completed in simulation. Investigate recurring delays."),
        ("prefilter_stock_low", "supply_low", "low", "Bearing supply running low", "Enough for this synthetic cycle. Replenish for future cycles."),
    ]
    return [ModuleCase(name,"Prefilter",defect,priority,issue,action,stages) for name,defect,priority,issue,action in definitions]
