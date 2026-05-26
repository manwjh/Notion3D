/**
 * Plan assembly_spec validation against measured part bounding boxes.
 */

const SPEC_CONTAINS_TOLERANCE_MM = 4;
const SPEC_ANCHOR_DISTANCE_RATIO = 0.65;
const SPEC_ANCHOR_MIN_DISTANCE_MM = 12;
const SPEC_HINGE_GAP_MM = 15;

function normalizePartName(name) {
  return String(name || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function findPartById(parts, id) {
  const needle = normalizePartName(id);
  if (!needle) return null;
  return (
    parts.find((part) => normalizePartName(part.label) === needle) ||
    parts.find((part) => normalizePartName(part.id) === needle) ||
    parts.find((part) => normalizePartName(part.label).includes(needle)) ||
    parts.find((part) => needle.includes(normalizePartName(part.label)))
  );
}

function bboxGapOnAxis(boxA, boxB, axis) {
  const aMin = boxA.min[axis];
  const aMax = boxA.max[axis];
  const bMin = boxB.min[axis];
  const bMax = boxB.max[axis];
  if (aMax < bMin) return bMin - aMax;
  if (bMax < aMin) return aMin - bMax;
  return 0;
}

function boxesOverlapOnAxis(boxA, boxB, axis) {
  return bboxGapOnAxis(boxA, boxB, axis) === 0;
}

function parseHinge(hinge) {
  const match = String(hinge || "").match(/^(.+)\.(left|right|front|back|top|bottom)(?:-edge)?$/i);
  if (!match) return null;
  return { parent: match[1], edge: match[2].toLowerCase() };
}

function validateContains(parent, child, tolerance) {
  const point = child.bbox.center;
  return (
    point[0] >= parent.bbox.min[0] - tolerance &&
    point[0] <= parent.bbox.max[0] + tolerance &&
    point[1] >= parent.bbox.min[1] - tolerance &&
    point[1] <= parent.bbox.max[1] + tolerance &&
    point[2] >= parent.bbox.min[2] - tolerance &&
    point[2] <= parent.bbox.max[2] + tolerance
  );
}

function validateAnchor(anchorPart, part) {
  const dist = Math.hypot(
    anchorPart.bbox.center[0] - part.bbox.center[0],
    anchorPart.bbox.center[1] - part.bbox.center[1],
    anchorPart.bbox.center[2] - part.bbox.center[2],
  );
  const anchorSize = anchorPart.bbox.size;
  const anchorDiagonal = Math.hypot(anchorSize[0], anchorSize[1], anchorSize[2]);
  const threshold = Math.max(anchorDiagonal * SPEC_ANCHOR_DISTANCE_RATIO, SPEC_ANCHOR_MIN_DISTANCE_MM);
  return dist <= threshold;
}

function validateHingeAdjacency(parent, lid, edge) {
  const axisMap = {
    left: 0,
    right: 0,
    front: 1,
    back: 1,
    top: 2,
    bottom: 2,
  };
  const axis = axisMap[edge];
  if (axis === undefined) return true;

  const hingeGap = bboxGapOnAxis(parent.bbox, lid.bbox, axis);
  if (hingeGap > SPEC_HINGE_GAP_MM) {
    return false;
  }

  const otherAxes = [0, 1, 2].filter((value) => value !== axis);
  return otherAxes.every((otherAxis) => boxesOverlapOnAxis(parent.bbox, lid.bbox, otherAxis));
}

export function validateAssemblySpec(parts, spec, warningPrefix) {
  const warnings = [];
  if (!Array.isArray(spec) || spec.length === 0) {
    return warnings;
  }

  const shellModules = spec.filter((module) => module.role === "shell");

  for (const module of spec) {
    const part = findPartById(parts, module.id);
    if (!part) {
      warnings.push(`${warningPrefix}plan 部件 ${module.id} 未在 ForgeCAD return 中找到`);
      continue;
    }

    for (const childId of module.contains || []) {
      const child = findPartById(parts, childId);
      if (!child) {
        warnings.push(`${warningPrefix}plan 子部件 ${childId}（${module.id}.contains）未渲染`);
        continue;
      }
      if (!validateContains(part, child, SPEC_CONTAINS_TOLERANCE_MM)) {
        warnings.push(
          `${warningPrefix}${childId} 未装入 ${module.id}（违反 plan.contains）`,
        );
      }
    }

    if (module.anchor) {
      const anchorPart = findPartById(parts, module.anchor);
      if (!anchorPart) {
        warnings.push(`${warningPrefix}plan 锚点部件 ${module.anchor} 未渲染`);
      } else if (!validateAnchor(anchorPart, part)) {
        warnings.push(
          `${warningPrefix}${module.id} 未靠近锚点 ${module.anchor}（违反 plan.anchor）`,
        );
      }
    }

    if (module.hinge) {
      const parsed = parseHinge(module.hinge);
      if (!parsed) {
        warnings.push(`${warningPrefix}${module.id}.hinge 格式无效（应为 Parent.left 等）`);
      } else {
        const parentPart = findPartById(parts, parsed.parent);
        if (!parentPart) {
          warnings.push(`${warningPrefix}plan 铰链父件 ${parsed.parent} 未渲染`);
        } else if (!validateHingeAdjacency(parentPart, part, parsed.edge)) {
          warnings.push(
            `${warningPrefix}${module.id} 未与 ${parsed.parent} 在 ${parsed.edge} 侧相邻（违反 plan.hinge）`,
          );
        }
      }
    }

    if (
      module.role === "internal" &&
      !(module.contains || []).length &&
      !module.anchor &&
      shellModules.length > 0
    ) {
      const insideAnyShell = shellModules.some((shellModule) => {
        const shellPart = findPartById(parts, shellModule.id);
        return shellPart && validateContains(shellPart, part, SPEC_CONTAINS_TOLERANCE_MM);
      });
      if (!insideAnyShell) {
        warnings.push(
          `${warningPrefix}${module.id}（role=internal）未装入任一 plan Shell`,
        );
      }
    }
  }

  return warnings;
}

const APPEARANCE_LABEL = /shell|外壳|case|enclosure|body|lid|cover|盖|hinge|铰链/i;

function roleForLabel(label, assemblySpec) {
  const norm = normalizePartName(label);
  for (const module of assemblySpec) {
    if (normalizePartName(module.id) === norm) {
      return module.role || "other";
    }
  }
  if (/shell|外壳|case|enclosure/i.test(label)) return "shell";
  if (/lid|cover|盖/i.test(label)) return "lid";
  return "other";
}

export function roleForPartLabel(label, assemblySpec = []) {
  return roleForLabel(label, assemblySpec);
}

export { findPartById, normalizePartName };
