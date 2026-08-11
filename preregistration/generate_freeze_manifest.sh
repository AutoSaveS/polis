#!/bin/sh
set -eu

export LC_ALL=C
export LANG=C

cd "$(dirname "$0")/.."

find preregistration -type f \
  ! -name 'freeze_manifest.sha256' \
  ! -name 'freeze_manifest.preview.sha256' \
  ! -name 'amendments.csv' \
  -print \
  | LC_ALL=C sort \
  | while IFS= read -r prereg_file; do
      shasum -a 256 "$prereg_file"
    done > preregistration/freeze_manifest.sha256

printf '%s\n' "Wrote preregistration/freeze_manifest.sha256"
