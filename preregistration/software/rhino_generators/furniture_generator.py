"""POLIS furniture generator for explicit points, dimensions, and orientation."""

from __future__ import print_function

import math

from polis_generator_common import GeneratorInputError, RG, base_record, number, point, require, run_records


DOMAIN = "furniture"
RESOURCE_CLASS = "furniture"


def _rectangle(location, width, depth, orientation_deg):
    if RG is None:
        raise GeneratorInputError("RhinoCommon is required")
    plane = RG.Plane(location, RG.Vector3d.ZAxis)
    rectangle = RG.Rectangle3d(
        plane, RG.Interval(-width / 2.0, width / 2.0), RG.Interval(-depth / 2.0, depth / 2.0)
    ).ToNurbsCurve()
    if not rectangle.Rotate(math.radians(orientation_deg), RG.Vector3d.ZAxis, location):
        raise GeneratorInputError("furniture footprint rotation failed")
    return rectangle


def _build(record, index, context, domain, resource_class):
    label = "furniture[{}]".format(index)
    location = point(record, label)
    width = number(record, "footprint_width_m", label, minimum=0.01)
    depth = number(record, "footprint_depth_m", label, minimum=0.01)
    orientation = number(record, "orientation_deg", label, minimum=0.0, maximum=360.0)
    furniture_type = str(require(record, "furniture_type", label))
    clearance_reviewed = record.get("clearance_reviewed")
    if not isinstance(clearance_reviewed, bool):
        raise GeneratorInputError("{}: clearance_reviewed must be true or false".format(label))
    return base_record(context, record, index, domain, resource_class, _rectangle(location, width, depth, orientation), {
        "geometry_kind": "furniture_footprint",
        "furniture_type": furniture_type,
        "footprint_width_m": width,
        "footprint_depth_m": depth,
        "orientation_deg": orientation,
        "clearance_reviewed": str(clearance_reviewed).lower(),
    })


def generate(records, context):
    return run_records(records, context, DOMAIN, RESOURCE_CLASS, _build)

