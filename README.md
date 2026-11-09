# Group 13 StoryMap

The current title is **Here Are the Service Gaps Close to Home!**. `story.json` controls the narrative, chapter order, layouts and asset references. `storymap.py` is the single editing entry point. All public text and derived assets are English.

## Current analysis

The November 6 model follows the updated proposal: select groups with both a 65+ population share at or above P60 and a residential-area share beyond NEC 800 m at or above P60. Each of the 210 assessed STPUGs has equal weight, and ties are included. The exact cutoffs are 19.913163372872837% and 30.75788624778998%. There are 13 selected areas; group 295 has no assigned residential cells and remains unassessed.

The supplied fixed 20% / 30% rule selects 14 areas. It is a labelled comparison, not the main result. Group 149 belongs only to that comparison. The 27 sensitivity scenarios combine three radii with P50/P60/P70 for each indicator, recalculating gap percentiles at each radius. Separate fixed-cutoff distance tests produce 32, 13 and 10 selections. Alternative age definitions use their own cohort P60 cutoffs.

Local reviews cover Wan Chai (131), Ta Kwu Ling (620S) and Cheung Chau (920). Model A maximises additional residential ground area; independent B and complementary C answer different questions. Existing community venues provide addresses for review, not evidence of spare capacity. Global portfolio totals from the supplied 14-area model are excluded from the 13-area narrative.

Population and residential land describe 2021. SWD premises were retrieved on November 2, 2026; HAD venues were checked on November 5. Classification is independently recalculated from the supplied proximity outputs. This is not an independent rerun of the complete proximity geoprocessing. Residential area is not people served, capacity or walking accessibility. See `assets/analysis/provenance.json` for source hashes and validation scope.

## Editing and deployment

1. Keep original handoffs in ignored `build/handoff-20261106/`. The extracted package contains `redo7302/` and `HK_Elderly_Analysis_Tables.xlsx`.
2. Prepare the approved model and narrative locally:

   ```powershell
   & 'D:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe' -X utf8 storymap.py --prepare
   ```

3. Validate the configuration with the same interpreter and `storymap.py` without arguments. `--apply` uses the committed derivatives and does not require the original handoff.
4. Export the online story with `storymap.py --inspect`. Review the snapshot report and reconcile collaborators' manual changes into the generator before a full rebuild. A full apply replaces all draft content. Obtain user approval for that reconciliation; never silently discard manual edits.
5. Commit and push only when authorised, then check that GitHub Pages serves the new embed files. No credentials, original bilingual handoffs or snapshots belong in Git.
6. Sign into ArcGIS Pro as the owner, close StoryMap editor tabs to avoid stale autosaves, and apply the approved update:

   ```powershell
   & 'D:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe' -X utf8 storymap.py --apply --based-on snapshots/REVIEWED_SNAPSHOT
   ```

Apply saves an **unpublished draft**. On November 6, 2026, the project owner granted standing authorisation to publish subsequent approved project updates. After validation, commit, push, rebuild the draft and publish unless the user gives a later instruction to stop at local changes or draft preview. On November 8, 2026, the owner additionally authorised public publication: everyone may view and duplicate the story. Retain the `GEOG-7302 Group 13` sharing group and make current map dependencies public along with the story. ArcGIS API for Python is pinned to 2.4.3; revalidate the template adapter before upgrading it.

## Publication isolation

The new draft uses `docs/embeds/20261106/`. Existing unversioned embed files remain unchanged so the published story retains its previous results until publication is approved. When `model_version` changes, the map importer creates separately versioned Web Map items rather than updating maps used by the published story. The ledger retains the previous item ID. Do not reuse or overwrite a published model's version identifier for another model.

The four embed components are the workflow, coverage explorer, linked location comparison and charts. They are hosted by GitHub Pages. The cover, text, tables, headings, Sidecars, analytical maps, references and Credit use native StoryMap components. The comparison uses the ArcGIS Maps SDK Swipe widget to keep its two legends fixed inside opposite map corners.

## Design and interpretation rules

- Keep the white Summit theme, top-left cover panel, short main title, GEOG7302 and English member names without student numbers. The approved cover photograph's source and licence are in `assets/cover/attribution.json` and Credit.
- Keep six numbered navigation chapters: Introduction; Data & Objective; Methodology; Spatial Analysis; Conclusions; References. Credit is an unnumbered footer outside navigation.
- Use Floating and Docked Sidecars with small narrative panels. Do not use Slideshow layouts. Allow space between chapters.
- Use the shared muted-lavender map theme, pale-blue water, dark-red study boundary, deep-green NEC diamonds and deep-orange DECC triangles. The dissolved outline preserves islands and uses an explicit Hong Kong 1980 to WGS84 transformation.
- Legend labels must match actual classes, including zero, missing values and threshold endpoints. Hide unused fallback legend classes. Where both facility types are visible, use the combined categorical point layer to avoid a separator between them.
- Put both comparison legends inside the map, left and right, clear of Home and zoom controls. Keep matched geography and distinguish the two coverage palettes.
- Number standalone figures as `Fig. N.` with smaller captions. Sidecar maps do not receive separate figure numbers. References contain only numbered APA-style entries; do not append explanatory paragraphs.
- Keep coverage and sensitivity chart tabs separate. Support table view and responsive pagination. Do not add CSV or SVG export controls.
- The workflow starts neutral. Fit resets selection, search, zoom and playback. Pause freezes traversal and flowing edges. Animate outgoing edges from the active node only. Preserve a static centre line and readable inactive nodes.

