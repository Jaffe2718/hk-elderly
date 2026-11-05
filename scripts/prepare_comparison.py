"""Prepare two aligned local map panels from supplied native Web Map features."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def polygon(rings):
    polygons=[]
    for ring in rings:
        area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]))
        if area<0 or not polygons:polygons.append([list(reversed(ring))])
        else:polygons[-1].append(list(reversed(ring)))
    return {'type':'MultiPolygon','coordinates':polygons}
def convert(layer):
    sub=layer['featureCollection']['layers'][0];features=[]
    for f in sub['featureSet']['features']:
        g=f['geometry'];geo=polygon(g['rings']) if 'rings' in g else {'type':'Point','coordinates':[g['x'],g['y']]}
        features.append({'type':'Feature','properties':f['attributes'],'geometry':geo})
    return {'type':'FeatureCollection','features':features}
def run():
    output=ROOT/'docs/embeds/coverage-comparison';output.mkdir(exist_ok=True)
    a=json.loads((ROOT/'assets/webmaps/M11_residential_nec.json').read_text());b=json.loads((ROOT/'assets/webmaps/M12_residential_combined.json').read_text())
    assert a['bookmarks']==b['bookmarks'],'Comparison bookmarks differ'
    panels=[]
    for source in [a,b]:
        layer=next(l for l in source['operationalLayers'] if l['id']=='residential')
        panels.append({'residential':convert(layer),'field':layer['featureCollection']['layers'][0]['layerDefinition']['drawingInfo']['renderer']['field1']})
    data={'panels':panels,'cases':a['bookmarks'],'land':json.loads((ROOT/'assets/boundaries/hk-study-area-land.geojson').read_text()),'outline':json.loads((ROOT/'assets/boundaries/hk-study-area-outline.geojson').read_text())}
    for key in ['nec_sites','decc_sites']:
        data[key]=convert(next(l for l in b['operationalLayers'] if l['id']==key))
    (output/'data.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    print('Prepared matched comparison panels:',[len(p['residential']['features']) for p in panels])
if __name__=='__main__':run()
