"""Rebuild the configured StoryMap draft. Requires ArcGIS API for Python 2.4.3."""
import argparse
import copy
import html
import json
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def inspect_story(cfg):
    """Read-only export, including unknown nodes and all item resource files."""
    from arcgis.gis import GIS
    from arcgis.apps.storymap import StoryMap
    import datetime as dt
    gis = GIS('pro')
    item = gis.content.get(cfg['item_id'])
    if not item or item.type != 'StoryMap':
        raise RuntimeError('StoryMap is not accessible')
    story = StoryMap(item, gis=gis)
    folder = ROOT / 'snapshots' / dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True)

    def write(name, value):
        (folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

    draft = copy.deepcopy(story._properties)
    write('draft.json', draft)
    write('item.json', dict(item))
    write('item-data.json', item.get_data())
    write('local-config.json', cfg)
    resources = item.resources.list()
    write('resource-list.json', resources)
    downloads, errors = [], []
    for resource in resources:
        name = resource['resource']
        target = (folder / 'resources' / name).resolve()
        try:
            if not target.is_relative_to((folder / 'resources').resolve()):
                raise ValueError('Unsafe resource path')
            target.parent.mkdir(parents=True, exist_ok=True)
            result = item.resources.get(name, try_json=False, out_folder=str(target.parent), out_file_name=target.name)
            if not target.is_file():
                raise RuntimeError(f'Resource was not downloaded: {type(result).__name__}')
            downloads.append({'resource': name, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'bytes': target.stat().st_size})
        except Exception as exc:
            errors.append({'resource': name, 'error': str(exc)})
    # Re-read to detect changes made while the snapshot was being collected.
    stable = fingerprint(StoryMap(cfg['item_id'], gis=gis)._properties) == fingerprint(draft)
    manifest = {'item_id': cfg['item_id'], 'draft_sha256': fingerprint(draft), 'stable': stable,
                'complete_item_resources': not errors, 'resources': downloads, 'errors': errors}
    write('manifest.json', manifest)
    nodes = draft.get('nodes', {})
    lines = ['# StoryMap inspection', '', 'Read-only export. Review this report and the full JSON before changing the generator.',
             '', f'Item: {cfg["item_id"]}', f'Draft fingerprint: {manifest["draft_sha256"]}',
             f'Stable during export: {stable}', f'Resource download errors: {len(errors)}', '',
             '## Reading order', '']
    visited = set()

    def walk(node_id, depth=0):
        if node_id in visited:
            lines.append('  ' * depth + f'- {node_id} (already listed)')
            return
        visited.add(node_id)
        node = nodes.get(node_id, {})
        text = node.get('data', {}).get('text') or node.get('data', {}).get('title', '')
        lines.append('  ' * depth + f'- {node_id}: {node.get("type", "MISSING")} {text}')
        for child in node.get('children', []):
            walk(child, depth + 1)
    walk(draft['root'])
    lines += ['', '## Nodes outside the reading tree', '', ', '.join(sorted(set(nodes) - visited)) or 'None',
              '', '## Complete node inventory', '', 'Includes all data, configuration, links, actions, and unknown node types.']
    for node_id, node in nodes.items():
        lines += ['', f'### {node_id} ({node.get("type")})', '', '```json', json.dumps(node, ensure_ascii=False, indent=2), '```']
    lines += ['', '## Complete top-level styles and non-node data', '', '```json',
              json.dumps({k: v for k, v in draft.items() if k != 'nodes'}, ensure_ascii=False, indent=2), '```',
              '', '## Review workflow', '',
              'Compare this snapshot with local-config.json and storymap.py. List manual additions, removals, reordering, text edits, layout changes, and unsupported components.',
              'Do not flatten unknown content into the current limited schema. Extend the generator or preserve the original node/resource graph first.',
              'Ask the user to approve the proposed synchronization before editing story.json or the generator to adopt manual edits.',
              '', '## Scope and limitations', '',
              'Item resources and raw story JSON are included. External URLs, web maps/layers, and custom theme items remain references: their remote contents are not an offline backup.',
              'Inspect referenced items and browser rendering when needed. This report cannot capture viewport-dependent rendering, live data, or unpublished browser edits.',
              'Any errors or an unstable export make this snapshot ineligible as an apply baseline.']
    (folder / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Inspection saved: {folder}', flush=True)
    print(f'{len(nodes)} nodes; {len(downloads)}/{len(resources)} resources; stable={stable}', flush=True)
    if errors or not stable:
        raise RuntimeError('Snapshot is incomplete or changed during export; see manifest.json')
    return folder


def check_baseline(story, cfg, baseline):
    if not baseline:
        raise RuntimeError('Run --inspect, review manual edits, obtain user approval, then use --apply --based-on SNAPSHOT_FOLDER')
    folder = Path(baseline)
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    saved = json.loads((folder / 'draft.json').read_text(encoding='utf-8'))
    if (manifest['item_id'] != cfg['item_id'] or not manifest['stable'] or not manifest['complete_item_resources']
            or fingerprint(saved) != manifest['draft_sha256'] or fingerprint(story._properties) != manifest['draft_sha256']):
        raise RuntimeError('Online draft changed or baseline is invalid. Inspect again and review the new differences before applying.')


def load_config():
    cfg = json.loads((ROOT / 'story.json').read_text(encoding='utf-8'))
    if cfg.get('cover_media'):
        local_asset(cfg['cover_media']['path'])
    if cfg.get('theme', 'summit') not in {'summit', 'tidal', 'mesa', 'ridgeline', 'slate', 'obsidian'}:
        raise ValueError('Unsupported built-in theme')
    if len(cfg['item_id']) != 32 or not all(c in '0123456789abcdef' for c in cfg['item_id']):
        raise ValueError('Invalid target item ID')
    ids = [s['id'] for s in cfg['sections']]
    if len(ids) != len(set(ids)):
        raise ValueError('Section IDs must be unique')
    for section in cfg['sections']:
        if section.get('layout', 'docked-panel') not in {'docked-panel', 'floating-panel', 'slideshow'}:
            raise ValueError('Invalid Sidecar layout')
        if section.get('panel_position', 'start') not in {'start', 'end'}:
            raise ValueError('Panel position must be start or end')
        if not section['title'] or not (section.get('slides') or section.get('before') or section.get('after')):
            raise ValueError('Each section needs a title and slides')
        for slide in section['slides']:
            if not slide['title']:
                raise ValueError('Each slide needs a title')
            media = slide.get('media')
            if media:
                if media['type'] == 'image':
                    local_asset(media['path'])
                elif media['type'] == 'embed':
                    embed_url(cfg, media['path'])
                elif media['type'] == 'swipe':
                    for image_path in media.get('images', []):
                        local_asset(image_path)
                elif media['type'] != 'map':
                    raise ValueError('Media type must be image, embed, or map')
    return cfg


def local_asset(path):
    asset = (ROOT / path).resolve()
    if not asset.is_relative_to(ROOT) or not asset.is_file():
        raise ValueError(f'Asset missing or outside repository: {path}')
    return asset


def embed_url(cfg, path):
    if urlparse(path).scheme:
        url = path
    else:
        base = cfg['pages_base_url']
        if not base:
            raise ValueError('Set pages_base_url before using hosted embeds')
        local_asset('docs/' + urlparse(path).path)
        url = urljoin(base.rstrip('/') + '/', path)
    if urlparse(url).scheme != 'https':
        raise ValueError('Embeds require HTTPS')
    if cfg.get('asset_revision') and url.startswith(cfg.get('pages_base_url','__none__').rstrip('/')+'/'):
        parts=urlparse(url)
        query=(parts.query+'&' if parts.query else '')+'v='+cfg['asset_revision']
        url=parts._replace(query=query).geturl()
    return url


def configure_cover(story, cfg):
    from arcgis.apps.storymap.story_content import Cover
    cover = next(c for c in story.contents if isinstance(c, Cover))
    cover.title = cfg['title']
    cover.summary = cfg.get('subtitle', '')
    cover.byline = ' '.join(filter(None, [cfg.get('course'), cfg['byline']])) + ' | ' + ' · '.join(cfg.get('members', []))
    cover.type = cfg.get('cover_type', 'full')
    if cover.type == 'full':
        cover.style = cfg.get('cover_style', 'themed')
        cover.vertical_position = cfg.get('cover_vertical_position', 'top')
        cover.horizontal_position = cfg.get('cover_horizontal_position', 'start')
        cover.size = cfg.get('cover_size', 'large')
    if cfg.get('cover_media'):
        from arcgis.apps.storymap.story_content import Image
        cover.media=Image(str(local_asset(cfg['cover_media']['path'])))
    return cover


def save_draft(story, cfg):
    from arcgis.apps.storymap import _utils
    props = _utils.prepare_story_for_save(story, False, None, None, cfg['title'], None, _utils.get_version(story))
    props.pop('access', None)
    if not story._item.update(item_properties=props):
        raise RuntimeError('ArcGIS rejected draft metadata update')


def configure_credits(story, cfg):
    credits = next((n for n in story._properties['nodes'].values() if n.get('type') == 'credits'), None)
    if credits is not None:
        credits['children'] = []
        credits.setdefault('config', {})['isHidden'] = False
    description = ('We acknowledge the <a href="https://www.census2021.gov.hk/en/main_tables.html" target="_blank" rel="noopener noreferrer">Census and Statistics Department</a> for the 2021 Census and statistical boundaries, the '
                   '<a href="https://www.swd.gov.hk/" target="_blank" rel="noopener noreferrer">Social Welfare Department</a> for elderly-centre premises data, and the '
                   '<a href="https://www.pland.gov.hk/" target="_blank" rel="noopener noreferrer">Planning Department</a> for 2021 land-use data, accessed through the '
                   '<a href="https://portal.csdi.gov.hk/" target="_blank" rel="noopener noreferrer">CSDI Portal</a> and DATA.GOV.HK. Analysis and presentation by GEOG7302 Group 13.')
    if cfg.get('model_version'):
        description+=' We also acknowledge the Home Affairs Department for community-hall and community-centre locations checked on 5 November 2026.'
    if cfg.get('cover_media'):
        attribution=json.loads(local_asset('assets/cover/attribution.json').read_text(encoding='utf-8'))
        description+=' Cover photograph: '+attribution['title']+'. Photograph by '+attribution['photographer']+'. <a href="'+html.escape(attribution['source'],quote=True)+'">Image source</a>; <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. Responsive cover framing may crop the original photograph. The image illustrates an elderly-care environment, not an NEC study location.'
    description = cfg.get('credit_html', description)
    story.credits(heading=cfg.get('credit_heading', 'Credit'), description=description)
    # Acknowledgement is a footer, not a chapter/navigation target.
    for child in credits.get('children', []):
        node=story._properties['nodes'][child]
        if node.get('data', {}).get('type')=='h4':
            node['data'].update(type='paragraph',text='<strong>'+html.escape(cfg.get('credit_heading', 'Credit'))+'</strong>')


def chapter_title(cfg, index, section):
    return (f"{index+1}{cfg.get('chapter_number_separator', '. ')}" if cfg.get('numbered_chapters') else '') + section['title']


def configure_map_views(story, cfg):
    """Give each displayed map its own valid extent, scale and layer state."""
    import math
    import uuid
    ledger_path = ROOT / 'assets/map_items.json'
    if not ledger_path.exists():
        return
    ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    media_queue = []
    def collect(media):
        if media.get('type') == 'map': media_queue.append(media)
        for child in media.get('maps', []): collect(child)
    for section in cfg['sections']:
        for block in section.get('before', []): collect(block)
        for slide in section['slides']: collect(slide.get('media', {}))
        for block in section.get('after', []): collect(block)
    by_item = {}
    for media in media_queue:
        key = media.get('webmap')
        item_id = ledger[key]['item_id'] if key else media['item_id']
        by_item.setdefault(item_id, []).append(media)
    resources = story._properties['resources']
    for node in story._properties['nodes'].values():
        if node.get('type') != 'webmap': continue
        original = resources[node['data']['map']]
        item_id = original['data']['itemId']
        if not by_item.get(item_id):
            raise RuntimeError(f'No configured map view for {item_id}')
        media = by_item[item_id].pop(0)
        data = json.loads(local_asset('assets/webmaps/' + media['webmap'] + '.json').read_text(encoding='utf-8'))
        extent = data['initialState']['viewpoint']['targetGeometry']
        if media.get('bookmark'):
            extent = next(b['extent'] for b in data['bookmarks'] if b['name'].startswith(media['bookmark']))
        extent = copy.deepcopy(extent)
        # Shift the camera west to move the study area right on screen.
        # This changes only framing; analytical geometries and scale stay intact.
        shift = media.get('view_shift_right', 0)
        if not isinstance(shift, (int, float)) or not 0 <= shift <= .15:
            raise ValueError('view_shift_right must be a fraction between 0 and 0.15')
        dx = (extent['xmax'] - extent['xmin']) * shift
        extent['xmin'] -= dx
        extent['xmax'] -= dx
        if extent['spatialReference']['wkid'] != 4326: raise RuntimeError('Review projected extent before applying view fix')
        x=(extent['xmin']+extent['xmax'])/2; y=(extent['ymin']+extent['ymax'])/2
        if not (113 < x < 115 and 21 < y < 24): raise RuntimeError('Map extent is outside Hong Kong')
        width=(extent['xmax']-extent['xmin'])*111320*math.cos(math.radians(y))
        height=(extent['ymax']-extent['ymin'])*111320
        scale=max(width,height)*3779.52756/750*1.18
        center={'x':x,'y':y,'spatialReference':{'wkid':4326}}
        viewpoint={'rotation':0,'scale':scale,'targetGeometry':center}
        layer_state=[{'id':l['id'],'title':l['title'],'visible':l.get('visibility',True)} for l in data['operationalLayers']]
        if media.get('visible_layers'):
            for layer in layer_state: layer['visible']=layer['id'] in media['visible_layers'] or layer['id'] in {'study_land','study_outline'}
        state_by_id={layer['id']:layer for layer in layer_state}
        if all(key in state_by_id for key in ['facilities','nec_sites','decc_sites']):
            both=state_by_id['nec_sites']['visible'] and state_by_id['decc_sites']['visible']
            state_by_id['facilities']['visible']=both
            if both:
                state_by_id['nec_sites']['visible']=False
                state_by_id['decc_sites']['visible']=False
        resource_id='r-'+uuid.uuid4().hex[:12]
        resource=copy.deepcopy(original)
        resource['data'].update(extent=extent,center=center,viewpoint=viewpoint,zoom=math.log2(591657527.59/scale),mapLayers=layer_state)
        resources[resource_id]=resource
        show_legend=media.get('show_legend',True)
        node['data'].update(map=resource_id,extent=extent,center=center,viewpoint=viewpoint,mapLayers=layer_state,isShowingLegend=show_legend,legendPinned=show_legend)


def configure_embeds(story):
    # SDK 2.4.3 omits isEmbedSupported; the reader falls back to a link card.
    # These flags match a working published StoryMaps inline embed.
    for node in story._properties['nodes'].values():
        if node.get('type') != 'embed':
            continue
        data = node['data']
        url = data['url']
        parts = urlparse(url)
        data.update(isEmbedSupported=True, display='inline', embedSrc=url,
                    providerUrl=f'{parts.scheme}://{parts.netloc}',
                    hasPlaceholderOpenButton=False, hasEmbedOpenButton=False, isLiveOnMobile=True)
        data['caption'] = data.get('caption', data.get('description', ''))
        if node.get('config', {}).get('size') == 'full':
            node['config']['size'] = 'wide'


def publish_current(cfg, baseline, generated=None):
    """Publish reviewed content without changing its existing group-only audience."""
    from arcgis.gis import GIS
    from arcgis.apps.storymap import StoryMap, _utils
    gis = GIS('pro')
    item = gis.content.get(cfg['item_id'])
    story = StoryMap(item, gis=gis)
    check_baseline(story, cfg, baseline)
    groups = {g.id: g.title for g in item.sharing.groups.list()}
    if item.owner != gis.users.me.username or item.access not in {'private', 'shared'} or not groups:
        raise RuntimeError('Expected owner account and existing group-only sharing')
    if '16d0debba6b24c88afffca891f37958a' not in groups:
        raise RuntimeError('The original GEOG-7302 Group 13 is not in the sharing list')
    if generated:
        path = local_asset(generated)
        staged_config = json.loads((path.parent / 'config.json').read_text(encoding='utf-8'))
        if fingerprint(staged_config) != fingerprint(cfg):
            raise RuntimeError('Staged graph was generated from a different configuration')
        story._properties = json.loads(path.read_text(encoding='utf-8'))
        nodes = story._properties['nodes']
        for node in nodes.values():
            if any(child not in nodes for child in node.get('children', [])):
                raise RuntimeError('Staged graph has a missing child node')
        headings = [nodes[n]['data']['text'] for link in next(n for n in nodes.values() if n['type']=='navigation')['data']['links'] for n in [link['nodeId']]]
        if headings != [html.escape(chapter_title(cfg,i,s)) for i,s in enumerate(cfg['sections'])]:
            raise RuntimeError('Staged graph navigation does not match configuration')
    configure_credits(story, cfg)
    configure_embeds(story)
    configure_map_views(story, cfg)
    check_baseline(StoryMap(cfg['item_id'], gis=gis), cfg, baseline)
    # Keep publication metadata consistent while avoiding the SDK access='shared' bug.
    props = _utils.prepare_story_for_save(story, True, True, False, cfg['title'], None, _utils.get_version(story))
    props.pop('access', None)
    # The REST text parameter sanitizes HTML inside JSON, stripping reference
    # href attributes. A JSON file upload preserves the complete story graph.
    import tempfile
    import time
    with tempfile.TemporaryDirectory(prefix='storymap-publish-') as temp_dir:
        published_file = Path(temp_dir) / 'published_data.json'
        published_file.write_text(json.dumps(story._properties, ensure_ascii=False), encoding='utf-8')
        if any(r['resource'] == 'published_data.json' for r in item.resources.list()):
            result = item.resources.update(file=str(published_file), file_name='published_data.json')
        else:
            result = item.resources.add(file=str(published_file), file_name='published_data.json', access='inherit')
        if not result or (isinstance(result, dict) and not result.get('success')):
            raise RuntimeError('Published resource file upload failed')
    props.update(text=json.dumps(story._properties), url=f'https://storymaps.arcgis.com/stories/{item.id}')
    if not item.update(item_properties=props):
        raise RuntimeError('Publication update failed')
    actual = gis.content.get(item.id)
    if actual.access not in {'private', 'shared'} or {g.id for g in actual.sharing.groups.list()} != set(groups):
        raise RuntimeError('Publication audience changed unexpectedly')
    if 'Viewer Copyable' not in actual.typeKeywords or 'smstatuspublished' not in actual.typeKeywords:
        raise RuntimeError('Publication or duplication flag is missing')
    if fingerprint(actual.get_data()) != fingerprint(story._properties):
        raise RuntimeError('Published content readback failed')
    published = gis._con.get(
        gis._portal.resturl + 'content/items/' + item.id + '/resources/published_data.json',
        {'f': 'json', '_ts': str(time.time_ns())},
    )
    if fingerprint(published) != fingerprint(story._properties):
        raise RuntimeError('Published resource differs from the story, including HTML links')
    print('Published and verified. Group-only audience preserved:', groups, flush=True)
    print(f'https://storymaps.arcgis.com/stories/{item.id}')


def apply(cfg, baseline=None, cover_only=False):
    # Lazy import allows offline validation without ArcGIS or a Pro license.
    import arcgis
    from arcgis.gis import GIS
    from arcgis.apps.storymap import StoryMap, Themes
    from arcgis.apps.storymap.story_content import (
        Cover, Navigation, Separator, Text, TextStyles, Sidecar, SidecarSlide, Image, Map, Embed, Swipe, Table,
    )
    if arcgis.__version__ != '2.4.3':
        raise RuntimeError('Revalidate template adapter before changing arcgis 2.4.3')

    class TemplateSlide(SidecarSlide):
        # 2.4.3 accepts media=None in the constructor but its setter rejects it.
        # An empty slide is valid (the SDK reader also handles a missing media child).
        @SidecarSlide.media.setter
        def media(self, content):
            if content is not None:
                self._media = None
                SidecarSlide.media.fset(self, content)

    gis = GIS('pro')
    me = gis.users.me
    item = gis.content.get(cfg['item_id'])
    if not me or not item or item.type != 'StoryMap' or item.owner != me.username:
        raise RuntimeError('Target must be a StoryMap owned by the signed-in user')
    story = StoryMap(item, gis=gis)
    check_baseline(story, cfg, baseline)
    import datetime as dt
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = ROOT / 'backups' / stamp
    backup.mkdir(parents=True)
    (backup / 'draft.json').write_text(json.dumps(story._properties, ensure_ascii=False, indent=2), encoding='utf-8')
    (backup / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Backed up draft JSON: {backup}', flush=True)

    if cover_only:
        original_nodes = copy.deepcopy(story._properties['nodes'])
        cover = configure_cover(story, cfg)
        check_baseline(StoryMap(cfg['item_id'], gis=gis), cfg, baseline)
        save_draft(story, cfg)
        actual = StoryMap(cfg['item_id'], gis=gis)
        if actual._properties['nodes'][cover._node] != story._properties['nodes'][cover._node]:
            raise RuntimeError('Saved cover did not match requested design')
        for node_id, node in original_nodes.items():
            if node_id != cover._node and actual._properties['nodes'].get(node_id) != node:
                raise RuntimeError(f'Unexpected non-cover change: {node_id}')
        print('Cover updated; all non-cover nodes preserved. Draft saved; not published.')
        return

    # Version-pinned adapter: reset IN MEMORY using Esri's own blank template.
    # Do not delete the item or its resources: old assets remain available for recovery.
    template = story._get_storymap_template()
    story._customize_template(template)
    story._create_unique_story_node(template)
    story._properties = copy.deepcopy(template)
    # Strings are custom theme item IDs in SDK 2.4.3. Built-ins require enums.
    story.theme(Themes(cfg.get('theme', 'summit')))
    for resource in story._properties['resources'].values():
        if resource.get('type') == 'story-theme':
            resource['data'].pop('themeItemId', None)
    cover = configure_cover(story, cfg)

    from scripts.arcgis_maps import ensure_maps
    all_media = [s.get('media', {}) for section in cfg['sections'] for s in section['slides']]
    all_media += [b for section in cfg['sections'] for b in section.get('before', [])+section.get('after', [])]
    all_media += [m for b in list(all_media) for m in b.get('maps', [])]
    map_keys = [m['webmap'] for m in all_media if m.get('type') == 'map' and m.get('webmap')]
    ledger = ensure_maps(gis, item, map_keys, version=cfg.get('model_version'))

    def native_table(rows):
        import pandas as pd
        return Table(df=pd.DataFrame([[{'value': str(c)} for c in row] for row in rows],
                                    index=[str(i) for i in range(len(rows))], columns=[str(i) for i in range(len(rows[0]))]))

    def make_media(media):
        if not media:
            return None
        kind = media['type']
        if kind == 'image':
            return Image(str(local_asset(media['path'])))
        if kind == 'map':
            item = gis.content.get(ledger[media['webmap']]['item_id'] if media.get('webmap') else media['item_id'])
            result = Map(item)
            if media.get('visible_layers'):
                for layer in result.map_layers:
                    result.update_map_layers(layer['id'], layer['id'] in media['visible_layers'])
            if media.get('bookmark'):
                bookmark = next(b for b in item.get_data()['bookmarks'] if b['name'].startswith(media['bookmark']))
                result.set_viewpoint(extent=bookmark['extent'])
            return result
        if kind == 'swipe':
            if media.get('maps'):
                return Swipe(content=[make_media(m) for m in media['maps']])
            return Swipe(content=[Image(str(local_asset(p))) for p in media['images']])
        return Embed(embed_url(cfg, media['path']))

    figure_number=0
    def add_block(block):
        nonlocal figure_number
        kind = block['type']
        if kind == 'comparison_legend':
            story.add(Image(str(local_asset(block['path']))), alt_text='Left: NEC-only map legend. Right: NEC and DECC map legend.')
        elif kind == 'table':
            story.add(native_table(block['rows']))
        elif kind in {'text', 'quote', 'heading'}:
            style = {'text': TextStyles.PARAGRAPH, 'quote': TextStyles.QUOTE, 'heading': TextStyles.SUBHEADING}[kind]
            story.add(Text(html.escape(block['text']), style=style))
        elif kind == 'references':
            for reference_number,source in enumerate(cfg.get('references', []),1):
                url = html.escape(source['url'], quote=True)
                story.add(Text(f'[{reference_number}] {source["html"]} <a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'))
        else:
            content = make_media(block)
            figure_number+=1
            title=html.escape(block.get('figure_title',''))
            caption=f'<strong>Fig. {figure_number}. {title}</strong> '+html.escape(block.get('caption',''))
            story.add(content, caption=caption, alt_text=block.get('alt', block.get('caption', '')))
            if isinstance(content, Embed):
                content.display = 'inline'
                story._properties['nodes'][content._node].setdefault('config', {})['size'] = 'full'

    chapter_headings = []
    if cfg.get('cover_note'):
        story.add(Text(html.escape(cfg['cover_note']), style=TextStyles.PARAGRAPH))
    for index, section in enumerate(cfg['sections']):
        if index:
            story.add(Separator())
            # Native text spacing; no unsupported injected CSS or themed font overrides.
            for _ in range(cfg.get('chapter_spacing_lines',0)):
                story.add(Text('<br>',style=TextStyles.PARAGRAPH))
        heading = Text(html.escape(chapter_title(cfg,index,section)), style=TextStyles.HEADING)
        story.add(heading)
        chapter_headings.append(heading)
        if section.get('intro'):
            story.add(Text(html.escape(section['intro'])))
        for block in section.get('before', []):
            add_block(block)
        if section['slides']:
            sidecar = Sidecar(style=section.get('layout', 'docked-panel'))
            story.add(sidecar)
            slides = []
            for slide in section['slides']:
                texts = [Text(html.escape(slide['title']), style=TextStyles.SUBHEADING)]
                if slide.get('summary'):
                    texts.append(Text(html.escape(slide['summary'])))
                if slide.get('text'):
                    texts.append(Text(html.escape(slide['text']).replace('\n', '<br>')))
                content = make_media(slide.get('media'))
                slides.append(TemplateSlide(content=texts, media=content))
            sidecar.slides = slides
            # SDK has no public switch-panel-placement setter in 2.4.3.
            position = section.get('panel_position', 'start')
            story._properties['nodes'][sidecar._node]['data']['narrativePanelPosition'] = position
            story._properties['nodes'][sidecar._node]['data']['narrativePanelSize'] = section.get('panel_size', 'small')
            for slide in slides:
                if isinstance(slide.media, Embed):
                    slide.media.display = 'inline'
                panel = story._properties['nodes'][slide._node]['children'][0]
                panel_position = position + '-top' if section.get('layout') == 'slideshow' else position
                story._properties['nodes'][panel]['data']['position'] = panel_position
        for block in section.get('after', []):
            add_block(block)
    configure_credits(story, cfg)
    configure_embeds(story)
    configure_map_views(story, cfg)
    navigation = next(c for c in story.contents if isinstance(c, Navigation))
    navigation.hidden = False
    # SDK 2.4.3's setter writes bare IDs, but the builder expects link objects.
    story._properties['nodes'][navigation._node]['data']['links'] = [
        {'nodeId': heading._node} for heading in chapter_headings
    ]
    (backup / 'generated.json').write_text(json.dumps(story._properties, ensure_ascii=False, indent=2), encoding='utf-8')
    # SDK 2.4.3 save() tries to reapply access='shared' via a missing
    # SharingGroupManager.update method. Prepare the same draft, then update
    # metadata WITHOUT an access field so existing sharing stays untouched.
    from arcgis.apps.storymap import _utils
    check_baseline(StoryMap(cfg['item_id'], gis=gis), cfg, baseline)
    props = _utils.prepare_story_for_save(
        story, False, None, None, cfg['title'], None, _utils.get_version(story)
    )
    props.pop('access', None)
    if not item.update(item_properties=props):
        raise RuntimeError('ArcGIS rejected draft metadata update')
    # Read back the server's latest draft instead of assuming a save succeeded.
    actual = StoryMap(cfg['item_id'], gis=gis)
    themes = [r['data'] for r in actual._properties['resources'].values() if r.get('type') == 'story-theme']
    if len(themes) != 1 or themes[0].get('themeId') != cfg.get('theme', 'summit') or 'themeItemId' in themes[0]:
        raise RuntimeError('Saved built-in theme contains an invalid reference')
    saved_nav = next(c for c in actual.contents if isinstance(c, Navigation))
    nav_node = actual._properties['nodes'][saved_nav._node]
    if nav_node['config']['isHidden'] or nav_node['data']['links'] != [{'nodeId': h._node} for h in chapter_headings]:
        raise RuntimeError('Saved chapter navigation did not match the headings')
    sidecars = [c for c in actual.contents if isinstance(c, Sidecar)]
    immersive_sections = [s for s in cfg['sections'] if s['slides']]
    if len(sidecars) != len(immersive_sections) or [len(c.slides) for c in sidecars] != [len(s['slides']) for s in immersive_sections]:
        raise RuntimeError('Saved draft structure did not match configuration')
    for sidecar, section in zip(sidecars, immersive_sections):
        node = actual._properties['nodes'][sidecar._node]
        if node['data']['subtype'] != section.get('layout', 'docked-panel') or node['data']['narrativePanelPosition'] != section.get('panel_position', 'start'):
            raise RuntimeError('Saved layout or panel placement did not match configuration')
        for slide, slide_config in zip(sidecar.slides, section['slides']):
            panel = actual._properties['nodes'][slide._node]['children'][0]
            expected = section.get('panel_position', 'start')
            if section.get('layout') == 'slideshow':
                expected += '-top'
            if actual._properties['nodes'][panel]['data']['position'] != expected:
                raise RuntimeError('Saved slide panel placement did not match configuration')
            if slide_config.get('media', {}).get('type') == 'embed':
                if not isinstance(slide.media, Embed):
                    raise RuntimeError('Saved embed is missing')
                embed_data = actual._properties['nodes'][slide.media._node]['data']
                if embed_data['display'] != 'inline' or embed_data['url'] != embed_url(cfg, slide_config['media']['path']):
                    raise RuntimeError('Saved embed URL or display did not match configuration')
    actual_cover = next(c for c in actual.contents if isinstance(c, Cover))
    if actual_cover.summary != cfg.get('subtitle', '') or actual_cover.byline != cover.byline:
        raise RuntimeError('Saved cover did not match configuration')
    print(f'Verified {len(sidecars)} sidecars. Draft saved; not published.', flush=True)
    print(f'https://storymaps.arcgis.com/stories/{cfg["item_id"]}/edit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--apply', action='store_true', help='Overwrite draft after inspection and user-approved reconciliation')
    actions.add_argument('--inspect', action='store_true', help='Read-only export of the current story and all item resources')
    actions.add_argument('--prepare', action='store_true', help='Prepare the approved handoff data and current narrative locally; no online writes')
    actions.add_argument('--update-cover', action='store_true', help='Update only the cover, preserving manual edits elsewhere')
    actions.add_argument('--publish', action='store_true', help='Publish reviewed draft, preserving exact group sharing and allowing duplication')
    parser.add_argument('--based-on', help='Reviewed snapshot folder required by --apply')
    parser.add_argument('--generated', help='Optional reviewed generated.json from a matching local backup, for publication')
    args = parser.parse_args()
    if args.prepare:
        from scripts.update_handoff_20261106 import run
        from scripts.style_webmaps import run as style
        import sys
        sys.path.insert(0,str(ROOT/'scripts'))
        from scripts.compose_current_story import compose
        run();style();compose()
        return
    cfg = json.loads((ROOT / 'story.json').read_text(encoding='utf-8')) if args.inspect else load_config()
    if args.inspect:
        inspect_story(cfg)
        return
    print(f'{cfg["title"]}: {len(cfg["sections"])} sections, {sum(len(s["slides"]) for s in cfg["sections"])} slides', flush=True)
    if args.publish:
        publish_current(cfg, args.based_on, args.generated)
    elif args.apply or args.update_cover:
        apply(cfg, args.based_on, cover_only=args.update_cover)
    else:
        print('Configuration valid. Use --apply to overwrite the online draft.')


if __name__ == '__main__':
    main()
