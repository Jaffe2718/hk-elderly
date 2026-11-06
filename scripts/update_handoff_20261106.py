"""Prepare the approved P60 model from the November 6 handoff; never publish."""
import csv,copy,hashlib,json,math,re
from pathlib import Path
import numpy as np
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
EMBEDS=ROOT/'docs/embeds/20261106'
SOURCE=ROOT/'build/handoff-20261106/redo7302'
AGE=19.913163372872837
GAP=30.75788624778998
CASES=['131','620S','920']
NAMES={'131':'Wan Chai','620S':'Ta Kwu Ling area','920':'Cheung Chau'}
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def records(path):return list(csv.DictReader(path.open(encoding='utf-8-sig')))
def clean(p):return {k:v for k,v in p.items() if not k.endswith('_zh') and not(k=='address' and isinstance(v,str) and re.search('[\u4e00-\u9fff]',v))}
def esri(g):
 if g['type']=='Point':return {'x':g['coordinates'][0],'y':g['coordinates'][1]}
 rings=[]
 for polygon in ([g['coordinates']] if g['type']=='Polygon' else g['coordinates']):
  for i,ring in enumerate(polygon):
   area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]))
   rings.append(list(reversed(ring)) if (i==0 and area>0) or(i>0 and area<0) else ring)
 return {'rings':rings}
def layer(key,title,fc,renderer,visible=True):
 props=[{k:(json.dumps(v) if isinstance(v,(list,dict)) else v) for k,v in clean(f['properties']).items()} for f in fc['features']];keys=sorted(set().union(*(p.keys() for p in props)))
 fields=[{'name':'OBJECTID','type':'esriFieldTypeOID','alias':'OBJECTID'}]
 for k in keys:
  if k=='OBJECTID':continue
  value=next((p[k] for p in props if p.get(k)is not None),None)
  fields.append({'name':k,'alias':k.replace('_',' '),'type':'esriFieldTypeDouble' if isinstance(value,(int,float)) else 'esriFieldTypeString',**({} if isinstance(value,(int,float)) else {'length':500})})
 features=[{'geometry':esri(f['geometry']),'attributes':{**p,'OBJECTID':i+1}} for i,(f,p) in enumerate(zip(fc['features'],props))]
 geom='esriGeometryPoint' if fc['features'][0]['geometry']['type']=='Point' else 'esriGeometryPolygon'
 popup={'title':title+' · {stpug_id}','popupElements':[{'type':'fields','fieldInfos':[{'fieldName':k,'label':{'stpug_id':'STPUG','stpug':'STPUG','place_en':'Area','pop_total':'All residents (2021)','pop_65plus':'Residents aged 65+ (2021)','pct65':'Residents aged 65+ (%)','res_cells':'Residential 10 m cells','nec_out800_pct':'Residential land beyond NEC 800 m (%)','scenario_hits':'Selections across 27 scenarios','patch_ha':'Residential ground area (ha)','A_status':'Coverage after model A','venue_status':'Coverage after community venue'}.get(k,k.replace('_',' '))} for k in ['stpug_id','stpug','place_en','pop_total','pop_65plus','pct65','res_cells','nec_out800_pct','scenario_hits','patch_ha','A_status','venue_status'] if k in keys]},{'type':'text','text':'Population and housing: 2021. Facilities: 2 November 2026. Straight-line distances in metres; coverage is residential ground area, not people served.'}]}
 return {'id':key,'title':title,'layerType':'ArcGISFeatureLayer','visibility':visible,'opacity':1,'showLegend':True,'featureCollection':{'layers':[{'layerDefinition':{'name':title,'type':'Feature Layer','geometryType':geom,'objectIdField':'OBJECTID','fields':fields,'drawingInfo':{'renderer':renderer}},'featureSet':{'geometryType':geom,'spatialReference':{'wkid':4326},'features':features},'popupInfo':popup}]}}
