"""Apply the November 8 final English wording without changing analytical assets."""
import json,re,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def apply_copy(cfg):
 d=json.loads((ROOT/'assets/editorial/20261108.json').read_text(encoding='utf-8'));e=d['entries'];ss=cfg['sections']
 cfg.update(title=e['01'],subtitle=e['02'],cover_note=e['04'],chapter_number_separator=' ',editorial_version='20261108')
 for s,n in zip(ss,['05','11','19','31','61','69']):s['title']=re.sub(r'^\d+\s+','',e[n])
 for i,n in enumerate(['06','12','20','32','62']):ss[i]['intro']=e[n]
 ss[0]['before'][0]['text']=e['07']
 def slide(s,i,n):
  for field,k in zip(['title','summary','text'],range(n,n+3)):ss[s]['slides'][i][field]=e[f'{k:02}']
 slide(0,0,8);slide(1,0,13);slide(1,1,16)
 ss[1]['before'][0]['rows']=d['tables'][0]
 for i,n in enumerate(range(22,31)):ss[2]['before'][i+1]['text']=e[f'{n:02}']
 for i,n in enumerate(range(33,52,3)):slide(3,i,n)
 for index,n in [(0,54),(1,55),(4,57),(6,59)]:ss[3]['after'][index]['text']=e[str(n)]
 for b,n in [(ss[2]['before'][0],21),(ss[3]['after'][2],56),(ss[3]['after'][5],58),(ss[3]['after'][7],60)]:
  t=re.sub(r'^Fig\. \d+\. ','',e[str(n)]);title,body=t.split('. ',1);b.update(figure_title=title+'.',caption=body)
 ss[3]['after'][3]['rows']=d['tables'][1]
 for i,n in enumerate(range(63,69)):ss[4]['before'][i]['text']=e[str(n)]
 # Retain existing APA italics and the verified URLs.
 a=json.loads((ROOT/'assets/cover/attribution.json').read_text(encoding='utf-8'));credit=html.escape(e['79'])
 links={'Census and Statistics Department':'https://www.census2021.gov.hk/en/main_tables.html','Planning Department':'https://www.pland.gov.hk/','Social Welfare Department':'https://www.swd.gov.hk/','Home Affairs Department':'https://www.had.gov.hk/','DATA.GOV.HK':'https://data.gov.hk/','CSDI Portal':'https://portal.csdi.gov.hk/','CC BY-SA 4.0':a['license_url'],'TSunbenmongos':'https://commons.wikimedia.org/wiki/User:TSunbenmongos','garden entrance to the Jockey Club Tuen Mun Home for the Aged Blind, Hong Kong':a['source']}
 for name,url in links.items():credit=credit.replace(name,'<a href="'+html.escape(url,quote=True)+'">'+name+'</a>')
 cfg.update(credit_heading=e['78'],credit_html=credit)
 return cfg
