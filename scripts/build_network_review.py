"""Build a local review of the pedestrian-network handoff using the project map theme."""
import argparse
import html
import json
from pathlib import Path
import runpy
import shutil

ROOT = Path(__file__).resolve().parents[1]
PALETTE = json.loads((ROOT / "assets/map-theme.json").read_text())
MAP_THEME = json.loads((ROOT / "assets/webmaps/M03_binary800.json").read_text(encoding="utf-8"))
BASEMAP = MAP_THEME["baseMap"]
BOUNDARY = next(layer for layer in MAP_THEME["operationalLayers"] if layer["id"] == "study_outline")
LAND = next(layer for layer in MAP_THEME["operationalLayers"] if layer["id"] == "study_land")
CATEGORIES = {
    "priority_transition": {
        "Retained priority": "#9ebdb4", "New priority": "#18685e",
        "Not selected": "#e7eae8", "Uncertain": "#ddbd9c",
        "Not assessed": PALETTE["not_assessed"],
    },
    "screen_class": {
        "Priority": "#18685e", "Higher ageing, lower gap": "#9ebdb4",
        "Lower ageing": "#e7eae8", "Uncertain": "#ddbd9c",
        "Not assessed": PALETTE["not_assessed"],
    },
    "status": {0: "#e6ebe7", 1: "#b9c9c6", 2: "#ddbd9c", 3: "#bc936d", 4: "#946c4c"},
    "route_role": {
        "Network route": "#087b82", "Assumed entry connectors": "#b75d22",
        "Straight line to nearest NEC": "#536b78",
    },
    "point_role": {
        "Residential cell": "#087b82", "Network target NEC": PALETTE["facility"],
        "Euclidean nearest NEC": "#536b78",
    },
    "category": {"ShaKokOnly": "#a7c9bd", "Both": "#18685e", "PokHongOnly": "#b79b7a"},
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_maps(source, output, network_gdb=None):
    # Reuse the handoff's geometry converter. The maps are rebuilt from GeoJSON.
    build = runpy.run_path(str(source / "arcgis/build_webmaps.py"))
    manifest = read(source / "arcgis/map_manifest.json")
    target = output / "webmaps"
    target.mkdir(parents=True, exist_ok=True)
    maps = {}
    for entry in manifest["maps"]:
        layers = [LAND]
        if network_gdb and entry["id"] in {"08_case755", "09_case231", "10_case141"}:
            import arcpy
            from scripts.network_paths import export_network
            routes = output / (entry["id"] + "-network.geojson")
            export_network(arcpy, network_gdb, entry["extent"], routes)
            entry["layers"].insert(1, {"id": "pedestrian_network", "title": "Enabled 3D pedestrian links",
                "file": str(routes.resolve()), "popup_fields": ["route_id", "street"],
                "aliases": {"route_id": "CSDI route ID", "street": "Street"},
                "style": {"type": "simple", "color": "#85969b", "width": 0.75,
                          "label": "Local pedestrian network"}})
        for spec in entry["layers"]:
            if entry["id"] in {"08_case755", "09_case231", "10_case141"} and spec["id"] in {"gains", "venues"}:
                continue
            style = spec.get("style", {})
            field = style.get("field")
            if style.get("type") == "breaks":
                colors = PALETTE["age_share"] if field == "pct65" else (["#f5e9db", "#ddbd9c", "#be926e", "#9d653a"] if field == "priority_gain_ha" else PALETTE["sequential"])
                classes = style["classes"]
                for index, category in enumerate(classes):
                    category["color"] = colors[round(index * (len(colors) - 1) / (len(classes) - 1))]
                style["default"] = PALETTE["not_assessed"]
            if field in CATEGORIES:
                for category in style["classes"]:
                    category["color"] = CATEGORIES[field][category["value"]]
            if spec["id"] in {"nec", "centres"}:
                style.update(color=PALETTE["facility"], size=5.5)
            if spec["id"] == "gains":
                style["color"] = "#4d897b"
            layer = build["make_layer"](source, spec)
            sub = layer["featureCollection"]["layers"][0]
            renderer = sub["layerDefinition"]["drawingInfo"]["renderer"]
            if spec["id"] == "route_points":
                features = sub["featureSet"]["features"]
                targets = [f["geometry"] for f in features if f["attributes"][field] == "Network target NEC"]
                same = [f for f in features if f["attributes"][field] == "Euclidean nearest NEC"
                        and f["geometry"] in targets]
                sub["featureSet"]["features"] = [f for f in features if f not in same]
                if same:
                    for category in renderer["uniqueValueInfos"]:
                        if category["value"] == "Network target NEC":
                            category["label"] = "NEC for both distance measures"
            if spec["id"] in {"nec", "centres"}:
                renderer["symbol"]["style"] = "esriSMSDiamond"
            if renderer["type"] == "uniqueValue":
                observed = {str(row["attributes"][field]) for row in sub["featureSet"]["features"]}
                declared = {str(category["value"]) for category in renderer["uniqueValueInfos"]}
                if observed <= declared:
                    renderer.pop("defaultSymbol", None)
                    renderer.pop("defaultLabel", None)
                renderer["uniqueValueInfos"] = [
                    category for category in renderer["uniqueValueInfos"]
                    if str(category["value"]) in observed
                ]
            layers.append(layer)
        layers.append(BOUNDARY)
        a, b = (build["project"](entry["extent"][x:x+2]) for x in (0, 2))
        sr = build["SR"]
        extent = dict(xmin=a[0], ymin=a[1], xmax=b[0], ymax=b[1], spatialReference=sr)
        data = dict(version="2.31", authoringApp="ArcGIS Web Map", spatialReference=sr,
                    operationalLayers=layers, baseMap=BASEMAP, tables=[],
                    initialState={"viewpoint": {"targetGeometry": extent}})
        payload = json.dumps(data, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
        (target / (entry["id"] + ".json")).write_text(payload, encoding="utf-8")
        # A local script also allows the preview to open directly from disk.
        (target / (entry["id"] + ".js")).write_text(
            f"window.networkMaps[{json.dumps(entry['id'])}]={payload};\n", encoding="utf-8")
        maps[entry["id"]] = entry["title"]
    return maps


WORKFLOW = [
    ("Assemble source data", "Use the 2021 census and residential land, the NEC inventory, and the September 2026 CSDI 3D Pedestrian Network."),
    ("Build the 3D network", "Keep enabled directed links and match endpoints in XYZ. Sum the lengths of their 3D segments."),
    ("Calculate residential access", "Attach cells and centres to eligible outdoor links within 100 m. Include connector lengths in the shortest path. Classify coverage at 800 m and keep threshold status unresolved where necessary."),
    ("Apply the two conditions", "Select census groups only when their 65+ population share is at least 20% and their lower-bound residential gap is at least 30%."),
    ("Review changes and venue options", "Compare distance measures under identical cutoffs, vary the screening assumptions and calculate the non-overlapping gain of existing venues."),
]


def write_preview(source, output, maps):
    story = read(source / "story/story_content.json")
    parts = [f"<h1>{html.escape(story['title'])}</h1>", f"<p>{html.escape(story['subtitle'])}</p>",
             f"<p>{html.escape(story['byline'])}</p>"]
    def paragraphs(value):
        return "".join(f"<p>{html.escape(p)}</p>" for p in ([value] if isinstance(value, str) else value or []))
    for chapter in story["chapters"]:
        parts += [f"<h2>{html.escape(chapter['title'])}</h2>", paragraphs(chapter.get("body"))]
        for slide in chapter.get("slides", []):
            body = slide.get("body")
            if isinstance(body, str):
                body = body.replace("Move the divider to compare the spatial pattern, then use",
                                    "Compare the two maps, then use")
            parts += [f"<h3>{html.escape(slide['title'])}</h3>", paragraphs(body)]
            ids = [slide[key] for key in ("map", "left_map", "right_map") if key in slide]
            if ids:
                parts.append('<div class="maps">' + "".join(
                    f'<section><h4>{html.escape(maps[key])}</h4><div class="map" data-key="{key}"><button>Load map</button></div></section>'
                    for key in ids) + "</div>")
            if slide.get("image"):
                parts.append('<div class="workflow">' + "".join(
                    f"<details><summary>{html.escape(title)}</summary>{paragraphs(body)}</details>"
                    for title, body in WORKFLOW) + "</div>")
            parts.append(paragraphs(slide.get("caption")))
    for closing in story["closing"]:
        parts += [f"<h2>{html.escape(closing['title'])}</h2>", paragraphs(closing["body"])]
    parts.append("<h2>References</h2><ol>")
    for ref in story["references"]:
        url = ref.get("url", "")
        label = html.escape(ref["label"])
        parts.append(f'<li><a href="{html.escape(url, quote=True)}">{label}</a></li>' if url.startswith("https://") else f"<li>{label}</li>")
    parts.append("</ol>")
    template = (ROOT / "scripts/network_review.html").read_text(encoding="utf-8")
    (output / "index.html").write_text(template.replace("<!-- STORY -->", "\n".join(parts)), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    maps = build_maps(args.source.resolve(), args.output)
    for name in ("leaflet.js", "leaflet.css"):
        shutil.copyfile(ROOT / "docs/vendor" / name, args.output / name)
    write_preview(args.source, args.output, maps)
    print(f"Built {len(maps)} native web maps and a local review at {args.output / 'index.html'}")


if __name__ == "__main__":
    main()
