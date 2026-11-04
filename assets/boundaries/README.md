# Study area boundary

Generated locally with ArcPy by `scripts/prepare_study_area.py` from the 18 district display polygons embedded in `assets/webmaps/M01_population.json`.

- `hk-study-area-outline.geojson`: one multipart line feature containing only exterior rings. District boundaries and interior hole rings are excluded; all island exteriors are retained. Use this layer for a map outline.
- `hk-study-area-land.geojson`: dissolved multipart land polygon, retaining interior holes. Use this for land fill or masking, with polygon outlines disabled when drawing the exterior-line layer above it.
- `provenance.json`: source hash, ArcGIS Pro version, transformation, geometry repair, area checks and processing results.

Processing projects the source to Hong Kong 1980 Grid (EPSG:2326), repairs the detected self-intersection in a local working copy, dissolves all districts, extracts exterior rings and explicitly projects back to WGS84 with the same datum transformation before GeoJSON serialization. Automatic GeoJSON projection omitted the required datum shift in an earlier local output; the corrected exporter requires a sampled round-trip error below 2 cm. The repair did not change measured area. The dissolved polygon matches an independent sequential geometry union exactly. Source polygon overlaps account for the small difference between summed district areas and union area.

The working geodatabase and a diagnostic PNG preview are under ignored `build/geoprocessing/`. Original handoff files and online ArcGIS items are not modified. These derivatives describe the land extent of supplied display geometries, not a maritime administrative boundary or a replacement for original high-resolution boundary data.

Run with the ArcGIS Pro Python environment:

```powershell
& 'D:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat' scripts/prepare_study_area.py
```
