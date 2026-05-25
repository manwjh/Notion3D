---
name: notion3d-review
description: >-
  Notion3D design review phase after STL render: check validation_warnings,
  part count vs plan, semantic fit vs user intent, decide pass/retry/accept_warnings.
  Use after notion3d_wait_job. Requires notion3d_report_design_review.
---

# Notion3D Review（设计验收）

Design Turn 第五阶段：**几何合法 ≠ 设计正确**。

## 必须检查

1. **Job / Version 的 `validation_warnings`**（壁厚、床尺寸、面数）
2. **装配语义**：`parts.json` 部件数、命名是否与 plan.summary 一致
3. **造型**：比例、穿插、明显胡编（经验判断）
4. **可制造性**：薄壁、尖底、超大悬空

## 读取数据

```
notion3d_get_job / notion3d_wait_job  → validation_warnings
notion3d_list_versions                → version + parts 数量
notion3d_get_design_state             → plan / design_phase
```

用户已在 Web 装配预览（部件树、半透明外壳）；你根据 warnings + plan 判断。

## report_design_review

| status | 含义 |
|--------|------|
| `pass` | 无问题，结束 turn |
| `accept_warnings` | 有 warnings 但用户可接受 |
| `retry` | 需修改；附 `retry_phase` |

retry 示例：

```json
{
  "status": "retry",
  "notes": ["plan 要求 5 件，实际仅 2 件；外壳未命名 Shell"],
  "retry_phase": "author"
}
```

## 迭代上限

- Engine 限制 **最多 2 次 retry**（`revision` 0→1→2）
- 第 2 次 retry 时 Web 对话区会出现「最后一次自动迭代」system 提示
- 第 3 次 retry 会被 API 拒绝，并提示手动编辑或重新描述需求

## 通过后

- 2–4 句中文总结版本、关键尺寸、部件数
- **不要**主动 save_template（模板库仅演示，不扩展）
