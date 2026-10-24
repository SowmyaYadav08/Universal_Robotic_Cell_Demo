"""Render the saved stacked-plate recovery as a local MP4 using OpenCV."""
import argparse
import json
import math
from pathlib import Path
import textwrap

import cv2
import numpy as np


def target_after(state, event):
    state = dict(state)
    kind = event["event"]
    if kind == "placement_confirmed":
        if event["cycle"] == 1:
            state.update(p1=True, x=510, y=110)
        else:
            state.update(p2=True, carry=False)
    elif kind == "cycle_started" and event["cycle"] == 2:
        state.update(x=350,y=110,carry=True)
    elif kind == "defect_detected":
        state.update(carry=False,dropped=True)
    elif kind == "return_to_supply":
        state.update(x=105,y=147)
    elif kind == "replacement_picked":
        state.update(carry=True)
    elif kind == "replacement_transported":
        state.update(x=510,y=120)
    elif kind == "replacement_released":
        state.update(x=510,y=135,carry=False,p2=True)
    elif kind == "gripper_withdrawn":
        state.update(y=75)
    return state


def draw_frame(state, event, t, drop_time):
    frame = np.full((720,1280,3),(248,245,240),dtype=np.uint8)
    cv2.rectangle(frame,(0,0),(1280,90),(115,83,14),-1)
    cv2.putText(frame,"Plate Replacement Playback",(35,44),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2,cv2.LINE_AA)
    cv2.putText(frame,"SIMULATION ONLY | No physical robot control",(35,75),cv2.FONT_HERSHEY_SIMPLEX,0.6,(235,240,240),1,cv2.LINE_AA)
    scale = 1.4
    def point(x,y):
        return round(95+x*scale),round(130+y*scale)
    def rect(x,y,w,h,color):
        cv2.rectangle(frame,point(x,y),point(x+w,y+h),color,-1)
    def label(text,x,y,color=(65,50,35),size=0.52):
        cv2.putText(frame,text,point(x,y),cv2.FONT_HERSHEY_SIMPLEX,size,color,1,cv2.LINE_AA)
    x,y = state["x"],state["y"]
    arm = np.array([point(80,55),point((80+x)/2,65),point(x,y-20)],dtype=np.int32)
    cv2.polylines(frame,[arm],False,(60,130,225),22,cv2.LINE_AA)
    label("Robot arm",180,40,size=0.62)
    rect(60,210,100,20,(205,210,215))
    rect(70,190,70,12,(185,115,35))
    label("Replacement plate rack",25,260)
    rect(440,195,140,50,(180,170,160))
    label("Housing",480,275,size=0.65)
    if state["p1"]:
        rect(475,180,70,12,(185,115,35))
        label("Plate 1 - lower layer",565,192)
    if state["p2"]:
        rect(475,166,70,12,(230,175,90))
        label("Plate 2 - replacement",565,174)
    if state["dropped"]:
        fall = min(1,max(0,(t-drop_time)/0.45))
        dropped_y = 145+(285-145)*fall
        rect(300,dropped_y,70,10,(30,125,215))
        label("Dropped plate left clear",260,315,size=0.5)
    rect(x-22,y-20,44,30,(90,135,20))
    cv2.line(frame,point(x-20,y+10),point(x-20,y+30),(90,135,20),6,cv2.LINE_AA)
    cv2.line(frame,point(x+20,y+10),point(x+20,y+30),(90,135,20),6,cv2.LINE_AA)
    if state["carry"]:
        rect(x-35,y+31,70,12,(230,175,90))
    label("Gripper",x+32,y-8)
    title = event["event"].replace('_',' ').capitalize()
    if event["event"] == "pause_started":
        title = "Plate dropped - pause for 2 seconds"
    cv2.putText(frame,f"Simulated process time: {t:05.2f}s",(35,122),cv2.FONT_HERSHEY_SIMPLEX,0.63,(85,65,45),1,cv2.LINE_AA)
    cv2.rectangle(frame,(20,605),(1260,710),(255,255,255),-1)
    cv2.putText(frame,title,(35,635),cv2.FONT_HERSHEY_SIMPLEX,0.7,(100,75,20),2,cv2.LINE_AA)
    for row,line in enumerate(textwrap.wrap(event["message"],110)[:2]):
        cv2.putText(frame,line,(35,663+23*row),cv2.FONT_HERSHEY_SIMPLEX,0.52,(75,65,50),1,cv2.LINE_AA)
    return frame


