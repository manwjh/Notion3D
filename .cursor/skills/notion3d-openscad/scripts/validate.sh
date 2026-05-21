#!/usr/bin/env bash
# Validate OpenSCAD syntax (export to null STL).
set -euo pipefail

SCAD="${1:?Usage: validate.sh model.scad}"
OPENSCAD="${OPENSCAD:-openscad}"

if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
  echo "ERROR: openscad not found in PATH" >&2
  exit 1
fi

tmp="$(mktemp /tmp/notion3d-validate-XXXXXX.stl)"
trap 'rm -f "$tmp"' EXIT

if "$OPENSCAD" -o "$tmp" "$SCAD" 2>&1; then
  echo "OK: $SCAD"
else
  echo "FAIL: $SCAD" >&2
  exit 1
fi
