
# Light Localizer assembly configuration

MODULE_NAME = "light_localizer"

ASSEMBLY_STAGES = [
    "pickup",
    "transport",
    "positioning",
    "placement",
    "completion"
]

# One sequence represents one plate-placement cycle.
# Multiple cycles are allowed.

EXPECTED_SEQUENCE = ASSEMBLY_STAGES

POSSIBLE_ANOMALIES = {
    "component_drop": {
        "description": "Component lost during handling",
        "investigation": [
            "Check gripper retention",
            "Check release command timing",
            "Inspect component contact surfaces",
            "Review robot trajectory"
        ]
    },

    "incorrect_position": {
        "description": "Component position differs from expected",
        "investigation": [
            "Check fixture alignment",
            "Review robot positioning"
        ]
    },

    "incomplete_placement": {
        "description": "Placement operation not completed",
        "investigation": [
            "Inspect component and mounting fixture",
            "Review placement sequence"
        ]
    },

    "unexpected_delay": {
        "description": "Operation duration exceeds normal variation",
        "investigation": [
            "Review robot motion",
            "Check process interruptions"
        ]
    }
}


if __name__ == "__main__":
    print("Module:", MODULE_NAME)
    print("Expected sequence:")

    for stage in EXPECTED_SEQUENCE:
        print("-", stage)

    print("\nConfigured anomaly categories:")

    for anomaly in POSSIBLE_ANOMALIES:
        print("-", anomaly)

    print("\nConfiguration loaded successfully!")
