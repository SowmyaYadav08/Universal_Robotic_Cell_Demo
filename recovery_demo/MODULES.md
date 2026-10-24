# Assembly module coverage

## Run the three-module synthetic monitor

```powershell
python recovery_demo/run_demo.py
python -m unittest discover -s recovery_demo -p "test_*.py" -v
```

Open outputs/dashboard.html. Select Light Localizer, Prefilter, or Tube Interface.
There are 30 synthetic cases: the existing 20 Light Localizer cases plus five
Prefilter and five Tube Interface examples. Only modules represented in results
appear in the filters and charts. This does not upload or open manufacturing videos.

| Module | Synthetic workflow | Cases added | Recovery coverage |
| --- | --- | --- | --- |
| Light Localizer | Pick, transport, stack, verify | Existing cases | Conditional replacement simulation |
| Prefilter | Pick bearing, transport, position, press, verify | Normal, failed pickup, incomplete press, cleared delay, low stock | Faults held; automatic press recovery not defined |
| Tube Interface | Pick, transport, position, screw, verify | Normal, dropped component, incomplete screwing, restored feedback, low stock | Faults held; fastening recovery not defined |

The new stage sequences are explicit synthetic assumptions, not a process
reconstruction from videos. Module-specific force, seating, torque and sensor
assignments are unknown. No actual tool, robot or PLC is commanded. Generic
operations are counted separately from the Light Localizer's two plate placements.

## Video inventory — filenames only so far

Prefilter folder: S:/Hackathon/Videos (5)/Videos/01_prefilter_labeled

- prefilter_good_bearingpick.mp4 / prefilter_bad_bearingpick.mp4
- prefilter_good_bearingpress_1.mp4 / prefilter_bad_bearingpress_1.mp4
- prefilter_good_1.mp4 / prefilter_bad_1.mp4
- 01_prefilter_good_01.mp4

Tube Interface folder: S:/Hackathon/Videos (5)/Videos/05_tubeinterface_labeled

- tubeinterface_good_dropped_1.mp4 / tubeinterface_bad_dropped_1.mp4
- tubeinterface_good_screwing.mp4 / tubeinterface_bad_screwing.mp4
- 05_tubeinterface_good_01.mp4 / tubeinterface_bad_1.mp4

Names suggest paired examples but do not establish event labels. The user approved both folders as non-confidential. Footage has not yet been visually inspected; preview extraction requires the working Python terminal. Other module folders contain apparently normal-only recordings for
Bottom Sheet, Drive Unit and Module Carrier; those have not been inspected.

## Next for real-video detection

Video approval is recorded. Next: extract a small contact sheet, confirm the actual process
and visible defect, configure module-specific ROIs, then evaluate normal/failure
recordings. The Light Localizer optical-flow thresholds and coordinates must not
be assumed valid for another camera view or operation. The DINOv2 comparison
experiment remains separate and unchanged.

