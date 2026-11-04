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
                    for image_path in media['images']:
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
        local_asset('docs/' + path)
        url = urljoin(base.rstrip('/') + '/', path)
    if urlparse(url).scheme != 'https':
        raise ValueError('Embeds require HTTPS')
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
    story.credits(heading='Credits and sources', description='GEOG7302 | Group 13')
    story.credits(content='Research and authorship', attribution=' · '.join(cfg['members']))
    story.credits(content='Study scope', attribution='Residential-area proximity and explicit Binary screening. 2021 Census and land use; SWD premises snapshot retrieved 2 November 2026.')
    for source in cfg.get('sources', []):
        story.credits(content=html.escape(source['name']), attribution=f'<a href="{html.escape(source["url"], quote=True)}" target="_blank" rel="noopener noreferrer">Official source</a>')
    story.credits(content='Maps and analytical graphics', attribution='Group 13 collaborator handoff: supplied Python/GDAL pre-analysis, English figures and Web Map definitions. ArcGIS account import and StoryMap assembly completed in this project.')
    story.credits(content='Interactive components', attribution='Project-specific workflow and coverage explorer; Leaflet 1.9.4. Workflow interaction direction inspired by Archify (GongYuanCaiJi/dsh-archify).')
    story.credits(content='Interpretation', attribution='Priority areas warrant further investigation. Distances are planar, not walking routes; residential-area coverage is not people served; premises counts are not capacity.')


def publish_current(cfg, baseline):
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
    configure_credits(story, cfg)
    # Keep publication metadata consistent while avoiding the SDK access='shared' bug.
    props = _utils.prepare_story_for_save(story, True, True, False, cfg['title'], None, _utils.get_version(story))
    props.pop('access', None)
    for resource in item.resources.list():
        if resource['resource'] == 'published_data.json':
            _utils.remove_resource(story, file='published_data.json')
    _utils.add_resource(story, resource_name='published_data.json', text=json.dumps(story._properties))
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
    map_keys = [m['webmap'] for m in all_media if m.get('type') == 'map' and m.get('webmap')]
    ledger = ensure_maps(gis, item, map_keys)

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
            return Map(gis.content.get(ledger[media['webmap']]['item_id'] if media.get('webmap') else media['item_id']))
        if kind == 'swipe':
            return Swipe(content=[Image(str(local_asset(p))) for p in media['images']])
        return Embed(embed_url(cfg, media['path']))

    def add_block(block):
        kind = block['type']
        if kind == 'table':
            story.add(native_table(block['rows']))
        elif kind in {'text', 'quote', 'heading'}:
            style = {'text': TextStyles.PARAGRAPH, 'quote': TextStyles.QUOTE, 'heading': TextStyles.SUBHEADING}[kind]
            story.add(Text(html.escape(block['text']), style=style))
        else:
            content = make_media(block)
            story.add(content, caption=block.get('caption'), alt_text=block.get('alt', block.get('caption', '')))
            if isinstance(content, Embed):
                content.display = 'inline'
                story._properties['nodes'][content._node].setdefault('config', {})['size'] = 'full'

    chapter_headings = []
    for index, section in enumerate(cfg['sections']):
        if index:
            story.add(Separator())
        heading = Text(html.escape(section['title']), style=TextStyles.HEADING)
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
            for slide in slides:
                if isinstance(slide.media, Embed):
                    slide.media.display = 'inline'
                panel = story._properties['nodes'][slide._node]['children'][0]
                panel_position = position + '-top' if section.get('layout') == 'slideshow' else position
                story._properties['nodes'][panel]['data']['position'] = panel_position
        for block in section.get('after', []):
            add_block(block)
    configure_credits(story, cfg)
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
    actions.add_argument('--update-cover', action='store_true', help='Update only the cover, preserving manual edits elsewhere')
    actions.add_argument('--publish', action='store_true', help='Publish reviewed draft, preserving exact group sharing and allowing duplication')
    parser.add_argument('--based-on', help='Reviewed snapshot folder required by --apply')
    args = parser.parse_args()
    cfg = json.loads((ROOT / 'story.json').read_text(encoding='utf-8')) if args.inspect else load_config()
    if args.inspect:
        inspect_story(cfg)
        return
    print(f'{cfg["title"]}: {len(cfg["sections"])} sections, {sum(len(s["slides"]) for s in cfg["sections"])} slides', flush=True)
    if args.publish:
        publish_current(cfg, args.based_on)
    elif args.apply or args.update_cover:
        apply(cfg, args.based_on, cover_only=args.update_cover)
    else:
        print('Configuration valid. Use --apply to overwrite the online draft.')


if __name__ == '__main__':
    main()
