#!/usr/bin/env bash
# Validate all builtin templates (syntax + manifold STL export).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATE="${ROOT}/../.cursor/skills/notion3d-openscad/scripts/validate.sh"

if [[ ! -x "$VALIDATE" ]]; then
  echo "ERROR: validate.sh not found at $VALIDATE" >&2
  exit 1
fi

failed=0
passed=0

for scad in "$ROOT"/builtin/*/model.scad; do
  if "$VALIDATE" "$scad"; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
  fi
done

echo "---"
echo "Passed: $passed  Failed: $failed"
[[ "$failed" -eq 0 ]]
