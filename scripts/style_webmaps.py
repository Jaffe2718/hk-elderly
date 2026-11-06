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
    current=(ROOT/'assets/analysis/current_model.json').exists()
    embed_root=ROOT/('docs/embeds/20261106/elderly-map' if current else 'docs/embeds/elderly-map')
    for path in sorted((ROOT/'assets/webmaps').glob('M*.json')):
        if current and path.stem not in {'M01_population','M02_coverage','M03_binary800','M06_sensitivity27','M10_facility_definition','M13_case131','M14_case620S','M15_case920'}:continue
        data=json.loads(path.read_text(encoding='utf-8'))
        layers=[l for l in data['operationalLayers'] if l['id'] not in {'study_land','study_outline','facilities'}]
        for layer in layers:
            key=layer['id']
            if key=='district_context':layer['visibility']=False
            for sub in layer.get('featureCollection',{}).get('layers',[]):
                renderer=sub['layerDefinition'].get('drawingInfo',{}).get('renderer',{})
                renderer.setdefault('legendOptions',{})['title']=''
                field=renderer.get('field1',renderer.get('field'))
                titles={'elderly_pct':'Residents aged 60+ (%)','elderly_n':'Residents aged 65+ (2021)','pct65':'Residents aged 65+ (%)','age65_assessed':'Residents aged 65+ (%)',
                        'nec_out800_pct':'Residential land beyond NEC 800 m (%)','any_out800_pct':'Residential land beyond NEC + DECC 800 m (%)',
                        'sensitivity_hits27':'Selections across 27 scenarios','nec2plus_pct800':'Residential land within 800 m of 2+ NECs (%)',
                        'centroid_disagree':'Residential vs centroid screening','nec_decc_gain_pp':'Coverage gain from adding DECC (pp)',
                        'demand_coverage_class':'Older population and residential proximity'}
                if field in titles: layer['title']=titles[field]
                elif field and field.startswith('priority_'):
                    suffix={'priority_main':'800 m','priority_500':'500 m','priority_1000':'1,000 m','priority_age65':'age 65+ · 800 m','priority_age75':'age 75+ · 800 m'}.get(field,'800 m')
                    layer['title']='Priority screen · '+suffix
                sub['layerDefinition']['name']=layer.get('title',sub['layerDefinition'].get('name',''))
                if key!='district_context':
                    layer['showLegend']=True
                    layer.get('featureCollection',{})['showLegend']=True
                    sub['showLegend']=True
                entries=renderer.get('classBreakInfos',renderer.get('uniqueValueInfos',[]))
                pastel=[rgba(c) for c in theme['sequential']]
                for i,info in enumerate(entries):
                    if info.get('symbol',{}).get('type')=='esriSFS' and field not in {'A_status','venue_status'}:
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
                    renderer['symbol']={'type':'esriSMS','style':'esriSMSDiamond' if key=='nec_sites' else 'esriSMSTriangle','color':rgba(theme['facility']) if key=='nec_sites' else rgba(theme['decc']),'size':5.5 if key=='nec_sites' else 7,'outline':{'type':'esriSLS','style':'esriSLSSolid','color':[255,255,255,250],'width':.7}}
                if key=='population60':
                    for info,size in zip(renderer['classBreakInfos'],[6,10,15,21,27]):
                        info['symbol'].update(color=rgba(theme['population'])[:3]+[185],size=size)
                        info['symbol']['outline']={'type':'esriSLS','style':'esriSLSSolid','color':[255,255,255,230],'width':.7}
                    renderer['defaultSymbol']=copy.deepcopy(renderer['classBreakInfos'][0]['symbol'])
                    renderer['defaultSymbol']['color']=[165,173,176,255]
                if key=='age_share':
                    for info,colour in zip(renderer['classBreakInfos'],[rgba(c) for c in theme['age_share']]):info['symbol']['color']=colour
                if renderer.get('type')=='uniqueValue':
                    for info in renderer.get('uniqueValueInfos',[]):
                        value=str(info['value'])
                        if field and field.startswith('priority_') and value in {'0','1'}:info['label']='Selected for review' if value=='1' else 'Not selected'
                        if field=='centroid_disagree' and value in {'0','1'}:info['label']='Same result' if value=='0' else 'Different result'
                if renderer.get('type')=='classBreaks':
                    values=[f['attributes'].get(field) for f in sub['featureSet']['features']]
                    lo=renderer.get('minValue',0);hi=renderer['classBreakInfos'][-1]['classMaxValue']
                    if all(isinstance(v,(int,float)) and lo<=v<=hi for v in values):
                        renderer['defaultSymbol']=None;renderer.pop('defaultLabel',None)
                    else:
                        renderer['defaultLabel']='Not assessed'
                if key=='residential' and path.stem in {'M11_residential_nec','M12_residential_combined'}:
                    colours=(['#eee8f4','#af98c4'] if path.stem=='M11_residential_nec' else ['#f3eadf','#b79b7a'])
                    for info in renderer['uniqueValueInfos']:
                        info['symbol']['color']=rgba(colours[int(info['value'])])
        by_id={l['id']:l for l in layers}
        if {'nec_sites','decc_sites'} <= by_id.keys():
            # One point layer gives the two facility classes one coherent legend,
            # without a native layer separator between NEC and DECC.
            combined=copy.deepcopy(by_id['nec_sites'])
            combined.update(id='facilities',title='Elderly centre premises',visibility=False)
            sub=combined['featureCollection']['layers'][0]
            definition=sub['layerDefinition']
            fields={f['name']:copy.deepcopy(f) for key in ['nec_sites','decc_sites'] for f in by_id[key]['featureCollection']['layers'][0]['layerDefinition']['fields']}
            fields['facility_kind']={'name':'facility_kind','alias':'Facility type','type':'esriFieldTypeString','length':8}
            definition.update(name='Elderly centre premises',fields=list(fields.values()))
            features=[];infos=[]
            for key,kind in [('nec_sites','NEC'),('decc_sites','DECC')]:
                source=by_id[key]['featureCollection']['layers'][0]
                infos.append({'value':kind,'label':kind+' premises','symbol':copy.deepcopy(source['layerDefinition']['drawingInfo']['renderer']['symbol'])})
                for feature in source['featureSet']['features']:
                    feature=copy.deepcopy(feature)
                    feature['attributes']={name:feature['attributes'].get(name) for name in fields}
                    feature['attributes'].update(facility_kind=kind)
                    feature['attributes'][definition.get('objectIdField','OBJECTID')]=len(features)+1
                    features.append(feature)
            sub['featureSet']['features']=features
            definition['drawingInfo']['renderer']={'type':'uniqueValue','field1':'facility_kind','uniqueValueInfos':infos,'defaultSymbol':None,'legendOptions':{'title':''}}
            sub['popupInfo']={'title':'{facility_kind}: {name_en}','popupElements':[{'type':'fields','fieldInfos':[{'fieldName':'facility_kind','label':'Facility type'},{'fieldName':'name_en','label':'Name'},{'fieldName':'address_en','label':'Address'}]},{'type':'text','text':'Mapped premises indicate location, not service capacity.'}],'showAttachments':False}
            layers.append(combined)
        data['operationalLayers']=[copy.deepcopy(land_layer)]+layers+[copy.deepcopy(outline_layer)]
        if path.stem=='M01_population':
            boundary=data['operationalLayers'][-1]['featureCollection']['layers'][0]['layerDefinition']['drawingInfo']['renderer']['symbol']
            boundary.update(color=[128,40,53,190],width=.8)
        data['baseMap']={'title':'Minimal pale-blue vector basemap','baseMapLayers':[{'id':'pale_blue_water_context','layerType':'VectorTileLayer','title':'Esri World Basemap v2 (minimal, no labels)','styleUrl':'https://jaffe2718.github.io/hk-elderly/embeds/20261106/elderly-map/native-basemap.json','visibility':True,'opacity':1}]}
        if not path.stem.startswith(('M13_','M14_','M15_')):
            data.setdefault('initialState',{}).setdefault('viewpoint',{})['targetGeometry']=copy.deepcopy(study_extent)
        path.write_text(json.dumps(data,ensure_ascii=False)+'\n',encoding='utf-8')
    (embed_root/'theme.json').write_text(json.dumps(theme)+'\n',encoding='utf-8')
    (embed_root/'study-outline.geojson').write_bytes((ROOT/'assets/boundaries/hk-study-area-outline.geojson').read_bytes())
    (embed_root/'native-basemap.json').write_bytes((ROOT/'assets/basemaps/minimal-vector.json').read_bytes())
    print('Styled active native Web Maps using the shared muted-lavender theme.')

if __name__=='__main__':run()
