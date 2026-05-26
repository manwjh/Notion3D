import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { validateAssemblyParts } from "../validate-assembly.mjs";

function part(label, min, max) {
  const center = [
    (min[0] + max[0]) / 2,
    (min[1] + max[1]) / 2,
    (min[2] + max[2]) / 2,
  ];
  const size = [max[0] - min[0], max[1] - min[1], max[2] - min[2]];
  return {
    id: label.toLowerCase(),
    label,
    bbox: { min, max, center, size },
  };
}

describe("validateAssemblyParts", () => {
  it("skips checks for fewer than 3 parts", () => {
    const result = validateAssemblyParts([
      part("Shell", [0, 0, 0], [40, 20, 60]),
      part("Motor", [5, 5, 5], [15, 15, 25]),
    ]);
    assert.equal(result.warnings.length, 0);
  });

  it("flags orphan parts far from assembly center", () => {
    const result = validateAssemblyParts([
      part("CaseShell", [0, 0, 0], [40, 20, 60]),
      part("Insert", [2, 2, 2], [38, 18, 58]),
      part("FlintWheel", [80, 0, 30], [90, 10, 40]),
    ]);
    assert.ok(result.warnings.some((w) => w.includes("FlintWheel") && w.includes("远离装配主体")));
  });

  it("flags internal parts outside shell bbox", () => {
    const result = validateAssemblyParts([
      part("CaseShell", [0, 0, 0], [40, 20, 60]),
      part("Chimney", [45, 0, 30], [55, 10, 50]),
      part("Motor", [5, 5, 5], [15, 15, 25]),
    ]);
    assert.ok(result.warnings.some((w) => w.includes("Chimney") && w.includes("Shell 外")));
  });

  it("accepts compact hello-assembly-like layout", () => {
    const result = validateAssemblyParts([
      part("Shell", [0, 0, 0], [36, 36, 90]),
      part("Motor", [8, 8, 10], [20, 20, 38]),
      part("Battery", [9, 9, 12], [27, 27, 48]),
      part("PCB", [20, 6, 40], [30, 34, 42]),
    ]);
    assert.equal(result.warnings.length, 0);
  });
});
