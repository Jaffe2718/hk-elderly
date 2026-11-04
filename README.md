# Group 13 StoryMap

## Editing rules

- Use English for all repository documentation, story text, interface labels, map popups, figures and tables. Original bilingual handoff files remain only in ignored local preparation folders.
- `story.json` is the source of truth for chapter order, text, layouts, and asset references. `storymap.py` is the single entry point for rebuilding the online draft.
- Every apply run replaces all draft content while retaining the item ID and URL. Before applying, export the current online state, reconcile manual edits, and obtain explicit user approval to update the generator. Never silently discard collaborators' manual changes.
- Keep the current chapter order until a new outline is agreed. Titles and the subtitle remain editable placeholders, not research conclusions.
- Use the built-in Summit theme, a full cover with a top-left themed title panel, a title, subtitle, and member names without student IDs.
- Use owned or appropriately licensed assets. Never commit credentials, tokens, login profiles, sensitive source data, or local backups.
- Sign into ArcGIS Pro as the StoryMap owner. Close the StoryMap editor tab before applying changes to prevent stale browser autosaves; reopen it afterward to preview.
- Apply runs save unpublished drafts and preserve sharing settings. Review the result in the StoryMaps builder before publishing.
- `backups/` stores the previous draft JSON, configuration, and generated JSON. It is ignored by Git and is not a complete offline media backup. The script does not proactively delete old item resources.

## Layout

| Chapter | Native composition |
| --- | --- |
| Introduction | Opening question, Floating Sidecar and population Web Map |
| Data & Objective | Native evidence table, Slideshow, premises Web Map and age-share Web Map |
| Methodology | Interactive workflow embed, native headings, quotation and explanatory text |
| Spatial Analysis | Docked Sidecar, analytical Web Maps, coverage-explorer embed, case table, native Web Map Swipe and interactive CSV-backed charts |
| Conclusions | Native headings, evidence-based synthesis, limitations and next steps |
| References | Native official-source links, followed by a native Credit acknowledgement |

The visible top navigation always links to these six chapter headings. The white Summit theme, top-left cover, course code and English member names are retained. Only the workflow, coverage explorer and interactive charts use GitHub Pages. All other content uses native StoryMap components. The HTML map's analytical attributes come from the supplied Web Map definitions; inherited geometry and the illustrative residential overlay come from the original collaborator demo.

## Run

Validate locally without network access or an ArcGIS license:

```powershell
python storymap.py
```

Replace the online draft using the signed-in ArcGIS Pro account:

```powershell
& 'D:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat' -u storymap.py --apply --based-on snapshots/REVIEWED_SNAPSHOT
```

In Codex, the apply command requires execution outside the sandbox to access the Pro license. ArcGIS API for Python is pinned to **2.4.3**. After saving, the script reads back the draft and verifies chapter and slide counts, layouts, panel placements, cover text, embed settings, chapter navigation, and the theme reference.

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

## Visual structure

The current reference is recorded in `reference_id`. Keep the white Summit theme and a top-left title/subtitle/member block while no cover image is available. Chapter headings are followed by short editorial introductions, separators between chapters, and mixed Sidecar layouts. Slide summaries describe the intended reading task without inventing findings; media remains empty where no asset is configured.

The visible top chapter navigation is mandatory. Each apply run binds it to the configured chapter headings using builder-compatible `nodeId` link objects, and verifies the saved links and visibility. The SDK 2.4.3 navigation setter writes a different schema, so the adapter sets these link objects directly. Preserve this navigation when changing chapter order.

## Inspect manual edits before rebuilding

Export the current online StoryMap without changing it or adopting changes into the local generator:

```powershell
& 'D:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat' -u storymap.py --inspect
```

Each ignored `snapshots/TIMESTAMP/` directory contains:

- `REPORT.md`: reading order, complete per-node data/configuration, disconnected nodes, complete top-level styles/resources/actions, and review instructions.
- `draft.json`: the complete current draft graph, without filtering unknown node types or fields.
- `item.json` and `item-data.json`: item metadata and item data, including published content where stored there.
- `resource-list.json` and `resources/`: every resource listed by ArcGIS, including draft/published JSON and media files.
- `manifest.json`: the item ID, draft fingerprint, download hashes, errors, and an export stability check.
- `local-config.json`: the local configuration at inspection time for comparison.

Agent workflow: read the report and original JSON, compare against the generator, list differences, and propose how to preserve each manual change. Request explicit user approval before adopting the online state into `story.json` or `storymap.py`. Unsupported components must be represented or preserved before a rebuild; never ignore them just because the local schema is narrower.

After approval, update the generator/configuration, validate locally, and apply using `--based-on` with the reviewed snapshot directory. An apply without a baseline is blocked. The script checks that the online draft still matches the reviewed fingerprint both before building and immediately before saving; if collaborators changed it again, inspect and review again. This is a drift check, not an atomic server lock. Close editor tabs during the final apply.

