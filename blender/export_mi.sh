#!/usr/bin/env bash
# Rebuild the «Маҷмааи истиқоматӣ» model and copy it into the web viewer.
#
#   tools/ab/py tools/mi/genplan.py   # (only when the genplan changes) -> build/genplan.json
#   tools/ab/py tools/mi/plans.py     # (only when the plans change)    -> build/plan_K.json
#   blender/export_mi.sh              # -> public/models/mi.glb, src/model/complex.json
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
export PATH="$HOME/.local/opt/node/bin:$PATH"
OUT=build/mi
mkdir -p build public/models src/model
PYTHONPATH=.pylib-blender "$BLENDER" -b --factory-startup --python-use-system-env -P blender/build_mi.py -- --out "$OUT" "$@" 2>&1 | grep -v '^[0-9:]* | INFO' | grep -v '^Info' || true
GT=(npx --yes @gltf-transform/cli@4.1.1)
"${GT[@]}" dedup "$OUT.glb" "$OUT.dedup.glb"
"${GT[@]}" weld "$OUT.dedup.glb" "$OUT.weld.glb"
"${GT[@]}" meshopt "$OUT.weld.glb" public/models/mi.glb
rm -f "$OUT.dedup.glb" "$OUT.weld.glb"
cp "$OUT.json" src/model/complex.json
ls -la public/models/mi.glb src/model/complex.json
