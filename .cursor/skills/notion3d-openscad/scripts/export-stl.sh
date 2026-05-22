#!/usr/bin/env bash
# Export STL from OpenSCAD; optional -D overrides.
set -euo pipefail

SCAD="${1:?Usage: export-stl.sh model.scad output.stl [-D key=value ...]}"
OUT="${2:?Usage: export-stl.sh model.scad output.stl}"
shift 2

OPENSCAD="${OPENSCAD:-openscad}"

if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
  echo "ERROR: openscad not found in PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
args=(-o "$OUT")
for arg in "$@"; do
  args+=(-D "$arg")
done
args+=("$SCAD")

log="$(mktemp /tmp/notion3d-export-XXXXXX.log)"
trap 'rm -f "$log"' EXIT

if ! "$OPENSCAD" "${args[@]}" >"$log" 2>&1; then
  cat "$log" >&2
  exit 1
fi
if grep -qiE 'ERROR:|mesh is not closed' "$log"; then
  cat "$log" >&2
  echo "FAIL: non-manifold or OpenSCAD error" >&2
  exit 1
fi

echo "Wrote $OUT ($(wc -c < "$OUT" | tr -d ' ') bytes)"
