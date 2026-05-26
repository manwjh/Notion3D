import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { extractReturnExpression } from "../part-source.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runnerRoot = path.resolve(__dirname, "..");
const modelS = path.resolve(runnerRoot, "test/fixtures/model-s.forge.js");

test("extractReturnExpression uses final return, not inner IIFE returns", () => {
  const source = fs.readFileSync(modelS, "utf8");
  const ret = extractReturnExpression(source);
  assert.ok(ret);
  assert.match(ret.expr, /^\[/);
  assert.match(ret.expr, /BodyShell/);
  assert.doesNotMatch(ret.expr, /sk\.solve/);
  assert.match(ret.preamble, /return sk\.solve\(\)/);
});

test("export-parts emits distinct per-part STLs for multi-part script", () => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "notion3d-export-"));
  const script = path.join(outDir, "model.forge.js");
  fs.copyFileSync(modelS, script);

  const result = spawnSync(process.execPath, [path.join(runnerRoot, "export-parts.mjs"), script, outDir], {
    encoding: "utf8",
    cwd: runnerRoot,
  });
  assert.equal(result.status, 0, result.stderr || result.stdout);

  const hashes = new Set(
    fs
      .readdirSync(path.join(outDir, "parts"))
      .filter((name) => name.endsWith(".stl"))
      .map((name) => fs.readFileSync(path.join(outDir, "parts", name)).length),
  );
  assert.ok(hashes.size > 1, "expected distinct part STL sizes");
});
