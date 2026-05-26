---
name: notion3d-review
description: >-
  Optional — report_design_review or natural-language handoff after render.
  validation_warnings are advisory only.
---

# Review（可选）

Engine 在 render 成功后会 **auto-complete** turn；显式 review 仅在需要记录时使用。

## 读

- `wait_job` → `validation_warnings`、`spatial_digest`
- `建模建议：` / `装配校验：` → **可选**改 forge，非必须 retry

## report_design_review（可选）

| status | 何时 |
|--------|------|
| pass | 用户满意 |
| accept_warnings | 用户接受已知简化 |
| retry | Agent 主动继续大改（revision ≤8） |

默认：用自然语言向用户说明结果即可。
