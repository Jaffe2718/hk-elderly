# Legend audit (local only)

- Audit checks renderer fields, declared classes, observed values, missing-data keys and source-geometry preservation.

## M01_population
- age_share (`elderly_pct`): 0–25%; >25–50%; >50–75%; >75–100%.
- population60 (`elderly_n`): 0–5,000; 5,001–15,000; 15,001–30,000; 30,001–60,000; >60,000.
## M02_coverage
- coverage (`nec_out800_pct`): 0–25%; >25–50%; >50–75%; >75–100%.
## M03_binary800
- typology (`demand_coverage_class`): High population + weak coverage; High population + stronger coverage; Lower population + weak coverage; Lower population + stronger coverage; Not assessed.
- main (`priority_main`): Meets both conditions; Does not meet both; Not assessed.
## M04_binary500
- r500 (`priority_500`): Meets both conditions; Does not meet both; Not assessed.
## M05_binary1000
- r1000 (`priority_1000`): Meets both conditions; Does not meet both; Not assessed.
## M06_sensitivity27
- scenario (`sensitivity_hits27`): 0; 1–3; 4–9; 10–18; 19–27.
## M07_age_definition
- a75 (`priority_age75`): Meets both conditions; Does not meet both; Not assessed.
- a65 (`priority_age65`): Meets both conditions; Does not meet both; Not assessed.
- a60 (`priority_main`): Meets both conditions; Does not meet both; Not assessed.
## M08_choices
- choice (`nec2plus_pct800`): 0–25%; >25–50%; >50–75%; >75–100%.
## M09_centroid_comparison
- centroid (`centroid_disagree`): Same classification; Different classification; Not assessed.
## M10_facility_definition
- gain (`nec_decc_gain_pp`): 0–5 pp; >5–15 pp; >15–30 pp; >30 pp.
- neconly (`nec_out800_pct`): 0–25%; >25–50%; >50–75%; >75–100%.
- any (`any_out800_pct`): 0–25%; >25–50%; >50–75%; >75–100%.
## M11_residential_nec
- residential (`outside_nec800`): Within 800 m; Beyond 800 m.
## M12_residential_combined
- residential (`outside_any800`): Within 800 m; Beyond 800 m.

## HTML legends
- Percentage classes aligned with native maps: 0–25%, >25–50%, >50–75%, >75–100%; boundary 25 remains in the first class.
- Scenario frequency aligned with native map: 0, 1–3, 4–9, 10–18, 19–27.
- Residential gaps uses the outside-distance field directly; no within/beyond inversion.
- Priority 1 uses the emphasis colour, 0 a pale neutral, and not-assessed a separate grey.
- Housing charts retain explicit NEC-only versus NEC + DECC series; matrix 1/0 labels are categorical, not percentages.

## Pending native layout limitation
- Native Floating legend horizontal placement has not been verified. The introductory text/legend overlap is still pending; no unsupported positioning property was added.
- Other flagged map views receive a 6% westward camera shift (rightward subject framing), without changing scale or geometry.

## Subsequent review corrections
- Facilities overview now uses only NEC and DECC locations, with no residential-patch layer or residential legend. Source patch counts are 113 within / 202 beyond for NEC only, and 241 within / 74 beyond for the combined scope; these local-case geometries are retained in the Swipe comparison.
- Population symbols and age-share fills use muted lavender after the warm-palette review.
- Comparison uses distinct muted lavender and grey-apricot colours; native internal Swipe legends are disabled to prevent the two overlays colliding. A compact paired key sits immediately below the native Swipe.
