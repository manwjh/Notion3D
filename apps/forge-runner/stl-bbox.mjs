/**
 * Minimal STL bounding-box parser (ASCII + binary).
 */

import fs from "node:fs";

const EMPTY_BBOX = {
  min: [0, 0, 0],
  max: [0, 0, 0],
  center: [0, 0, 0],
  size: [0, 0, 0],
};

function initBounds() {
  return {
    min: [Infinity, Infinity, Infinity],
    max: [-Infinity, -Infinity, -Infinity],
  };
}

function includePoint(bounds, x, y, z) {
  if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(z)) return;
  bounds.min[0] = Math.min(bounds.min[0], x);
  bounds.min[1] = Math.min(bounds.min[1], y);
  bounds.min[2] = Math.min(bounds.min[2], z);
  bounds.max[0] = Math.max(bounds.max[0], x);
  bounds.max[1] = Math.max(bounds.max[1], y);
  bounds.max[2] = Math.max(bounds.max[2], z);
}

function finalizeBounds(bounds) {
  if (!Number.isFinite(bounds.min[0])) {
    return { ...EMPTY_BBOX };
  }
  const center = [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ];
  const size = [
    bounds.max[0] - bounds.min[0],
    bounds.max[1] - bounds.min[1],
    bounds.max[2] - bounds.min[2],
  ];
  return { min: [...bounds.min], max: [...bounds.max], center, size };
}

function bboxFromAscii(text) {
  const bounds = initBounds();
  for (const line of text.split("\n")) {
    const m = line.trim().match(/^vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)/);
    if (!m) continue;
    includePoint(bounds, Number(m[1]), Number(m[2]), Number(m[3]));
  }
  return finalizeBounds(bounds);
}

function bboxFromBinary(buffer) {
  if (buffer.length < 84) {
    return { ...EMPTY_BBOX };
  }
  const count = buffer.readUInt32LE(80);
  const expected = 84 + count * 50;
  if (buffer.length < expected) {
    return { ...EMPTY_BBOX };
  }

  const bounds = initBounds();
  let offset = 84;
  for (let i = 0; i < count; i += 1) {
    offset += 12; // normal
    for (let v = 0; v < 3; v += 1) {
      includePoint(
        bounds,
        buffer.readFloatLE(offset),
        buffer.readFloatLE(offset + 4),
        buffer.readFloatLE(offset + 8),
      );
      offset += 12;
    }
    offset += 2; // attribute byte count
  }
  return finalizeBounds(bounds);
}

export function readStlBoundingBox(filePath) {
  const buffer = fs.readFileSync(filePath);
  const head = buffer.slice(0, 5).toString("utf8").toLowerCase();
  if (head === "solid") {
    return bboxFromAscii(buffer.toString("utf8"));
  }
  return bboxFromBinary(buffer);
}

export function bboxDiagonal(size) {
  return Math.hypot(size[0], size[1], size[2]);
}

export function distance(a, b) {
  return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
}
