---
name: notion3d-intake
description: >-
  Notion3D design intake phase: clarify user intent, classify tasks as A/B/C,
  collect dimensions and constraints before planning. Use at the start of every
  Notion3D modeling turn or when requirements are ambiguous.
---

# Notion3D Intake（需求 intake）

Design Turn 第一阶段：**理解能否做、缺什么信息**。

## 输出

在脑中（或简短对用户）明确：

| 字段 | 说明 |
|------|------|
| task_class | A 装配/参数化 / B 装饰简化 / C 不适合 ForgeCAD |
| 关键尺寸 | mm，打印用途 |
| 缺失信息 | 需向用户追问的 1–2 项 |

## A / B / C 分类

| 类 | 示例 | 下一步 |
|----|------|--------|
| **A** | 多部件装配、盒子、支架、指定 mm | → plan |
| **B** | logo、地标轮廓、装饰造型 | → plan（注明装饰级） |
| **C** | 卡通、人脸、有机雕塑 | → plan(class=C)，**不 render** |

## 规则

- 用户闲聊 / 问怎么用 → `strategy=chat_only`，不进入 author
- 用户只改参数且已有 vN → 可跳过深 intake，直接 plan(template_edit)
- 缺宽度/高度/用途时 **先问再 plan**，不要猜尺寸
- 本阶段 **不要** 写 ForgeCAD，**不要** `render_forge`

## 完成后

进入 **notion3d-plan**，调用 `notion3d_report_design_plan`。
