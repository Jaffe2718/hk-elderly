"""Generate public network explorer, SOP and chart assets for the StoryMap."""
import argparse
import csv
import html
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_network_review import build_maps, read

DEST = ROOT / "docs/embeds/20261118"
SELECTED = ["05_priority", "03_network", "02_euclidean", "06_uncertainty",
            "08_case755", "09_case231", "10_case141", "15_case755_overlap", "14_case920_venue"]


def rows(source, filename):
    with (source / "tables" / filename).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_embeds(source, output, gdb):
    maps = build_maps(source, output, gdb)
    explorer = DEST / "network"
    explorer.mkdir(parents=True, exist_ok=True)
    (explorer / "webmaps").mkdir(exist_ok=True)
    for key in SELECTED:
        shutil.copyfile(output / "webmaps" / (key + ".js"), explorer / "webmaps" / (key + ".js"))
    template = (ROOT / "scripts/network_review.html").read_text(encoding="utf-8-sig")
    template = template.replace('href="leaflet.css"', 'href="../../../vendor/leaflet.css"')
    template = template.replace('src="leaflet.js"', 'src="../../../vendor/leaflet.js"')
    template = template.replace('main{max-width:1040px;margin:auto;padding:48px 24px}', '''
main{display:flex;flex-direction:column;gap:6px;height:100dvh;padding:8px 10px;font:14px/1.4 Arial,sans-serif}
.controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.controls label{display:flex;align-items:center;gap:5px}
.controls button,.controls input,.controls select{font:inherit;color:#183d40;padding:5px 7px;border:1px solid #a6c2bc;border-radius:4px;background:white;max-width:100%}
.controls [hidden]{display:none}.controls select{max-width:min(100%,58vw)}
[data-panel]{flex:1;min-height:0}.map{height:100%!important;min-height:225px}.map .leaflet-popup-content{max-height:200px;overflow:auto}
''')
    tabs = ['<div class="controls"><label for="network-view">Map view</label> <select id="network-view">' +
            "".join(f'<option value="{key}">{html.escape(maps[key])}</option>' for key in SELECTED) +
            '</select><button id="reset-view">Reset view</button>'
            '<form id="find-area" class="controls" aria-label="Find a census group"><label>STPUG '
            '<input id="area-code" size="5" placeholder="755" required></label><button>Find</button></form></div>'
            '<div id="screening-controls" class="controls">'
            '<label>Radius <select id="radius"><option>500</option><option selected>800</option><option>1000</option></select> m</label>'
            '<label>Age 65+ <select id="age-cut"><option>18</option><option selected>20</option><option>22</option></select>%</label>'
            '<label>Gap <select id="gap-cut"><option>20</option><option selected>30</option><option>40</option></select>%</label>'
            '</div><output id="results" aria-live="polite"></output>']
    for index, key in enumerate(SELECTED):
        hidden = ' hidden' if index else ''
        tabs.append(f'<section data-panel="{key}"{hidden}><div class="map" data-key="{key}"><button>Load map</button></div></section>')
    template = template.replace("<!-- STORY -->", "\n".join(tabs))
    template = template.replace("section.append(title);", '''section.append(title);
    const scenarioLabels = {"Priority": "Meets both cutoffs", "Higher ageing, lower gap": "Meets age cutoff only",
      "Lower ageing": "Below age cutoff", "Uncertain": "Unresolved at the gap cutoff", "Not assessed": "No residential cells"};
    if (layer.id === "priority" && r.uniqueValueInfos) {
      for (const entry of r.uniqueValueInfos) entry.label = scenarioLabels[entry.value] || entry.label;
    }''')
    template = template.replace("i => values.has(String(i.value))",
                                "i => layer.id === 'priority' || values.has(String(i.value))")
    template = template.replace("    const section = document.createElement", '''    if (layer.id === "priority" && !entries.some(i => i.value === "Uncertain")) {
      entries.push({value:"Uncertain", label:"Unresolved at the gap cutoff",
                    symbol:{type:"esriSFS",color:[221,189,156,255]}});
    }
    const section = document.createElement''')
    template = template.replace("</script>\n</body>", '''
const select = document.getElementById("network-view");
const controls = document.getElementById("screening-controls");
const output = document.getElementById("results");
const find = document.getElementById("find-area");
const activeFrame = () => document.querySelector('[data-key="' + select.value + '"]');
const ref = id => document.getElementById(id);
function screen() {
  const frame = activeFrame();
  if (select.value !== "05_priority" || !frame.networkAreas) return;
  let selected = 0, uncertain = 0;
  const radius = +ref("radius").value, age = +ref("age-cut").value, gap = +ref("gap-cut").value;
  const colours = {priority:"#9e83b6", uncertain:"#ddbd9c", below:"#f2edf7", ageOnly:"#ddd1e9", unassessed:"#a5adb0"};
  for (const [key, {item, attributes:a}] of frame.networkAreas) {
    const lo = a['net_out'+radius+'_lo'], hi = a['net_out'+radius+'_hi'];
    const state = !a.res_cells || lo == null ? "unassessed" : a.pct65 < age ? "below" :
      lo >= gap ? "priority" : hi >= gap ? "uncertain" : "ageOnly";
    if (state === "priority") selected++;
    if (state === "uncertain") uncertain++;
    item.setStyle({fillColor:colours[state], fillOpacity:.88});
    const popup = document.createElement("div"), title = document.createElement("strong");
    title.textContent = "STPUG " + key + (a.place_en ? " · " + a.place_en : "");
    popup.append(title);
    const pct = n => n == null ? "—" : Number(n).toFixed(2) + "%";
    const lines = ["Residents aged 65+: "+pct(a.pct65), "Straight-line gap: "+pct(a["eu_out"+radius]),
      "Network gap: "+pct(lo)+" to "+pct(hi), "Screening: "+({priority:"Priority", uncertain:"Uncertain", below:"Below age cutoff",
        ageOnly:"Below gap cutoff", unassessed:"No residential cells"})[state]];
    for (const text of lines) { const line = document.createElement("div"); line.textContent = text; popup.append(line); }
    if(item.getPopup()) item.setPopupContent(popup); else item.bindPopup(popup);
  }
  output.textContent = selected + " priority groups · " + uncertain + " uncertain";
}
function showView() {
  controls.hidden = select.value !== "05_priority";
  find.hidden = !["05_priority","03_network","02_euclidean","06_uncertainty"].includes(select.value);
  output.textContent = "";
  for (const panel of document.querySelectorAll("[data-panel]")) {
    panel.hidden = panel.dataset.panel !== select.value;
    if (panel.hidden) continue;
    const frame = panel.querySelector(".map");
    if (frame.networkMap) requestAnimationFrame(() => {frame.networkMap.invalidateSize();screen();});
    else {
      frame.addEventListener("networkready", screen, {once:true});
      frame.querySelector("button")?.click();
    }
  }
}
controls.addEventListener("change", screen);
ref("reset-view").onclick = () => activeFrame().resetNetworkView?.();
find.onsubmit = event => {
  event.preventDefault();
  const frame = activeFrame(), code = ref("area-code").value.trim().toUpperCase();
  const area = frame.networkAreas?.get(code);
  if (!area) { output.textContent = "Group " + code + " was not found in this view."; return; }
  frame.networkMap.fitBounds(area.item.getBounds(), {padding:[24,32], maxZoom:15});
  area.item.openPopup();
};
select.onchange = showView;
showView();
</script>
</body>''')
    (explorer / "index.html").write_text(template.rstrip() + "\n", encoding="utf-8")

    workflow = DEST / "workflow"
    shutil.copytree(ROOT / "docs/embeds/20261106/workflow", workflow, dirs_exist_ok=True)
    steps_path = workflow / "steps.js"
    steps = json.loads(steps_path.read_text(encoding="utf-8-sig").removeprefix("window.WORKFLOW_STEPS=").strip().rstrip(";"))
    updates = [
        ("Census evidence","2021 · 211 STPUGs","Join Census A503 to the statistical boundaries.","65+ / all residents",["Keep age counts and area denominators."]),
        ("Centres and outreach venues","215 NEC · 62 DECC · 115 venues","Use 215 distinct NECs for the baseline. Use the 62 DECCs in a separate facility scenario and test 115 documented HAD venues for outreach.","215 baseline NECs",["The NECs and DECCs come from the 2 November 2026 SWD snapshot.", "HAD venue records were checked on 18 November 2026."]),
        ("Residential land","2021 · 10 m cells","Assign residential cell centres to the census areas.","792,049 assigned cells",["Each cell represents 100 m² of residential ground area."]),
        ("Build the 3D graph","Enabled links · direction · XYZ","Keep enabled links from the 16 September 2026 CSDI network. Use XYZ endpoints for connectivity and sum three-dimensional segment lengths.","465,866 enabled links",["Planar crossings at different elevations remain separate.", "Respect directional restrictions.", "The baseline assumes enabled links are available regardless of opening schedules."]),
        ("Calculate shortest routes","Outdoor snap · 3D path","Project each residential cell centre and NEC onto the nearest eligible outdoor segment within 100 m. Add the two assumed connector lengths to the shortest directed 3D path.","800 m baseline",["The 100 m limit applies to each connector.", "The straight-line comparison uses the same cells, NECs and 800 m threshold."]),
        ("Ageing condition","65+ share","Calculate older residents as a share of the group population.","At least 20%",["Apply the same fixed cutoff to both distance methods."]),
        ("Residential gap","Lower bound · unresolved cells","Classify a cell as beyond 800 m if its shortest network route exceeds 800 m or its straight-line distance already proves it is beyond 800 m.","At least 30%",["A failed route within 800 m by straight line remains unresolved.", "The gap lower bound uses all assigned residential cells as its denominator."]),
        ("Apply both conditions","Ageing AND gap","Select a group when at least 20% of residents are 65+ and its residential gap lower bound is at least 30%.","33 priority groups",["Flag uncertainty when the age cutoff is met and the gap bounds straddle 30%.", "14 qualified using straight-line distance and the same fixed thresholds."]),
        ("Test assumptions","Distance · thresholds · connectors","Cross 500, 800 and 1,000 m with age cutoffs of 18%, 20% and 22% and gap cutoffs of 20%, 30% and 40%.","9–93 groups",["Separately test connector limits of 50, 100 and 150 m."]),
        ("Compare venue gains","Additional residential land","Use the network to estimate how much confirmed uncovered residential land in the 33 priority groups each venue could add. Subtract any area already gained.","76.67 ha in three steps",["The greedy sequence selects Sha Kok, Lek Yuen and Cheung Chau."]),
        ("Guide field review","Routes · entrances · venues","Check actual routes, entrance access and venue feasibility before drawing service conclusions.","33 areas for review",["The static route model does not estimate walking time."]),
    ]
    for step, (title, sub, description, metric, details) in zip(steps, updates):
        step[3:5] = [title, sub]
        step[6:] = [description, metric, details]
    steps_path.write_text("window.WORKFLOW_STEPS=" + json.dumps(steps) + ";\n", encoding="utf-8")
    script = workflow / "workflow.js"
    edges = [["census","population"],["sites","distance"],["land","distance"],["prepare","distance"],
             ["distance","coverage"],["population","binary"],["coverage","binary"],["binary","checks"],
             ["binary","cases"],["cases","review"],["checks","review"]]
    workflow_js = script.read_text(encoding="utf-8").replace("#7050a4", "#087b82").replace("#a14065", "#8a562b")
    workflow_js = re.sub(r"^const links=.*;$", "const links=" + json.dumps(edges, separators=(",",":")) + ";",
                         workflow_js, count=1, flags=re.M)
    script.write_text(workflow_js, encoding="utf-8")
    index = workflow / "index.html"
    index.write_text(index.read_text(encoding="utf-8").replace("v=20261106-p60", "v=20261118-r2"), encoding="utf-8")

    chart = DEST / "charts"
    chart.mkdir(exist_ok=True)
    data = {
        "housing": [{key: r[key] for key in ("label", "eu_covered800_pct", "net_covered800_pct",
                                              "both_covered800_pct", "unknown_pct")} for r in rows(source, "housing_access.csv")],
        "scenarios": rows(source, "sensitivity27.csv"),
        "venue": rows(source, "venues_overlap_755.csv"),
    }
    for venue in data["venue"]:
        data["venue"][data["venue"].index(venue)] = {key: venue[key] for key in ("name_en", "gain_ha")}
    (chart / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("source", "output", "gdb"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    build_embeds(args.source.resolve(), args.output.resolve(), args.gdb.resolve())
