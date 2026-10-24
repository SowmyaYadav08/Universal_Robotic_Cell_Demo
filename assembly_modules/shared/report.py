"""Compact intervention report and separate synthetic recovery playback."""
import html
import json
from collections import Counter
from pathlib import Path
from .timing import summarize_timing

OUTCOME_LABELS = {
    "completed": "Assembly Completed",
    "recovered": "Replacement Completed",
    "intervention_required": "Manual Action Required",
    "completed_with_warning": "Completed — Follow-up Needed",
}


def bar_chart(counts, title):
    """Inline SVG: explicit counts, common zero baseline, no external library."""
    esc = lambda value: html.escape(str(value))
    maximum = max(max(counts.values(), default=0), 1)
    height = 55 + 48 * len(counts)
    parts = [f'<svg viewBox="0 0 650 {height}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>']
    for index, (label, value) in enumerate(counts.items()):
        y = 18 + index * 48
        width = value / maximum * 330
        parts.append(f'<text x="0" y="{y+19}" fill="#405169" font-size="15">{esc(label)}</text><rect x="220" y="{y}" width="330" height="28" rx="5" fill="#edf1f5"/><rect x="220" y="{y}" width="{width:.2f}" height="28" rx="5" fill="#bc3d49"><title>{esc(label)}: {value} cases</title></rect><text x="570" y="{y+20}" font-size="17" font-weight="700" fill="#172639">{value}</text>')
    axis_y = height - 14
    parts.append(f'<text x="220" y="{axis_y}" font-size="12" fill="#65748a">0</text><text x="550" y="{axis_y}" text-anchor="end" font-size="12" fill="#65748a">{maximum} cases</text></svg>')
    return ''.join(parts)


def render_report(results):
    esc = lambda value: html.escape(str(value))
    scenario_labels = json.loads(Path(__file__).with_name("scenario_labels.json").read_text(encoding="utf-8"))
    labels = {"component_drop": "Component drop", "incorrect_position": "Incorrect position",
              "incomplete_placement": "Incomplete placement", "unexpected_delay": "Unexpected delay",
              "pickup_failure": "Pickup failure", "press_incomplete": "Incomplete bearing press",
              "screwing_incomplete": "Incomplete screwing", "supply_low": "Supply running low",
              "feedback_restored": "Feedback restored"}
    records = []
    for r in results:
        if r["defect"] == "none":
            continue
        high = r["outcome"] == "intervention_required"
        event = next((e for e in reversed(r["events"]) if e["event"] == "manual_intervention"), r["events"][-1])
        records.append({"module": r.get("module", "Light Localizer"),
                        "scenario": r["scenario"].replace("_", " "),
                        "reason": r.get("issue_label", scenario_labels.get(r["scenario"], r["scenario"].replace("_", " "))),
                        "defect": labels.get(r["defect"], scenario_labels.get(r["defect"], r["defect"])),
                        "priority": r.get("priority", "high" if high or r["defect"] == "component_drop" else "low"),
                        "status": r.get("status", "resolved" if r["outcome"] == "recovered" else "open"),
                        "action": event["message"], "outcome": OUTCOME_LABELS.get(r["outcome"], r["outcome"].replace("_", " ")),
                        "timing": summarize_timing(r)})
    modules = sorted({r.get("module", "Light Localizer") for r in results})
    options = ''.join(f'<option value="{esc(module)}">{esc(module)}</option>' for module in modules)
    scenario_options = ''.join(f'<option value="{esc(reason)}">{esc(reason)}</option>' for reason in sorted({r["reason"] for r in records}))
    urgent = [r for r in records if r["priority"] == "high" and r["status"] == "open"]
    defect_chart = bar_chart(dict(Counter(r["defect"] for r in urgent)), "Manual intervention cases by defect")
    module_chart = bar_chart(dict(Counter(r["reason"] for r in urgent)), "Manual intervention cases by scenario")
    payload = json.dumps(records).replace("<", "\\u003c")
    template = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Assembly Recovery Monitor</title>
