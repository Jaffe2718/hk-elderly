"""Import reviewed English Web Maps and share them to the story's exact groups."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ensure_maps(gis, story_item, keys, version=None):
    path = ROOT / 'assets/map_items.json'
    ledger = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    groups = story_item.sharing.groups.list()
    if story_item.access not in {'private', 'shared'}:
        raise RuntimeError('Expected a private/group-shared story; review audience before importing maps')
    for key in sorted(set(keys)):
        data = json.loads((ROOT / 'assets/webmaps' / (key + '.json')).read_text(encoding='utf-8'))
        prior = ledger.get(key, {})
        tag=f'geog7302-{key}'+('-'+version if version else '')
        compatible=not version or prior.get('model_version')==version
        item = gis.content.get(prior.get('item_id')) if compatible and prior.get('item_id') else None
        if item and item.owner != gis.users.me.username:
            raise RuntimeError('Existing map belongs to another account')
        if not item:
            # Search a deterministic tag to recover if a previous run stopped before ledger write.
            hits = gis.content.search(f'owner:{gis.users.me.username} AND tags:"{tag}"', item_type='Web Map', max_items=20)
            exact = [x for x in hits if tag in x.tags]
            if len(exact) > 1:
                raise RuntimeError(f'Duplicate imported map key: {key}')
            item = exact[0] if exact else None
        props = {'type': 'Web Map', 'title': 'GEOG7302 | ' + key[4:].replace('_', ' ').title(),
                 'tags': ['GEOG7302', 'Hong Kong', 'NEC', tag],
                 'snippet': 'Residential-area spatial screening: 2021 Census and land use; 2 November 2026 SWD premises.',
                 'description': 'Straight-line proximity and explicit Binary screening. Coverage refers to residential ground area, not people served. Location counts do not establish capacity.'}
        unchanged = item is not None and item.get_data() == data
        if item and not unchanged:
            item.update(item_properties=props, data=json.dumps(data))
        elif not item:
            item = gis.content.folders.get().add(item_properties=props, text=json.dumps(data)).result()
        existing_groups = {g.id for g in item.sharing.groups.list()}
        for group in groups:
            if group.id not in existing_groups and not item.sharing.groups.add(group):
                raise RuntimeError('Unable to share dependency with story group')
        ledger[key] = {'item_id': item.id, 'title': item.title, 'groups': [g.id for g in groups], 'model_version':version, 'previous_item_id':prior.get('item_id') if not compatible else prior.get('previous_item_id')}
        path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
        # Read the actual data back; do not treat creation as data validation.
        actual = item.get_data()
        if actual.get('operationalLayers') != data['operationalLayers']:
            raise RuntimeError(f'Web Map readback failed: {key}')
        print(f'Web Map ready: {key} / {item.id}', flush=True)
    return ledger
