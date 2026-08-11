#!/usr/bin/env python3
"""Run the six generator logic paths without Rhino using a small geometry shim.

This is an interface-level feasibility test, not a Rhino certification test.
It verifies required fields, planar footprint construction, stable provenance,
resource classes, and deliberate rejection of missing critical inputs.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from types import SimpleNamespace

from shapely import affinity
from shapely.geometry import LineString, Point as ShapelyPoint, Polygon
from shapely.ops import polygonize, unary_union


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import polis_generator_common as common
import activity_generator
import ecology_generator
import furniture_generator
import hardscape_generator
import hydrology_generator
import vegetation_generator


class GeometryBase:
    pass


class Point3d:
    def __init__(self, x, y, z=0.0):
        self.X = float(x)
        self.Y = float(y)
        self.Z = float(z)


class Point(GeometryBase):
    def __init__(self, location):
        self.Location = location


def xy(point):
    return (point.X, point.Y)


class Curve(GeometryBase):
    def __init__(self, shape):
        self.shape = shape

    @property
    def IsValid(self):
        return self.shape.is_valid and not self.shape.is_empty

    @property
    def IsClosed(self):
        if isinstance(self.shape, Polygon):
            return True
        coordinates = list(self.shape.coords)
        return len(coordinates) > 2 and coordinates[0] == coordinates[-1]

    def IsPlanar(self):
        return True

    @property
    def PointAtStart(self):
        coordinates = list(self.shape.exterior.coords if isinstance(self.shape, Polygon) else self.shape.coords)
        return Point3d(*coordinates[0])

    @property
    def PointAtEnd(self):
        coordinates = list(self.shape.exterior.coords if isinstance(self.shape, Polygon) else self.shape.coords)
        return Point3d(*coordinates[-1])

    def GetLength(self):
        return self.shape.length

    def Offset(self, plane, distance, tolerance, style):
        side = "left" if distance > 0 else "right"
        offset = self.shape.parallel_offset(abs(distance), side, join_style=2)
        return [] if offset.is_empty else [Curve(offset)]

    def Rotate(self, radians, axis, origin):
        self.shape = affinity.rotate(self.shape, math.degrees(radians), origin=xy(origin))
        return True

    def ToNurbsCurve(self):
        return self

    @staticmethod
    def JoinCurves(curves, tolerance):
        pieces = [curve.shape for curve in curves]
        polygons = list(polygonize(unary_union(pieces)))
        return [Curve(polygon) for polygon in polygons]


class LineCurve(Curve):
    def __init__(self, left, right):
        super().__init__(LineString([xy(left), xy(right)]))


class Circle:
    def __init__(self, centre, radius):
        self.centre = centre
        self.radius = radius

    def ToNurbsCurve(self):
        return Curve(ShapelyPoint(xy(self.centre)).buffer(self.radius, resolution=32))


class AreaMassProperties:
    @staticmethod
    def Compute(curve):
        return SimpleNamespace(Area=curve.shape.area)


class Plane:
    WorldXY = object()

    def __init__(self, location, normal):
        self.location = location


class Interval:
    def __init__(self, left, right):
        self.left = float(left)
        self.right = float(right)


class Rectangle3d:
    def __init__(self, plane, x_interval, y_interval):
        x, y = xy(plane.location)
        self.shape = Polygon([
            (x + x_interval.left, y + y_interval.left),
            (x + x_interval.right, y + y_interval.left),
            (x + x_interval.right, y + y_interval.right),
            (x + x_interval.left, y + y_interval.right),
        ])

    def ToNurbsCurve(self):
        return Curve(self.shape)


class Vector3d:
    ZAxis = object()


class CurveOffsetCornerStyle:
    Sharp = object()


FAKE_RG = SimpleNamespace(
    GeometryBase=GeometryBase,
    Point3d=Point3d,
    Point=Point,
    Curve=Curve,
    LineCurve=LineCurve,
    Circle=Circle,
    AreaMassProperties=AreaMassProperties,
    Plane=Plane,
    Interval=Interval,
    Rectangle3d=Rectangle3d,
    Vector3d=Vector3d,
    CurveOffsetCornerStyle=CurveOffsetCornerStyle,
)
FAKE_RHINO = SimpleNamespace(RhinoDoc=SimpleNamespace(ActiveDoc=SimpleNamespace(ModelAbsoluteTolerance=0.001)))
MODULES = (
    vegetation_generator,
    hardscape_generator,
    hydrology_generator,
    furniture_generator,
    activity_generator,
    ecology_generator,
)


def install_shim():
    common.RG = FAKE_RG
    common.Rhino = FAKE_RHINO
    for module in MODULES:
        module.RG = FAKE_RG
    hardscape_generator.Rhino = FAKE_RHINO


CONTEXT = {
    "scenario_id": "SUZ-GE-S",
    "analysis_crs": "EPSG:32651",
    "units": "m",
    "provenance_reference": "scenario:SUZ-GE-S",
    "generator_version": "1.0.0",
}
COMMON = {"source_id": "INT-PREREG", "source_need_ids": ["SUZ-N01"]}


def assert_output(module, record, expected_area_minimum=0.0):
    first = module.generate([record], CONTEXT)[0]
    second = module.generate([record], CONTEXT)[0]
    attributes = first["attributes"]
    assert attributes["design_domain"] == module.DOMAIN
    assert attributes["resource_class"] == module.RESOURCE_CLASS
    assert attributes["object_id"] == second["attributes"]["object_id"]
    assert attributes["source_need_ids"] == "SUZ-N01"
    assert attributes["provenance_reference"].endswith(attributes["object_id"])
    assert first["geometry"].shape.area >= expected_area_minimum


def assert_rejected(module, record, context=CONTEXT):
    try:
        module.generate([record], context)
    except common.GeneratorInputError:
        return
    raise AssertionError("{} unexpectedly accepted an invalid input".format(module.DOMAIN))


def main():
    install_shim()
    assert_output(vegetation_generator, dict(COMMON, geometry=Point3d(2, 2), planting_type="tree", species_status="locally_adapted", canopy_radius_m=2.0, shade_model_eligible=True, height_m=7.0), 12.0)
    assert_output(hardscape_generator, dict(COMMON, geometry=Curve(LineString([(0, 0), (10, 0)])), clear_width_m=2.0, running_slope=0.03, cross_slope=0.01, route_role="primary", accessible_route=True), 19.9)
    assert_output(hydrology_generator, dict(COMMON, geometry=Curve(Polygon([(0, 0), (4, 0), (4, 3), (0, 3)])), design_storage_m3=4.5, hydraulic_type="bioswale", drainage_destination="approved_outfall"), 11.9)
    assert_output(furniture_generator, dict(COMMON, geometry=Point3d(5, 5), footprint_width_m=1.2, footprint_depth_m=0.6, orientation_deg=30.0, furniture_type="bench", clearance_reviewed=True), 0.7)
    assert_output(activity_generator, dict(COMMON, geometry=Curve(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])), use_type="quiet_recreation", accessible_connection_id="ROUTE-01", unobstructed=True), 99.9)
    assert_output(ecology_generator, dict(COMMON, geometry=Curve(Polygon([(0, 0), (15, 0), (15, 14), (0, 14)])), habitat_type="native_meadow", native_or_adapted_fraction=0.8, protected=True), 209.9)

    assert_rejected(vegetation_generator, dict(COMMON, geometry=Point3d(2, 2), planting_type="tree", species_status="locally_adapted", canopy_radius_m=2.0, shade_model_eligible=True))
    assert_rejected(hardscape_generator, dict(COMMON, geometry=Curve(LineString([(0, 0), (10, 0)])), clear_width_m=2.0, cross_slope=0.01, route_role="primary", accessible_route=True))
    assert_rejected(ecology_generator, dict(COMMON, geometry=Curve(Polygon([(0, 0), (4, 0), (4, 4), (0, 4)])), habitat_type="meadow", native_or_adapted_fraction=1.1, protected=True))
    assert_rejected(activity_generator, dict(COMMON, geometry=Curve(Polygon([(0, 0), (4, 0), (4, 4), (0, 4)])), use_type="play", accessible_connection_id="ROUTE-01", unobstructed=True, source_need_ids=[]))
    assert_rejected(furniture_generator, dict(COMMON, geometry=Point3d(5, 5), footprint_width_m=1.2, footprint_depth_m=0.6, orientation_deg=30.0, furniture_type="bench", clearance_reviewed=True), dict(CONTEXT, units="ft"))
    print("RHINO_GENERATOR_SIMULATION_PASS domains=6 negative_cases=5")


if __name__ == "__main__":
    main()

