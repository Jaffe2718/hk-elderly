"""Prepare English-only assets from the collaborator's local handoff package.

Run once before replacing the original demo, or provide its archived path.
Source files remain in the ignored build/handoff directory.
"""
import argparse
import csv
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile('[\u4e00-\u9fff]')


def english(value):
    if isinstance(value, dict):
        return {k: english(v) for k, v in value.items() if not k.endswith('_zh')}
    if isinstance(value, list):
        return [english(v) for v in value if not (isinstance(v, dict) and any(str(v.get(k, '')).endswith('_zh') for k in ['name', 'fieldName']))]
    if isinstance(value, str) and HAN.search(value):
        translations = {'\u8bbe\u65bd\u540d\u79f0': 'Facility name', '\u5730\u5740': 'Address'}
        if value in translations:
            return translations[value]
        first = value.split(' / ')[0]
        if not HAN.search(first):
            return first
        raise ValueError(f'Untranslated text: {value!r}')
    return value


def run(source, original_demo):
    source = Path(source)
    (ROOT / 'assets/webmaps').mkdir(parents=True, exist_ok=True)
    for path in source.joinpath('webmaps').glob('M*.json'):
        data = english(json.loads(path.read_text(encoding='utf-8')))
        (ROOT / 'assets/webmaps' / path.name).write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    (ROOT / 'assets/figures').mkdir(exist_ok=True)
    for path in source.joinpath('figures/en').glob('*.png'):
        shutil.copy2(path, ROOT / 'assets/figures' / path.name)
    (ROOT / 'assets/tables').mkdir(exist_ok=True)
    for name in ['housing_coverage_en.csv', 'district_coverage_en.csv', 'age_binary_decisions.csv', 'distance_binary_decisions.csv']:
        shutil.copy2(source / 'tables/charts' / name, ROOT / 'assets/tables' / name)

    html = Path(original_demo).read_text(encoding='utf-8')
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
    vendor = ROOT / 'docs/vendor'
    vendor.mkdir(parents=True, exist_ok=True)
    (vendor / 'leaflet.js').write_text(scripts[0], encoding='utf-8')
    (vendor / 'leaflet.css').write_text(re.findall(r'<style>(.*?)</style>', html, re.S)[0], encoding='utf-8')
    raw = scripts[-1].split('const D=', 1)[1]
    data = json.JSONDecoder().raw_decode(raw)[0]
    data = english(data)
    webmap = json.loads((ROOT / 'assets/webmaps/M03_binary800.json').read_text(encoding='utf-8'))
    rows = webmap['operationalLayers'][0]['featureCollection']['layers'][0]['featureSet']['features']
    lookup = {r['attributes']['stpug_id']: r['attributes'] for r in rows}
    for f in data['groups']['features']:
        p = f['properties']
        a = lookup[p['stpug_id']]
        assert p['elderly_n'] == a['elderly_n']
        p.update(a)
        p['assessed'] = int(a['res_area_km2'] is not None and a['res_area_km2'] > 0)
        p['out_share_800'] = a['nec_out800_pct'] / 100 if p['assessed'] else None
        p['nec_decc_out_share_800'] = a['any_out800_pct'] / 100 if p['assessed'] else None
    output = ROOT / 'docs/embeds/elderly-map/data.json'
    output.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    assert not HAN.search(output.read_text(encoding='utf-8'))
    selected = [p for p in lookup.values() if p['priority_main'] == 1]
    assert {p['stpug_id'] for p in selected} == {'524', '628', '833', '950S'}
    print(f'Prepared 12 Web Maps, 22 English figures, 4 tables and {len(lookup)} map areas')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', default='build/handoff/StoryMaps_assets')
    p.add_argument('--original-demo', required=True)
    a = p.parse_args()
    run(a.source, a.original_demo)