<style>body{font:16px system-ui;max-width:1260px;margin:30px auto;padding:0 20px;background:#f4f7fb;color:#182738}h1{margin-bottom:8px}h2{font-size:20px}a{color:#006c78}table{width:100%;border-collapse:collapse;background:white}td,th{padding:12px;text-align:left;border-bottom:1px solid #e2e8f0}th{background:#e4ebf0}.high{color:#a72132;font-weight:700}.resolved{color:#007868;font-weight:700}.banner{padding:16px;background:#fff0d6;margin:20px 0;border-radius:8px}.panels{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:20px 0}.panel{background:white;padding:20px;border:1px solid #e1e7ef;border-radius:12px}.panel svg{width:100%;display:block}.sub{color:#60718a;font-size:14px}.tablewrap{overflow:auto}nav,.filters{display:flex;gap:20px;flex-wrap:wrap;margin:16px 0}.filters{background:white;padding:18px;border-radius:10px}select,button{padding:10px;border:1px solid #bac8d6;border-radius:6px;margin-left:8px} @media(max-width:850px){.panels{grid-template-columns:1fr}}</style>
<style id="monitor-color-theme">
body{background:linear-gradient(135deg,#eef6fb 0%,#f3f0fb 52%,#edf8f4 100%);color:#18344b}
h1{background:linear-gradient(105deg,#075a74,#126f86,#5b4b9a);color:#fff;padding:22px 26px;border-radius:15px;box-shadow:0 7px 22px #16486818;margin-top:20px;font-size:30px}
.filters{background:#fff;border-top:4px solid #258da0;box-shadow:0 4px 15px #234b6610;align-items:center}
.filters label{color:#28516a;font-weight:600;font-size:14px}
select{background:#f0f7fc;color:#21455d;border-color:#b8d4e2;font-weight:500}
select:focus,button:focus-visible,summary:focus-visible{outline:3px solid #78b6dc;outline-offset:3px}
.banner{background:linear-gradient(110deg,#fff0ce,#fff8e8);border-left:5px solid #d18b19;color:#68460b;font-weight:650;box-shadow:0 3px 10px #9d76100b}
.panel{box-shadow:0 4px 16px #214a6410;border-color:#d4e4ed;border-top:4px solid #258da0}
.panel h2{color:#126279}
.tablewrap{border-radius:12px;border:1px solid #d3e3ee;box-shadow:0 4px 15px #25496310}
th{background:#175b73;color:#fff;font-size:14px}
tbody tr:nth-child(even){background:#f0f7fc}
tbody tr:hover{background:#e5f3f4}
td:first-child{font-weight:700}
button{background:#eaf4f8;color:#12556d;border:1px solid #b5d6e2;font-weight:600;cursor:pointer}
button:hover:not(:disabled){background:#d7edf1;border-color:#65a6b8}
button:disabled{opacity:.45;cursor:default}
#reset{background:#6553a0;color:white;border-color:#6553a0}
#reset:hover{background:#514086}
tbody button{background:#08788a;color:#fff;border-color:#08788a;padding:7px 13px}
tbody button:hover{color:#164b60}
.report-menu{background:#ffffffb8;border:1px solid #dce6ef;border-radius:10px;padding:10px 15px}
.report-menu a{background:#e9f3fa;padding:7px 11px;border-radius:7px;text-decoration:none;color:#145f7c}
.report-menu a:hover{background:#d6eaf5}
#caseDetails{background:#f7fbfe;border-top:5px solid #168795!important;box-shadow:0 20px 65px #16374f40}
#caseDetails::backdrop{background:#17304b70}
#caseDetails h2{color:#126279}
#priorityScope{color:#4f677d}
@media(prefers-reduced-motion:no-preference){button,tbody tr{transition:background .15s ease}}
</style>
<h1>Assembly Recovery Monitor</h1><p class="sub">Synthetic examples, not live tasks. Priority tells you urgency: <strong>High:</strong> immediate action when open. <strong>Medium:</strong> investigate. <strong>Low:</strong> routine attention. Status tells you whether the issue is <strong>Open</strong> or <strong>Resolved</strong>. Low does not mean resolved.</p>
<details class="report-menu" style="margin:12px 0"><summary style="cursor:pointer;color:#006c78;font-weight:600">Reports &amp; demo</summary><nav><a href="events.csv">Assembly Event Log (CSV)</a><a href="results.json">Scenario Results (JSON)</a><a href="video_library/library.html">Module Video Library (generate previews first)</a></nav></details>
<div class="filters"><label for="module">Module<select id="module"><option value="">All modules</option>__OPTIONS__</select></label>
<label for="priority">Priority<select id="priority"><option value="high" selected>High - immediate intervention</option><option value="medium">Medium - investigate</option><option value="low">Low - routine attention</option><option value="">All priorities</option></select></label><label for="status">Status<select id="status"><option value="open" selected>Open</option><option value="resolved">Resolved</option><option value="">All statuses</option></select></label><label for="scenario">Scenario<select id="scenario"><option value="">All scenarios</option>__SCENARIOS__</select></label><button id="reset">Reset filters</button></div>
<div class="banner" id="summary" role="status" aria-live="polite">__COUNT__ scenarios require operator attention. Enable JavaScript for filtering.</div>
<section class="panel" style="margin:16px 0;padding:14px 20px"><h2 style="margin:0 0 8px">Priority Overview</h2><div id="priorityChart"></div><p class="sub" id="priorityScope" style="margin:5px 0">Uses module, scenario, and status filters. The priority filter affects the table, not this comparison.</p></section>
<h2>Assembly Issue List</h2><div class="tablewrap"><table><thead><tr><th>Priority</th><th>Status</th><th>Module</th><th>Issue</th><th>Details</th></tr></thead><tbody id="rows"></tbody></table></div><nav><button id="previous">Previous</button><span id="pageLabel"></span><button id="nextPage">Next</button></nav>
<details><summary>Show charts for the selected cases</summary><div class="panels"><section class="panel"><h2>Defect Breakdown</h2><div id="defectChart">__DEFECT_CHART__</div></section><section class="panel"><h2>Scenario Breakdown</h2><label for="group">Group chart by<select id="group"><option value="reason">Scenario / reason</option><option value="module">Assembly module</option></select></label><div id="moduleChart">__MODULE_CHART__</div></section></div></details>
<dialog id="caseDetails" style="max-width:650px;border:1px solid #ddd;border-radius:12px"><h2 id="detailTitle"></h2><p id="detailSummary"></p><p id="detailAction"></p><form method="dialog"><button>Close</button></form></dialog>
<p class="sub">10 rows per page. Charts cover all matching cases. This report contains synthetic examples for this module only, not live incidents. This module uses its own synthetic cases; undefined recovery operations remain on hold.</p>
<script>const records=__DATA__;
if(new URLSearchParams(location.search).get('embedded')==='1'){const embedStyle=document.createElement('style');embedStyle.textContent='body{margin:0!important;padding:10px 16px!important;max-width:none!important;background:transparent!important}h1,.report-menu,.filters label[for="module"]{display:none!important}';document.head.appendChild(embedStyle);}
const get=id=>document.getElementById(id);
let page=1;const pageSize=10;
function chart(id,items,key){const counts=new Map();items.forEach(r=>counts.set(r[key],(counts.get(r[key])||0)+1));const host=get(id);host.replaceChildren();
if(!counts.size){host.textContent='No matching cases.';return;}
const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 650 '+(55+counts.size*48));svg.setAttribute('role','img');svg.setAttribute('aria-label','Filtered cases by '+key);
function add(tag,attrs,text){const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;svg.appendChild(e);}
const max=Math.max(...counts.values(),1);let i=0;counts.forEach((v,k)=>{let y=18+48*i++;const words=k.split(' ');let first='',second='';words.forEach(w=>{if(!second&&(first+' '+w).trim().length<=28){first=(first+' '+w).trim();}else{second=(second+' '+w).trim();}});add('text',{x:0,y:y+11,fill:'#405169','font-size':12},first);if(second)add('text',{x:0,y:y+27,fill:'#405169','font-size':12},second);add('rect',{x:220,y,width:330,height:28,rx:5,fill:'#edf1f5'});add('rect',{x:220,y,width:330*v/max,height:28,rx:5,fill:({high:'#bc3d49',medium:'#b47b10',low:'#168576'}[get('priority').value]||'#006c78')});add('text',{x:570,y:y+20,'font-size':17},v);});add('text',{x:220,y:41+counts.size*48,'font-size':12},'0');add('text',{x:550,y:41+counts.size*48,'text-anchor':'end','font-size':12},max+' cases');host.appendChild(svg);}
function drawPriorityOverview(){const m=get('module').value,s=get('status')?get('status').value:'',c=get('scenario').value;const scope=records.filter(r=>(!m||r.module===m)&&(!s||r.status===s)&&(!c||r.reason===c));const counts={high:0,medium:0,low:0};scope.forEach(r=>{if(r.priority in counts)counts[r.priority]++;});const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 700 135');svg.setAttribute('role','img');svg.setAttribute('aria-label','High: '+counts.high+', Medium: '+counts.medium+', Low: '+counts.low);svg.style.cssText='width:100%;max-width:780px;max-height:150px;display:block';const maximum=Math.max(1,...Object.values(counts));function add(tag,attrs,text){const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;svg.appendChild(e);}['high','medium','low'].forEach((k,i)=>{const y=8+39*i;add('text',{x:0,y:y+21,'font-size':16,fill:'#213348'},k[0].toUpperCase()+k.slice(1));add('rect',{x:95,y,width:500,height:27,rx:4,fill:'#e9eef4'});add('rect',{x:95,y,width:500*counts[k]/maximum,height:27,rx:4,fill:{high:'#b72e42',medium:'#bf8519',low:'#168576'}[k]});add('text',{x:612,y:y+21,'font-size':18,'font-weight':700,fill:'#213348'},counts[k]);});get('priorityChart').replaceChildren(svg);get('priorityScope').textContent=(s?(s[0].toUpperCase()+s.slice(1)):'All statuses')+' | '+scope.length+' cases across all priorities. Follows module and scenario filters; ignores the priority filter.';}function update(resetPage=true){if(resetPage)page=1;const module=get('module').value,priority=get('priority').value,scenario=get('scenario').value,status=get('status').value;const selected=records.filter(r=>(!module||r.module===module)&&(!priority||r.priority===priority)&&(!status||r.status===status)&&(!scenario||r.reason===scenario));
drawPriorityOverview();const rank={high:0,medium:1,low:2};selected.sort((a,b)=>rank[a.priority]-rank[b.priority]);const counts={high:0,medium:0,low:0};selected.forEach(r=>counts[r.priority]++);get('summary').textContent=selected.length+' cases | High: '+counts.high+' | Medium: '+counts.medium+' | Low: '+counts.low;
const pages=Math.max(1,Math.ceil(selected.length/pageSize));page=Math.max(1,Math.min(page,pages));get('pageLabel').textContent='Page '+page+' of '+pages;get('previous').disabled=page===1;get('nextPage').disabled=page===pages;
const rows=get('rows');rows.replaceChildren();selected.slice((page-1)*pageSize,page*pageSize).forEach(r=>{const tr=document.createElement('tr');[r.priority.toUpperCase(),r.status.toUpperCase(),r.module,r.reason].forEach((v,index)=>{const td=document.createElement('td');td.textContent=v;if(index===0){td.style.fontWeight='700';td.style.color={high:'#a72132',medium:'#946200',low:'#007868'}[r.priority];}tr.appendChild(td);});const td=document.createElement('td'),button=document.createElement('button');button.textContent='View';button.onclick=()=>{get('detailTitle').textContent=r.reason;get('detailSummary').textContent=r.module+' | '+r.priority.toUpperCase()+' | '+r.status.toUpperCase()+' | '+r.defect+' | '+r.outcome;get('detailAction').textContent=r.action+(r.timing?' | Simulated elapsed: '+r.timing.elapsed_process_sec+'s. Recovery: '+(r.timing.drop_to_recovery_sec===null?'not completed':r.timing.drop_to_recovery_sec+'s')+'. Check duration is not modeled.':'');get('caseDetails').showModal();};td.appendChild(button);tr.appendChild(td);rows.appendChild(tr);});
if(!selected.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='No issues match these filters.';tr.appendChild(td);rows.appendChild(tr);}
chart('defectChart',selected,'defect');chart('moduleChart',selected,get('group').value);}
get('module').onchange=()=>update();get('priority').onchange=()=>update();get('status').onchange=()=>update();get('scenario').onchange=()=>update();get('group').onchange=()=>update(false);get('previous').onclick=()=>{page--;update(false);};get('nextPage').onclick=()=>{page++;update(false);};get('reset').onclick=()=>{get('module').value='';get('priority').value='high';get('status').value='open';get('scenario').value='';get('group').value='reason';update();};update();</script></html>'''
    # Insert the JSON last so text inside data cannot be mistaken for a template token.
    return (template.replace("__OPTIONS__", options).replace("__SCENARIOS__", scenario_options).replace("__COUNT__", str(len(urgent)))
            .replace("__DEFECT_CHART__", defect_chart).replace("__MODULE_CHART__", module_chart)
            .replace("__DATA__", payload))




