"""Apply the 3D network handoff to the existing project StoryMap."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_network_embeds import build_embeds
from scripts.build_network_review import read
from storymap import apply, inspect_story, publish_current

TAG = "geog7302-network-review-20261118"


def paragraphs(value):
    return [value] if isinstance(value, str) else value or []


def blocks(value):
    return [{"type": "text", "text": text} for text in paragraphs(value)]

def figure(title, component):
    return {"type": "embed", "path": f"embeds/20261118/{component}/index.html", "figure_title": title}


def infographic(title, *values):
    return {"type": "infographic", "figure_title": title, "layout": "stacked",
            "values": [{"title": number, "description": label, "icon": icon}
                       for number, label, icon in values]}


SLIDE_INFO = {
    "08_case755": [("600", "m · direct distance", "pin"), ("1,200", "m · modelled route", "walking")],
    "01_age": [("211", "Census groups", "map"), ("210", "Groups with residential cells", "home")],
    "04_change": [("14", "Straight-line priorities", "pin"), ("33", "Network priorities", "walking"), ("19", "Additional groups", "flag")],
    "09_case231": [("696", "m · direct distance", "pin"), ("943", "m · modelled route", "walking")],
    "05_priority": [("20%", "Minimum age-65+ share", "group"), ("30%", "Minimum confirmed gap", "home")],
    "07_venues": [("115", "Community venues assessed", "home"), ("28.82", "ha · Sha Kok gain", "analysis")],
    "15_case755_overlap": [("25.88", "ha · shared gain", "analysis"), ("0.61", "ha · extra after Sha Kok", "home")],
    "14_case920_venue": [("26.71", "ha · straight-line gain", "pin"), ("23.58", "ha · network gain", "walking")],
    "11_sensitivity": [("27", "Cutoff combinations", "analysis"), ("33", "Groups at baseline thresholds", "flag")],
    "06_uncertainty": [("6.83", "% · no finite route", "walking"), ("0.52", "% · threshold unresolved", "analysis")],
}


def make_config(source, map_entries, receipt):
    narrative = read(source / "story/story_content.json")
    cfg = read(ROOT / "story.json")
    cfg.update(title="Walking Access to Elderly Centres in Hong Kong",
               subtitle="A 3D pedestrian network study of residential coverage and outreach venues",
               publish_audience="public",
               model_version="20261118-network", sections=[], asset_revision="20261118-r2",
               cover_note="3D pedestrian network revision · 18 November 2026")
    cfg["credit_html"] += ' Pedestrian network data from the <a href="https://portal.csdi.gov.hk/csdi-webpage/dataset/landsd_rcd_1637222018065_52265">Lands Department and CSDI Portal</a>.'
    refs = read(ROOT / "assets/references.json")
    refs[-1]["html"] = refs[-1]["html"].replace("November 5", "November 18")
    refs.append({
        "html": 'Lands Department. (2026). <em>3D pedestrian network</em> (September 2026 revision) [Data set]. Common Spatial Data Infrastructure Portal.',
        "url": narrative["references"][5]["url"],
    })
    cfg["references"] = refs

    def map_media(key):
        return {"type": "map", "item_id": receipt["maps"][key], "map_path": map_entries[key]["path"]}

    for i, chapter in enumerate(narrative["chapters"]):
        section = {"id": f"network-{i+1}", "title": re.sub(r"^\d+\s+", "", chapter["title"]),
                   "before": blocks(chapter.get("body")), "after": [], "slides": [],
                   "layout": "docked-panel", "panel_position": "start" if i % 2 == 0 else "end",
                   "panel_size": "small"}
        for slide in chapter.get("slides", []):
            if slide.get("image"):
                section["after"].append({"type": "heading", "text": slide["title"]})
                section["after"] += blocks(slide["body"] + " [2] [3] [5] [7] [9]")
                section["after"].append(figure("Analytical workflow", "workflow"))
                continue
            text = "\n\n".join(paragraphs(slide.get("body")) + paragraphs(slide.get("caption")))
            if "left_map" in slide:
                text = text.replace("Move the divider to compare the spatial pattern, then use", "Use the divider to compare the spatial pattern, then use")
                media = {"type": "swipe", "maps": [map_media(slide[k]) for k in ("left_map", "right_map")]}
                metrics = [("46.24", "% · straight-line coverage", "pin"),
                           ("31.90", "% · network coverage", "walking")]
            else:
                media = map_media(slide["map"])
                metrics = SLIDE_INFO[slide["map"]]
                if slide["title"] == "A large change in Sha Tin":
                    metrics = [("4.21", "% · straight-line gap", "pin"),
                               ("67.23", "% · minimum network gap", "walking")]
            citations = {"01_age": " [2] [3] [5]", "08_case755": " [7] [9]",
                         "07_venues": " [8] [9]", "09_case231": " [7] [9]"}
            text += citations.get(slide.get("map"), "")
            section["slides"].append({"title": slide["title"], "text": text, "media": media,
                                      "infographics": [infographic(slide["title"], *metrics)]})
        if i == 0:
            section["before"].append(infographic("Study overview", ("800", "m · baseline distance", "walking"),
                                                 ("33", "Priority groups", "flag"),
                                                 ("210", "Assessed census groups", "map")))
        if i == 2:
            section["after"] += [
                {"type": "heading", "text": "Explore the walking network"},
                figure("Pedestrian routes and residential gaps", "network"),
                {"type": "text", "text": "Adjust the screening cutoffs, find a census group or switch to a route case. Use Layers to toggle pedestrian links, example routes and residential areas."},
            ]
        if i == 4:
            section["after"].append(figure("Coverage and screening scenarios", "charts"))
        cfg["sections"].append(section)
    for item in narrative["closing"]:
        cfg["sections"][-1]["after"] += [{"type": "heading", "text": item["title"]}, *blocks(item["body"])]
    cfg["sections"].append({"id": "references", "title": "References", "before": [{"type": "references"}], "slides": []})
    return cfg


def main():
    from arcgis.apps.storymap import StoryMap
    from arcgis.gis import GIS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("gdb", type=Path)
    parser.add_argument("--based-on", required=True)
    parser.add_argument("--maps-from", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    maps = {m["id"]: m["title"] for m in read(source / "arcgis/map_manifest.json")["maps"]}
    if not (output / "webmaps/08_case755.json").exists():
        build_embeds(source, output, args.gdb.resolve())
    story_content = read(source / "story/story_content.json")
    used = {s[field] for c in story_content["chapters"] for s in c.get("slides", [])
            for field in ("map", "left_map", "right_map") if s.get(field)}
    manifest = {m["id"]: m for m in read(source / "arcgis/map_manifest.json")["maps"]}
    receipts_path = output / "arcgis-receipt.json"
    if receipts_path.exists():
        receipt = read(receipts_path)
    elif args.maps_from:
        receipt = {"maps": read(args.maps_from)["maps"]}
    else:
        receipt = {"maps": {}}

    def checkpoint():
        receipts_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    gis = GIS("pro")
    owner = gis.users.me.username
    if gis.content.get(read(ROOT / "story.json")["item_id"]).owner != owner:
        raise RuntimeError("ArcGIS Pro is signed into a different account.")
    folder = gis.content.folders.get()
    map_entries = {}
    for key in sorted(used):
        path = output / "webmaps" / (key + ".json")
        data = read(path)
        xmin, ymin, xmax, ymax = manifest[key]["extent"]
        data["initialState"]["viewpoint"]["targetGeometry"] = dict(
            xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax, spatialReference={"wkid": 4326})
        path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        map_entries[key] = {"path": path.relative_to(ROOT).as_posix()}
        item = gis.content.get(receipt["maps"][key]) if key in receipt["maps"] else None
        props = {"title": "GEOG7302 3D Network | " + maps[key], "type": "Web Map",
                 "tags": [TAG, TAG + "-" + key], "extent": ",".join(map(str, manifest[key]["extent"])),
                 "snippet": "CSDI 3D pedestrian network and residential ground-area screening."}
        if item and item.owner != owner:
            raise RuntimeError("Web Map is owned by another account.")
        if not item:
            item = folder.add(item_properties=props, text=json.dumps(data)).result()
            receipt["maps"][key] = item.id
            checkpoint()
        elif item.get_data() != data:
            if not item.update(item_properties=props, data=json.dumps(data)):
                raise RuntimeError("Web Map update rejected for " + key)
        if item.owner != owner or item.get_data() != data:
            raise RuntimeError("Web Map readback failed for " + key)
        print(f"Verified map {key} / {item.id}", flush=True)

    checkpoint()
    cfg = make_config(source, map_entries, receipt)
    (output / "native-story-config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    apply(cfg, args.based_on)
    baseline = inspect_story(cfg)
    from urllib.request import ProxyHandler, build_opener
    from urllib.parse import urljoin
    from time import sleep

    opener = build_opener(ProxyHandler())
    embeds = [block["path"] for section in cfg["sections"] for block in section.get("after", [])
              if block["type"] == "embed"]
    for path in embeds:
        url = urljoin(cfg["pages_base_url"], path) + "?v=" + cfg["asset_revision"]
        for attempt in range(7):
            try:
                with opener.open(url, timeout=10) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Embed returned HTTP {response.status}: {url}")
                break
            except OSError:
                if attempt == 6:
                    raise
                sleep(8)
        print(f"Hosted embed verified: {url}", flush=True)
    publish_current(cfg, str(baseline))


if __name__ == "__main__":
    main()
