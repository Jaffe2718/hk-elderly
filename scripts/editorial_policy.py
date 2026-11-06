"""Apply the approved layout, figure and bibliography policy to a story config."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def apply_policy(cfg):
    cfg['numbered_chapters']=True
    cfg['asset_revision']=cfg.get('asset_revision','20261106-p60')
    current=cfg.get('model_version')=='20261106-p60'
    cfg['cover_media']={'type':'image','path':'assets/cover/tuen-mun-aged-blind-garden.jpg'}
    cfg['chapter_spacing_lines']=2
    cfg['references']=json.loads((ROOT/'assets/references.json').read_text(encoding='utf-8'))
    for section in cfg['sections']:
        section['panel_size']='small'
        if section.get('layout')=='slideshow':section['layout']='floating-panel'
        if section['id']=='references':
            section['intro']=''
            section['before']=[{'type':'references'}]
            section['after']=[]
        if section['id']=='methodology':
            text='Accessibility has several dimensions; a geographical proximity screen captures only part of the wider concept (Geurs & van Wee, 2004). We therefore interpret this model as a transparent review shortlist, rather than an assessment of actual service use.'
            if not any(b.get('text')==text for b in section.get('before',[])):
                section.setdefault('before',[]).append({'type':'text','text':text})
        for block in section.get('before',[])+section.get('after',[]):
            if block.get('type')=='swipe' or block.get('path','').split('?')[0]=='embeds/coverage-comparison/index.html':
                if current:
                    block.update(type='embed',path='embeds/coverage-comparison/index.html?ui=20261106-p60',figure_title='Local location alternatives.',caption='Model reference A on the left; an existing community venue on the right. Both use the same NEC baseline and 800 m radius. Legends float inside the map.')
                else:
                    block.clear();block.update(type='embed',path='embeds/coverage-comparison/index.html?ui=20261105-layoutfix',figure_title='Facility scope in Tiu Keng Leng.',caption='NEC only on the left; NEC + DECC on the right. Both sides share one geographical view. In-map legends identify residential land within or beyond 800 m and the facility types.')
            if block.get('text','').startswith(('Drag the native Swipe divider','Compare matched residential patches')):
                block['text']='Drag the divider to compare NEC-only and NEC + DECC proximity in Tiu Keng Leng at the same geographical extent. The fixed in-map legends describe their respective layers. These are geographical proximity definitions, not interchangeable services or measures of operating capacity.'
            if block.get('text')=='Tiu Keng Leng: change the facility scope':block['text']='Compare local facility scope'
            if block.get('path')=='embeds/workflow/index.html':block['figure_title']='Analytical workflow.'
            elif block.get('type')=='swipe':block['figure_title']='Facility scope in Tiu Keng Leng.'
            elif block.get('path','').startswith('embeds/charts/index.html') and block['path'].endswith('#housing'):block['figure_title']='Residential-area coverage by housing type and district.'
            elif block.get('path','').startswith('embeds/charts/index.html') and block['path'].endswith('#sensitivity'):
                block['figure_title']='Sensitivity to distance and age definitions.'
                block['caption']='(A) Distance-threshold decisions at 500, 800 and 1,000 m. (B) Age-definition decisions for the four main-scenario groups. Each age cohort uses its own P75 cutoff. 1 = selected; 0 = not selected.'
            if current and block.get('path','').endswith('#sensitivity'):
                block['figure_title']='Screening sensitivity.'
                block['caption']='Compare fixed-cutoff distance tests, cohort-specific P60 age definitions and 27 recalibrated percentile scenarios. These are screening decisions, not probabilities.'
            if block.get('path','').startswith('embeds/charts/index.html'):
                block['caption']=block.get('caption','').replace('sort values, or download the source table','sort values or inspect the table')
                fragment=block['path'].split('#')[-1]
                group='coverage' if fragment=='housing' else 'sensitivity'
                block['path']=f"embeds/charts/index.html?group={group}&ui={cfg['asset_revision']}#{fragment}"
        for key in ['before','after']:
            section[key]=[b for b in section.get(key,[]) if b.get('type')!='comparison_legend']
        for slide in section.get('slides',[]):
            if section.get('layout')=='floating-panel' and '\n\n' in slide.get('text',''):
                first,remaining=slide['text'].split('\n\n',1)
                slide['text']=first
                if not any(b.get('text')==remaining for b in section.get('after',[])):
                    section.setdefault('after',[]).append({'type':'text','text':remaining})
            media=slide.get('media',{})
            if slide.get('title')=='Locations are not capacity':
                media.update(type='map',webmap='M10_facility_definition',visible_layers=['study_land','study_outline','nec_sites','decc_sites'])
                media.pop('view_shift_right',None)
            if section.get('layout')=='docked-panel' and media.get('webmap') in {'M02_coverage', 'M03_binary800', 'M09_centroid_comparison', 'M10_facility_definition'}:
                media['view_shift_right']=.06
            if media.get('webmap')=='M01_population' and media.get('visible_layers'):
                media['visible_layers']=['study_land','study_outline','age_share','nec_sites']
    return cfg

if __name__=='__main__':
    path=ROOT/'story.json'
    cfg=apply_policy(json.loads(path.read_text(encoding='utf-8')))
    path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
