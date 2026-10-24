from assembly_modules.shared.engine import ModuleCase


def scenarios():
    stages = ("pickup", "transport", "positioning", "screwing", "verification")
    definitions = [
        ("tube_normal", "none", "none", "Normal tube assembly", "All simulated checks passed."),
        ("tube_component_drop", "component_drop", "high", "Tube component dropped", "Hold. Check part location, fixture and retention; tube-specific recovery is not defined."),
        ("tube_screwing_incomplete", "screwing_incomplete", "high", "Screwing not completed", "Hold. Inspect engagement, thread and fastening feedback; torque verification is unavailable."),
        ("tube_feedback_restored", "feedback_restored", "medium", "Tool feedback restored", "Synthetic feedback restored before completion. Investigate reliability."),
        ("tube_supply_low", "supply_low", "low", "Tube component supply low", "Enough for this synthetic cycle. Replenish for future cycles."),
    ]
    return [ModuleCase(name,"Tube Interface",defect,priority,issue,action,stages) for name,defect,priority,issue,action in definitions]
