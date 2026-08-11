#!/usr/bin/env python3
"""Build a truthful fixed-workstation asset inventory with SHA-256 hashes.

Run this only where the actual Rhino/Grasshopper assets were created.  It does
not manufacture missing files or accept placeholder paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SOFTWARE = ROOT / "preregistration" / "software"
GENERATORS = SOFTWARE / "rhino_generators"
REQUIRED_WORKSTATION_FILES = (
    "POLIS_vegetation_v1.gh",
    "POLIS_vegetation_v1.ghx",
    "POLIS_hardscape_v1.gh",
    "POLIS_hardscape_v1.ghx",
    "POLIS_hydrology_v1.gh",
    "POLIS_hydrology_v1.ghx",
    "POLIS_furniture_v1.gh",
    "POLIS_furniture_v1.ghx",
    "POLIS_activity_v1.gh",
    "POLIS_activity_v1.ghx",
    "POLIS_ecology_v1.gh",
    "POLIS_ecology_v1.ghx",
    "POLIS_workstation_master_v1.3dm",
)
SOURCE_FILES = (
    "polis_generator_common.py",
    "vegetation_generator.py",
    "hardscape_generator.py",
    "hydrology_generator.py",
    "furniture_generator.py",
    "activity_generator.py",
    "ecology_generator.py",
    "generator_contract.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def asset_record(path: Path, relative_path: str, purpose: str, asset_type: str) -> dict[str, str]:
    return {
        "relative_path": relative_path,
        "sha256": sha256(path),
        "purpose": purpose,
        "asset_type": asset_type,
        "status": "verified",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True, help="Directory containing the real .gh/.ghx/.3dm assets")
    parser.add_argument("--workstation-id", required=True)
    parser.add_argument("--operating-system", required=True)
    parser.add_argument("--rhino-version", required=True)
    parser.add_argument("--grasshopper-version", required=True)
    parser.add_argument("--operator-id", required=True)
    parser.add_argument("--plugin", action="append", default=[], metavar="NAME=VERSION")
    parser.add_argument("--output", type=Path, default=SOFTWARE / "rhino_workstation_assets.json")
    args = parser.parse_args()

    if not args.rhino_version.startswith("8."):
        raise SystemExit("--rhino-version must begin with '8.'")
    if not args.asset_root.is_dir():
        raise SystemExit("asset root does not exist: {}".format(args.asset_root))
    plugins: list[dict[str, str]] = []
    for entry in args.plugin:
        if "=" not in entry:
            raise SystemExit("--plugin must have NAME=VERSION format")
        name, version = (part.strip() for part in entry.split("=", 1))
        if not name or not version:
            raise SystemExit("--plugin must have nonblank NAME and VERSION")
        plugins.append({"name": name, "version": version})

    missing = [name for name in REQUIRED_WORKSTATION_FILES if not (args.asset_root / name).is_file()]
    if missing:
        raise SystemExit("missing required workstation asset(s): {}".format(", ".join(missing)))
    source_missing = [name for name in SOURCE_FILES if not (GENERATORS / name).is_file()]
    if source_missing:
        raise SystemExit("missing generator source file(s): {}".format(", ".join(source_missing)))

    assets: list[dict[str, str]] = []
    for name in REQUIRED_WORKSTATION_FILES:
        extension = Path(name).suffix.lower()
        purpose = "POLIS six-domain master document" if extension == ".3dm" else "POLIS Grasshopper generator definition"
        assets.append(asset_record(args.asset_root / name, name, purpose, extension[1:]))
    for name in SOURCE_FILES:
        assets.append(asset_record(GENERATORS / name, "rhino_generators/" + name, "POLIS generator source or contract", "source"))

    payload: dict[str, Any] = {
        "schema_version": "1.1.0",
        "status": "VERIFIED_ON_FIXED_WORKSTATION",
        "workstation_id": args.workstation_id,
        "operating_system": args.operating_system,
        "rhino_version": args.rhino_version,
        "grasshopper_version": args.grasshopper_version,
        "plugins": plugins,
        "source_assets": assets,
        "generator_contract": "preregistration/software/rhino_generators/generator_contract.json",
        "export_contract": "preregistration/software/rhino_export_contract.schema.json",
        "verified_by_operator_id": args.operator_id,
        "verified_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "notes": "Inventory contains only actual files. Do not record passwords, licence keys, API keys, or participant data."
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
    print(json.dumps({"output": str(args.output), "asset_count": len(assets), "status": payload["status"]}, indent=2))


if __name__ == "__main__":
    main()

