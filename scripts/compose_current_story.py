"""Compose the approved six-chapter story for the November 2026 P60 model."""
import json
from pathlib import Path
from editorial_policy import apply_policy
ROOT=Path(__file__).resolve().parents[1]
def text(s):return {'type':'text','text':s}
def heading(s):return {'type':'heading','text':s}
def table(rows):return {'type':'table','rows':rows}
def media(key,**kw):return {'type':'map','webmap':key,**kw}
def slide(title,summary,body,m):return {'title':title,'summary':summary,'text':body,'media':m}
def section(id,title,intro,slides=(),before=(),after=(),layout='docked-panel',position='start'):
 return dict(id=id,title=title,intro=intro,slides=list(slides),before=list(before),after=list(after),layout=layout,panel_position=position)
def compose():
 cfg=json.loads((ROOT/'story.json').read_text(encoding='utf-8'));model=json.loads((ROOT/'assets/analysis/current_model.json').read_text());sites=json.loads((ROOT/'assets/analysis/site_results.json').read_text())
 cfg['model_version']='20261106-p60'
 for source in cfg.get('sources',[]):
  if 'Neighbourhood Elderly' in source['name']:source['url']=source['url'].replace('_1216','_34036')
  if 'District Elderly' in source['name']:source['url']=source['url'].replace('_34036','_1216')
 cfg.update(title='Ageing and NEC Access',subtitle='Screening residential coverage gaps and reviewing community support locations in Hong Kong',asset_revision='20261106-p60')
 selected=model['selected_ids'];counts=model.get('distance_counts')
 cfg['sections']=[
 section('introduction','Introduction','Where do older communities and gaps in neighbourhood-centre proximity coincide?',[
  slide('Ageing is a share, not a headcount','The main indicator is the percentage of residents aged 65 or above.','A large older population and a high ageing share describe different things. This study uses age composition to screen communities, while retaining the number of older residents and the population denominator for interpretation. Symbols represent entire statistical areas, not the residents at the symbol location.',media('M01_population'))
 ],before=[{'type':'quote','text':'A screening result identifies a place to investigate, not proof of unmet service demand.'}],layout='floating-panel',position='end'),
 section('data','Data & Objective','Combine census evidence, residential land and the existing network, then compare possible support locations.',[
  slide('Locations are not capacity','215 distinct NEC coordinates and 62 DECC locations describe two facility scenarios.','The SWD premises snapshot was retrieved on 2 November 2026. The 216 NEC records occupy 215 distinct coordinates; coincident coordinates are deduplicated for distance calculations. Premises and sub-bases do not represent equivalent service units, available places or actual utilisation.',media('M10_facility_definition',visible_layers=['study_land','study_outline','nec_sites','decc_sites'])),
  slide('Read the denominator','Ageing share is residents aged 65+ divided by all residents in the same STPUG.','The 2021 Census covers 211 small tertiary planning unit groups. Residential coverage can be assessed for 210; group 295 has no assigned residential cells and remains unassessed. A high percentage in a small community should be read alongside its headcount and residential-cell count.',media('M01_population',visible_layers=['study_land','study_outline','age_share','nec_sites']))
 ],before=[table([['Evidence','Date and scope','Use'],['Census A503 and STPUG boundaries','2021 · 211 groups','Age shares, counts and population denominators'],['Residential land-use grid','2021 · 10 m cells','Private/public housing and rural settlements'],['NEC and DECC premises','Retrieved 2 November 2026','Existing-network proximity; DECC is an alternative scope'],['Community halls and centres','115 venues · checked 5 November 2026','Existing addresses for outreach-site review'],['District boundaries','2021 · 18 districts','Geographical context; no population redistribution']])],layout='floating-panel',position='end'),
 section('methodology','Methodology','Screen two indicators independently, retain the continuous evidence, and test how assumptions change the result.',before=[
  {'type':'embed','path':'embeds/workflow/index.html','figure_title':'Analytical workflow.','caption':'From census, residential land and facility locations to a two-condition screen, sensitivity checks and local site review.'},
  heading('A transparent two-condition rule'),
  text('Among the 210 assessed groups, calculate the 60th percentile of the 65+ population share and of the residential-area share beyond 800 m from the nearest NEC. Each STPUG receives equal weight. The unrounded cutoffs are 19.913163372872837% and 30.75788624778998%, respectively. Include ties: 84 groups meet each condition and 13 meet both. Neither indicator compensates for a low value of the other.'),
  heading('Measure residential proximity'),
  text('Use Hong Kong 1980 Grid (EPSG:2326). Assign each 10 m residential-cell centre to a group and measure its straight-line distance to the nearest NEC anywhere in Hong Kong, including across group boundaries. A cell exactly 800 m away counts as covered. Each cell represents 100 m² of residential ground area; this is not a population served estimate or a walking-time model.'),
  heading('Separate two sensitivity questions'),
  text('The 27 scenarios combine P50, P60 and P70 for both indicators with 500, 800 and 1,000 m radii, recalculating the outside-area percentile for each radius. A separate comparison holds the two main 800 m cutoffs fixed and changes distance alone. Age-60+ and age-75+ tests use their own P60 age-share cutoffs. Adding DECC locations changes the facility scope, not the meaning of service capacity.'),
  heading('Review locations within shortlisted groups'),
  text('Take one residential cell nearest the centre of each occupied 200 m grid square as a model reference. A maximises newly covered residential land. B is the strongest independent alternative at least 400 m from A. C is chosen on the remaining uncovered cells after A; its contribution is additional coverage, not its stand-alone gain. Compare model points with documented community venues and DECC locations. Model points do not establish land availability, accessible entrances or operator approval.')
 ]),
 section('spatial','Spatial Analysis','Read the continuous indicators before the shortlist, then examine what local service alternatives could add.',[
  slide('Residential gaps have endpoints','At 800 m, 80 groups have no residential land outside coverage; 42 have all residential land outside.','These ties matter when interpreting percentile thresholds and colour classes. The whole statistical area is coloured for orientation, but only residential-cell area enters the denominator. Parks, mountains and airports are not counted as residential demand.',media('M02_coverage',view_shift_right=.06)),
  slide('Thirteen areas meet both criteria','The approved main screen uses P60 ageing share and P60 residential gap.','The main shortlist is '+', '.join(selected)+'. The supplied fixed 20% / 30% model selects 14 areas, including group 149; it is retained only as an explicitly labelled comparison. No assigned residential cells means unassessed, not a zero-gap result.',media('M03_binary800',view_shift_right=.06)),
  slide('Explore assumptions','Compare the main rule, fixed thresholds, age definitions and the DECC scope.','The explorer reports group-wide population and residential denominators. A higher gap is a geographical screening signal, not evidence that residents receive no support. Scenario counts describe sensitivity and must not be interpreted as probabilities.',{'type':'embed','path':'embeds/elderly-map/index.html'}),
  slide('Sensitivity remains visible','The 27 recalibrated scenarios preserve the distinction between assumptions and findings.','Inspect each group’s selection frequency, then compare the distance and age matrices below. Changing a percentile threshold changes a relative screening rule; changing a radius while holding cutoffs fixed answers a different question.',media('M06_sensitivity27',view_shift_right=.06)),
  slide('Wan Chai · group 131','A small residential denominator requires careful interpretation.','The group has 5,290 residents aged 65+ (20.20%) and 12.00 ha of residential land. Of this, 11.69 ha lies beyond 800 m from an NEC. Model A newly covers all 11.69 ha. Nearby DECC locations also warrant review; geographical overlap does not establish equivalent functions or spare capacity.',media('M13_case131',view_shift_right=.06)),
  slide('Ta Kwu Ling · group 620S','Choose a second location for additional coverage, not its independent score.','All 110.36 ha of residential land lies beyond the existing NEC radius. A adds 31.01 ha. B adds only 3.05 ha after A, although it covers 28.63 ha independently. Re-optimised C adds 25.09 ha after A, giving 56.10 ha together. Ta Kwu Ling Community Hall alone adds 19.62 ha; a complementary second point could add 25.09 ha. These are reference arrangements requiring field checks.',media('M14_case620S',view_shift_right=.06)),
  slide('Cheung Chau · group 920','An existing venue offers a different route to practical review.','The group has 4,450 residents aged 65+ (22.51%) and 56.54 ha of residential land. Model A adds 28.93 ha; Cheung Chau Community Hall adds 26.71 ha. After A, independent alternative B adds no additional area. After the hall, a complementary H2 could add 4.01 ha. Check actual street routes, steps, entrances and venue schedules before considering an outreach arrangement.',media('M15_case920',view_shift_right=.06))
 ],after=[
  heading('Compare model and existing locations'),
  text('Choose one of the three cases and drag the divider. Left shows coverage after adding model point A; right shows an existing community venue. Grey residential patches were already covered by NECs, coloured patches are newly covered, and pale patches remain outside. Both sides use the same view and the same NEC baseline.'),
  {'type':'embed','path':'embeds/coverage-comparison/index.html','figure_title':'Local location alternatives.','caption':'Model reference A on the left; an existing community venue on the right. Newly covered area is additional residential ground area within 800 m, not people served. Fixed legends float inside each map side.'},
  table([['Case','Model A: new coverage','Community venue: new coverage','Complementary second-point lesson'],['Wan Chai 131','11.69 ha','11.69 ha','Little remaining gap after A'],['Ta Kwu Ling 620S','31.01 ha','19.62 ha','C adds 25.09 ha after A; B adds 3.05 ha'],['Cheung Chau 920','28.93 ha','26.71 ha','H2 adds 4.01 ha after the hall']]),
  heading('Coverage by residential type'),
  {'type':'embed','path':'embeds/charts/index.html?group=coverage#housing','figure_title':'Residential-area coverage.','caption':'Compare coverage by housing type and district. Coverage is residential ground area, not the share of older residents served.'},
  heading('How the shortlist changes'),
  {'type':'embed','path':'embeds/charts/index.html?group=sensitivity#sensitivity','figure_title':'Screening sensitivity.','caption':'Compare fixed-cutoff distance tests, cohort-specific P60 age definitions and the 27 recalibrated percentile scenarios. Scenario counts are not probabilities.'}
 ]),
 section('conclusions','Conclusions','The screen identifies 13 communities for closer review; it does not prescribe 13 new centres.',before=[
  heading('What the analysis supports'),text('Older population share and residential proximity reveal different dimensions of the geography of ageing. Their intersection provides an explicit, reproducible starting point for community-support review. The population and residential-cell denominators remain essential to interpretation.'),
  heading('What local comparisons add'),text('Existing venues can offer known addresses for further discussion, while model points reveal where residential gaps are concentrated. A second point should be assessed on its additional contribution after the first: independently attractive locations can cover the same housing. Benefits from different groups cannot simply be added to claim an optimal Hong Kong-wide venue plan.'),
  heading('Limits and next steps'),text('Population and residential land describe 2021; facilities are a 2026 snapshot. Residential area varies in density and does not measure floorspace, capacity, cost or participation. Straight-line radii omit slopes, barriers and actual walking routes. Verify the geoprocessing in ArcGIS Pro, inspect boundary cells and ties, and check venue availability, accessible entrances and operator arrangements before any recommendation.')
 ]),
 section('references','References','',before=[{'type':'references'}])]
 cfg=apply_policy(cfg)
 # The approved proposal supersedes legacy automatic four-area narrative policies.
 cfg['title']='Ageing and NEC Access';cfg['asset_revision']='20261106-green'
 for s in cfg['sections']:
  if s['id']=='spatial':
   for b in s['after']:
    if b.get('path','').startswith('embeds/coverage-comparison/'):
     b.update(figure_title='Local location alternatives.',caption='Model reference A on the left; an existing community venue on the right. Both use the same NEC baseline and 800 m radius. Legends float inside the map.')
    if '#sensitivity' in b.get('path',''):b.update(figure_title='Screening sensitivity.',caption='Compare fixed-cutoff distance tests, cohort-specific P60 age definitions and 27 recalibrated percentile scenarios. These are screening decisions, not probabilities.')
 for chapter in cfg['sections']:
  for block in chapter.get('before',[])+chapter.get('after',[])+[slide.get('media',{}) for slide in chapter['slides']]:
   if block.get('path','').startswith('embeds/') and not block['path'].startswith('embeds/20261106/'):
    block['path']=block['path'].replace('embeds/','embeds/20261106/',1)
 from scripts.editorial_20261108 import apply_copy
 cfg=apply_copy(cfg)
 from scripts.visual_20261108 import apply_visuals
 cfg=apply_visuals(cfg)
 from scripts.citations_20261109 import apply_citations
 cfg=apply_citations(cfg)
 cfg['asset_revision']='20261109-details'
 (ROOT/'story.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Composed six chapters with a short cover title and the approved 13-area model.')
if __name__=='__main__':compose()
