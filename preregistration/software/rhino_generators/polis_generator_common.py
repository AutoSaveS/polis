"""Shared Rhino 8/GhPython helpers for the six POLIS design generators.

The functions in this module are deliberately conservative.  They require all
geometry and numerical design inputs that affect a result; they never infer
building/tree heights, legal applicability, budgets, or resident preferences.
The returned records are the attribute contract used when exporting the
``design_objects`` GeoPackage layer.
"""

from __future__ import print_function

import hashlib
import json
import math


try:
    import Rhino
    import Rhino.Geometry as RG
except ImportError:  # Allows syntax/contract checks on the analysis machine.
    Rhino = None
    RG = None


class GeneratorInputError(ValueError):
    pass


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def require(mapping, key, label="record"):
    if not isinstance(mapping, dict) or key not in mapping:
        raise GeneratorInputError("{}: missing required field '{}'".format(label, key))
    value = mapping[key]
    if value is None or (isinstance(value, str) and not value.strip()):
        raise GeneratorInputError("{}: required field '{}' is blank".format(label, key))
    return value


def number(mapping, key, label="record", minimum=None, maximum=None):
    value = require(mapping, key, label)
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise GeneratorInputError("{}: '{}' must be numeric".format(label, key))
    if not math.isfinite(value):
        raise GeneratorInputError("{}: '{}' must be finite".format(label, key))
    if minimum is not None and value < minimum:
        raise GeneratorInputError("{}: '{}' must be >= {}".format(label, key, minimum))
    if maximum is not None and value > maximum:
        raise GeneratorInputError("{}: '{}' must be <= {}".format(label, key, maximum))
    return value


def context_check(context, domain):
    if not isinstance(context, dict):
        raise GeneratorInputError("context must be a dictionary")
    for key in ("scenario_id", "analysis_crs", "provenance_reference"):
        require(context, key, "context")
    if context.get("units", "m") != "m":
        raise GeneratorInputError("context.units must be 'm'; convert geometry before running")
    allowed = ("vegetation", "hardscape", "hydrology", "furniture", "activity", "ecology")
    if domain not in allowed:
        raise GeneratorInputError("unknown design domain: {}".format(domain))


def stable_object_id(context, record, index, domain):
    payload = {
        "scenario_id": _text(context["scenario_id"]),
        "domain": domain,
        "source_id": _text(record.get("source_id")),
        "index": int(index),
    }
    return "{}-{}".format(domain, hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16])


def provenance(context, record, domain, object_id):
    need_ids = record.get("source_need_ids", record.get("need_ids", []))
    if not isinstance(need_ids, (list, tuple)) or not need_ids or any(not _text(item) for item in need_ids):
        raise GeneratorInputError("{}: source_need_ids must contain at least one need ID".format(object_id))
    source_ref = _text(record.get("source_id"))
    if not source_ref:
        raise GeneratorInputError("{}: source_id is required".format(object_id))
    return "{}|{}|{}|{}".format(
        _text(context["provenance_reference"]), source_ref, ",".join(sorted(set(map(_text, need_ids)))), object_id
    )


def geometry(record, label):
    value = require(record, "geometry", label)
    if RG is None:
        raise GeneratorInputError("RhinoCommon is required to construct geometry")
    if not isinstance(value, RG.GeometryBase):
        raise GeneratorInputError("{}: geometry must be a RhinoCommon geometry object".format(label))
    if value.IsValid is False:
        raise GeneratorInputError("{}: geometry is invalid".format(label))
    return value


def point(record, label):
    value = require(record, "geometry", label)
    if RG is None:
        raise GeneratorInputError("RhinoCommon is required to construct geometry")
    if isinstance(value, RG.Point3d):
        return value
    if isinstance(value, RG.Point):
        return value.Location
    raise GeneratorInputError("{}: geometry must be a Rhino point".format(label))


def closed_curve(record, label):
    value = geometry(record, label)
    curve = value if isinstance(value, RG.Curve) else None
    if curve is None or not curve.IsClosed:
        raise GeneratorInputError("{}: geometry must be a closed planar curve".format(label))
    if not curve.IsPlanar():
        raise GeneratorInputError("{}: geometry must be planar".format(label))
    return curve


def curve(record, label):
    value = geometry(record, label)
    if not isinstance(value, RG.Curve):
        raise GeneratorInputError("{}: geometry must be a curve".format(label))
    return value


def area(curve_value, label):
    amp = RG.AreaMassProperties.Compute(curve_value)
    if amp is None or amp.Area <= 0:
        raise GeneratorInputError("{}: closed geometry has no positive area".format(label))
    return float(amp.Area)


def base_record(context, input_record, index, domain, resource_class, geometry_value, attributes=None):
    object_id = stable_object_id(context, input_record, index, domain)
    attrs = {
        "object_id": object_id,
        "scenario_id": _text(context["scenario_id"]),
        "design_domain": domain,
        "resource_class": resource_class,
        "source_need_ids": ";".join(
            sorted(set(map(_text, input_record.get("source_need_ids", input_record.get("need_ids", [])))))
        ),
        "source_id": _text(input_record.get("source_id")),
        "provenance_reference": provenance(context, input_record, domain, object_id),
        "generator_version": _text(context.get("generator_version", "1.0.0")),
    }
    if attributes:
        attrs.update(attributes)
    return {"geometry": geometry_value, "attributes": attrs}


def run_records(records, context, domain, resource_class, builder):
    context_check(context, domain)
    if not isinstance(records, (list, tuple)):
        raise GeneratorInputError("records must be a list")
    outputs = []
    failures = []
    for index, item in enumerate(records):
        label = "{}[{}]".format(domain, index)
        try:
            if not isinstance(item, dict):
                raise GeneratorInputError("input must be a dictionary")
            outputs.append(builder(item, index, context, domain, resource_class))
        except (GeneratorInputError, TypeError, ValueError) as exc:
            failures.append({"index": index, "source_id": _text(item.get("source_id")) if isinstance(item, dict) else "", "error": str(exc)})
    if failures:
        raise GeneratorInputError("{} rejected {} input record(s): {}".format(domain, len(failures), json.dumps(failures, sort_keys=True)))
    return outputs


def attach_user_strings(rhino_object, attributes):
    """Attach export attributes to a baked Rhino object for auditability."""
    if rhino_object is None or not hasattr(rhino_object, "Attributes"):
        return
    for key, value in attributes.items():
        rhino_object.Attributes.SetUserString(str(key), _text(value))
