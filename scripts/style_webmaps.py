"""Apply the approved native-map palette and local ArcPy-derived study outline."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def collection(key,title,geometry_type,geometry,symbol):
    return {'id':key,'title':title,'layerType':'ArcGISFeatureLayer','visibility':True,'opacity':1,'showLegend':False,'disablePopup':True,
            'featureCollection':{'layers':[{'layerDefinition':{'name':title,'type':'Feature Layer','geometryType':geometry_type,'objectIdField':'OBJECTID','fields':[{'name':'OBJECTID','type':'esriFieldTypeOID','alias':'OBJECTID'}],'drawingInfo':{'renderer':{'type':'simple','symbol':symbol}}},'featureSet':{'geometryType':geometry_type,'spatialReference':{'wkid':4326},'features':[{'attributes':{'OBJECTID':1},'geometry':geometry}]},'showLegend':False}]}}

def run():
    land=json.loads((ROOT/'assets/boundaries/hk-study-area-land.geojson').read_text())['features'][0]['geometry']
    polygons=land['coordinates'] if land['type']=='MultiPolygon' else [land['coordinates']]
    rings=[]
    for polygon in polygons:
        for i,ring in enumerate(polygon):
            area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]))
            rings.append(list(reversed(ring)) if (i==0 and area>0) or (i>0 and area<0) else ring)
    line=json.loads((ROOT/'assets/boundaries/hk-study-area-outline.geojson').read_text())['features'][0]['geometry']
    points=[point for part in line['coordinates'] for point in part]
    xmin=min(p[0] for p in points);xmax=max(p[0] for p in points);ymin=min(p[1] for p in points);ymax=max(p[1] for p in points)
    dx=(xmax-xmin)*.05;dy=(ymax-ymin)*.05
    study_extent={'xmin':xmin-dx,'xmax':xmax+dx,'ymin':ymin-dy,'ymax':ymax+dy,'spatialReference':{'wkid':4326}}
    land_layer=collection('study_land','Study area land','esriGeometryPolygon',{'rings':rings,'spatialReference':{'wkid':4326}}, {'type':'esriSFS','style':'esriSFSSolid','color':[249,251,250,225],'outline':{'type':'esriSLS','style':'esriSLSNull'}})
    outline_layer=collection('study_outline','Hong Kong study area outline','esriGeometryPolyline',{'paths':line['coordinates'],'spatialReference':{'wkid':4326}},{'type':'esriSLS','style':'esriSLSSolid','color':[128,40,53,245],'width':1.2})
    for path in sorted((ROOT/'assets/webmaps').glob('M*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        layers=[l for l in data['operationalLayers'] if l['id'] not in {'study_land','study_outline'}]
        for layer in layers:
            key=layer['id']
            if key=='district_context':layer['visibility']=False
            for sub in layer.get('featureCollection',{}).get('layers',[]):
                renderer=sub['layerDefinition'].get('drawingInfo',{}).get('renderer',{})
                if key in {'nec_sites','decc_sites'}:
                    renderer['symbol']={'type':'esriSMS','style':'esriSMSDiamond' if key=='nec_sites' else 'esriSMSTriangle','color':[20,83,65,245] if key=='nec_sites' else [20,83,65,245],'size':5.5 if key=='nec_sites' else 7,'outline':{'type':'esriSLS','style':'esriSLSSolid','color':[255,255,255,250],'width':.7}}
                if key=='population60':
                    for info,size in zip(renderer['classBreakInfos'],[6,10,15,21,27]):
                        info['symbol'].update(color=[190,173,218,155],size=size)
                    renderer['defaultSymbol']=copy.deepcopy(renderer['classBreakInfos'][0]['symbol'])
                if key=='age_share':
                    for info,colour in zip(renderer['classBreakInfos'],[[229,242,249,240],[172,210,231,240],[96,160,196,240],[36,103,145,245]]):info['symbol']['color']=colour
        data['operationalLayers']=[copy.deepcopy(land_layer)]+layers+[copy.deepcopy(outline_layer)]
        data['baseMap']={'title':'Minimal pale-blue vector basemap','baseMapLayers':[{'id':'pale_blue_water_context','layerType':'VectorTileLayer','title':'Esri World Basemap v2 (minimal, no labels)','styleUrl':'https://jaffe2718.github.io/hk-elderly/embeds/elderly-map/native-basemap.json','visibility':True,'opacity':1}]}
        data.setdefault('initialState',{}).setdefault('viewpoint',{})['targetGeometry']=copy.deepcopy(study_extent)
        path.write_text(json.dumps(data,ensure_ascii=False)+'\n',encoding='utf-8')
    (ROOT/'docs/embeds/elderly-map/study-outline.geojson').write_bytes((ROOT/'assets/boundaries/hk-study-area-outline.geojson').read_bytes())
    (ROOT/'docs/embeds/elderly-map/native-basemap.json').write_bytes((ROOT/'assets/basemaps/minimal-vector.json').read_bytes())
    print('Styled 12 native Web Maps: pale-purple circles, dark-green facility points, pale-blue water and dark-red exterior outline.')

if __name__=='__main__':run()
