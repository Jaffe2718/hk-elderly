"""Clarify revision and source dates, and edit the network story's prose."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REVISION = "3D pedestrian network analysis revised 18 November 2026"

PROSE = {
    "3D pedestrian network revision · 18 November 2026": REVISION,
    "How does walking access to neighbourhood elderly centres vary across Hong Kong?": "We assessed how walking access to neighbourhood elderly centres varies across Hong Kong using the 3D pedestrian network.",
    "Combine population, residential cells, centre locations and the CSDI pedestrian network. [2] [3] [5] [7] [9]": "We combined 2021 census and residential land data with elderly centre locations from the 2 November 2026 SWD snapshot and the September 2026 CSDI pedestrian network. [2] [3] [5] [6] [7] [9]",
    "Use all residents for each group’s age-share denominator and all assigned residential ground area for the gap denominator. Group 295 has no assigned residential cells. [2] [3] [5]": "We calculated the share aged 65+ using all residents in each census group and the coverage gap using all assigned residential ground area. Group 295 has no assigned residential cells. [2] [3] [5]",
    "Select a census group when at least 20% of its residents are aged 65+ and the lower bound of its residential gap is at least 30%.": "We shortlisted census groups where at least 20% of residents were aged 65+ and the lower bound of the residential coverage gap was at least 30%.",
    "Use enabled CSDI links with directional restrictions and shared XYZ endpoints. Include both assumed connectors to eligible outdoor links, each capped at 100 m, in the shortest-path distance. Keep unresolved near-threshold cells separate. [9]": "We measured shortest paths along enabled CSDI links, respecting direction restrictions and joining links at shared XYZ endpoints. Each route included two assumed connectors to eligible outdoor links, each capped at 100 m. We reported unresolved cells near the threshold separately. [9]",
    "Vary the screening cutoffs across 27 combinations of 500/800/1,000 m, 18/20/22% age share and 20/30/40% gap. Separately test 50, 100 and 150 m connector limits.": "We tested 27 combinations of distance (500, 800 and 1,000 m), age share (18%, 20% and 22%) and residential gap (20%, 30% and 40%). We tested connector limits of 50, 100 and 150 m separately.",
    "Compare HAD-listed community venues by newly covered residential ground area. Deduct coverage gained by earlier selections when comparing additional venues. [8] [9]": "We compared HAD-listed community venues using the residential ground area each could newly cover. When evaluating additional venues, we excluded ground already covered by earlier selections. [8] [9]",
    "Compare the 800 m network results with straight-line coverage and examine the shortlist and potential outreach venues.": "We compared residential coverage within 800 m by straight-line and network distance, then examined how the shortlist changed and where outreach venues could extend coverage.",
    "Adjust the three screening cutoffs, look up a census group or switch to a local route case. Open Layers on the map to control what is visible.": "The interactive map shows how the shortlist changes under different screening assumptions. It also includes individual census groups and local route examples.",
    "The model measures static route length over enabled links. Check route conditions, entrances, access hours and service capacity in fieldwork. Coverage percentages use residential ground area. [4] [9]": "We modelled route length over enabled links and measured coverage as a share of residential ground area. Fieldwork could verify route conditions, entrances, access hours and service capacity. [4] [9]",
    "Measure residential proximity": "Residential proximity",
    "Separate two sensitivity questions": "Screening and connector sensitivity",
    "Review locations within shortlisted groups": "Outreach venues in shortlisted groups",
    "Explore assumptions": "Screening assumptions on the map",
    "Compare model and existing locations": "Modelled coverage and existing venues",
}


def clarify_credits(text):
    return text.replace("community-venue records checked on 5 November 2026.", "community-venue records [8].")


def revise(graph, cfg):
    if "credit_html" in cfg:
        cfg["credit_html"] = clarify_credits(cfg["credit_html"])
    changed = 0
    cover_config = graph["nodes"][graph["root"]]["config"]
    if cover_config.get("coverDate") != "none":
        cover_config["coverDate"] = "none"
        changed += 1
    for node in graph["nodes"].values():
        data = node.get("data", {})
        original = data.get("text")
        if not isinstance(original, str):
            continue
        text = PROSE.get(original, original)
        text = clarify_credits(text)
        if text != original:
            data["text"] = text
            changed += 1
    return changed


def main():
    from scripts.build_network_review import read
    from storymap import check_baseline, inspect_story, publish_current, save_draft

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    cfg = read(args.config)
    baseline = inspect_story(cfg)
    graph = read(baseline / "draft.json")
    changed = revise(graph, cfg)
    if not changed and not args.publish:
        print("The editorial changes are already present.")
        return
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    generated = args.output / "generated.json"
    generated.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Applied {changed} editorial changes.", flush=True)
    if args.publish:
        from arcgis.apps.storymap import StoryMap
        from arcgis.gis import GIS

        story = StoryMap(cfg["item_id"], gis=GIS("pro"))
        check_baseline(story, cfg, baseline)
        saved = baseline
        if changed:
            story._properties = graph
            save_draft(story, cfg)
            saved = inspect_story(cfg)
        publish_current(cfg, str(saved), str(generated), refresh_map_views=False)


if __name__ == "__main__":
    main()
