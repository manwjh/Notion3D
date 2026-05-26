/**
 * Assembly spatial checks from per-part STL bounding boxes.
 */

import fs from "node:fs";
import path from "node:path";
import { bboxDiagonal, distance, readStlBoundingBox } from "./stl-bbox.mjs";
import { validateAssemblySpec, normalizePartName } from "./validate-assembly-spec.mjs";

const ASSEMBLY_WARNING_PREFIX = "装配校验：";
const MIN_PARTS_FOR_CHECKS = 3;
const ORPHAN_DISTANCE_RATIO = 0.75;
const SHELL_OUTSIDE_TOLERANCE_MM = 2.5;
const MIN_ORPHAN_DISTANCE_MM = 8;

const SHELL_PATTERN = /shell|外壳|case|enclosure|body/i;
const LID_PATTERN = /lid|cover|盖|hinge|铰链/i;

function isShellLabel(label) {
  return SHELL_PATTERN.test(label);
}

function isLidLikeLabel(label) {
  return LID_PATTERN.test(label);
}

function pointInsideBox(point, box, tolerance = 0) {
  return (
    point[0] >= box.min[0] - tolerance &&
    point[0] <= box.max[0] + tolerance &&
    point[1] >= box.min[1] - tolerance &&
    point[1] <= box.max[1] + tolerance &&
    point[2] >= box.min[2] - tolerance &&
    point[2] <= box.max[2] + tolerance
  );
}

function unionBounds(parts) {
  const bounds = {
    min: [Infinity, Infinity, Infinity],
    max: [-Infinity, -Infinity, -Infinity],
  };
  for (const part of parts) {
    for (let i = 0; i < 3; i += 1) {
      bounds.min[i] = Math.min(bounds.min[i], part.bbox.min[i]);
      bounds.max[i] = Math.max(bounds.max[i], part.bbox.max[i]);
    }
  }
  if (!Number.isFinite(bounds.min[0])) {
    return null;
  }
  const size = [
    bounds.max[0] - bounds.min[0],
    bounds.max[1] - bounds.min[1],
    bounds.max[2] - bounds.min[2],
  ];
  const center = [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ];
  return { min: bounds.min, max: bounds.max, center, size };
}

function largestPartByVolume(parts) {
  let best = null;
  let bestVolume = -1;
  for (const part of parts) {
    const volume = part.bbox.size[0] * part.bbox.size[1] * part.bbox.size[2];
    if (volume > bestVolume) {
      best = part;
      bestVolume = volume;
    }
  }
  return best;
}

function assemblyAnchor(parts) {
  const shellParts = parts.filter((part) => isShellLabel(part.label));
  if (shellParts.length > 0) {
    const sum = [0, 0, 0];
    for (const shell of shellParts) {
      for (let i = 0; i < 3; i += 1) {
        sum[i] += shell.bbox.center[i];
      }
    }
    return sum.map((value) => value / shellParts.length);
  }

  const largest = largestPartByVolume(parts);
  if (largest) {
    return largest.bbox.center;
  }

  const union = unionBounds(parts);
  return union ? union.center : [0, 0, 0];
}

function assemblyAnchorScale(parts) {
  const shellParts = parts.filter((part) => isShellLabel(part.label));
  if (shellParts.length > 0) {
    const diagonals = shellParts.map((part) => bboxDiagonal(part.bbox.size));
    return Math.max(...diagonals, 1);
  }
  const largest = largestPartByVolume(parts);
  if (largest) {
    return Math.max(bboxDiagonal(largest.bbox.size), 1);
  }
  const union = unionBounds(parts);
  return union ? Math.max(bboxDiagonal(union.size), 1) : 1;
}

