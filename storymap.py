"""Rebuild the configured StoryMap draft. Requires ArcGIS API for Python 2.4.3."""
import argparse
import copy
import html
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent


def load_config():
    cfg = json.loads((ROOT / 'story.json').read_text(encoding='utf-8'))
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
        if not section['title'] or not section['slides']:
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


def apply(cfg):
    # Lazy import allows offline validation without ArcGIS or a Pro license.
    import arcgis
    from arcgis.gis import GIS
    from arcgis.apps.storymap import StoryMap
    from arcgis.apps.storymap.story_content import (
        Cover, Text, TextStyles, Sidecar, SidecarSlide, Image, Map, Embed,
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
    import datetime as dt
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = ROOT / 'backups' / stamp
    backup.mkdir(parents=True)
    (backup / 'draft.json').write_text(json.dumps(story._properties, ensure_ascii=False, indent=2), encoding='utf-8')
    (backup / 'config.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Backed up draft JSON: {backup}', flush=True)

    reference = StoryMap(cfg['reference_id'], gis=gis)
    # Version-pinned adapter: reset IN MEMORY using Esri's own blank template.
    # Do not delete the item or its resources: old assets remain available for recovery.
    template = story._get_storymap_template()
    story._customize_template(template)
    story._create_unique_story_node(template)
    story._properties = copy.deepcopy(template)
    story.theme(reference.get_theme())
    cover = next(c for c in story.contents if isinstance(c, Cover))
    cover.title = cfg['title']
    cover.summary = cfg.get('subtitle', '')
    cover.byline = cfg['byline'] + ' | ' + ' · '.join(cfg.get('members', []))
    cover.type = cfg.get('cover_type', 'full')
    if cover.type == 'full':
        cover.style = 'themed'
        cover.vertical_position = 'middle'
        cover.horizontal_position = 'start'
        cover.size = 'large'

    for section in cfg['sections']:
        story.add(Text(html.escape(section['title']), style=TextStyles.HEADING))
        sidecar = Sidecar(style=section.get('layout', 'docked-panel'))
        story.add(sidecar)
        slides = []
        for slide in section['slides']:
            texts = [Text(html.escape(slide['title']), style=TextStyles.SUBHEADING)]
            if slide.get('text'):
                texts.append(Text(html.escape(slide['text']).replace('\n', '<br>')))
            media = slide.get('media')
            content = None
            if media:
                if media['type'] == 'image':
                    content = Image(str(local_asset(media['path'])))
                elif media['type'] == 'map':
                    content = Map(gis.content.get(media['item_id']))
                else:
                    content = Embed(embed_url(cfg, media['path']))
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
    (backup / 'generated.json').write_text(json.dumps(story._properties, ensure_ascii=False, indent=2), encoding='utf-8')
    # SDK 2.4.3 save() tries to reapply access='shared' via a missing
    # SharingGroupManager.update method. Prepare the same draft, then update
    # metadata WITHOUT an access field so existing sharing stays untouched.
    from arcgis.apps.storymap import _utils
    props = _utils.prepare_story_for_save(
        story, False, None, None, cfg['title'], None, _utils.get_version(story)
    )
    props.pop('access', None)
    if not item.update(item_properties=props):
        raise RuntimeError('ArcGIS rejected draft metadata update')
    # Read back the server's latest draft instead of assuming a save succeeded.
    actual = StoryMap(cfg['item_id'], gis=gis)
    sidecars = [c for c in actual.contents if isinstance(c, Sidecar)]
    if len(sidecars) != len(cfg['sections']) or [len(c.slides) for c in sidecars] != [len(s['slides']) for s in cfg['sections']]:
        raise RuntimeError('Saved draft structure did not match configuration')
    for sidecar, section in zip(sidecars, cfg['sections']):
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
    parser.add_argument('--apply', action='store_true', help='Overwrite all draft content from story.json')
    args = parser.parse_args()
    cfg = load_config()
    print(f'{cfg["title"]}: {len(cfg["sections"])} sections, {sum(len(s["slides"]) for s in cfg["sections"])} slides', flush=True)
    if args.apply:
        apply(cfg)
    else:
        print('Configuration valid. Use --apply to overwrite the online draft.')


if __name__ == '__main__':
    main()
