"""Attach source references without rewriting the approved handoff prose."""

def apply_citations(cfg):
    intro, data, method, spatial, conclusions, _ = cfg['sections']
    intro['slides'][0]['text_citations'] = [2, 3]
    data['intro_citations'] = [2, 3, 5, 6, 7, 8]
    data['slides'][0]['text_citations'] = [6, 7]
    data['slides'][1]['text_citations'] = [2, 3, 5]
    for event, sources in zip(next(b for b in data['after'] if b['type']=='timeline')['events'], [[2,3,5],[6,7],[8]]):
        event['citations'] = sources
    for block in method['before']:
        if block.get('text','').startswith('Distances are calculated'):
            block['citations'] = [2, 5, 7]
        elif block.get('text','').startswith('Within each shortlisted group'):
            block['citations'] = [6, 8]
        elif block.get('text','').startswith('Geographical proximity'):
            block['citations'] = [4]
    # These citations identify input datasets; local gains remain this study's results.
    for slide in spatial['slides'][4:]:
        slide['text_citations'] = [2, 3, 5, 6, 7, 8]
    for block in spatial['after']:
        if block.get('path','').endswith('#housing'):
            block['citations'] = [1, 5, 6, 7]
    conclusions['before'][-1]['citations'] = [3, 5, 6, 7]
    return cfg
