# Assembly recovery demo — start here

## Priority and status are different

An always-visible **Issues by priority** graph compares High, Medium, and Low,
including zero-count categories. It follows module, scenario, and status filters,
but intentionally ignores the priority filter so all three levels remain visible.
The graph caption states its scope; the table still follows every filter.

Priority is urgency: High = immediate action when open, Medium = investigate,
Low = routine attention. Status is Open or Resolved. A low-priority replenishment
notice stays Open until addressed. A successfully recovered drop keeps its High
priority but becomes Resolved. The dashboard defaults to High + Open; choose
All priorities + Resolved to see completed recoveries. No-defect completion has
no issue priority and is excluded. Both fields are retained in results and logs.

## Priority examples and compact dashboard

Run `python recovery_demo/run_demo.py` to generate all 20 synthetic scenarios.
The dashboard shows short issue labels, 10 cases per page, a View button for full
details, and expandable charts. The default filter is High; use Medium, Low, or
All priorities to see other cases. The recovery animation is unchanged.

| Priority | Meaning | Added examples |
| --- | --- | --- |
| High | Task held; immediate help needed | Gripper not empty; tool identity unavailable |
| Medium | Task completed; investigate recurring issues | Brief delay cleared; sensor connection restored |
| Low | Routine attention; still Open | Rack stock low but sufficient for this task; small timing variation |

Medium/low examples are scripted advisories with confirmed simulated completion;
they do not allow failed required recovery checks to be bypassed. Every blocked
recovery remains High. Priority is also stored with results and as case_priority
in the complete event log. Counts are test cases, not live factory incidents.

## Which page should I open?

1. **Video finding:** `outputs/real_video_review/review.html` — what the computer
   noticed in the recording, when it happened, and the supporting pictures.
2. **Recovery result:** `outputs/video_alert_replay/replay.html` — whether the
   simulated replacement completed, the pause duration, and replacement attempts.
3. **Watch replacement:** the button on the recovery result page opens the existing
   stacked-plate animation. Its behavior is unchanged.
4. **Management dashboard:** `outputs/dashboard.html` — compare simulated cases
   by module and priority. It is separate from the real-video evidence.

The first two reports now keep detailed measurements in an optional section and
separate real recorded evidence from simulated checks and actions. Their layouts
are in templates/video_review.html and templates/replay_report.html.

## Replay a video alert through simulated recovery

```powershell
python recovery_demo/replay_video_alert.py
```

Open `recovery_demo/outputs/video_alert_replay/replay.html`. The command reads a
saved real-video motion alert, automatically runs a synthetic all-checks-pass
recovery scenario, and provides a replacement-pickup animation and event log.
No timestamp annotation is required for this demonstration. The real alert remains
unconfirmed; treating it as a drop is an explicit simulation assumption.

To demonstrate a blocked recovery instead:

```powershell
python recovery_demo/replay_video_alert.py --checks blocked
```

Use `--checks unknown` for uncertain workspace clearance. Both hold without a
replacement pickup. Commands overwrite the latest replay report. Real-video time
is recorded separately from simulated elapsed time. No physical robot is controlled.
Running evaluation still requires independently checked reference intervals.

## What do the results mean?

- **Dashboard:** shows simulated assembly problems and whether a person needs to help.
- **Watch simulated recovery:** illustrates the robot returning to the rack and
  replacing a dropped plate. No real robot is controlled.
- **Real-video review:** shows moments in the actual recording that need checking.
  An alert means "look here", not "a drop has been proved".
- **Evaluation:** compares alerts with times checked by a person. If the reference
  file is empty, accuracy has not been checked; this is not a program failure.

The latest saved real-video run found one alert at **11.50 seconds**, with no alerts
on the normal recording used for setup. That is a result of this run, not proof
that future videos will be handled correctly. Open the before/after pictures and
replay the original footage to confirm what happened.

Start with `python recovery_demo/run_demo.py` for the simulated dashboard, or
`python recovery_demo/review_real_videos.py` for the real-video review. Only run
`python recovery_demo/evaluate_real_review.py` after entering checked time ranges
in `reference_intervals.csv`. Machine-readable field names in CSV/JSON are retained
for compatibility; the reports explain them in ordinary language.

## New: approved real-video review

The optional reviewer scans both approved Light Localizer recordings without
receiving a failure timestamp. It uses CPU OpenCV optical flow, a forward/backward
tracking check, and the existing transport ROI. No downloads or services are used.

```powershell
python recovery_demo/review_real_videos.py
```

