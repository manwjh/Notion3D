/**
 * ForgeCAD capability analysis — advisory hints vs plan recipes.
 */

import fs from "node:fs";
import path from "node:path";

export const CAPABILITY_GAP_PREFIX = "建模建议：";

const FEATURE_PATTERNS = {
  constrainedSketch: /\bconstrainedSketch\s*\(/g,
  extrude: /\.extrude\s*\(|\bextrude\s*\(/g,
  loft: /\bloft\s*\(/g,
  sweep: /\bsweep\s*\(/g,
  fillet: /\.fillet\s*\(|\bfillet\s*\(/g,
  chamfer: /\.chamfer\s*\(|\bchamfer\s*\(/g,
  revolve: /\brevolve\s*\(/g,
  subtract: /\.subtract\s*\(/g,
  union: /\bunion\s*\(/g,
  spline2d: /\bspline2d\s*\(/g,
  sphere: /\bsphere\s*\(/g,
  box: /\bbox\s*\(/g,
  cylinder: /\bcylinder\s*\(/g,
};

const RECIPE_REQUIRED = {
  sketch_extrude: ["constrainedSketch", "extrude"],
  sketch_extrude_shell: ["constrainedSketch", "extrude", "subtract"],
  loft: ["loft"],
  sweep: ["sweep"],
  revolve: ["revolve"],
  union_bracket: ["union"],
  primitive_shell: ["cylinder", "subtract"],
  primitive_layout: [],
};

const RECIPE_LABELS = {
  sketch_extrude: "草图拉伸实体",
  sketch_extrude_shell: "草图拉伸空心壳",
  loft: "截面放样",
  sweep: "扫掠",
  revolve: "旋转体",
  union_bracket: "板件并集支架",
  primitive_shell: "回转壳体（简易）",
  primitive_layout: "布局级体素",
};

export function isCapabilityGap(message) {
  return typeof message === "string" && message.startsWith(CAPABILITY_GAP_PREFIX);
}

export function countFeatures(source) {
  const text = source || "";
  const counts = {};
  for (const [name, pattern] of Object.entries(FEATURE_PATTERNS)) {
    counts[name] = (text.match(pattern) || []).length;
  }
  return counts;
}

export function readGeometryRecipes(outDir) {
  const recipePath = path.join(outDir, "geometry_recipes.json");
  if (!fs.existsSync(recipePath)) return [];
  try {
    const parsed = JSON.parse(fs.readFileSync(recipePath, "utf8"));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function readDesignIntent(outDir) {
  const intentPath = path.join(outDir, "design_intent.json");
  if (!fs.existsSync(intentPath)) return {};
  try {
    const parsed = JSON.parse(fs.readFileSync(intentPath, "utf8"));
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

export function analyzeForgeCapability(options = {}) {
  const forgeSource = options.forgeSource || "";
  const recipes = options.geometryRecipes || [];
  const features = countFeatures(forgeSource);

  const strengths = [];
  if (features.constrainedSketch > 0) strengths.push("约束草图");
  if (features.extrude > 0) strengths.push("拉伸");
  if (features.loft > 0) strengths.push("放样");
  if (features.fillet > 0) strengths.push("圆角");
  if (features.subtract > 0) strengths.push("布尔减腔");

  const advanced =
    features.constrainedSketch > 0 ||
    features.loft > 0 ||
    features.sweep > 0 ||
    features.revolve > 0 ||
    features.fillet > 0;

  const gaps = [];
  for (const entry of recipes) {
    const partId = entry.part_id || entry.partId || "";
    const recipe = entry.recipe || "";
    const required = RECIPE_REQUIRED[recipe] || [];
    const missing = required.filter((key) => (features[key] || 0) <= 0);
    if (missing.length > 0 && partId) {
      const label = RECIPE_LABELS[recipe] || recipe;
      gaps.push(
        `${CAPABILITY_GAP_PREFIX}部件 ${partId} 计划为「${label}」，脚本未检测到 ${missing.join("、")}`,
      );
    }
  }

  const nextSteps = [];
  if (gaps.length > 0) {
    nextSteps.push("可选：按 geometry_recipes 补齐特征（docs/forge-modeling-guide.md）");
  } else if (advanced) {
    nextSteps.push("特征级建模已启用；对照 spatial_digest 检查比例与装配");
  }

  return {
    features,
    strengths,
    advanced_modeling: advanced,
    gaps: [...new Set(gaps)],
    next_steps: nextSteps,
    recipe_count: recipes.length,
  };
}

export function analyzeForgeCapabilityFromDir(outDir) {
  const forgePath = path.join(outDir, "model.forge.js");
  let forgeSource = "";
  if (fs.existsSync(forgePath)) {
    forgeSource = fs.readFileSync(forgePath, "utf8");
  }
  const srcDir = path.join(outDir, "src");
  if (fs.existsSync(srcDir)) {
    for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
      if (!entry.isFile()) continue;
      forgeSource += `\n${fs.readFileSync(path.join(srcDir, entry.name), "utf8")}`;
    }
  }

  const report = analyzeForgeCapability({
    forgeSource,
    geometryRecipes: readGeometryRecipes(outDir),
    designIntent: readDesignIntent(outDir),
  });

  return {
    warnings: report.gaps,
    capability: report,
  };
}
