"""Apply the approved layout, figure and bibliography policy to a story config."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def apply_policy(cfg):
    cfg['numbered_chapters']=True
    cfg['asset_revision']='20261105-review2'
    cfg['chapter_spacing_lines']=2
    cfg['references']=json.loads((ROOT/'assets/references.json').read_text(encoding='utf-8'))
    for section in cfg['sections']:
        if section.get('layout')=='slideshow':section['layout']='floating-panel'
        if section['id']=='references':
            section['intro']='Scholarly literature and official datasets cited in this study. Entries follow APA style; undated datasets are identified as n.d. rather than assigned an unverified publication year.'
        if section['id']=='methodology':
            text='Accessibility has several dimensions; a geographical proximity screen captures only part of the wider concept (Geurs & van Wee, 2004). We therefore interpret this model as a transparent review shortlist, rather than an assessment of actual service use.'
            if not any(b.get('text')==text for b in section.get('before',[])):
                section.setdefault('before',[]).append({'type':'text','text':text})
        for block in section.get('before',[])+section.get('after',[]):
            if block.get('path')=='embeds/workflow/index.html':block['figure_title']='Analytical workflow.'
            elif block.get('type')=='swipe':block['figure_title']='Facility scope in Tiu Keng Leng.'
            elif block.get('path')=='embeds/charts/index.html#housing':block['figure_title']='Residential-area coverage by housing type and district.'
            elif block.get('path')=='embeds/charts/index.html#sensitivity':
                block['figure_title']='Sensitivity to distance and age definitions.'
                block['caption']='(A) Distance-threshold decisions at 500, 800 and 1,000 m. (B) Age-definition decisions for the four main-scenario groups. Each age cohort uses its own P75 cutoff. 1 = selected; 0 = not selected.'
        for slide in section.get('slides',[]):
            if section.get('layout')=='floating-panel' and '\n\n' in slide.get('text',''):
                first,remaining=slide['text'].split('\n\n',1)
                slide['text']=first
                if not any(b.get('text')==remaining for b in section.get('after',[])):
                    section.setdefault('after',[]).append({'type':'text','text':remaining})
            media=slide.get('media',{})
            if media.get('webmap')=='M01_population' and media.get('visible_layers'):
                media['visible_layers']=['study_land','study_outline','age_share','nec_sites']
    return cfg

if __name__=='__main__':
    path=ROOT/'story.json'
    cfg=apply_policy(json.loads(path.read_text(encoding='utf-8')))
    path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
