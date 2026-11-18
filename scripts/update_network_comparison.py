"""Replace the oversized native swipe legend with a compact two-sided comparison."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_network_review import read
from storymap import check_baseline, inspect_story, publish_current, save_draft

PATH = "embeds/20261118/comparison/index.html"
VERSION = "20261118-compact-swipe"
CAPTION = "Straight-line and 3D network gaps."


def replace_comparison(graph, cfg):
    nodes = graph["nodes"]
    children = nodes[graph["root"]]["children"]
    caption_index = next(
        i for i, key in enumerate(children)
        if nodes[key].get("data", {}).get("text", "").endswith(CAPTION + "</strong>")
    )
    key = children[caption_index - 1]
    old = nodes[key]
    if old["type"] == "swipe":
        for child in old["data"]["contents"].values():
            nodes.pop(child)
    elif old["type"] != "embed" or PATH not in old["data"]["url"]:
        raise RuntimeError("Figure caption is not next to the expected comparison.")
    url = urljoin(cfg["pages_base_url"], PATH) + "?v=" + VERSION
    nodes[key] = {
        "type": "embed",
        "data": {
            "url": url,
            "embedSrc": url,
            "embedType": "link",
            "title": "Straight-line and 3D network gaps",
            "display": "inline",
            "isEmbedSupported": True,
            "hasPlaceholderOpenButton": False,
            "hasEmbedOpenButton": False,
            "isLiveOnMobile": True,
            "description": "",
            "caption": "",
            "alt": "Aligned maps with straight-line gaps on the left and network gap lower bounds on the right, both at 800 metres.",
        },
        "config": {"size": "wide"},
    }
    return url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    cfg = read(args.config)
    graph = read(args.baseline / "draft.json")
    url = replace_comparison(graph, cfg)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in [("config.json", cfg), ("generated.json", graph)]:
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.publish:
        from time import sleep
        from urllib.request import urlopen
        from arcgis.gis import GIS
        from arcgis.apps.storymap import StoryMap

        for attempt in range(10):
            try:
                with urlopen(url, timeout=10) as response:
                    if 'id="right-legend"' not in response.read().decode("utf-8"):
                        raise RuntimeError("The comparison is not deployed yet.")
                break
            except (OSError, RuntimeError):
                if attempt == 9:
                    raise
                sleep(5)

        gis = GIS("pro")
        story = StoryMap(cfg["item_id"], gis=gis)
        check_baseline(story, cfg, args.baseline)
        story._properties = graph
        save_draft(story, cfg)
        baseline = inspect_story(cfg)
        publish_current(cfg, str(baseline), str(args.output / "generated.json"), refresh_map_views=False)


if __name__ == "__main__":
    main()
