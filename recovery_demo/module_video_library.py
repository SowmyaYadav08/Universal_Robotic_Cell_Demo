"""Create local preview sheets from explicitly approved module recordings."""
import argparse
import html
import json
import math
from pathlib import Path

import cv2
import numpy as np

VIDEO_ROOT = Path("S:/Hackathon/Videos (5)/Videos")
PAIRS = [
    ("Prefilter", "Bearing pickup", "01_prefilter_labeled", "prefilter_good_bearingpick.mp4", "prefilter_bad_bearingpick.mp4"),
    ("Prefilter", "Bearing pressing", "01_prefilter_labeled", "prefilter_good_bearingpress_1.mp4", "prefilter_bad_bearingpress_1.mp4"),
    ("Tube Interface", "Component handling", "05_tubeinterface_labeled", "tubeinterface_good_dropped_1.mp4", "tubeinterface_bad_dropped_1.mp4"),
    ("Tube Interface", "Screwing", "05_tubeinterface_labeled", "tubeinterface_good_screwing.mp4", "tubeinterface_bad_screwing.mp4"),
]


def preview(video, output, basename, samples):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video}")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if not math.isfinite(fps) or not math.isfinite(count) or fps <= 0 or count <= 0:
            raise ValueError(f"Invalid timing metadata: {video.name}")
        duration = count/fps
        requested = np.linspace(0,max(0,duration-1/fps),samples)
        tiles, frames = [], []
        width = height = None
        for index,t in enumerate(requested):
            cap.set(cv2.CAP_PROP_POS_FRAMES,round(float(t)*fps))
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError(f"Could not read requested {t:.2f}s in {video.name}")
            height,width = frame.shape[:2]
            name = f"{basename}_{index+1:02d}.jpg"
            # Preserve aspect ratio; retain an original-resolution frame for ROI setup.
            if not cv2.imwrite(str(output/name),frame):
                raise RuntimeError("Could not save preview frame")
            tile = np.full((260,400,3),245,dtype=np.uint8)
            scale = min(400/width,225/height)
            small = cv2.resize(frame,(round(width*scale),round(height*scale)),interpolation=cv2.INTER_AREA)
            top,left = (225-small.shape[0])//2,(400-small.shape[1])//2
            tile[top:top+small.shape[0],left:left+small.shape[1]] = small
            cv2.putText(tile,f"Frame {index+1} | requested {t:.2f}s",(10,248),cv2.FONT_HERSHEY_SIMPLEX,0.5,(30,50,70),1)
            tiles.append(tile)
            frames.append({"image":name,"requested_time_sec":round(float(t),4)})
        while len(tiles)%4:
            tiles.append(np.full((260,400,3),245,dtype=np.uint8))
        sheet = cv2.vconcat([cv2.hconcat(tiles[i:i+4]) for i in range(0,len(tiles),4)])
        sheet_name = basename+"_sheet.jpg"
        if not cv2.imwrite(str(output/sheet_name),sheet):
            raise RuntimeError("Could not save preview sheet")
        return {"video":str(video),"duration_sec":duration,"fps":fps,"width":width,"height":height,
                "sheet":sheet_name,"frames":frames,"timestamps":"requested seek times; not verified event boundaries"}
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples",type=int,default=8)
    parser.add_argument("--module",choices=("Prefilter","Tube Interface","all"),default="all")
    parser.add_argument("--output-dir",type=Path,default=Path(__file__).resolve().parent/"outputs/module_video_library")
    args = parser.parse_args()
    if not 4 <= args.samples <= 16:
        parser.error("Use 4 to 16 pictures per clip")
    args.output_dir.mkdir(parents=True,exist_ok=True)
    records, cards = [], []
    for pair_index,(module,operation,folder,good,bad) in enumerate(PAIRS,1):
        if args.module != "all" and module != args.module:
            continue
        pair_html = []
        for category,filename in (("Normal-labeled",good),("Failure-labeled",bad)):
            print(f"{module} | {operation} | {filename}: extracting {args.samples} previews...",flush=True)
            record = preview(VIDEO_ROOT/folder/filename,args.output_dir,
                             f"pair_{pair_index}_{'normal' if filename == good else 'failure'}",args.samples)
            record.update(module=module,operation=operation,filename_label=category,visually_verified=False)
            records.append(record)
            esc = html.escape
            frame_links = ' · '.join(f'<a href="{esc(frame["image"])}">{frame["requested_time_sec"]:.2f}s</a>' for frame in record["frames"])
            pair_html.append(f'<article><h3>{esc(category)} recording</h3><p>{esc(filename)} | {record["duration_sec"]:.1f} seconds | {record["width"]}×{record["height"]}</p><a href="{esc(record["sheet"])}"><img src="{esc(record["sheet"])}" alt="{esc(module+": "+operation+" "+category)} preview sheet"></a><details><summary>Open individual full-size pictures</summary>{frame_links}</details></article>')
        cards.append(f'<section><h2>{html.escape(module)} — {html.escape(operation)}</h2>'+''.join(pair_html)+'</section>')
    summary = {"source":"approved_local_recordings","mode":"preview_only","records":records,
               "limitations":"Good/bad labels come from filenames. Preview images are not detector predictions. No process reconstruction, fault confirmation, automatic recovery, or physical commands have been performed."}
    (args.output_dir/"video_inventory.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    from library_report import render_library
    (args.output_dir/"library.html").write_text(render_library(summary),encoding="utf-8")
    print(f"Finished: {len(records)} clips. Open {args.output_dir/'library.html'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError,RuntimeError,ValueError) as error:
        print(f"Preview preparation did not finish: {error}")
        print("No video findings are claimed. Check the video paths and local OpenCV environment.")
        raise SystemExit(1)


