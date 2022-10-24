from typing import Union

import geojson
import shapely.wkt
from shapely.geometry import shape, GeometryCollection, Point, MultiPoint, \
    LineString, MultiLineString, Polygon, MultiPolygon

GeoJsonType: type = Union[geojson.Feature, geojson.FeatureCollection]
WktType: type = Union[GeometryCollection, Point, MultiPoint,
                      LineString, MultiLineString, Polygon, MultiPolygon]


def wkt2geojson(wkt: str) -> GeoJsonType:
    wkt = shapely.wkt.loads(wkt)
    wkt = validate_wkt(wkt)
    if type(wkt) == GeometryCollection:
        features = [geojson.Feature(geometry=o, properties={})
                    for o in wkt.geoms]
        feature_collection = geojson.FeatureCollection(features)
        return feature_collection
    else:
        feature = geojson.Feature(geometry=wkt, properties={})
        return feature


def geojson2wkt(data: Union[GeoJsonType, dict]) -> WktType:
    data = validate_geojson(data)
    if data.get("type") == "Feature":
        g = shape(data.get("geometry"))
        return g.wkt
    elif data.get("type") == "FeatureCollection":
        g = [shape(f.get("geometry")) for f in data.get("features")]
        gc = GeometryCollection(g)
        return gc.wkt
    else:
        raise Exception


def validate_geojson(data: Union[GeoJsonType, dict]) -> GeoJsonType:
    data = geojson.loads(geojson.dumps(data))
    if not data.is_valid:
        raise ValueError("value is not a valid GeoJson")
    return data


def validate_wkt(data: WktType) -> WktType:
    if not data.is_valid:
        raise ValueError("value is not a valid WKT")
    return data
