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
SELECTED = ["03_network", "05_priority", "06_uncertainty",
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
    template = template.replace('main{max-width:1040px;margin:auto;padding:48px 24px}',
                                'main{margin:auto;padding:10px 14px}.map{height:calc(100dvh - 72px)!important;min-height:280px}')
    tabs = [f'<label for="network-view">Map view</label> <select id="network-view">' +
            "".join(f'<option value="{key}">{html.escape(maps[key])}</option>' for key in SELECTED) +
            '</select>']
    for index, key in enumerate(SELECTED):
        hidden = ' hidden' if index else ''
        tabs.append(f'<section data-panel="{key}"{hidden}><div class="map" data-key="{key}"><button>Load map</button></div></section>')
    template = template.replace("<!-- STORY -->", "\n".join(tabs))
    template = template.replace('if (!item) continue;', 'if (!item) continue;')
    template = template.replace('legend.addTo(map);', 'legend.addTo(map); frame.networkMap = map;')
    template = template.replace("</script>\n</body>", '''
const select = document.getElementById("network-view");
function showView() {
  for (const panel of document.querySelectorAll("[data-panel]")) {
    panel.hidden = panel.dataset.panel !== select.value;
    if (panel.hidden) continue;
    const frame = panel.querySelector(".map");
    if (frame.networkMap) frame.networkMap.invalidateSize();
    else frame.querySelector("button")?.click();
  }
}
select.onchange = showView;
showView();
</script>
</body>''')
    (explorer / "index.html").write_text(template, encoding="utf-8")

    workflow = DEST / "workflow"
    shutil.copytree(ROOT / "docs/embeds/20261106/workflow", workflow, dirs_exist_ok=True)
    steps_path = workflow / "steps.js"
    steps = json.loads(steps_path.read_text(encoding="utf-8-sig").removeprefix("window.WORKFLOW_STEPS=").strip().rstrip(";"))
    updates = [
        ("Census evidence","2021 · 211 STPUGs","Join Census A503 to the statistical boundaries.","65+ / all residents",["Keep age counts and area denominators."]),
        ("Facilities and venues","215 NEC · 62 DECC · 115 venues","Use deduplicated SWD premises and the HAD venue inventory.","215 distinct NEC locations",["Use DECC in a separate facility scenario."]),
        ("Residential land","2021 · 10 m cells","Assign residential cell centres to the census areas.","792,049 assigned cells",["Each cell represents 100 m² of residential ground area."]),
        ("Build the 3D graph","Direct links · preserve XYZ","Keep enabled CSDI links and use their direction, XYZ endpoints and three-dimensional segment lengths.","465,866 enabled links",["Paths that cross in plan connect only where their XYZ endpoints match."]),
        ("Calculate shortest routes","Outdoor connections · route length","Connect residences and centres to eligible outdoor paths within 100 m and include both connectors in route distance.","800 m baseline",["Compare the same residential cells and facilities against straight-line distance."]),
        ("Ageing condition","65+ share","Calculate older residents as a share of the group population.","At least 20%",["Apply the same fixed cutoff to both distance methods."]),
        ("Residential gap","Conservative lower bound","Count confirmed network gaps and cells whose straight-line distance already exceeds 800 m.","At least 30%",["Keep unresolved cells separate."]),
        ("Apply both conditions","Ageing AND gap","Select groups meeting both conditions.","33 priority groups",["14 qualified with straight-line distance at the same cutoffs."]),
        ("Test assumptions","Distance · thresholds · connectors","Compare 27 distance and cutoff scenarios, then vary the connector limit.","9–93 groups",["Test 50, 100 and 150 m connector limits."]),
        ("Compare venue gains","Additional residential land","Assess existing community venues, subtracting any coverage already gained by previously selected venues.","76.67 ha in three steps",["The portfolio is a greedy sequence across 33 priority groups."]),
        ("Guide field review","Routes · entrances · venues","Check actual routes, entrance access and venue feasibility before drawing service conclusions.","33 areas for review",["The static route model does not estimate walking time."]),
    ]
    for step, (title, sub, description, metric, details) in zip(steps, updates):
        step[3:5] = [title, sub]
        step[6:] = [description, metric, details]
    steps_path.write_text("window.WORKFLOW_STEPS=" + json.dumps(steps) + ";\n", encoding="utf-8")
    script = workflow / "workflow.js"
    script.write_text(script.read_text(encoding="utf-8").replace("#7050a4", "#087b82").replace("#a14065", "#8a562b"), encoding="utf-8")

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
