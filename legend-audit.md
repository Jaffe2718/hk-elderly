# Legend audit — current implementation

12 native Web Map assets checked; original feature attributes and geometry remain unchanged.

## M01_population
- Residents aged 60+ (%): 0–25%; >25–50%; >50–75%; >75–100%.
- Residents aged 60+ (2021): 0–5,000; 5,001–15,000; 15,001–30,000; 30,001–60,000; >60,000.
- NEC premises: single facility symbol.
## M02_coverage
- Residential land beyond NEC 800 m (%): 0–25%; >25–50%; >50–75%; >75–100%.
- NEC premises: single facility symbol.
## M03_binary800
- Older population and residential proximity: High population + weak coverage; High population + stronger coverage; Lower population + weak coverage; Lower population + stronger coverage; Not assessed.
- Priority screen · 800 m: Selected for review; Not selected; Not assessed.
- NEC premises: single facility symbol.
## M04_binary500
- Priority screen · 500 m: Selected for review; Not selected; Not assessed.
- NEC premises: single facility symbol.
## M05_binary1000
- Priority screen · 1,000 m: Selected for review; Not selected; Not assessed.
- NEC premises: single facility symbol.
## M06_sensitivity27
- Selections across 27 scenarios: 0; 1–3; 4–9; 10–18; 19–27.
- NEC premises: single facility symbol.
## M07_age_definition
- Priority screen · age 75+ · 800 m: Selected for review; Not selected; Not assessed.
- Priority screen · age 65+ · 800 m: Selected for review; Not selected; Not assessed.
- Priority screen · 800 m: Selected for review; Not selected; Not assessed.
- NEC premises: single facility symbol.
## M08_choices
- Residential land within 800 m of 2+ NECs (%): 0–25%; >25–50%; >50–75%; >75–100%.
- NEC premises: single facility symbol.
## M09_centroid_comparison
- Residential vs centroid screening: Same result; Different result; Not assessed.
- NEC premises: single facility symbol.
## M10_facility_definition
- Coverage gain from adding DECC (pp): 0–5 pp; >5–15 pp; >15–30 pp; >30 pp.
- Residential land beyond NEC 800 m (%): 0–25%; >25–50%; >50–75%; >75–100%.
- Residential land beyond NEC + DECC 800 m (%): 0–25%; >25–50%; >50–75%; >75–100%.
- NEC premises: single facility symbol.
- DECC premises: single facility symbol.
- Elderly centre premises: NEC premises; DECC premises.
## M11_residential_nec
- Residential land coverage / NEC only: Within 800 m; Beyond 800 m.
- NEC premises: single facility symbol.
## M12_residential_combined
- Residential land coverage / NEC and DECC: Within 800 m; Beyond 800 m.
- NEC premises: single facility symbol.
- DECC premises: single facility symbol.
- Elderly centre premises: NEC premises; DECC premises.

## Display rules
- NEC: deep-green diamond (#145341). DECC: deep-orange triangle (#b75d22).
- Combined facility views use a derived point layer with two categories. Original source layers remain intact; they are hidden only when the combined layer is displayed. This removes the layer separator between NEC and DECC.
- Percentage and percentage-point indicators retain explicit units; residential coverage refers to ground area, not people served.
- Not assessed is a separate grey category. Redundant unused fallback classes and repeated renderer subtitles are omitted.
- HTML map keys use trapezoid area swatches and have no separators.
- Comparison embeds an ArcGIS Maps SDK Swipe; both small legends are fixed inside opposite map corners, independent of pan/zoom and slider movement.
- No external comparison legend image is inserted.
- Separators between different geometry layers in native StoryMap legends remain platform-controlled.
