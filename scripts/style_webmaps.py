"""Apply the approved native-map palette and local ArcPy-derived study outline."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def collection(key,title,geometry_type,geometry,symbol):
    return {'id':key,'title':title,'layerType':'ArcGISFeatureLayer','visibility':True,'opacity':1,'showLegend':False,'disablePopup':True,
            'featureCollection':{'layers':[{'layerDefinition':{'name':title,'type':'Feature Layer','geometryType':geometry_type,'objectIdField':'OBJECTID','fields':[{'name':'OBJECTID','type':'esriFieldTypeOID','alias':'OBJECTID'}],'drawingInfo':{'renderer':{'type':'simple','symbol':symbol}}},'featureSet':{'geometryType':geometry_type,'spatialReference':{'wkid':4326},'features':[{'attributes':{'OBJECTID':1},'geometry':geometry}]},'showLegend':False}]}}

def run():
    theme=json.loads((ROOT/'assets/map-theme.json').read_text())
    def rgba(c): return [int(c[i:i+2],16) for i in (1,3,5)]+[255]
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
                if key!='district_context':
                    layer['showLegend']=True
                    layer.get('featureCollection',{})['showLegend']=True
                    sub['showLegend']=True
                entries=renderer.get('classBreakInfos',renderer.get('uniqueValueInfos',[]))
                pastel=[rgba(c) for c in theme['sequential']]
                for i,info in enumerate(entries):
                    if info.get('symbol',{}).get('type')=='esriSFS':
                        info['symbol']['color']=pastel[round(i*4/max(1,len(entries)-1))]
                # Categorical semantics must not inherit the sequential ramp order.
                if renderer.get('type')=='uniqueValue':
                    field=renderer.get('field1')
                    for info in entries:
                        value=str(info['value'])
                        if value=='-1':
                            info['label']='Not assessed'
                            info['symbol']['color']=[165,173,176,255]
                        elif field and (field.startswith('priority_') or field=='centroid_disagree'):
                            info['symbol']['color']=([144,105,177,255] if value=='1' else [239,235,245,255])
                    declared={str(e['value']) for e in entries}
                    observed={str(f['attributes'].get(field)) for f in sub['featureSet']['features']}
                    if observed <= declared:
                        # No fallback is needed; leaving it creates a duplicate legend item.
                        renderer['defaultSymbol']=None
                        renderer.pop('defaultLabel',None)
                    else:
                        renderer['defaultLabel']='Other / missing value'
                if key in {'nec_sites','decc_sites'}:
                    renderer['symbol']={'type':'esriSMS','style':'esriSMSDiamond' if key=='nec_sites' else 'esriSMSTriangle','color':[20,83,65,245] if key=='nec_sites' else [20,83,65,245],'size':5.5 if key=='nec_sites' else 7,'outline':{'type':'esriSLS','style':'esriSLSSolid','color':[255,255,255,250],'width':.7}}
                if key=='population60':
                    for info,size in zip(renderer['classBreakInfos'],[6,10,15,21,27]):
                        info['symbol'].update(color=rgba(theme['population'])[:3]+[185],size=size)
                        info['symbol']['outline']={'type':'esriSLS','style':'esriSLSSolid','color':[255,255,255,230],'width':.7}
                    renderer['defaultSymbol']=copy.deepcopy(renderer['classBreakInfos'][0]['symbol'])
                    renderer['defaultSymbol']['color']=[165,173,176,255]
                if key=='age_share':
                    for info,colour in zip(renderer['classBreakInfos'],[rgba(c) for c in theme['age_share']]):info['symbol']['color']=colour
                if key=='residential' and path.stem in {'M11_residential_nec','M12_residential_combined'}:
                    colours=(['#eee8f4','#af98c4'] if path.stem=='M11_residential_nec' else ['#f3eadf','#b79b7a'])
                    for info in renderer['uniqueValueInfos']:
                        info['symbol']['color']=rgba(colours[int(info['value'])])
        data['operationalLayers']=[copy.deepcopy(land_layer)]+layers+[copy.deepcopy(outline_layer)]
        if path.stem=='M01_population':
            boundary=data['operationalLayers'][-1]['featureCollection']['layers'][0]['layerDefinition']['drawingInfo']['renderer']['symbol']
            boundary.update(color=[128,40,53,190],width=.8)
        data['baseMap']={'title':'Minimal pale-blue vector basemap','baseMapLayers':[{'id':'pale_blue_water_context','layerType':'VectorTileLayer','title':'Esri World Basemap v2 (minimal, no labels)','styleUrl':'https://jaffe2718.github.io/hk-elderly/embeds/elderly-map/native-basemap.json','visibility':True,'opacity':1}]}
        data.setdefault('initialState',{}).setdefault('viewpoint',{})['targetGeometry']=copy.deepcopy(study_extent)
        path.write_text(json.dumps(data,ensure_ascii=False)+'\n',encoding='utf-8')
    (ROOT/'docs/embeds/elderly-map/theme.json').write_text(json.dumps(theme)+'\n',encoding='utf-8')
    (ROOT/'docs/embeds/elderly-map/study-outline.geojson').write_bytes((ROOT/'assets/boundaries/hk-study-area-outline.geojson').read_bytes())
    (ROOT/'docs/embeds/elderly-map/native-basemap.json').write_bytes((ROOT/'assets/basemaps/minimal-vector.json').read_bytes())
    print('Styled 12 native Web Maps using the shared muted-lavender theme.')

if __name__=='__main__':run()
