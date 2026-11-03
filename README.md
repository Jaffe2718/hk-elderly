# Group 13 StoryMap

## Editing rules

- Use English for repository documentation, code comments, and story text. The collaborator's demo HTML is temporarily exempt; keep its content unchanged unless requested.
- `story.json` is the source of truth for chapter order, text, layouts, and asset references. `storymap.py` is the single entry point for rebuilding the online draft.
- Every apply run replaces all draft content while retaining the item ID and URL. Manual edits in the online builder are overwritten on the next run.
- Keep the current chapter order until a new outline is agreed. Titles and the subtitle remain editable placeholders, not research conclusions.
- Use the built-in Summit theme, a full cover with a themed title panel, a title, subtitle, and member names without student IDs.
- Use owned or appropriately licensed assets. Never commit credentials, tokens, login profiles, sensitive source data, or local backups.
- Sign into ArcGIS Pro as the StoryMap owner. Close the StoryMap editor tab before applying changes to prevent stale browser autosaves; reopen it afterward to preview.
- Apply runs save unpublished drafts and preserve sharing settings. Review the result in the StoryMaps builder before publishing.
- `backups/` stores the previous draft JSON, configuration, and generated JSON. It is ignored by Git and is not a complete offline media backup. The script does not proactively delete old item resources.

## Layout

| Chapter | Layout | Narrative panel |
| --- | --- | --- |
| 01 Background | Docked | Left |
| 02 Data & Methods | Floating | Right |
| 03 Spatial Patterns | Slideshow | Top left |
| 04 Accessibility & Service Provision | Docked | Right |
| 05 Discussion & Conclusions | Floating | Left |

Chapter 04 uses Docked to reserve a separate media area for the embedded map. Available `layout` values are `docked-panel`, `floating-panel`, and `slideshow`. `panel_position` accepts `start` (left) and `end` (right) for this English story; slideshow panels use the corresponding top corners. Media areas stay empty until assets are supplied.

## Run

Validate locally without network access or an ArcGIS license:

```powershell
python storymap.py
```

Replace the online draft using the signed-in ArcGIS Pro account:

```powershell
& 'D:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat' -u storymap.py --apply
```

In Codex, the apply command requires execution outside the sandbox to access the Pro license. ArcGIS API for Python is pinned to **2.4.3**. After saving, the script reads back the draft and verifies chapter and slide counts, layouts, panel placements, cover text, embed settings, and the theme reference.

## Theme and SDK compatibility

The `theme` configuration selects a built-in theme, currently `summit`. The script passes a `Themes` enum to the API. SDK 2.4.3 interprets the string `"summit"` as a custom theme item ID, creating an invalid `themeItemId` reference that causes the **Theme not found** warning. The script removes custom theme references and verifies the saved built-in `themeId`.

`reference_id` records the original visual reference only. Rebuilding does not depend on that story being accessible and does not copy its content.

The version-pinned adapter in `apply()` uses Esri's internal blank template and draft preparation methods. It also supports empty Sidecar media, sets panel placement fields directly, and avoids reapplying `access` during draft metadata updates because SDK 2.4.3 calls a missing `SharingGroupManager.update` method for group-shared items. These adapters do not modify the installed SDK. Revalidate them before upgrading ArcGIS.

## Add assets

Place local images in `assets/`, then add optional `text` and `media` fields to a slide:

```json
{"title":"Population Distribution", "text":"Your narrative", "media":{"type":"image", "path":"assets/population.png"}}
```

For an ArcGIS WebMap or WebScene:

```json
{"type":"map", "item_id":"ARCGIS_ITEM_ID"}
```

For an embedded page, place the file at `docs/embeds/chart/index.html` and reference it relative to the Pages root:

```json
{"type":"embed", "path":"embeds/chart/index.html"}
```

Embeds display inline. Apply runs preserve all configured asset references.

## GitHub Pages

- Repository: <https://github.com/Jaffe2718/hk-elderly>
- Publishing source: `docs/` on `main`.
- Base URL: <https://jaffe2718.github.io/hk-elderly/>
- Demo: <https://jaffe2718.github.io/hk-elderly/embeds/elderly-map/index.html>

Use relative URLs inside hosted pages to support the repository URL prefix. Pages hosts public static HTML/CSS/JS and appropriately sized public datasets; it does not run a Python backend. Images can also be uploaded directly to ArcGIS.

The collaborator's demo is stored unchanged at `docs/embeds/elderly-map/index.html`. Leaflet, styles, and data are embedded in the file, with no additional linked assets or fetch requests. It appears in chapter 04, **Service Distribution**. Treat it as an interactive preview rather than validated final research findings.

Push new embed assets and wait for Pages deployment to succeed before applying the StoryMap configuration. Pages deployment and StoryMap updates are separate operations; StoryMap updates currently use local ArcGIS Pro authentication.
