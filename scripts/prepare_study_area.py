"""Use ArcPy to dissolve the supplied district polygons into a study outline.

Run with ArcGIS Pro's propy.bat. No online items are read or modified.
The supplied Web Map contains display geometries, not original survey data.
"""
import hashlib
import json
from pathlib import Path

import arcpy

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build/geoprocessing'
OUTPUT = ROOT / 'assets/boundaries'


def run():
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    arcpy.env.overwriteOutput = True
    source = ROOT / 'assets/webmaps/M01_population.json'
    webmap = json.loads(source.read_text(encoding='utf-8'))
    layer = next(l for l in webmap['operationalLayers'] if l['id'] == 'district_context')['featureCollection']['layers'][0]
    feature_set = dict(layer['featureSet'])
    feature_set['fields'] = layer['layerDefinition']['fields']
    source_json = WORK / 'source_districts.json'
    source_json.write_text(json.dumps(feature_set), encoding='utf-8')
    gdb = WORK / 'study_area.gdb'
    if not arcpy.Exists(str(gdb)):
        arcpy.management.CreateFileGDB(str(WORK), gdb.name)
    districts = str(gdb / 'districts_wgs84')
    projected = str(gdb / 'districts_hk1980')
    dissolved = str(gdb / 'study_area_land')
    outline = str(gdb / 'study_area_outline')
    arcpy.conversion.JSONToFeatures(str(source_json), districts, 'POLYGON')
    count = int(arcpy.management.GetCount(districts)[0])
    if count != 18:
        raise RuntimeError(f'Expected 18 supplied districts, received {count}')
    hk = arcpy.SpatialReference(2326)
    transformations = arcpy.ListTransformations(arcpy.SpatialReference(4326), hk)
    if not transformations:
        raise RuntimeError('No WGS84 / Hong Kong 1980 transformation available')
    transformation = transformations[0]
    arcpy.management.Project(districts, projected, hk, transformation)
    check = str(gdb / 'geometry_checks')
    arcpy.management.CheckGeometry(projected, check)
    errors = int(arcpy.management.GetCount(check)[0])
    input_issues = list(arcpy.da.SearchCursor(check, ['FEATURE_ID', 'PROBLEM']))
    area_before_repair = sum(row[0] for row in arcpy.da.SearchCursor(projected, ['SHAPE@AREA']))
    if errors:
        if any(problem != 'self intersections' for _, problem in input_issues):
            raise RuntimeError(f'Review unsupported geometry issues: {input_issues}')
        arcpy.management.RepairGeometry(projected, delete_null='KEEP_NULL', validation_method='ESRI')
        arcpy.management.CheckGeometry(projected, check)
        if int(arcpy.management.GetCount(check)[0]) or int(arcpy.management.GetCount(projected)[0]) != count:
            raise RuntimeError('Geometry repair failed or removed a source feature')
    area_after_repair = sum(row[0] for row in arcpy.da.SearchCursor(projected, ['SHAPE@AREA']))
    arcpy.management.Dissolve(projected, dissolved, multi_part='MULTI_PART')
    arcpy.management.CheckGeometry(dissolved, check)
    if int(arcpy.management.GetCount(check)[0]):
        raise RuntimeError('Invalid dissolved polygon')
    union = next(arcpy.da.SearchCursor(dissolved, ['SHAPE@']))[0]
    # Each multipart polygon part starts with its exterior ring; None separates
    # interior rings. Retain every island exterior and omit all hole outlines.
    rings = arcpy.Array()
    holes = 0
    for part in union:
        ring = arcpy.Array()
        in_hole = False
        for point in part:
            if point is None:
                holes += 1
                in_hole = True
            elif not in_hole:
                ring.add(point)
        if ring.count >= 4:
            rings.add(ring)
    boundary = arcpy.Polyline(rings, hk)
    arcpy.management.CopyFeatures([boundary], outline)
    arcpy.management.CheckGeometry(outline, check)
    if int(arcpy.management.GetCount(check)[0]):
        raise RuntimeError('Invalid outline geometry')
    input_area = 0.0
    input_perimeter = 0.0
    expected_union = None
    with arcpy.da.SearchCursor(projected, ['SHAPE@']) as rows:
        for (geometry,) in rows:
            input_area += geometry.area
            input_perimeter += geometry.length
            expected_union = geometry if expected_union is None else expected_union.union(geometry)
    relative_area_difference = abs(union.area - input_area) / input_area
    symmetric_difference = union.symmetricDifference(expected_union).area
    if symmetric_difference / union.area > 1e-6:
        raise RuntimeError('Dissolve differs from an independent geometry union')
    if boundary.length >= input_perimeter:
        raise RuntimeError('Internal boundaries were not removed')
    for dataset, name in [(dissolved, 'hk-study-area-land.geojson'), (outline, 'hk-study-area-outline.geojson')]:
        # FeaturesToJSON's automatic WGS84 projection can omit the datum
        # transformation. Explicitly reverse the same transformation first.
        wgs_dataset=dataset+'_wgs84'
        arcpy.management.Project(dataset,wgs_dataset,arcpy.SpatialReference(4326),transformation)
        arcpy.conversion.FeaturesToJSON(wgs_dataset, str(OUTPUT / name), geoJSON='GEOJSON', outputToWGS84='KEEP_INPUT_SR')
        data = json.loads((OUTPUT / name).read_text(encoding='utf-8'))
        for feature in data['features']:
            feature['properties'] = {'name': 'Hong Kong study area', 'source': 'Supplied 2021 district display geometries', 'geometry_role': 'land extent' if dataset == dissolved else 'exterior outline'}
        (OUTPUT / name).write_text(json.dumps(data, ensure_ascii=False) + '\n', encoding='utf-8')
    exported=json.loads((OUTPUT/'hk-study-area-outline.geojson').read_text(encoding='utf-8'))
    back=arcpy.AsShape(exported['features'][0]['geometry'],False).projectAs(hk,transformation)
    points=[point for part in back for point in part if point is not None]
    stride=max(1,len(points)//1000)
    roundtrip=max(arcpy.PointGeometry(point,hk).distanceTo(boundary) for point in points[::stride])
    if roundtrip>.02:
        raise RuntimeError(f'Export datum transformation failed: {roundtrip:.4f} m round-trip error')
    report = {
        'source': 'assets/webmaps/M01_population.json / district_context',
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'input_districts': count, 'processing_crs': 'EPSG:2326',
        'input_geometry_issues_repaired': [{'feature_id': fid, 'problem': problem} for fid, problem in input_issues],
        'repair_area_change_m2': area_after_repair - area_before_repair,
        'geographic_transformation': transformation,
        'output_crs': 'EPSG:4326', 'arcpy_version': arcpy.GetInstallInfo()['Version'],
        'dissolved_features': int(arcpy.management.GetCount(dissolved)[0]),
        'exterior_rings_retained': rings.count, 'hole_rings_excluded_from_outline': holes,
        'land_area_km2': union.area / 1e6,
        'relative_sum_area_difference_due_to_overlaps': relative_area_difference,
        'source_overlap_area_m2': input_area - union.area,
        'independent_union_symmetric_difference_m2': symmetric_difference,
        'sampled_export_roundtrip_max_offset_m': roundtrip,
        'export_projection': 'Explicit Project to WGS84 with the same datum transformation before GeoJSON serialization',
        'sum_input_perimeters_km': input_perimeter / 1000,
        'exterior_outline_length_km': boundary.length / 1000,
        'geometry_checks': 'passed',
        'scope': 'Land extent from supplied display polygons; not a maritime administrative boundary. All island exteriors retained. Internal district lines and hole boundaries omitted from the line asset.'
    }
    (OUTPUT / 'provenance.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)
    preview(boundary)


def preview(boundary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
    ax.set_facecolor('#e4f2f8')
    for part in boundary:
        points = [p for p in part if p]
        ax.plot([p.X for p in points], [p.Y for p in points], color='#234f59', linewidth=.8)
    ax.set_aspect('equal')
    ax.set_title('Hong Kong study area | Exterior outline', loc='left', fontsize=16, pad=16)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    fig.text(.125, .04, '18 supplied district polygons dissolved with ArcPy. Islands retained; internal boundaries removed.', fontsize=9, color='#405c65')
    fig.savefig(WORK / 'study-area-outline-preview.png', bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    run()
