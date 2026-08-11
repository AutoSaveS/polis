"""POLIS activity-zone generator for supplied usable-space polygons."""

from __future__ import print_function

from polis_generator_common import area, base_record, closed_curve, require, run_records


DOMAIN = "activity"
RESOURCE_CLASS = "activity"


def _build(record, index, context, domain, resource_class):
    label = "activity[{}]".format(index)
    output_geometry = closed_curve(record, label)
    use_type = str(require(record, "use_type", label))
    accessible_connection_id = str(require(record, "accessible_connection_id", label))
    unobstructed = record.get("unobstructed")
    if not isinstance(unobstructed, bool):
        raise ValueError("{}: unobstructed must be true or false".format(label))
    return base_record(context, record, index, domain, resource_class, output_geometry, {
        "geometry_kind": "activity_zone",
        "use_type": use_type,
        "accessible_connection_id": accessible_connection_id,
        "unobstructed": str(unobstructed).lower(),
        "usable_area_m2": area(output_geometry, label),
    })


def generate(records, context):
    return run_records(records, context, DOMAIN, RESOURCE_CLASS, _build)

