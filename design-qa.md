# Design QA — 5 November 2026

## Scope
Local embedded components and generated StoryMap configuration. Authenticated StoryMaps rendering is verified through draft readback; the local cover framing study is an approximation, not a screenshot of the native reader.

## Verified
- Coverage explorer: real Esri Light Gray Base raster tiles loaded through the browser, visually inspected after provider validation. No API-key placeholder tiles are retained. Subtle cool tint, pale-purple area ramp, dark-green facilities and dark-red exterior boundary.
- Explorer controls reduced to 210 px; native narrative panels configured as small to avoid the oversized double-sidebar layout.
- Distances retain 11 / 4 / 2 selections; alternative age and facility scenarios and case popups pass regression checks.
- Linked comparison: 315 residential patches per panel; distinct scope fields (202 versus 74 patches beyond reach), four cases, synchronized centres/scales, fixed opposite-corner legends, responsive layout.
- Charts: 25 chart/frame combinations checked, including both sensitivity matrices, pagination, scope-specific tabs and coloured hover glow.
- Workflow: obstruction hint removed; previously validated outgoing flow geometry retained.
- Native map legends enabled; six numbered navigation chapters; Credit excluded; seven bracket-numbered APA references; four figure captions.
- Selected Tuen Mun care-home entrance cover retained, with original source, photographer and licence metadata. Native cover accepts a single photo.
- Latest inspected online narrative matches the previous generated narrative; no manual text changes found before rebuild.

## Evidence
Ignored local build screenshots include map-desktop.png, map-mobile.png, comparison-desktop.png, comparison-mobile.png, workflow-desktop.png and cover-framing-desktop.png. Browser checks report no script errors. The cover framing image explicitly identifies itself as an approximation.

## Workflow controls follow-up
- Initial state has no active node.
- Browser test confirms Pause freezes CSS animation time and walkthrough selection; Resume advances again.
- Fit clears selection, search, timer and transforms; mobile reset also verified.
- SVG export UI and its download handler removed. No SVG export remains in embedded components.

## In-map comparison revision
Browser checks pass for an ArcGIS Maps SDK 4.33 Swipe, 315 features per scenario, stable in-map legend rectangles after pan/swipe, and non-overlapping mobile legend cards. Desktop and mobile screenshots are saved under build/native-swipe-*.png. The StoryMap-native layer legend separators remain unsupported for direct styling.