## Snapshots and recovery

`--inspect` exports the current draft, published data, item metadata, all item resources, node/resource JSON and a readable report under ignored `snapshots/TIMESTAMP/`. The report lists every node and asset reference, including style, geometry, unknown fields and orphaned nodes. Referenced remote maps or embeds are not complete offline media copies.

Apply requires a complete, stable snapshot and checks its draft fingerprint before building and immediately before saving. This detects drift; it is not an atomic server lock. Backups retain the prior draft, configuration and generated JSON in ignored `backups/`. Old item resources are not proactively deleted. Unsaved browser changes cannot be inspected.

`--update-cover --based-on SNAPSHOT` is a targeted alternative for an approved cover-only change. It verifies that non-cover nodes remain unchanged. Full rebuilds still require reconciliation into the generator.

## Source files

- `scripts/update_handoff_20261106.py`: prepare current English datasets, model classifications, site comparisons and native maps.
- `scripts/compose_current_story.py`: compose the approved six-chapter narrative. `scripts/compose_story.py` is a compatibility entry point.
- `scripts/style_webmaps.py`: style active maps and matching embed basemap assets.
- `scripts/arcgis_maps.py`: import versioned maps, preserve group access and verify saved data.
- `scripts/editorial_policy.py`: chapter, figure, bibliography and layout rules.
- Older preparation scripts and unversioned derived assets are retained for the earlier published model. Do not run them to prepare the current model; use `storymap.py --prepare`.

Publication uploads `published_data.json` as a file. The REST text-upload parameter can sanitize HTML inside JSON and remove reference hyperlinks. The publication adapter verifies both the published item data and the published resource against the intended graph.

The November 8 editorial update follows the final handoff wording in `assets/editorial/20261108.json`, applied by `scripts/editorial_20261108.py` after the base composer. It changes narrative, captions, tables, the date note and Credits only. Analytical thresholds, geography, component styles and embed interfaces remain unchanged. Public prose rounds the main cutoffs to approximately 20% and 31%; calculations retain the exact P60 values.

Native visual enrichment is applied by `scripts/visual_20261108.py`: an introductory large-number infographic before the first Sidecar; one metric per local case in its narrative panel; and a three-event data-provenance timeline. These inherit the Summit theme and do not replace the handoff text, analytical layers or interactive embeds. `publish_audience` controls public publication; map dependencies follow that audience.

All ten Sidecar pages use the same reading order: current-level heading, summary/body paragraphs, then one context-specific native infographic. The standalone Intro infographic remains before its Sidecar. The data-provenance Timeline uses the native `single-side` layout value, verified against a published StoryMaps layout example; `timeline` is not a valid layout name.

Figure numbering follows the full reading order: all 11 native infographics, the evidence timeline and four standalone embedded figures share one continuous sequence. Only the Sidecar main map/media panels and the cover are excluded. Infographic numbers appear in their native descriptions beneath the large metric; the timeline has a separate caption. Captions are generated at build time so later chapter edits cannot introduce duplicate figure numbers.

Infographic presentation now uses native StoryMaps grid groups with 2–4 separately labelled values per figure. Layouts vary by content (Basic, Stacked, Compact and Titled), using the same theme typography and colour tokens. Native grid captions contain only a short Fig title; values and their labels are separate children. Extended standalone figure explanations remain ordinary narrative paragraphs rather than long Fig captions. The grid and layout fields were verified against the official live StoryMaps renderer because SDK 2.4.3 does not expose a grid builder.

The browser viewer suppresses captions on native large-number grids. The adapter therefore renders every Fig caption as a separate native paragraph below its figure, with the same theme font, medium text size and bold short title. This also applies to embedded figures; analytical explanations remain separate narrative paragraphs. Caption normalization runs before draft generation and publication.

The adapter resolves semantic icon aliases to the live StoryMaps icon catalogue (`people`, `governmentBuilding`, `personWalking`, `globe`, `magnifyingGlass`, `flag`, `pinEsri`). Generic Calcite names can silently fall back to a pin; the reader was visually checked before adopting these catalogue IDs.
