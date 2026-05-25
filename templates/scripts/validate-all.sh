#!/usr/bin/env bash
# Validate builtin ForgeCAD templates.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
FORGE_RUNNER="$REPO/apps/forge-runner"

failed=0
passed=0

if [[ -d "$FORGE_RUNNER" ]]; then
  for forge in "$ROOT"/builtin/*/model.forge.js; do
    [[ -f "$forge" ]] || continue
    out="/tmp/notion3d-validate-$$"
    if node "$FORGE_RUNNER/export-parts.mjs" "$forge" "$out" --project-id validate --version 1 >/dev/null 2>&1; then
      echo "OK  forge  $forge"
      passed=$((passed + 1))
    else
      echo "FAIL forge  $forge" >&2
      failed=$((failed + 1))
    fi
    rm -rf "$out"
  done
fi

echo "---"
echo "Passed: $passed  Failed: $failed"
[[ "$failed" -eq 0 ]]
