"""Native visual hierarchy for the approved handoff narrative."""
def apply_visuals(cfg):
 sections=cfg['sections'];intro,data,method,spatial=sections[:4]
 info=lambda title,description,icon='':dict(type='infographic',title=title,description=description,icon=icon)
 intro['before']=[b for b in intro['before'] if b.get('type')!='infographic']+[info('13','Priority areas for community service review. Screened from 210 assessed STPUGs using two P60 conditions and an 800 m NEC radius.','pin')]
 timeline={'type':'timeline','events':[
 {'title':'2021 · Population and housing','text':'Census A503 and STPUG boundaries describe 211 groups. Residential land is represented by 10 m cells.'},
 {'title':'2 November 2026 · Elderly centres','text':'SWD premises records supply 215 distinct NEC locations and 62 DECC locations for the network comparison.'},
 {'title':'5 November 2026 · Community venues','text':'115 community halls and centres provide existing addresses for outreach-site comparison.'}]}
 data['after']=[b for b in data['after'] if b.get('type')!='timeline']+[timeline]
 # Keep the actual research wording; use one focal metric per case, with explicit baselines.
 metrics=[('11.69 ha','Newly covered residential land with either model A or the community venue. Wan Chai 131.','home'),('56.10 ha','Total additional residential coverage with A + C: 31.01 ha from A, then 25.09 ha from C. Ta Kwu Ling 620S.','analysis'),('92.3%','Community Hall gain relative to model A: 26.71 ha compared with 28.93 ha. Cheung Chau 920.','home')]
 for slide,(title,description,icon) in zip(spatial['slides'][4:7],metrics):slide['infographics']=[info(title,description,icon)]
 cfg['publish_audience']='public'
 return cfg