export function validateAssemblyParts(parts, options = {}) {
  const warnings = [];
  const assemblySpec = options.assemblySpec || [];
  const useSpec = assemblySpec.length > 0;
  if (!parts.length) {
    return { warnings, bboxes: [] };
  }

  const bboxes = parts.map((part) => ({
    id: part.id,
    label: part.label,
    bbox: part.bbox,
  }));

  if (parts.length < MIN_PARTS_FOR_CHECKS && !useSpec) {
    return { warnings, bboxes };
  }

  if (useSpec) {
    warnings.push(...validateAssemblySpec(parts, assemblySpec, ASSEMBLY_WARNING_PREFIX));
  }

  const anchor = assemblyAnchor(parts);
  const anchorScale = assemblyAnchorScale(parts);
  const orphanThreshold = Math.max(
    anchorScale * ORPHAN_DISTANCE_RATIO,
    MIN_ORPHAN_DISTANCE_MM,
  );

  const shellParts = parts.filter((part) => isShellLabel(part.label));
  const internalCandidates = parts.filter(
    (part) => !isShellLabel(part.label) && !isLidLikeLabel(part.label),
  );
  const specShellIds = new Set(
    assemblySpec
      .filter((module) => module.role === "shell")
      .map((module) => normalizePartName(module.id)),
  );
  const specContainsChildIds = new Set(
    assemblySpec
      .flatMap((module) => module.contains || [])
      .map((childId) => normalizePartName(childId)),
  );

  for (const part of parts) {
    if (isLidLikeLabel(part.label)) continue;
    if (useSpec && specShellIds.has(normalizePartName(part.label))) continue;
    const dist = distance(part.bbox.center, anchor);
    if (dist > orphanThreshold) {
      warnings.push(
        `${ASSEMBLY_WARNING_PREFIX}${part.label} 远离装配主体（${dist.toFixed(1)}mm），可能 translate 坐标错误`,
      );
    }
  }

  if (shellParts.length > 0 && !useSpec) {
    for (const part of internalCandidates) {
      const insideAnyShell = shellParts.some((shell) =>
        pointInsideBox(part.bbox.center, shell.bbox, SHELL_OUTSIDE_TOLERANCE_MM),
      );
      if (!insideAnyShell) {
        warnings.push(
          `${ASSEMBLY_WARNING_PREFIX}${part.label} 中心在 Shell 外，可能未装入外壳/内胆`,
        );
      }
    }
  }

  if (useSpec) {
    for (const part of internalCandidates) {
      if (specContainsChildIds.has(normalizePartName(part.label))) continue;
      const insideAnyShell = shellParts.some((shell) =>
        pointInsideBox(part.bbox.center, shell.bbox, SHELL_OUTSIDE_TOLERANCE_MM),
      );
      if (!insideAnyShell && shellParts.length > 0) {
        warnings.push(
          `${ASSEMBLY_WARNING_PREFIX}${part.label} 中心在 Shell 外，可能未装入外壳/内胆`,
        );
      }
    }
  }

  return { warnings: [...new Set(warnings)], bboxes };
}

function readAssemblySpec(outDir) {
  const specPath = path.join(outDir, "assembly_spec.json");
  if (!fs.existsSync(specPath)) {
    return [];
  }
  try {
    const parsed = JSON.parse(fs.readFileSync(specPath, "utf8"));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function validateAssemblyFromDir(outDir, manifestParts) {
  const partsDir = path.join(outDir, "parts");
  const measured = [];
  const assemblySpec = readAssemblySpec(outDir);

  for (const manifestPart of manifestParts) {
    const stlPath = path.join(partsDir, `${manifestPart.id}.stl`);
    if (!fs.existsSync(stlPath)) continue;
    const bbox = readStlBoundingBox(stlPath);
    if (bbox.size.every((value) => value <= 0)) continue;
    measured.push({
      id: manifestPart.id,
      label: manifestPart.label,
      bbox,
    });
  }

  return validateAssemblyParts(measured, { assemblySpec });
}

export function isAssemblyWarning(message) {
  return typeof message === "string" && message.startsWith(ASSEMBLY_WARNING_PREFIX);
}

export { ASSEMBLY_WARNING_PREFIX };
