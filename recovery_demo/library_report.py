"""Captioned module preview report; annotations describe visible poses, not fault truth."""
import html
import json
from pathlib import Path


def render_library(summary):
    captions = json.loads(Path(__file__).with_name("image_captions.json").read_text(encoding="utf-8-sig"))
    esc = lambda value: html.escape(str(value))
    cards = []
    for record in summary["records"]:
        filename = record["video"].replace('\\','/').rsplit('/',1)[-1]
        module, operation = record["module"], record["operation"]
        clip_label = record["filename_label"]
        overview = captions["clip_overviews"].get(filename,"Overview of this recorded operation.")
        guide = captions["operation_guides"].get(operation,"Compare the tool, component and fixture.")
        notes = captions["sample_notes"].get(filename,[]) if len(record["frames"]) == 8 else []
        figures = []
        for index,frame in enumerate(record["frames"]):
            title = f'{module} — {operation} — frame {index+1}, {frame["requested_time_sec"]:.2f}s'
            description = notes[index] if index < len(notes) else guide
            figures.append(f'<figure><a href="{esc(frame["image"])}"><img loading="lazy" src="{esc(frame["image"])}" alt="{esc(title)}"></a><figcaption><strong>{esc(title)}</strong><p>{esc(description)}</p></figcaption></figure>')
        cards.append(f'<section><h2>{esc(module)} — {esc(operation)}</h2><p class="badge">{esc(clip_label)} recording · label from filename</p><p><strong>What the sequence shows:</strong> {esc(overview)}</p><figure><a href="{esc(record["sheet"])}"><img src="{esc(record["sheet"])}" alt="{esc(module+": "+operation+" overview sequence")}"></a><figcaption>{esc(operation)}: {len(record["frames"])} sampled pictures across {record["duration_sec"]:.1f} seconds. Read left to right, then the next row.</figcaption></figure><p><strong>What to look for:</strong> {esc(guide)}</p><details><summary>See each picture with its description</summary><div class="frames">'+''.join(figures)+f'</div></details><p class="small">Source: {esc(filename)}. Times are requested video seek times. Captions describe preview observations, not verified fault labels or sensor measurements.</p></section>')
    modules = sorted({r["module"] for r in summary["records"]})
    title = modules[0]+" Video Library" if len(modules) == 1 else "Module Video Library"
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>body{font:17px system-ui;max-width:1200px;margin:30px auto;padding:20px;background:#f2f7fb;color:#20354b}section{background:white;border-radius:12px;padding:24px;margin:24px 0}img{width:100%;border:1px solid #ddd;border-radius:7px}figure{margin:0}figcaption{padding:10px 0;line-height:1.5}.frames{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:20px}.badge{display:inline-block;padding:6px 12px;background:#e5f1f6;border-radius:6px}.small{font-size:14px;color:#5e7083}a{color:#006d7a}summary{cursor:pointer;font-weight:650;padding:12px 0}p{line-height:1.5}@media(max-width:700px){.frames{grid-template-columns:1fr}}</style><h1>'+esc(title)+'</h1><p>Each sequence now has a title and a description. Expand the individual pictures to read what is visible at each sampled time. Click a picture for full size.</p><p>Normal/failure labels come from filenames. Still pictures can suggest motion or a pause, but do not establish pickup success, bearing seating, torque or the exact time of a fault.</p>'+''.join(cards)+'</html>'
