"""Draw paired legend keys directly from the native comparison renderers."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def run():
 im=Image.new('RGB',(1600,290),'white');d=ImageDraw.Draw(im)
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',27);bold=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30)
 for i,(key,title) in enumerate([('M11_residential_nec','Left map — NEC only'),('M12_residential_combined','Right map — NEC + DECC')]):
  x=40+i*800;y=28;d.text((x,y),title,font=bold,fill='#33464f');y+=58
  m=json.loads((ROOT/f'assets/webmaps/{key}.json').read_text(encoding='utf-8'))
  r=next(l for l in m['operationalLayers'] if l['id']=='residential')['featureCollection']['layers'][0]['layerDefinition']['drawingInfo']['renderer']
  for entry in r.get('uniqueValueInfos',r.get('classBreakInfos',[])):
   c=entry['symbol']['color'];d.rectangle((x,y+4,x+26,y+27),fill=tuple(c[:3]));d.text((x+42,y),entry['label'],font=font,fill='#33464f');y+=44
  for label,shape in [('NEC site','diamond')]+([('DECC site','triangle')] if i else []):
   pts=[(x+13,y+2),(x+25,y+14),(x+13,y+26),(x+1,y+14)] if shape=='diamond' else [(x+13,y+2),(x+25,y+26),(x+1,y+26)]
   d.polygon(pts,fill='#145341' if shape=='diamond' else '#b75d22');d.text((x+42,y),label,font=font,fill='#33464f');y+=44
 target=ROOT/'assets/legends/facility-comparison.png';target.parent.mkdir(exist_ok=True);im.save(target)
if __name__=='__main__':run()
