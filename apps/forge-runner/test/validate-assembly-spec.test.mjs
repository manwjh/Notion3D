import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { validateAssemblySpec } from "../validate-assembly-spec.mjs";
import { validateAssemblyParts } from "../validate-assembly.mjs";

const PREFIX = "装配校验：";

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

describe("validateAssemblySpec", () => {
  it("flags child outside parent contains", () => {
    const parts = [
      part("CaseShell", [0, 0, 0], [40, 20, 60]),
      part("FlintWheel", [80, 0, 30], [90, 10, 40]),
    ];
    const spec = [
      { id: "CaseShell", role: "shell", contains: ["FlintWheel"] },
      { id: "FlintWheel", role: "internal", anchor: "Chimney" },
      { id: "Chimney", role: "internal" },
    ];
    const warnings = validateAssemblySpec(parts, spec, PREFIX);
    assert.ok(warnings.some((w) => w.includes("FlintWheel") && w.includes("contains")));
  });

  it("flags missing anchor proximity", () => {
    const parts = [
      part("Chimney", [0, 0, 40], [10, 10, 60]),
      part("FlintWheel", [50, 0, 0], [60, 10, 10]),
    ];
    const spec = [
      { id: "Chimney", role: "internal" },
      { id: "FlintWheel", role: "internal", anchor: "Chimney" },
    ];
    const warnings = validateAssemblySpec(parts, spec, PREFIX);
    assert.ok(warnings.some((w) => w.includes("FlintWheel") && w.includes("anchor")));
  });

  it("accepts valid contains layout", () => {
    const parts = [
      part("Shell", [0, 0, 0], [40, 40, 90]),
      part("Motor", [8, 8, 10], [20, 20, 38]),
      part("Battery", [9, 9, 12], [27, 27, 48]),
    ];
    const spec = [
      { id: "Shell", role: "shell", contains: ["Motor", "Battery"] },
      { id: "Motor", role: "internal" },
      { id: "Battery", role: "internal" },
    ];
    const warnings = validateAssemblySpec(parts, spec, PREFIX);
    assert.equal(warnings.length, 0);
  });
});

describe("validateAssemblyParts with assembly_spec", () => {
  it("merges spec warnings with heuristics", () => {
    const parts = [
      part("CaseShell", [0, 0, 0], [40, 20, 60]),
      part("Insert", [2, 2, 2], [38, 18, 58]),
      part("FlintWheel", [80, 0, 30], [90, 10, 40]),
    ];
    const assemblySpec = [
      { id: "CaseShell", role: "shell", contains: ["Insert", "FlintWheel"] },
      { id: "Insert", role: "internal" },
      { id: "FlintWheel", role: "internal" },
    ];
    const result = validateAssemblyParts(parts, { assemblySpec });
    assert.ok(result.warnings.some((w) => w.includes("FlintWheel") && w.includes("contains")));
  });
});
