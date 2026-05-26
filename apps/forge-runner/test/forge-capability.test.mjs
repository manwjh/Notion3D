import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  analyzeForgeCapability,
  countFeatures,
  CAPABILITY_GAP_PREFIX,
} from "../forge-capability.mjs";

describe("forge-capability", () => {
  it("detects sketch_extrude_shell features", () => {
    const source = `
      const sk = constrainedSketch();
      const body = sk.solve().extrude(5).subtract(box(1,1,1));
      return [{ name: "CaseShell", shape: body }];
    `;
    const features = countFeatures(source);
    assert.ok(features.constrainedSketch >= 1);
    assert.ok(features.extrude >= 1);
    assert.ok(features.subtract >= 1);
  });

  it("flags missing recipe features", () => {
    const source = `return [{ name: "CaseShell", shape: box(10,10,10) }];`;
    const report = analyzeForgeCapability({
      forgeSource: source,
      geometryRecipes: [{ part_id: "CaseShell", recipe: "sketch_extrude_shell" }],
      designIntent: { task_class: "A", fidelity: "printable" },
    });
    assert.ok(report.gaps.some((g) => g.startsWith(CAPABILITY_GAP_PREFIX)));
    assert.ok(report.gaps.some((g) => g.includes("CaseShell")));
  });

  it("does not flag sphere stacking when no recipes declared", () => {
    const spheres = Array.from({ length: 8 }, (_, i) => `sphere(${i + 1})`).join(";");
    const source = `return [{ name: "Body", shape: ${spheres} }];`;
    const report = analyzeForgeCapability({
      forgeSource: source,
      geometryRecipes: [],
      designIntent: { task_class: "A" },
    });
    assert.equal(report.gaps.length, 0);
  });

  it("recognizes advanced modeling strengths", () => {
    const source = `
      const hull = loft([box(1,1,1), box(2,2,2)], [0, 10]);
      return [{ name: "Hull", shape: hull.fillet(1) }];
    `;
    const report = analyzeForgeCapability({
      forgeSource: source,
      geometryRecipes: [{ part_id: "Hull", recipe: "loft" }],
      designIntent: {},
    });
    assert.equal(report.advanced_modeling, true);
    assert.ok(report.strengths.includes("放样"));
    assert.equal(report.gaps.length, 0);
  });
});
