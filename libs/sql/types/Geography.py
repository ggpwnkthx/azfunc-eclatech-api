from sqlalchemy import func
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.schema import Column
from sqlalchemy.types import UserDefinedType, TypeEngine

from ...utils.geometry import wkt2geojson, geojson2wkt


class Geography(UserDefinedType):
    cache_ok = True
    
    __visit_name__ = "geography"

    def __init__(self, srid: int = 4326):
        self.srid = srid

    def get_col_spec(self):
        return "GEOGRAPHY"

    def bind_expression(self, bindvalue):
        # not able to use func here since "::" in function name
        exp = f"geography::STGeomFromText(:{bindvalue.key}, {self.srid})"
        f = text(exp)
        return f.bindparams(bindvalue)

    def column_expression(self, col: Column):
        # not able to use func here since function needs to be applied as method to the column itself
        # col.func() not func(col)
        exp = f"{col.key}.STAsText()"
        f1 = text(exp)
        f2 = func.IIF(col == None, None, f1, type_=self)
        return f2

    def bind_processor(self, dialect):
        def process(value):
            return geojson2wkt(value) if value else value

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return wkt2geojson(value) if value else value

        return process

    class comparator_factory(TypeEngine.Comparator):
        def __add__(self, other):
            return self.op("goofy")(other)

        def intersects_bounds(self, lon_min, lon_max, lat_min, lat_max):
            p = f'POLYGON (({lon_min} {lat_min}, {lon_max} {lat_min}, {lon_max} {lat_max}, {lon_min} {lat_max}, {lon_min} {lat_min}))'
            exp = f"geography::STGeomFromText('{p}', {self.type.srid}).STIntersects({self.expr.name}) = 1"
            f = text(exp)
            return f