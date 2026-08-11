"""POLIS hardscape and accessible-route generator for Rhino 8/GhPython.

Each source record contains a route centreline, explicit clear width and slope
values.  The supplied values are preserved for the evaluator; this generator
does not silently repair a non-compliant route.
"""

from __future__ import print_function

from polis_generator_common import (
    GeneratorInputError, RG, Rhino, base_record, curve, number, require, run_records,
)


DOMAIN = "hardscape"
RESOURCE_CLASS = "hardscape"


def _route_footprint(centerline, width, label):
    if RG is None:
        raise GeneratorInputError("RhinoCommon is required")
    tolerance = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance if Rhino and Rhino.RhinoDoc.ActiveDoc else 0.001
    half_width = width / 2.0
    positive = centerline.Offset(RG.Plane.WorldXY, half_width, tolerance, RG.CurveOffsetCornerStyle.Sharp)
    negative = centerline.Offset(RG.Plane.WorldXY, -half_width, tolerance, RG.CurveOffsetCornerStyle.Sharp)
    if not positive or not negative:
        raise GeneratorInputError("{}: centreline could not be offset into a footprint".format(label))
    left = positive[0]
    right = negative[0]
    connectors = [
        RG.LineCurve(left.PointAtStart, right.PointAtStart),
        RG.LineCurve(left.PointAtEnd, right.PointAtEnd),
    ]
    joined = RG.Curve.JoinCurves([left, connectors[1], right, connectors[0]], tolerance)
    closed = [candidate for candidate in joined if candidate.IsClosed]
    if len(closed) != 1:
        raise GeneratorInputError("{}: route footprint could not be closed".format(label))
    return closed[0]


def _build(record, index, context, domain, resource_class):
    label = "hardscape[{}]".format(index)
    centerline = curve(record, label)
    clear_width = number(record, "clear_width_m", label, minimum=0.01)
    running_slope = number(record, "running_slope", label, minimum=0.0)
    cross_slope = number(record, "cross_slope", label, minimum=0.0)
    route_role = str(require(record, "route_role", label))
    accessible_route = record.get("accessible_route")
    if not isinstance(accessible_route, bool):
        raise GeneratorInputError("{}: accessible_route must be true or false".format(label))
    footprint = _route_footprint(centerline, clear_width, label)
    return base_record(context, record, index, domain, resource_class, footprint, {
        "geometry_kind": "route_footprint",
        "route_role": route_role,
        "accessible_route": str(accessible_route).lower(),
        "clear_width_m": clear_width,
        "running_slope": running_slope,
        "cross_slope": cross_slope,
        "source_centerline_length_m": float(centerline.GetLength()),
    })


def generate(records, context):
    return run_records(records, context, DOMAIN, RESOURCE_CLASS, _build)
