"""Restore the tagged chapter hierarchy on the published network StoryMap."""
import argparse
import copy
import html
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_network_embeds import rows
from scripts.build_network_review import read
from storymap import check_baseline, inspect_story, publish_current, save_draft

TAG = "pre-3d-network-2026-11-18"
REVISION = "20261118-tag-layout"


def assemble(graph, tagged, source, maps):
    nodes, resources = graph["nodes"], graph["resources"]
    root = nodes[graph["root"]]
    old_children = root["children"]
    nav_id = next(k for k in old_children if nodes[k]["type"] == "navigation")
    immersive = [nodes[k] for k in old_children if nodes[k]["type"] == "immersive"]
    panel_template = copy.deepcopy(nodes[immersive[0]["children"][0]])
    grid_template = next(n for n in nodes.values() if n["type"] == "grid")
    metric_template = nodes[grid_template["children"][0]]
    embeds = {n["data"]["url"].split("/20261118/")[1].split("/")[0]: k for k,n in nodes.items() if n["type"] == "embed"}
    index = {key: mid for key, mid in maps["maps"].items()}
    map_node = {}
    for n in nodes.values():
        if n["type"] == "webmap":
            map_node.setdefault(resources[n["data"]["map"]]["data"]["itemId"], n)
    reference_ids = [k for k in old_children if re.match(r"^\[\d+\]", nodes[k].get("data",{}).get("text",""))]
    graph["resources"] = resources

    def add(node, collection=nodes, prefix="n-"):
        key = prefix + uuid4().hex[:10]
        collection[key] = node
        return key

    def text(value, style="paragraph"):
        return add({"type":"text", "data":{"type":style, "text":html.escape(value)}})

    counter = 0

    def caption(label):
        nonlocal counter
        counter += 1
        return add({"type":"text", "data":{"type":"paragraph","textSize":"small",
                                          "text":f"<strong>Fig. {counter}. {html.escape(label.rstrip('.'))}.</strong>"}})

    def info(label, *values):
        grid = copy.deepcopy(grid_template)
        del grid["data"]["items"][len(values):]
        grid["data"]["cols"] = len(values)
        grid["children"] = []
        for value, description, icon in values:
            node = copy.deepcopy(metric_template)
            node["data"].update(title=value, description=description, icon=icon)
            grid["children"].append(add(node))
        return [add(grid), caption(label)]

    def media(key, focus=None):
        node = copy.deepcopy(map_node[index[key]])
        if focus:
            # Frame the existing venue map on the relevant census group.
            # The working screen data supplies WGS 84 bounds after projection.
            data = read(source/"layers/areas_story.geojson")
            feature = next(f for f in data["features"] if str(f["properties"]["stpug_id"]) == focus)
            def xy(value):
                if isinstance(value[0], (float,int)):
                    yield value[:2]
                else:
                    for value in value:
                        yield from xy(value)
            points = list(xy(feature["geometry"]["coordinates"]))
            xs, ys = zip(*points)
            x,y = (min(xs)+max(xs))/2,(min(ys)+max(ys))/2
            assert 113 < x < 115 and 21 < y < 24
            dx,dy = max((max(xs)-min(xs))*.75,.008),max((max(ys)-min(ys))*.75,.006)
            sr={"wkid":4326}
            extent=dict(xmin=x-dx,xmax=x+dx,ymin=y-dy,ymax=y+dy,spatialReference=sr)
            center=dict(x=x,y=y,spatialReference=sr)
            scale=max(2*dx*111320*math.cos(math.radians(y)),2*dy*111320)*3779.52756/750*1.18
            view=dict(rotation=0,scale=scale,targetGeometry=center)
            res=copy.deepcopy(resources[node["data"]["map"]])
            res["data"].update(extent=extent,center=center,zoom=math.log2(591657527.59/scale),viewpoint=view)
            node["data"].update(extent=extent,center=center,viewpoint=view,map=add(res,resources,"r-"))
        return add(node)

    def card(heading, prose, key, label, values, focus=None):
        return (heading, prose, media(key,focus), label, values)

    def sidecar(index, cards):
        section = tagged["sections"][index]
        layout=section["layout"]
        position=section["panel_position"]
        slides=[]
        for title, body, media_id, label, values in cards:
            panel=add({"type":"immersive-narrative-panel","data":{"position":position,"size":"small","panelStyle":"themed"},
                       "children":[text(title,"h3"),text(body),*info(label,*values)]})
            slide=copy.deepcopy(panel_template)
            slide["children"]=[panel,media_id]
            slides.append(add(slide))
        return add({"type":"immersive","data":{"type":"sidecar","subtype":layout,
                     "narrativePanelPosition":position,"narrativePanelSize":"small"},"children":slides})

    def embed(key, label, fragment=""):
        node=copy.deepcopy(nodes[embeds[key]])
        for field in ("url","embedSrc"):
            node["data"][field]=node["data"][field].split("?")[0]+"?v="+REVISION+fragment
        return [add(node),caption(label)]

    children = [old_children[0],nav_id,old_children[2]]
    nav=[]
    titles=[section["title"] for section in tagged["sections"]]
    def chapter(i, intro=None):
        if i:
            children.extend([add({"type":"separator"}), add({"type":"text","data":{"type":"paragraph","text":"<br>"}})])
        h=text(f"{i+1} {titles[i]}","h2")
        nav.append({"nodeId":h})
        children.append(h)
        if intro:
            children.append(text(intro))

    a = [r for r in rows(source,"areas.csv") if int(r["res_cells"])]
    b = [float(r["net_out800_lo"]) for r in a]
    zero, maximum = b.count(0), b.count(100)
    chapter(0,"How does walking access to neighbourhood elderly centres vary across Hong Kong?")
    children += info("Study overview",("800","m · baseline distance","personWalking"),("33","Priority groups","flag"),("210","Assessed census groups","globe"))
    children.append(sidecar(0,[card("Older resident numbers and population shares",
        "The screening uses the share of residents aged 65+ in each census group. Headcounts describe a different part of the population picture. [2] [3]",
        "01_age","Census population measures", [("65+","Age group used in the screen","people"),("211","Census groups","globe")])]))
    chapter(1,"Combine population, residential cells, centre locations and the CSDI pedestrian network. [2] [3] [5] [7] [9]")
    children.append(sidecar(1,[
        card("Elderly centre locations","The main model uses 215 distinct NEC locations. A separate scenario adds 62 DECC locations. [6] [7]",
            "01_age","Elderly centre locations",[("215","Distinct NEC locations","pinEsri"),("62","DECC locations","governmentBuilding")]),
        card("Population and residential denominators","Use all residents for each group’s age-share denominator and all assigned residential ground area for the gap denominator. Group 295 has no assigned residential cells. [2] [3] [5]",
            "06_uncertainty","Assessment coverage",[("210","Assessed groups","globe"),("1","Group without residential cells","governmentBuilding")])]))
    chapter(2)
    children += embed("workflow","Analytical workflow")
    methods=[
        ("A transparent two-condition rule","Select a census group when at least 20% of its residents are aged 65+ and the lower bound of its residential gap is at least 30%."),
        ("Measure residential proximity","Use enabled CSDI links with directional restrictions and shared XYZ endpoints. Include both assumed connectors to eligible outdoor links, each capped at 100 m, in the shortest-path distance. Keep unresolved near-threshold cells separate. [9]"),
        ("Separate two sensitivity questions","Vary the screening cutoffs across 27 combinations of 500/800/1,000 m, 18/20/22% age share and 20/30/40% gap. Separately test 50, 100 and 150 m connector limits."),
        ("Review locations within shortlisted groups","Compare HAD-listed community venues by newly covered residential ground area. Deduct coverage gained by earlier selections when comparing additional venues. [8] [9]"),
    ]
    for title,body in methods: children += [text(title,"h3"),text(body)]
    chapter(3,"Compare the 800 m network results with straight-line coverage and examine the shortlist and potential outreach venues.")
    children.append(sidecar(3,[
        card("Residential outside-area shares cluster at zero and 100 percent",
             f"Among {len(a)} assessed groups, the network gap lower bound is zero in {zero} groups and 100% in {maximum}. The other {len(a)-zero-maximum} groups lie between these endpoints.",
             "03_network","Residential gap distribution",[(str(zero),"Zero gap","home"),(str(maximum),"Entirely beyond reach","personWalking")]),
        card("Thirty-three areas meet both criteria","The same 20% and 30% cutoffs select 14 areas by straight-line distance and 33 by network distance. The network adds 19 priorities.",
             "04_change","Priority screening results",[("14","Straight-line priorities","pinEsri"),("33","Network priorities","personWalking"),("19","Additional groups","flag")])]))
    children += [text("Explore assumptions","h3"),text("Adjust the three screening cutoffs, look up a census group or switch to a local route case. Open Layers on the map to control what is visible."),*embed("network","Pedestrian routes and residential gaps")]
    cases=rows(source,"venues_original_cases.csv")
    cards=[card("Sensitivity remains visible","Across 27 combinations, the shortlist ranges from 9 to 93 groups. At the baseline settings, 0.52% of assigned residential land remains unresolved at 800 m.",
                "11_sensitivity","Scenario sensitivity",[("27","Screening combinations","magnifyingGlass"),("33","Priority groups at baseline","flag")])]
    labels={"131":"Wan Chai group 131","620S":"Ta Kwu Ling group 620S","920":"Cheung Chau group 920"}
    for key,title in labels.items():
        case=next(r for r in cases if r["old_case_id"]==key)
        direct,network=(f"{float(case[f]):.2f}" for f in ("old_euclidean_gain_ha","network_gain_ha"))
        children_text=f"{case['name_en']} could add {network} ha of coverage within this group under the network model, compared with {direct} ha in the straight-line scenario. [8] [9]"
        cards.append(card(title,children_text,"14_case920_venue" if key=="920" else "07_venues",
                          "Potential venue coverage",[(direct,"ha · straight-line gain","pinEsri"),(network,"ha · network gain","personWalking")],
                          focus=None if key=="920" else key))
    children.append(sidecar(3,cards))
    children += [text("Compare model and existing locations","h3"),
                 text("Both distance models use the same residential denominator and 215 NECs. At 800 m, straight-line coverage is 46.24% and network coverage is 31.90%. Sha Tin and Kowloon route cases are available in the explorer. Comparing outreach venues also requires checking overlap, entrances and service capacity."),
                 next(k for k, n in nodes.items() if n["type"] == "swipe"), caption("Straight-line and 3D network gaps"),
                 *embed("charts","Additional coverage and overlap","#venue"),
                 text("Coverage by residential type and district","h3"),*embed("charts","Residential ground-area coverage","#housing"),
                 text("How the shortlist changes","h3"),*embed("charts","Screening sensitivity","#scenarios")]
    chapter(4)
    for title,body in [
        ("What the analysis supports","The network screen identifies 33 census groups where older-resident share and residential proximity both warrant local review."),
        ("What local comparisons add","In Sha Tin, a modelled route is about 1,200 m for a location 600 m away in a straight line. Across priority groups, a greedy sequence of Sha Kok, Lek Yuen and Cheung Chau adds 76.67 ha of residential coverage."),
        ("Limits and next steps","The model measures static route length over enabled links. Check route conditions, entrances, access hours and service capacity in fieldwork. Coverage percentages use residential ground area. [4] [9]")]:
        children += [text(title,"h3"),text(body)]
    chapter(5)
    children += reference_ids + [old_children[-1]]
    root["children"]=children
    nodes[nav_id]["data"]["links"]=nav
    reachable = set()

    def visit(key):
        if key in reachable:
            return
        reachable.add(key)
        node = nodes[key]
        for child in node.get("children", []):
            visit(child)
        if node["type"] == "swipe":
            for child in node["data"]["contents"].values():
                visit(child)

    visit(graph["root"])
    graph["nodes"] = {key: node for key, node in nodes.items() if key in reachable}
    return titles


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("baseline",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--maps-from",type=Path,default=ROOT/"build/network-update/revision2/arcgis-receipt.json")
    parser.add_argument("--publish",action="store_true")
    args=parser.parse_args()
    cfg=read(args.baseline/"local-config.json")
    tagged=json.loads(subprocess.check_output(["git","show",TAG+":story.json"],cwd=ROOT,encoding="utf-8"))
    data=read(args.baseline/"draft.json")
    receipt=read(args.maps_from)
    titles=assemble(data,tagged,args.source,receipt)
    cfg.update(asset_revision=REVISION,sections=[{"id":s["id"],"title":title,"slides":[]} for s,title in zip(tagged["sections"],titles)])
    args.output.mkdir(parents=True,exist_ok=True)
    for filename,obj in (("config.json",cfg),("generated.json",data)):
        (args.output/filename).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    if args.publish:
        from time import sleep
        from urllib.parse import urljoin
        from urllib.request import urlopen
        from arcgis.gis import GIS
        from arcgis.apps.storymap import StoryMap
        for path, marker in [("network/index.html", "explorer-controls"), ("charts/data.json", '"districts"')]:
            url = urljoin(cfg["pages_base_url"], "embeds/20261118/" + path) + "?v=" + REVISION
            for attempt in range(10):
                try:
                    with urlopen(url, timeout=10) as response:
                        if marker not in response.read().decode("utf-8"):
                            raise RuntimeError("The revised embed is not deployed yet.")
                    break
                except (OSError, RuntimeError):
                    if attempt == 9:
                        raise
                    sleep(5)
            print("Verified hosted asset:", url, flush=True)
        gis=GIS("pro")
        story=StoryMap(cfg["item_id"],gis=gis)
        check_baseline(story,cfg,args.baseline)
        story._properties=data
        save_draft(story,cfg)
        print("Restored tagged chapters in the original draft.",flush=True)
        baseline=inspect_story(cfg)
        publish_current(cfg,str(baseline),str(args.output/"generated.json"),refresh_map_views=False)


if __name__=="__main__":
    main()
