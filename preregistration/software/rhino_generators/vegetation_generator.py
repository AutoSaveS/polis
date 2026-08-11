"""POLIS vegetation generator for a Rhino 8 Python 3 or GhPython component.

Grasshopper inputs: ``records`` (list of dictionaries) and ``context`` (dict).
Output: ``generate(records, context)`` returns geometry/attribute records.
Point inputs require an explicit canopy radius.  Height is required only when a
record is deliberately marked as shade-model eligible; this script never
guesses height or emits shade footprints.
"""

from __future__ import print_function

from polis_generator_common import (
    GeneratorInputError, RG, area, base_record, closed_curve, number, point,
    require, run_records,
)


DOMAIN = "vegetation"
RESOURCE_CLASS = "vegetation"


def _build(record, index, context, domain, resource_class):
    label = "vegetation[{}]".format(index)
    planting_type = str(require(record, "planting_type", label))
    species_status = str(require(record, "species_status", label))
    shade_eligible = bool(record.get("shade_model_eligible", False))
    raw = record.get("geometry")
    if RG is None:
        raise GeneratorInputError("RhinoCommon is required")
    if isinstance(raw, (RG.Point, RG.Point3d)):
        radius = number(record, "canopy_radius_m", label, minimum=0.01)
        output_geometry = RG.Circle(point(record, label), radius).ToNurbsCurve()
        geometry_kind = "tree_canopy_circle"
    else:
        output_geometry = closed_curve(record, label)
        area(output_geometry, label)
        geometry_kind = "planting_zone"
    attributes = {
        "planting_type": planting_type,
        "species_status": species_status,
        "geometry_kind": geometry_kind,
        "shade_model_eligible": str(shade_eligible).lower(),
    }
    if shade_eligible:
        attributes["height_m"] = number(record, "height_m", label, minimum=0.01)
        attributes["canopy_radius_m"] = number(record, "canopy_radius_m", label, minimum=0.01)
        attributes["shade_input_status"] = "explicit_height_and_crown"
    else:
        attributes["shade_input_status"] = "not_requested"
    return base_record(context, record, index, domain, resource_class, output_geometry, attributes)


def generate(records, context):
    return run_records(records, context, DOMAIN, RESOURCE_CLASS, _build)
