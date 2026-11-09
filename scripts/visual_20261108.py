"""Native visual hierarchy for the approved handoff narrative."""
def apply_visuals(cfg):
 sections=cfg['sections'];intro,data,method,spatial=sections[:4]
 info=lambda title,description,icon='':dict(type='infographic',title=title,description=description,icon=icon)
 intro['before']=[b for b in intro['before'] if b.get('type')!='infographic']+[info('13','Priority areas for community service review. Screened from 210 assessed STPUGs using two P60 conditions and an 800 m NEC radius.','pin')]
 timeline={'type':'timeline','style':'single-side','events':[
 {'title':'2021 · Population and housing','text':'Census A503 and STPUG boundaries describe 211 groups. Residential land is represented by 10 m cells.'},
 {'title':'2 November 2026 · Elderly centres','text':'SWD premises records supply 215 distinct NEC locations and 62 DECC locations for the network comparison.'},
 {'title':'5 November 2026 · Community venues','text':'115 community halls and centres provide existing addresses for outreach-site comparison.'}]}
 data['after']=[b for b in data['after'] if b.get('type')!='timeline']+[timeline]
 # One context-specific metric after the full body on every Sidecar page.
 intro['slides'][0]['infographics']=[info('65+','The map shows older-resident counts; the joint screen uses their share of total population.','group')]
 data['slides'][0]['infographics']=[info('215 + 62','215 distinct NEC locations in the baseline; 62 DECC locations in the alternative network.','pin')]
 data['slides'][1]['infographics']=[info('210 / 211','STPUGs with assessable residential coverage. Group 295 has no assigned residential cells.','analysis')]
 overview=[('80 + 42','80 groups have a 0% outside-area share; 42 have a 100% share. Another 88 fall between these endpoints.','analysis'),('13','Groups meeting both P60 conditions: older-resident share and residential land beyond NEC 800 m.','pin'),('800 m','Baseline NEC coverage radius. Compare distance, age cohort and facility-network assumptions in the explorer.','walking'),('27','Scenario combinations: 3 radii × 3 age-share percentiles × 3 outside-area percentiles.','analysis')]
 for slide,(title,description,icon) in zip(spatial['slides'][:4],overview):slide['infographics']=[info(title,description,icon)]
 # Keep the actual research wording; use one focal metric per case, with explicit baselines.
 metrics=[('11.69 ha','Newly covered residential land with either model A or the community venue. Wan Chai 131.','home'),('56.10 ha','Total additional residential coverage with A + C: 31.01 ha from A, then 25.09 ha from C. Ta Kwu Ling 620S.','analysis'),('92.3%','Community Hall gain relative to model A: 26.71 ha compared with 28.93 ha. Cheung Chau 920.','home')]
 for slide,(title,description,icon) in zip(spatial['slides'][4:7],metrics):slide['infographics']=[info(title,description,icon)]
 from scripts.infographic_groups import apply_infographic_groups
 cfg=apply_infographic_groups(cfg)
 cfg['publish_audience']='public'
 return cfg
