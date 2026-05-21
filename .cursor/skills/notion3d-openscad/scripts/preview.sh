#!/usr/bin/env bash
# Render a single PNG preview from OpenSCAD.
set -euo pipefail

SCAD="${1:?Usage: preview.sh model.scad output.png [--camera=...]}"
OUT="${2:?Usage: preview.sh model.scad output.png}"
shift 2

OPENSCAD="${OPENSCAD:-openscad}"
CAMERA="${CAMERA:---camera=0,0,0,55,0,25,180}"

if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
  echo "ERROR: openscad not found in PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
extra=()
for arg in "$@"; do extra+=("$arg"); done
if [ ${#extra[@]} -eq 0 ]; then
  extra=("$CAMERA")
fi

"$OPENSCAD" --preview "${extra[@]}" -o "$OUT" "$SCAD"
echo "Wrote $OUT"
