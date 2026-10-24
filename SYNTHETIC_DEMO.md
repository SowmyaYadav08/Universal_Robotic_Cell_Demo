# Process-aware synthetic plate assembly demo

This offline demonstration uses generated colored shapes only. It does not open
manufacturing footage, contact external services, or download model weights.
The original step scripts and light_localizer_config.py are unchanged.

## Run

Use the same terminal and Python environment that ran your earlier demo:

```powershell
cd S:\Hackathon\URC_AI_Code_Workspace
python validate_synthetic_demo.py
```

Requires Python with NumPy and OpenCV. The command generates inputs, scans each
video, and evaluates results. Exit code 0 and top-level "passed": true mean all
checks passed. A failing report is retained for inspection.

Outputs go to outputs/synthetic_plate_demo_v2, preserving the earlier demo folder.
Rerunning overwrites only the named generated files in this v2 folder.

## Scenarios

Every video contains three plate cycles and separate housing slots.

| Video | Expected behavior |
| --- | --- |
| normal.avi | Three placements, no drop alarms |
| drop.avi | Cycle 2 transport drop, incomplete placement; two confirmed placements |
| occlusion.avi | Brief cycle 2 plate occlusion, uncertainty event, no drop, three placements |
| incomplete.avi | Cycle 2 plate stays with gripper during withdrawal; two placements and incomplete placement |
| normal_fast_dim.avi | Faster and dimmer normal assembly at a different frame rate |
| drop_slow.avi | Slower cycle 2 drop at a different frame rate |

Green is the gripper, blue is a plate, gray is the housing. Mounted plates remain
visible, so detecting any blue object is insufficient to confirm the next placement.

## How detection works

The detector reads video frames only. It never reads expected-event labels or
receives cycle boundaries or failure timestamps.

1. Recognize an attached plate in the configured pickup area over three frames.
2. Start a cycle and track the current plate, excluding previously mounted plates.
3. During transport, flag a relative displacement over 25 pixels persisting for
   at least 0.15 seconds. Missing observations instead produce tracking uncertainty.
4. Recognize positioning in the configured housing region.
5. After the gripper withdraws, wait 0.25 seconds and check the current target slot.
6. Log visible placement or incomplete placement; wait for a new pickup to restart.

The CSV records cycle number, timestamp, stage, visual evidence, and cumulative
confirmed placements. Drop and incomplete-placement events may both occur for the
same cycle: one describes transport behavior, the other its assembly outcome.
Unfinished recordings produce cycle_unresolved rather than a successful result.

## Results

- expected_events.csv: generator labels, used only by the validator after detection.
- events.csv: detector events; opens in Excel.
- validation_report.json: per-video checks, event delays, processing time and FPS.
- Six AVI files: fully artificial input recordings.

Validation requires exactly three cycle starts, correct placement totals, matching
event types and cycle numbers without duplicate alarms, and bounded event delays.
Drop/uncertainty delay must be within -0.1 to 1.0 seconds of labeled onset.
Placement outcomes must be within -0.1 to 1.5 seconds of release, allowing time for
withdrawal. The small negative tolerance covers frame rounding across cycle clips.
Unknown events are expected only in the occlusion scenario.

To run detection alone:

```powershell
python detect_plate_loss.py outputs/synthetic_plate_demo_v2/normal.avi outputs/synthetic_plate_demo_v2/drop.avi
```

## Limits and runtime status

These are synthetic acceptance tests, not evidence of manufacturing performance.
Geometry, color thresholds, and 640x360 resolution are specific to this scene.
The demo does not use MobileNet, prove mechanical seating, diagnose the physical
cause of a drop, or trigger robot actions. A plate visible at its target after
withdrawal is a visual placement confirmation only.

Occlusion is tested during transport. Longer occlusion, missing grippers, camera
movement, real reflections, and arbitrary plate geometries need separate tests.
Placement verification currently samples the target after a withdrawal dwell;
it does not establish continuous visibility or secure attachment.

The earlier single-cycle demo was reported to pass in the user's terminal.
The v2 suite has not yet been executed by this assistant: the workspace virtual
environment references an unavailable interpreter. A registered Windows Store
Python also returned Access denied, including outside the sandbox. Use the
working terminal above; do not treat this documentation as a passing v2 report.
