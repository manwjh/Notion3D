#!/usr/bin/env bash
# Validate OpenSCAD syntax and manifold export (null STL).
set -euo pipefail

SCAD="${1:?Usage: validate-scad.sh model.scad}"
OPENSCAD="${OPENSCAD:-openscad}"

if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
  echo "ERROR: openscad not found in PATH" >&2
  exit 1
fi

tmp="$(mktemp /tmp/notion3d-validate-XXXXXX.stl)"
log="$(mktemp /tmp/notion3d-validate-XXXXXX.log)"
trap 'rm -f "$tmp" "$log"' EXIT

if "$OPENSCAD" -o "$tmp" "$SCAD" >"$log" 2>&1; then
  if grep -qiE 'ERROR:|mesh is not closed' "$log"; then
    cat "$log" >&2
    echo "FAIL: non-manifold or OpenSCAD error in $SCAD" >&2
    exit 1
  fi
  echo "OK: $SCAD"
else
  cat "$log" >&2
  echo "FAIL: $SCAD" >&2
  exit 1
fi