Snapshots are local and ignored by Git because manually added content may not be intended for public sharing. Remote web maps, layers, custom themes, and embeds remain references, not complete offline copies. The report explicitly records this scope; inspect those referenced items and browser rendering when necessary. Unsaved browser edits cannot be exported. An incomplete or unstable snapshot cannot be used as a rebuild baseline.

## Cover-only updates

`course` adds the course code to the byline. The current cover uses Full with a themed title panel at the top left. `cover_vertical_position`, `cover_horizontal_position`, `cover_style`, and `cover_size` control its placement and appearance. Missing cover imagery remains empty.

After inspection and approval of a cover change, use `--update-cover --based-on snapshots/REVIEWED_SNAPSHOT` instead of `--apply` to preserve manually edited content outside the cover. The command verifies that every non-cover node remains unchanged. This targeted operation does not reconcile other manual edits into the full-rebuild configuration; those still require a separate approved reconciliation before a full rebuild.

## Rebuild and publication

The source handoff was reviewed before composition. It contains 12 embedded-feature Web Map definitions, 22 distinct English PNG/SVG figure pairs, chart tables and a private-import helper. The delivered ZIP is an asset subset, not the complete raw-data/geodatabase package described in the handoff PDF. Original inputs and full ArcGIS Pro reproduction are not claimed here.

- `scripts/prepare_assets.py`: creates English-only derivatives from the ignored local handoff and archived original HTML. It does not modify source materials.
- `scripts/compose_story.py`: optional bootstrap for the supplied narrative. It overwrites `story.json`; do not run it after manual content reconciliation without review.
- `scripts/arcgis_maps.py`: called by the main generator to import and verify referenced Web Maps. `assets/map_items.json` records item IDs and their exact sharing groups; it contains no credentials.
- `storymap.py --apply --based-on SNAPSHOT`: imports native map dependencies and writes a verified draft. Snapshot and drift requirements still apply.
- `storymap.py --publish --based-on SNAPSHOT`: publishes the reviewed current draft, refreshes native Credits, preserves its exact group-only audience, and enables duplication. Run only with explicit user authorization to publish. It refuses unexpected sharing scopes or a missing original group.

Before publication, deploy the workflow, map and chart embeds, check the live endpoints, review the current draft and take a fresh snapshot. Publication verifies the stored content, status, copyability and sharing. API publication bypasses the StoryMaps builder issue checker, so browser review and dependency-sharing checks remain important.

### Evidence and interpretation

The main rule is residents aged 60+ >= 14,695 AND over 50% of residential land beyond 800 m of the nearest NEC. It selects 524, 628, 833 and 950S among 210 assessed groups; group 295 remains unassessed. Source and interpretation notes appear in native Credits. All distances are planar; coverage describes residential ground area, not people served, centre capacity or walking accessibility. The published analysis reproduces supplied Python/GDAL results; it does not claim an independent ArcGIS Pro geoprocessing rerun.

### Interactive assets

- `docs/embeds/workflow/`: original SVG/HTML implementation with node detail panels, linked-path highlighting, search, walkthrough, pan, zoom and SVG export. Interaction direction is inspired by dsh-archify; no Archify source code is incorporated.
- `docs/embeds/elderly-map/`: English-only Leaflet explorer with distance/age/facility scenarios, area popups and case navigation. Main-scenario counts and alternatives are checked against the handoff data.
- `docs/vendor/`: Leaflet 1.9.4 and its BSD 2-Clause license.

Snapshots, local QA screenshots and raw handoff materials remain ignored. Only public-safe English derivatives and generator sources are committed.

Final figure policy: no PDF crops are used. Population composition uses a native Web Map with its age-share layer enabled. Housing/district coverage and age/distance decisions use interactive HTML charts generated from the supplied CSV tables. The Tiu Keng Leng comparison uses two native Web Maps with the same bookmark extent. `scripts/render_charts.py` remains an optional static fallback and is not inserted into the story. The original English handoff PNGs remain available as reference assets.

### Preview revision

- Six navigation chapters end with References, followed by a native Credit acknowledgement.
- Native Web Map nodes each receive an isolated resource and an explicit Hong Kong centre, extent and positive scale, including matched case-study Swipe views.
- HTML embeds declare supported inline rendering rather than link cards.
- The workflow uses five architecture layers, category colours, line icons and an English colour legend with step counts. All connections retain static centre lines. Only the selected step's outgoing connections carry glowing green packets; the packets fade at the ports and wrap seamlessly at a constant path speed. Reduced-motion settings disable animation. Inactive labels remain fully readable. SVG exports include the legend.
- The workflow omits the duplicate heading, sizes its SVG viewport to the actual iframe container and focuses the current step on narrow frames. Search, Previous/Next, Fit and pan/zoom remain available.
- Interactive housing/district coverage and distance/age decision charts are generated from the supplied CSVs with `scripts/prepare_chart_data.py`. They support exact-value inspection, table view and CSV download; coverage bars also support facility-scope filtering and sorting.
- Draft updates and publishing are separate. The current review authorises pushing assets and replacing the draft only; it does not authorise a new publication.
