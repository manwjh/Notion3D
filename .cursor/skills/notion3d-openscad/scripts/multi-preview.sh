#!/usr/bin/env bash
# Render multi-angle PNG previews for visual validation.
set -euo pipefail

SCAD="${1:?Usage: multi-preview.sh model.scad output_dir/}"
OUT_DIR="${2:?Usage: multi-preview.sh model.scad output_dir/}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREVIEW="$SCRIPT_DIR/preview.sh"

mkdir -p "$OUT_DIR"
base="$(basename "$SCAD" .scad)"

declare -A VIEWS=(
  [front]="--camera=0,0,0,90,0,0,180"
  [back]="--camera=0,0,0,90,0,180,180"
  [left]="--camera=0,0,0,90,0,90,180"
  [right]="--camera=0,0,0,90,0,270,180"
  [top]="--camera=0,0,0,0,0,0,180"
  [iso]="--camera=0,0,0,55,0,25,180"
)

for name in front back left right top iso; do
  "$PREVIEW" "$SCAD" "$OUT_DIR/${base}_${name}.png" "${VIEWS[$name]}"
done

echo "Previews in $OUT_DIR"