def fill(c):return {'type':'esriSFS','style':'esriSFSSolid','color':c,'outline':{'type':'esriSLS','style':'esriSLSSolid','color':[255,255,255,240],'width':.5}}
def breaks(field,bounds,labels):return {'type':'classBreaks','field':field,'minValue':0,'classBreakInfos':[{'classMaxValue':b,'label':l,'symbol':fill([210,195,225,255])} for b,l in zip(bounds,labels)],'defaultLabel':'Not assessed','defaultSymbol':fill([165,173,176,255])}
def unique(field,values,labels):return {'type':'uniqueValue','field1':field,'uniqueValueInfos':[{'value':str(v),'label':l,'symbol':fill([210,195,225,255])} for v,l in zip(values,labels)],'defaultSymbol':None}
def run():
 shared=read(ROOT/'assets/analysis/shared_2021_indicators.json')
 groups=read(SOURCE/'maps/layers/screening_web.geojson')
 w=openpyxl.load_workbook(SOURCE.parent/'HK_Elderly_Analysis_Tables.xlsx',read_only=True,data_only=True)
 dynamic={str(r[0]):r for r in list(w['动态筛查'].values)[7:] if r and r[0] is not None}
 scenarios=records(SOURCE/'model/tables/scenarios_27.csv');main=next(r for r in scenarios if r['id']=='r800_a60_g60')
 assert float(main['age_cut'])==AGE and float(main['gap_cut'])==GAP
 rows=[]
 for f in groups['features']:
  p=clean(f['properties']);sid=str(p['stpug_id']);old=shared[sid];r=dynamic[sid]
  assert p['pop_total']==old['pop_total'] and p['pop_65plus']==old['pop_65plus']
  assert p['res_cells']==old['res_cells']
  if p['assessed']:assert abs(p['out800_pct']-old['nec_out800_pct'])<1e-9
  p.update(old);p['pct60']=old['elderly_n']/p['pop_total']*100;p['pct75']=old['pop_75plus']/p['pop_total']*100
  p['elderly_n']=p['pop_65plus'];p['elderly_pct']=p['pct65'];p['age65_assessed']=p['pct65'] if p['assessed'] else None;p['res_area_km2']=p['res_cells']*.0001;p['nec_out800_pct']=p['out800_pct']
  for radius,col in [(500,5),(800,6),(1000,7)]:p['out_share_'+str(radius)]=r[col]/p['res_cells'] if p['assessed'] else None
  p['fixed_priority']=p['priority'];p['priority_main']=int(p['pct65']>=AGE and p['out800_pct']>=GAP) if p['assessed'] else -1
  p['priority']=p['priority_main'];p['sensitivity_hits27']=p['scenario_hits'];p['scenario_membership']=[int(sid in s['selected_ids'].split('|')) if p['assessed'] else None for s in scenarios]
  p['source_year']=2021;p['place_en']=p.get('place_en') or NAMES.get(sid,'Statistical area '+sid)
  p['demand_coverage_class']=1 if p['priority_main']==1 else 2 if p['pct65']>=AGE else 3 if p['assessed'] and p['out800_pct']>=GAP else 4
  if not p['assessed']:p['demand_coverage_class']=-1
  p['screen_class']={1:'Priority',2:'Age only',3:'Gap only',4:'Neither',-1:'Not assessed'}[p['demand_coverage_class']]
  p['class_en']=p['screen_class']
  f['properties']=p;rows.append(p)
 assessed=[p for p in rows if p['assessed']]
 cuts={a:float(np.quantile([p['pct'+a] for p in assessed],.6)) for a in ['60','65','75']}
 assert abs(cuts['65']-AGE)<1e-10
 for p in rows:
  for r in [500,800,1000]:p['priority_'+str(r)]=int(p['pct65']>=AGE and p['out_share_'+str(r)]*100>=GAP) if p['assessed'] else -1
  for a in ['60','65','75']:p['priority_age'+a]=int(p['pct'+a]>=cuts[a] and p['out800_pct']>=GAP) if p['assessed'] else -1
  p['nec_decc_priority_800']=int(p['pct65']>=AGE and p['any_out800_pct']>=GAP) if p['assessed'] else -1
 # Independently reproduce all source scenario memberships before writing outputs.
 for scenario in scenarios:
  radius=str(scenario['radius_m']);ac=float(np.quantile([p['pct65'] for p in assessed],float(scenario['age_quantile'])));gc=float(np.quantile([p['out_share_'+radius]*100 for p in assessed],float(scenario['gap_quantile'])))
  actual={p['stpug_id'] for p in assessed if p['pct65']>=ac and p['out_share_'+radius]*100>=gc}
  assert actual==set(scenario['selected_ids'].split('|')),scenario['id']
 for p in assessed:assert sum(p['scenario_membership'])==p['scenario_hits']
 selected=[p for p in rows if p['priority_main']==1]
 assert len(selected)==13 and {p['stpug_id'] for p in selected}==set(main['selected_ids'].split('|'))
 centres={}
 for key in ['nec','decc']:
  fc=read(SOURCE/f'maps/layers/{key}_sites.geojson')
  for f in fc['features']:f['properties']=clean(f['properties'])
  centres[key]=fc
 old_centres=read(ROOT/'assets/analysis/shared_facility_coordinates.json')
 for key,fc in centres.items():
  old=np.array(old_centres[key]);new=np.array([f['geometry']['coordinates'] for f in fc['features']])
  assert len(old)==len(new)
  scale=np.array([111320*math.cos(math.radians(22.35)),111320])
  assert max(np.min(np.linalg.norm((old-point)*scale,axis=1)) for point in new)<.1
 population={'type':'FeatureCollection','features':[{'type':'Feature','properties':f['properties'],'geometry':{'type':'Point','coordinates':[f['properties']['label_xy'][1],f['properties']['label_xy'][0]]}} for f in groups['features']]}
 payload={'groups':groups,'population':population,'centres':centres,'cohortCuts':cuts,'gapCut':GAP,'mainAge':'65','mainCount':13,'cases':CASES,'names':NAMES,'model':'P60/P60 · 800 m'}
 write(EMBEDS/'elderly-map/data.json',payload)
 write(ROOT/'assets/analysis/current_model.json',{'age_cut':AGE,'gap_cut':GAP,'selected_ids':[p['stpug_id'] for p in selected],'scenarios':scenarios,'cohort_cuts':cuts,'assessed':210,'fixed_threshold_count':14})
 template=read(ROOT/'assets/webmaps/M03_binary800.json')
 def save(key,layers,extent=None):
  d=copy.deepcopy(template);d['operationalLayers']=layers
  if extent:d['initialState']['viewpoint']={'targetGeometry':extent}
  d.pop('bookmarks',None);write(ROOT/f'assets/webmaps/{key}.json',d)
 site_layers=[layer(k+'_sites',k.upper()+' premises',fc,{'type':'simple','symbol':{'type':'esriSMS','style':'esriSMSDiamond','color':[20,83,65,255],'size':5.5}},k=='nec') for k,fc in centres.items()]
 priority=layer('main','Priority screen · 65+ · P60',groups,unique('priority_main',[1,0,-1],['Selected for review','Not selected','Not assessed']))
 save('M03_binary800',[priority,*copy.deepcopy(site_layers)])
 pop_renderer=breaks('elderly_n',[2500,5000,10000,20000,1000000],['0–2,500','2,501–5,000','5,001–10,000','10,001–20,000','>20,000'])
 for info,size in zip(pop_renderer['classBreakInfos'],[6,10,15,21,27]):info['symbol']={'type':'esriSMS','style':'esriSMSCircle','size':size,'color':[190,173,218,185]}
 save('M01_population',[layer('age_share','Residents aged 65+ (%)',groups,breaks('age65_assessed',[15,20,25,100],['0–15%','>15–20%','>20–25%','>25%']),False),layer('population60','Residents aged 65+ (2021)',population,pop_renderer),*copy.deepcopy(site_layers)])
 save('M02_coverage',[layer('coverage','Residential land beyond NEC 800 m (%)',groups,breaks('nec_out800_pct',[0,25,50,75,100],['0%','>0–25%','>25–50%','>50–75%','>75–100%'])),*copy.deepcopy(site_layers)])
 save('M06_sensitivity27',[layer('scenario','Selections across 27 scenarios',groups,breaks('sensitivity_hits27',[0,3,9,18,27],['0','1–3','4–9','10–18','19–27'])),*copy.deepcopy(site_layers)])
 both=copy.deepcopy(site_layers)
 for l in both:l['visibility']=True
 save('M10_facility_definition',[layer('any','Residential land beyond NEC + DECC 800 m (%)',groups,breaks('any_out800_pct',[0,25,50,75,100],['0%','>0–25%','>25–50%','>50–75%','>75–100%'])),*both])
 points=read(SOURCE/'sites/data/selected_reference_locations.geojson')
 case_payload=[]
 for sid,key in zip(CASES,['M13_case131','M14_case620S','M15_case920']):
  fc=read(SOURCE/f'sites/data/case_{sid}_coverage.geojson');pts={'type':'FeatureCollection','features':[]}
  for f in points['features']:
   if str(f['properties']['stpug'])!=sid:continue
   f=copy.deepcopy(f);f['properties']=clean(f['properties']);f['properties']['name_en']=f['properties'].get('name_en') or 'Model reference '+f['properties']['role'];pts['features'].append(f)
  native=read(SOURCE/f'maps/webmaps/case_{sid}.json');extent=native['initialState']['viewpoint']['targetGeometry']
  if extent['spatialReference']['wkid'] in [102100,3857]:
   extent={'xmin':math.degrees(extent['xmin']/6378137),'xmax':math.degrees(extent['xmax']/6378137),'ymin':math.degrees(2*math.atan(math.exp(extent['ymin']/6378137))-math.pi/2),'ymax':math.degrees(2*math.atan(math.exp(extent['ymax']/6378137))-math.pi/2),'spatialReference':{'wkid':4326}}
  colours={'Already covered':[235,236,238,255],'Newly covered':[175,152,196,255],'Still outside':[237,216,190,255]}
  r=unique('A_status',list(colours),list(colours))
  for info in r['uniqueValueInfos']:info['symbol']['color']=colours[info['value']]
  shown={'type':'FeatureCollection','features':[f for f in pts['features'] if f['properties']['role'] in {'A','HALL'}]}
  point_renderer={'type':'uniqueValue','field1':'role','defaultSymbol':None,'uniqueValueInfos':[{'value':role,'label':label,'symbol':{'type':'esriSMS','style':style,'color':colour,'size':8}} for role,label,style,colour in [('A','Model reference A','esriSMSDiamond',[144,105,177,255]),('HALL','Existing community venue','esriSMSSquare',[183,93,34,255])]]}
  point_layer=layer('case_points','Reference locations',shown,point_renderer)
  point_layer['featureCollection']['layers'][0]['popupInfo']={'title':'{role}: {name_en}','popupElements':[{'type':'fields','fieldInfos':[{'fieldName':k,'label':v} for k,v in [('address_en','Address'),('added_800_ha','Newly covered residential land (ha)'),('after_A_additional_ha','Additional land covered after A (ha)')]]},{'type':'text','text':'Model points are hypothetical reference locations, not approved sites. Venue access and availability require checking.'}]}
  save(key,[layer('case_A','Coverage with model site A',fc,r),point_layer,*copy.deepcopy(site_layers)],extent)
  case_payload.append({'id':sid,'name':NAMES[sid],'extent':extent,'coverage':fc,'points':pts})
 write(EMBEDS/'coverage-comparison/data-v2.json',{'cases':case_payload,'centres':centres,'land':read(ROOT/'assets/boundaries/hk-study-area-land.geojson'),'outline':read(ROOT/'assets/boundaries/hk-study-area-outline.geojson')})
 # Site gains are group-local and remain valid when area 149 is removed.
 sites=[clean(r) for r in records(SOURCE/'sites/data/site_summary.csv') if r['stpug'] in {p['stpug_id'] for p in selected}]
 write(ROOT/'assets/analysis/site_results.json',sites)
 # Keep compatible coverage series only after validating the updated NEC totals.
 charts=read(ROOT/'docs/embeds/charts/data.json')
 housing=list(w['住宅类型'].values)[4:7]
 for source,row in zip(housing,charts['housing']['rows']):
  assert abs(source[5]-float(row[1]))<.06
  row[1]=source[5]
 union=sorted({p['stpug_id'] for p in rows if any(p['priority_'+str(r)]==1 for r in [500,800,1000])})
 lookup={p['stpug_id']:p for p in rows}
 charts['distance']={'columns':['STPUG','500 m','800 m','1,000 m'],'rows':[[sid,*[lookup[sid]['priority_'+str(r)] for r in [500,800,1000]]] for sid in union]}
 age_union=[p for p in rows if any(p['priority_age'+a]==1 for a in ['60','65','75'])]
 charts['age']={'columns':['STPUG','60+','65+','75+'],'rows':[[p['stpug_id'],*[p['priority_age'+a] for a in ['60','65','75']]] for p in age_union]}
 charts['model']={'mainCount':13,'ageCut':AGE,'gapCut':GAP,'distanceCounts':[sum(p['priority_'+str(r)]==1 for p in rows) for r in [500,800,1000]],'scenarios':scenarios,'cohortCuts':cuts,'mainIds':[p['stpug_id'] for p in selected],'ageCounts':[sum(p['priority_age'+a]==1 for p in rows) for a in ['60','65','75']]}
 charts['scenarios']={'columns':['Radius (m)','Age percentile','Gap percentile','Age cutoff (%)','Gap cutoff (%)','Selected groups'],'rows':[[int(s['radius_m']),s['age_quantile'],s['gap_quantile'],float(s['age_cut']),float(s['gap_cut']),int(s['n_selected'])] for s in scenarios]}
 write(EMBEDS/'charts/data.json',charts)
 (EMBEDS/'workflow/steps.js').write_text('window.WORKFLOW_STEPS='+json.dumps(read(ROOT/'assets/analysis/workflow_steps.json'))+';\n')
 sources=[SOURCE/'model/tables/scenarios_27.csv',SOURCE/'maps/layers/screening_web.geojson',SOURCE.parent/'HK_Elderly_Analysis_Tables.xlsx',SOURCE.parent/'proposal.txt']
 provenance={'model_version':'20261106-p60','main_rule':'65+ share >= P60 AND residential land beyond NEC 800 m >= P60; equal STPUG weights; ties included','assessed_groups':210,'source_total_groups':211,'unassessed_group':'295','source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'validation_scope':'All 27 scenario memberships independently recalculated from supplied proximity outputs; retained counts and residential totals checked. This is not an independent rerun of the full proximity geoprocessing.','comparison_rule':'Fixed 20% ageing / 30% gap selects 14; main percentile rule selects 13. Group 149 belongs only to the fixed comparison.','site_scope':'Local gains for retained groups; 14-area global portfolio totals are excluded.'}
 write(ROOT/'assets/analysis/provenance.json',provenance)
 print('Prepared',len(rows),'areas;',len(selected),'main priorities; distance counts',charts['model']['distanceCounts'])
if __name__=='__main__':run()
