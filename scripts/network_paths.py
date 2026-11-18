"""Export local display geometry from the official enabled pedestrian network."""
import json
from pathlib import Path


def export_network(arcpy, gdb, extent, destination):
    sr = arcpy.SpatialReference(4326)
    x0, y0, x1, y1 = extent
    bounds = arcpy.Polygon(arcpy.Array([arcpy.Point(x, y) for x, y in
        [(x0,y0),(x0,y1),(x1,y1),(x1,y0),(x0,y0)]]), sr)
    routes = str(Path(gdb) / "PedestrianRoute")
    source_bounds = bounds.projectAs(arcpy.Describe(routes).spatialReference)
    features = []
    with arcpy.da.SearchCursor(routes, ["SHAPE@", "PedestrianRouteID", "StreetNameEN"],
                               where_clause="Enabled = 1", spatial_filter=source_bounds,
                               spatial_relationship="INTERSECTS") as cursor:
        for shape, route_id, street in cursor:
            clipped = shape.intersect(source_bounds, 2)
            if not clipped.pointCount:
                continue
            geom = clipped.projectAs(sr)
            lines = [[[round(p.X, 6), round(p.Y, 6)] for p in part if p] for part in geom]
            lines = [line for line in lines if len(line) >= 2]
            if lines:
                features.append({"type": "Feature", "geometry": {"type": "MultiLineString", "coordinates": lines},
                                 "properties": {"route_id": str(route_id), "street": street or ""}})
    if not features:
        raise RuntimeError("No enabled pedestrian links in map extent")
    destination.write_text(json.dumps({"type": "FeatureCollection", "features": features},
                                       separators=(",", ":")), encoding="utf-8")
    print(f"{destination.stem}: {len(features)} enabled links", flush=True)
