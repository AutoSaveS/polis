#!/bin/zsh
# Build the app and assemble the distributable POLIS_3D_Demo.zip.
# Usage: packaging/package-demo.sh [output-dir]   (default: ~/Desktop)
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:-$HOME/Desktop}"
STAGE="$(mktemp -d)/POLIS_3D_Demo"

cd "$REPO"
npm run build

mkdir -p "$STAGE"
cp -R dist/. "$STAGE/"
cp packaging/Start_POLIS_Demo.command packaging/Stop_POLIS_Demo.command packaging/README.txt "$STAGE/"
chmod +x "$STAGE"/*.command

cd "$(dirname "$STAGE")"
rm -f "$OUT_DIR/POLIS_3D_Demo.zip"
zip -qry "$OUT_DIR/POLIS_3D_Demo.zip" POLIS_3D_Demo
echo "packaged -> $OUT_DIR/POLIS_3D_Demo.zip"
