# Light Localizer fishbone diagram

- light_localizer_fishbone.svg: editable 1920x1080 vector graphic; recommended for slides.
- light_localizer_fishbone.png: 3840x2160 raster graphic for broad compatibility.
- create_fishbone.ps1: local reproducible renderer; uses Windows System.Drawing.

The diagram addresses observed plate loss during transport and the resulting
process interruption. Gripper, control, motion and contact branches are possible
physical/sequence causes. Sensing and recovery branches describe detection and
response gaps that can prolong interruption, not established causes of the drop.
The video does not establish retention force, controller release timing, contact
condition or trajectory settings. Every branch is an investigation hypothesis.
Sensor-list context supports distinguishing endpoint/tool/fixture feedback from
direct retention measurement. No new manufacturing footage was accessed for this diagram.

In a presentation, say: "We observed the loss; this diagram organizes the causes
and process gaps to investigate. We have not confirmed a physical root cause."

The main SVG/PNG now use one key point per branch for presentation readability. The earlier three-point version is preserved as light_localizer_fishbone_detailed.svg/.png.
