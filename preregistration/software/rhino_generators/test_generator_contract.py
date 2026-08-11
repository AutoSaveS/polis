#!/usr/bin/env python3
"""Static checks that can run without Rhino on the analysis machine."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
DOMAINS = ("vegetation", "hardscape", "hydrology", "furniture", "activity", "ecology")


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + "_generator.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    contract = json.loads((HERE / "generator_contract.json").read_text(encoding="utf-8"))
    assert contract["status"] == "SOURCE_CONTRACT_READY_RHINO_EXECUTION_REQUIRED"
    assert set(contract["domains"]) == set(DOMAINS)
    assert set(contract["resource_classes"]) == set(DOMAINS)
    for domain in DOMAINS:
        module = load(domain)
        assert module.DOMAIN == domain
        assert module.RESOURCE_CLASS == domain
        assert callable(module.generate)
        assert contract["domains"][domain]["script"] == domain + "_generator.py"
    print("RHINO_GENERATOR_STATIC_CONTRACT_PASS")


if __name__ == "__main__":
    main()
