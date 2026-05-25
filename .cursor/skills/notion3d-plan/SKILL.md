---
name: notion3d-plan
description: >-
  Notion3D design planning phase: choose from_scratch vs version edit vs demo
  template_apply, document assumptions. Use after intake and before writing
  ForgeCAD. Requires notion3d_report_design_plan MCP tool.
---

# Notion3D Plan（建模计划）

Design Turn 第二阶段：**决定怎么做，而不是怎么做形**。

## 默认路径（主流程）

| 情况 | strategy |
|------|----------|
| 有上一版 version | 基于 `model.forge.js` 修改（plan 写 summary + 变更点） |
| 新物件、无合适底稿 | `from_scratch` |
| 用户点名 hello-assembly / open-enclosure 演示 | `template_apply` |

**不要**每个请求都 `list_templates`。内置模板库**仅演示**，当前阶段不扩展。

仅在 `template_apply` 或需参考结构时：

```
notion3d_get_template(id)   # hello-assembly / open-enclosure
```

Legacy SCAD：`scope=legacy`（齿轮等，非主路径）

## strategy 说明

| strategy | 何时用 |
|----------|--------|
| `from_scratch` | **默认** — 写新 ForgeCAD 装配 |
| `template_edit` | 以某 demo 模板 forge_code 为底改结构（少见） |
| `template_apply` | 用户明确要求演示模板 + 改参 |
| `chat_only` | 不建模，只对话 |

## 禁止

- 无必要地检索/扩展模板库
- plan 里写完整 forge 代码
- 新模型走 `render_scad`（除非 legacy 模板）

## report_design_plan 示例

```json
{
  "task_class": "A",
  "summary": "90mm 五部件装配（外壳+电机+电池+PCB+线圈）",
  "strategy": "from_scratch",
  "assumptions": ["多部件可点选", "外壳半透明预览"]
}
```

## 完成后

→ **notion3d-forge-author**
