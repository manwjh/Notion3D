#!/usr/bin/env node
/**
 * ForgeCAD export runner for Notion3D Engine.
 * Exports combined STL + per-part STLs + parts.json manifest.
 *
 * Usage: node export-parts.mjs <script.forge.js> <outDir> [--project-id ID] [--version N]
 */

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { resolvePartSourceRef } from "./part-source.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PART_COLORS = [
  "#E74C3C",
  "#3498DB",
  "#2ECC71",
  "#F39C12",
  "#9B59B6",
  "#1ABC9C",
  "#E67E22",
  "#95A5A6",
  "#34495E",
  "#16A085",
];

function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48) || "part";
}

function forgecadRoot() {
  const local = path.join(__dirname, "node_modules", "forgecad");
  if (fs.existsSync(local)) return local;
  return __dirname;
}

function forgecadBin() {
  const root = forgecadRoot();
  const cli = path.join(root, "dist-cli", "forgecad.js");
  if (fs.existsSync(cli)) return cli;
  return "forgecad";
}

function runForgeExport(scriptPath, outputPath) {
  const bin = forgecadBin();
  const forgeRoot = forgecadRoot();
  const scriptAbs = path.resolve(scriptPath);
  const outputAbs = path.resolve(outputPath);
  const args =
    bin.endsWith(".js")
      ? [bin, "export", "stl", scriptAbs, "--output", outputAbs, "--quality", "default"]
      : ["export", "stl", scriptAbs, "--output", outputAbs, "--quality", "default"];
  const cmd = bin.endsWith(".js") ? process.execPath : bin;
  const result = spawnSync(cmd, args, {
    cwd: forgeRoot,
    encoding: "utf-8",
    maxBuffer: 20 * 1024 * 1024,
  });
  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  if (result.status !== 0) {
    throw new Error(output.trim() || `ForgeCAD export failed (${result.status})`);
  }
  if (!fs.existsSync(outputPath)) {
    throw new Error(`ForgeCAD did not write ${outputPath}\n${output}`);
  }
  return output;
}

function parsePartLines(exportOutput) {
  const parts = [];
  for (const line of exportOutput.split("\n")) {
    const m = line.match(/^\s+(.+?):\s*([\d,]+)\s+triangles\s*$/);
    if (m) {
      parts.push({ name: m[1].trim(), triangles: Number(m[2].replace(/,/g, "")) });
    }
  }
  return parts;
}

function extractReturnExpression(source) {
  const match = source.match(/return\s+([\s\S]+?)\s*;?\s*$/);
  if (!match) {
    return { preamble: source, expr: "null" };
  }
  const expr = match[1].trim().replace(/;\s*$/, "");
  const preamble = source.slice(0, match.index).trimEnd();
  return { preamble, expr };
}

function wrapForPart(source, partName) {
  const { preamble, expr } = extractReturnExpression(source);
  return `${preamble}

function __notion3d_flatten(value, out) {
  if (out === undefined) out = [];
  if (value == null) return out;
  if (Array.isArray(value)) {
    for (var i = 0; i < value.length; i++) __notion3d_flatten(value[i], out);
    return out;
  }
  if (typeof value === "object" && value.name && value.shape) {
    out.push(value);
    return out;
  }
  if (typeof value === "object" && value.group) {
    __notion3d_flatten(value.group, out);
    return out;
  }
  out.push({ name: "Part", shape: value });
  return out;
}

var __notion3d_all = __notion3d_flatten(${expr});
var __notion3d_target = ${JSON.stringify(partName)};
var __notion3d_hit = null;
for (var __i = 0; __i < __notion3d_all.length; __i++) {
  if (__notion3d_all[__i].name === __notion3d_target) {
    __notion3d_hit = __notion3d_all[__i];
    break;
  }
}
if (!__notion3d_hit && __notion3d_all.length > 0) __notion3d_hit = __notion3d_all[0];
if (!__notion3d_hit) throw new Error("No geometry to export for part: " + __notion3d_target);
return __notion3d_hit.shape;
`;
}

function copyDirRecursive(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const from = path.join(src, entry.name);
    const to = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDirRecursive(from, to);
    else fs.copyFileSync(from, to);
  }
}

function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: export-parts.mjs <script.forge.js> <outDir> [--project-id ID] [--version N]");
    process.exit(1);
  }

  const scriptPath = path.resolve(args[0]);
  const outDir = path.resolve(args[1]);
  let projectId = "project";
  let version = 1;
  for (let i = 2; i < args.length; i += 1) {
    if (args[i] === "--project-id" && args[i + 1]) projectId = args[++i];
    if (args[i] === "--version" && args[i + 1]) version = Number(args[++i]);
  }

  if (!fs.existsSync(scriptPath)) {
    console.error(`Script not found: ${scriptPath}`);
    process.exit(1);
  }

  fs.mkdirSync(outDir, { recursive: true });
  const partsDir = path.join(outDir, "parts");
  fs.mkdirSync(partsDir, { recursive: true });

  const workDir = path.join(outDir, ".forge-work");
  fs.mkdirSync(workDir, { recursive: true });

  const source = fs.readFileSync(scriptPath, "utf-8");
  const mainCopy = path.join(workDir, "model.forge.js");
  fs.copyFileSync(scriptPath, mainCopy);

  const srcDir = path.join(path.dirname(scriptPath), "src");
  const srcFiles = {};
  if (fs.existsSync(srcDir)) {
    copyDirRecursive(srcDir, path.join(workDir, "src"));
    for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
      if (!entry.isFile()) continue;
      srcFiles[entry.name] = fs.readFileSync(path.join(srcDir, entry.name), "utf-8");
    }
  }

  const combinedStl = path.join(outDir, "model.stl");
  const exportOutput = runForgeExport(mainCopy, combinedStl);
  const parsedParts = parsePartLines(exportOutput);

  const usedIds = new Set();
  const manifestParts = [];

  for (let i = 0; i < parsedParts.length; i += 1) {
    const { name } = parsedParts[i];
    let id = slugify(name);
    let suffix = 2;
    while (usedIds.has(id)) {
      id = `${slugify(name)}_${suffix}`;
      suffix += 1;
    }
    usedIds.add(id);

    const partStl = path.join(partsDir, `${id}.stl`);
    if (parsedParts.length === 1) {
      fs.copyFileSync(combinedStl, partStl);
    } else {
      const wrapped = wrapForPart(source, name);
      const wrappedPath = path.join(workDir, `part_${id}.forge.js`);
      fs.writeFileSync(wrappedPath, wrapped, "utf-8");
      try {
        runForgeExport(wrappedPath, partStl);
      } catch (err) {
        fs.copyFileSync(combinedStl, partStl);
        console.error(`Part export fallback for ${name}: ${err.message}`);
      }
    }

    const sourceRef = resolvePartSourceRef(source, name, id, srcFiles);

    manifestParts.push({
      id,
      label: name,
      color: PART_COLORS[i % PART_COLORS.length],
      stl_url: `/api/projects/${projectId}/versions/${version}/parts/${id}.stl`,
      opacity: name.toLowerCase().includes("shell") ? 0.35 : 1.0,
      ...(sourceRef ? { source_ref: sourceRef } : {}),
    });
  }

  const manifest = { parts: manifestParts, backend: "forgecad" };
  fs.writeFileSync(path.join(outDir, "parts.json"), JSON.stringify(manifest, null, 2), "utf-8");

  const summary = {
    ok: true,
    objects: parsedParts.length,
    parts: manifestParts.map((p) => ({ id: p.id, label: p.label })),
    combined_stl: combinedStl,
  };
  console.log(JSON.stringify(summary));
}

main();