def export(result, output, fps):
    events = result["events"]
    if result["outcome"] != "recovered" or not events:
        raise ValueError("Choose a successfully recovered scenario; a held task cannot be exported as success")
    if not math.isfinite(fps) or not 1 <= fps <= 60:
        raise ValueError("FPS must be between 1 and 60")
    times = [float(e["time_sec"]) for e in events]
    if any(not math.isfinite(t) or t < 0 for t in times) or times != sorted(times):
        raise ValueError("Invalid simulated event timestamps")
    output.parent.mkdir(parents=True,exist_ok=True)
    duration = times[-1]+2.0
    writer = cv2.VideoWriter(str(output),cv2.VideoWriter_fourcc(*"mp4v"),fps,(1280,720))
    if not writer.isOpened():
        raise RuntimeError("MP4 encoder could not start. No successful export is claimed.")
    state = {"x":100.,"y":130.,"p1":False,"p2":False,"carry":False,"dropped":False}
    drop_time = next(float(e["time_sec"]) for e in events if e["event"] == "defect_detected")
    index = -1
    try:
        for frame_number in range(math.ceil(duration*fps)):
            t = frame_number/fps
            while index+1 < len(events) and times[index+1] <= t:
                index += 1
                state = target_after(state,events[index])
            shown = dict(state)
            # Interpolate position only; attachment and placement flags change at
            # their logged event, so completion is never shown prematurely.
            if 0 <= index < len(events)-1 and times[index+1] > times[index]:
                next_state = target_after(state,events[index+1])
                fraction = (t-times[index])/(times[index+1]-times[index])
                shown["x"] += (next_state["x"]-state["x"])*fraction
                shown["y"] += (next_state["y"]-state["y"])*fraction
            writer.write(draw_frame(shown,events[max(0,index)],t,drop_time))
    finally:
        writer.release()
    check = cv2.VideoCapture(str(output))
    try:
        count = int(check.get(cv2.CAP_PROP_FRAME_COUNT))
        ok, first = check.read()
        check.set(cv2.CAP_PROP_POS_FRAMES,max(0,count-1))
        last_ok,_ = check.read()
        if not ok or not last_ok or first.shape[:2] != (720,1280) or count != math.ceil(duration*fps):
            raise RuntimeError("Export verification failed; do not use this MP4")
    finally:
        check.release()
    return {"file":str(output),"codec":"mp4v", "fps":fps,"width":1280,"height":720,
            "frames":count,"duration_sec":count/fps,"simulated_process_sec":times[-1],
            "closing_hold_sec":2,"physical_robot_control":False,"verified_decode":True}


def main():
    base = Path(__file__).resolve().parent/"outputs/video_alert_replay"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=base/"replay_result.json")
    parser.add_argument("--output",type=Path,default=base/"plate_replacement.mp4")
    parser.add_argument("--fps",type=float,default=20)
    args = parser.parse_args()
    result = json.loads(args.input.read_text(encoding="utf-8-sig"))
    report = export(result,args.output,args.fps)
    args.output.with_suffix('.export.json').write_text(json.dumps(report,indent=2),encoding="utf-8")
    # Add a video link only after the actual file has passed decode checks.
    html_path = args.output.parent/"replay.html"
    if html_path.exists():
        import html
        page = html_path.read_text(encoding="utf-8-sig")
        if 'id="mp4-export"' not in page:
            section = '<section id="mp4-export"><h2>MP4 playback</h2><p><a href="'+html.escape(args.output.name)+'" download>Download Plate Replacement Playback (MP4)</a></p><video controls preload="metadata" style="width:100%" src="'+html.escape(args.output.name)+'">Open the MP4 in a local video player.</video><p>Local schematic simulation. The 2-second pause follows simulated event time; the closing frame holds for 2 additional seconds.</p></section>'
            page = page.replace('</html>',section+'</html>')
            html_path.write_text(page,encoding="utf-8")
    print(f"MP4 created and decode-checked: {args.output}")
    print(f"{report['duration_sec']:.1f} seconds | 1280x720 | {args.fps:g} FPS | simulated robot actions only")
    print("If your browser does not support this codec, open the downloaded file in a local video player.")


if __name__ == "__main__":
    try:
        main()
    except (OSError,ValueError,RuntimeError,KeyError,StopIteration) as error:
        print(f"MP4 export did not finish: {error}")
        print("First create the replay with: python recovery_demo/replay_video_alert.py")
        raise SystemExit(1)