Open `recovery_demo/outputs/real_video_review/review.html`. It includes candidate
timestamps and real evidence frames. Normal footage calibrates a percentile
threshold; failure footage is reviewed for sustained unusual downward relative
motion. All motion measurements and tracking coverage are saved in CSV/JSON.
The reviewer also checks brief bursts: the speed must exceed both twice the
sustained threshold and 1.5 times the largest normal calibration score, with at
least six supporting downward tracks and an 8% support fraction. These tunable
defaults are hypotheses, not validated operating thresholds. Before/candidate/after
frames are saved for review. Normal calibration candidate counts are reported as
an in-sample diagnostic only; the burst threshold exceeds those scores by design.
The threshold and ROI are in `review_config.json`. The entry point restricts input
to the two approved files. Logs are separate from synthetic scenario results.

These are unvalidated motion candidates, not recognized plate drops. Optical-flow
clusters do not establish plate/gripper identity or process stage. The normal
recording is calibration data, not an independent validation set. A zero-candidate
result does not establish normal assembly. Recovery is never authorized from this
reviewer. It does not use MobileNet; the original MobileNet experiments remain
separate until an appearance adapter is implemented and evaluated.

After inspecting the recordings, fill `reference_intervals.csv` with non-overlapping
reviewed intervals: video filename, start/end seconds, label `drop` or `no_drop`,
and `verified=yes`. Drop intervals should begin at the observed drop onset and
cover a reasonable detection window. Leave unknown portions unannotated. The CSV
is intentionally header-only: no unverified timestamps have been invented.

```powershell
python recovery_demo/evaluate_real_review.py
```

Evaluation reports drop-interval hits/misses, candidates in no-drop intervals,
duplicates, unreviewed candidates, and delay measured from interval start.
It refuses to produce metrics without verified annotations. This does not establish
performance outside reviewed intervals or on independent recordings.

The other five modules and physical robot/PLC integration remain unimplemented.
Only the two specified Light Localizer recordings are approved for this reviewer.

This demonstrates a decision-making workflow, not automatic detection in camera
images. All defect observations and PLC readings are scripted synthetic inputs.
No robot, PLC, external service, real video, or model download is accessed.

## Run

From the workspace terminal with a working Python interpreter:

```powershell
python recovery_demo/run_demo.py
python -m unittest discover -s recovery_demo -p "test_*.py" -v
```

Only the Python standard library is needed. Open
`recovery_demo/outputs/dashboard.html` in your browser afterward. No web server
or installation is needed. The compact dashboard lists only scenarios ending in
manual intervention. All defects, checks, and successful recoveries remain in
`events.csv` (Excel compatible); `results.json` contains all inputs and results.
Rerunning overwrites these generated reports.

The dashboard includes bar charts of urgent cases by defect and by module. Each
held scenario counts once under its initiating defect. Module labels flow from
the scenario into results and CSV events; additional modules appear when their
scenarios are implemented and run, not as fabricated zero-result modules. Counts
are synthetic test counts, not measured production rates or cross-module rankings.
After a code change, rerun run_demo.py and refresh the HTML page to see new charts.

Use **Module** to select an assembly module and **Priority / action** to select
**High - immediate intervention**, **Low - routine attention**, or **All defects**.
The default is High + Open. Both charts, the count summary, and the table update together.
High means the simulated task is on hold and needs a person, not that a plate
drop is always high severity. The Scenario filter identifies recovery blockers
such as a wrong tool, old sensor data, obstruction, or failed replacement. The
Starting problem column keeps the initiating defect separate from that reason.
The second chart groups by scenario by default; choose Assembly module to compare
modules instead. Incorrect position, incomplete mounting and delays are included
as held scenarios too. These are synthetic cases, not live incident records.
Choose Light Localizer and All defects to see its unresolved and recovered cases.
Normal cases are excluded because they have no defect. Reset filters restores the
urgent view. Downloads always contain the full unfiltered log. Filtering runs
locally in the browser and requires JavaScript; no network is used.

Select **Watch simulated recovery** to open `recovery_playback.html`. Play, pause,
step, or scrub through the successful drop-recovery scenario: return empty to
supply, pick replacement, transport, release, withdraw, and verify. Plate 1
remains mounted. This is a scripted illustration of logged actions, not a robot
motion planner, camera detector, or controller integration.

The playback represents two stacked layers on one housing: plate 1 is the lower
layer and the replacement for plate 2 becomes the upper layer. The arm, gripper,
rack, housing, and plates are labeled. Expand Original assembly photos for
reference to see the previously approved scene and mounting-region extracts.
The recovery policy's position 1/2 refers to layer 1/2 in this two-plate case.

## What happens

Plate 1 is initially mounted. During plate 2 handling, a scripted defect may
occur. The policy logs the defect, simulates a two-second pause, and checks
whether recovery can proceed. No actual waiting or robot commands occur.

