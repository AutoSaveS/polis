"""POLIS hydrology generator for explicitly supplied drainage geometry."""

from __future__ import print_function

from polis_generator_common import area, base_record, closed_curve, number, require, run_records


DOMAIN = "hydrology"
RESOURCE_CLASS = "hydrology"


def _build(record, index, context, domain, resource_class):
    label = "hydrology[{}]".format(index)
    output_geometry = closed_curve(record, label)
    storage = number(record, "design_storage_m3", label, minimum=0.0)
    hydraulic_type = str(require(record, "hydraulic_type", label))
    drainage_destination = str(require(record, "drainage_destination", label))
    return base_record(context, record, index, domain, resource_class, output_geometry, {
        "geometry_kind": "hydrology_zone",
        "hydraulic_type": hydraulic_type,
        "design_storage_m3": storage,
        "drainage_destination": drainage_destination,
        "footprint_area_m2": area(output_geometry, label),
    })


def generate(records, context):
    return run_records(records, context, DOMAIN, RESOURCE_CLASS, _build)

