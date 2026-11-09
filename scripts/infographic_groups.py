"""Compose varied native multi-value infographics from verified research results."""
def apply_infographic_groups(cfg):
 def group(name,layout,values):return {'type':'infographic','figure_title':name,'layout':layout,'values':[{'title':str(v),'description':label,'icon':icon} for v,label,icon in values]}
 intro,data,method,spatial=cfg['sections'][:4]
 intro['before']=[b for b in intro['before'] if b.get('type')!='infographic']+[group('Study overview','stacked',[('210','Assessed STPUGs','map'),('215','Distinct NEC locations','pin'),('800 m','Baseline radius','walking'),('13','Priority groups','check')])]
 groups=[group('Population indicators','titled',[('65+','Age group used in the main screen','group'),('211','STPUGs in the census geography','map')]),group('Elderly-centre network','compact',[('215','Distinct NEC locations','pin'),('62','DECC locations in the alternative network','home')]),group('Assessment coverage','basic',[('211','Census groups',''),('210','Assessed groups',''),('1','Group without residential cells','')]),group('Residential gap distribution','basic',[('80','Groups with 0% beyond NEC 800 m',''),('88','Groups between 0% and 100%',''),('42','Groups with 100% beyond NEC 800 m','')]),group('Joint P60 screen','titled',[('~20%','65+ share cutoff (P60)','group'),('~31%','Outside-area cutoff (P60)','home'),('13','Groups meeting both conditions','check')]),group('Distance scenarios','compact',[('500 m','Shorter-radius comparison','walking'),('800 m','Baseline coverage radius','pin'),('1,000 m','Longer-radius comparison','walking')]),group('Sensitivity combinations','stacked',[('3','Distance radii','walking'),('3','Age-share percentiles','group'),('3','Outside-area percentiles','home'),('27','Scenario combinations','analysis')]),group('Wan Chai indicators','compact',[('5,290','Residents aged 65+','group'),('20.20%','Older-resident share','analysis'),('12.00','ha · residential land','home'),('11.69','ha · newly covered with A or venue','pin')]),group('Ta Kwu Ling marginal gains','titled',[('31.01','ha · model A gain','pin'),('3.05','ha · B added after A','home'),('25.09','ha · C added after A','analysis'),('56.10','ha · A + C total gain','check')]),group('Cheung Chau alternatives','compact',[('28.93','ha · model A gain','pin'),('26.71','ha · Community Hall gain','home'),('92.3%','Hall gain relative to model A','analysis'),('4.01','ha · H2 added after the hall','check')])]
 slides=[s for sec in cfg['sections'] for s in sec['slides']]
 assert len(slides)==len(groups)==10
 for slide,g in zip(slides,groups):slide['infographics']=[g]
 # Keep unit-bearing values compact; put the unit in its own descriptive label.
 for section in cfg['sections']:
  blocks=section.get('before',[])+section.get('after',[])
  for slide in section.get('slides',[]):blocks+=slide.get('infographics',[])
  for block in blocks:
   if block.get('type')!='infographic':continue
   for value in block.get('values',[]):
    if value['title'].endswith(' m'):
     value['title']=value['title'][:-2]
     value['description']='m · '+value['description']
 return cfg
