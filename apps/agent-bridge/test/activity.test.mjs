import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  createActivityCollector,
  toolActivityLabel,
  toolActivityDetail,
} from "../src/activity.js";

describe("activity", () => {
  it("labels notion3d tools", () => {
    assert.equal(toolActivityLabel("notion3d_render_forge"), "提交 ForgeCAD 渲染");
    assert.equal(toolActivityLabel("notion3d_wait_job"), "等待渲染完成");
  });

  it("extracts render detail from args", () => {
    assert.equal(
      toolActivityDetail("notion3d_render_forge", { label: "玩具小房子" }),
      "玩具小房子",
    );
  });

  it("collects tool_call lifecycle", () => {
    const collector = createActivityCollector();
    collector.ingest({
      type: "tool_call",
      call_id: "c1",
      name: "notion3d_render_forge",
      status: "running",
      args: { label: "box" },
    });
    collector.ingest({
      type: "tool_call",
      call_id: "c1",
      name: "notion3d_render_forge",
      status: "completed",
      args: { label: "box" },
    });
    const steps = collector.snapshot();
    assert.equal(steps.length, 1);
    assert.equal(steps[0].status, "done");
    assert.equal(steps[0].detail, "box");
  });
});
