#!/usr/bin/env node
/**
 * GitHub forgecad npm package ships CLI-only dist without a working Node solver path.
 * - Copy vendored WASM solver into node_modules/forgecad/solver/pkg/
 * - Patch dist-cli/forgecad.js (mesh export init + solver import path)
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runnerRoot = path.resolve(__dirname, "..");
const vendorDir = path.join(runnerRoot, "vendor", "solver-pkg");
const forgeRoot = path.join(runnerRoot, "node_modules", "forgecad");
const targetDir = path.join(forgeRoot, "solver", "pkg");
const forgeCli = path.join(forgeRoot, "dist-cli", "forgecad.js");

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const from = path.join(src, entry.name);
    const to = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(from, to);
    } else {
      fs.copyFileSync(from, to);
    }
  }
}

function newestMtime(dir) {
  let newest = 0;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    const t = entry.isDirectory() ? newestMtime(full) : fs.statSync(full).mtimeMs;
    if (t > newest) newest = t;
  }
  return newest;
}

function installSolverPkg() {
  if (!fs.existsSync(vendorDir)) {
    console.error(
      "ensure-forgecad-solver: missing vendor/solver-pkg — run from repo root: make install",
    );
    process.exit(1);
  }
  const vendorMtime = newestMtime(vendorDir);
  const targetMtime = fs.existsSync(targetDir) ? newestMtime(targetDir) : 0;
  if (vendorMtime > targetMtime || !fs.existsSync(path.join(targetDir, "solver_bg.wasm"))) {
    copyDir(vendorDir, targetDir);
    console.log("ensure-forgecad-solver: installed solver/pkg into node_modules/forgecad");
  }
}

function patchForgecadCli() {
  if (!fs.existsSync(forgeCli)) return;
  let src = fs.readFileSync(forgeCli, "utf8");
  let changed = false;

  const meshExportNeedle = `async function runMeshExportCli(format, argv) {
  const { scriptPath, outputPath, quality, backend } = parseArgs7(argv);
  const code = (await import("fs")).readFileSync(resolve23(scriptPath), "utf-8");
  const { allFiles, fileName, readBinaryFile } = collectProjectFiles(scriptPath);
  await initKernel();`;

  const meshExportPatched = meshExportNeedle.replace("await initKernel();", "await init();");

  if (src.includes(meshExportNeedle)) {
    src = src.replace(meshExportNeedle, meshExportPatched);
    changed = true;
  }

  const badImport = `"../../../../solver/pkg/solver.js"`;
  const goodImport = `"../solver/pkg/solver.js"`;
  if (src.includes(badImport)) {
    src = src.replaceAll(badImport, goodImport);
    changed = true;
  }

  if (changed) {
    fs.writeFileSync(forgeCli, src);
    console.log("ensure-forgecad-solver: patched dist-cli/forgecad.js for Node sketch export");
  }
}

if (!fs.existsSync(forgeRoot)) {
  console.warn("ensure-forgecad-solver: forgecad not installed yet — skip");
  process.exit(0);
}

installSolverPkg();
patchForgecadCli();
