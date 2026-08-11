"""POLIS ecology generator for explicit habitat and protection-zone polygons."""

from __future__ import print_function

from polis_generator_common import area, base_record, closed_curve, number, require, run_records


DOMAIN = "ecology"
RESOURCE_CLASS = "ecology"


def _build(record, index, context, domain, resource_class):
    label = "ecology[{}]".format(index)
    output_geometry = closed_curve(record, label)
    habitat_type = str(require(record, "habitat_type", label))
    native_fraction = number(record, "native_or_adapted_fraction", label, minimum=0.0, maximum=1.0)
    protected = record.get("protected")
    if not isinstance(protected, bool):
        raise ValueError("{}: protected must be true or false".format(label))
    return base_record(context, record, index, domain, resource_class, output_geometry, {
        "geometry_kind": "ecological_zone",
        "habitat_type": habitat_type,
        "native_or_adapted_fraction": native_fraction,
        "protected": str(protected).lower(),
        "zone_area_m2": area(output_geometry, label),
    })


def generate(records, context):
    return run_records(records, context, DOMAIN, RESOURCE_CLASS, _build)