For a drop, retry requires all of these simulated observations: first plate
still positioned, empty gripper, clear workspace, correct tool, expected cylinder
endpoint, occupied first fixture, fresh sensor feedback, and a replacement plate.
Unknown/contradictory/stale required feedback blocks recovery. One retry is allowed.
Incorrect position, incomplete placement, and delay are logged and held for manual
intervention; they do not have an automatic recovery policy yet.

Fourteen scenarios cover normal completion, successful drop recovery, displaced
first plate, obstruction, uncertain visibility, wrong tool, stale feedback,
contradictory cylinder contacts, unknown fixture presence, unavailable replacement,
exhausted retry, and the other three defect categories.

## Sensors and assumptions

Reed contacts indicate cylinder endpoints, not grip force. RFID checks tool
identity. Hall sensing is assumed on the first fixture for this simulation only;
actual Light Localizer sensor assignments are unverified. The expected recovery
cylinder endpoint is configured here as fully_in, not a universal robot rule.
Empty-gripper, first-plate position, and workspace-clear observations are simulated
vision signals, not measurements supplied by the sensor list.

`sensor_mapping.json` documents the equipment mapping and limitations. The policy
currently uses an explicit synthetic schema in simulator.py; the mapping JSON is
documentation, not a live PLC adapter or executable configuration.

## How to interpret the dashboard

Charts show deliberately selected test cases, not production defect rates.
Durations are simulated; actual intervention duration is unknown. This version
does not measure visual detection accuracy, prove secure attachment, or authorize
physical restart. Independent robot safety validation and real observation
adapters are required before any physical integration. The approved real-image
gallery and earlier visual experiments remain separate supporting artifacts.


The management report is titled **Assembly Recovery Monitor**. Open recovery_demo/outputs/dashboard.html; existing links are unchanged.

See RESULTS_GUIDE.md for the names, purpose, and file location of every result.

## Process timing

The Recovery Decision Report separates pause, replacement sequence, total recovery,
and whole simulated task duration. The current successful example has a 2-second
pause, 7.5-second replacement-and-verification sequence, 9.5-second total recovery,
and 15.5-second whole task. Recovery includes the pause; do not add it twice.
These values come from the scripted event clock. Checks have no modeled duration.
Holds exclude unknown future manual work. No factory time saving is claimed.
The video report separately lists measured computer analysis runtime, not robot
cycle duration or verified detection delay. Run run_demo.py to export timings.csv
and add timing to each case's View details. Timing tests require a fresh test run.

## Added modules

See MODULES.md for Prefilter and Tube Interface scenarios, filenames and current
limits. Run run_demo.py again to regenerate the monitor with 30 synthetic cases
across three modules. Additional module video access is pending approval; these
new cases are scripted examples, not detections from the new recordings. Generic
module operations are counted separately from stacked plate placements.

## Approved new-module video previews

The user approved the Prefilter and Tube Interface folders as non-confidential.
Run `python recovery_demo/module_video_library.py`, then open
`recovery_demo/outputs/module_video_library/library.html`. It extracts eight
pictures from each of eight shorter paired clips, saves full-size pictures and
contact sheets, and records video metadata. It does not copy or alter source
videos, download anything, upload footage, or classify faults. Labels are from
filenames and must be checked against the footage. The large overview clips are
not decoded by this first preview command.

## Module separation — current organization

Prefilter and Tube Interface now live separately under assembly_modules. Run
`python assembly_modules/run_all.py` and open assembly_modules/index.html for all
three modules. Their logs and reports are separate. This original run_demo.py now
runs only Light Localizer (20 cases). Older instructions above mentioning a
combined 30-case dashboard are superseded by this separation. Existing saved
outputs are preserved; rerun the appropriate command to refresh them.

## Export the simulation as MP4

Run `python recovery_demo/export_recovery_mp4.py` from the workspace.
It reads the saved successful video-alert replay and writes
`recovery_demo/outputs/video_alert_replay/plate_replacement.mp4` at 1280x720,
20 FPS, with labels and event explanations. It also adds a download and video
player to the saved Recovery Decision Report. Refresh that report after export.

The MP4 is a local OpenCV schematic of the same robot/gripper, rack, stacked
plates and housing. It uses simulated event time, including the 2-second pause,
plus a 2-second final hold. It is not footage of a physical recovery. With the
current successful 15.5-second process the resulting clip is 17.5 seconds long.
The encoding is mp4v (MPEG-4 Part 2); browser/slide compatibility varies, so use a
local video player if embedded playback is unavailable. No downloads are required.
The exporter checks the first/last frames, frame count and dimensions before
claiming success. Rerunning overwrites the selected exported MP4 and metadata.
Future regenerated replay HTML may need a fresh export to restore its MP4 link.
Actual export remains pending in the working Python terminal.
