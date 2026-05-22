# Notion3D 模板库

OpenSCAD 模板以**数据**形式存放，Engine 只负责读取与渲染，不含领域逻辑。

## 目录

```
templates/
  builtin/{id}/     # 随仓库发布，已校验
    meta.json
    model.scad
data/templates/
  user/{id}/        # 用户 / Agent 另存（运行时生成）
    meta.json
    model.scad
```

## meta.json

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 与目录名一致，小写连字符 |
| `title` | 是 | 显示名称 |
| `description` | 否 | 简短说明 |
| `tags` | 否 | 检索标签 |
| `category` | 否 | 如 `basic` / `utility` / `mechanical` |
| `license` | 否 | 如 `MIT` |
| `source` | 否 | `notion3d-builtin` 或 `user` |
| `params` | 否 | `[{ "name", "label", "default", "unit" }]` |

## 内置模板一览

| ID | 分类 | 说明 |
|----|------|------|
| `parametric-cube` | basic | 参数化立方体 |
| `open-box` | basic | 开放式收纳盒 |
| `cable-clip` | utility | 线夹（卡扣式） |
| `box-with-hole` | utility | 带孔收纳盒 |
| `sd-card-box` | utility | SD 卡收纳盒 |
| `phone-stand` | utility | 手机支架 |
| `wall-hook` | utility | 壁挂挂钩 |
| `spacer-washer` | mechanical | 垫片 / 间隔圈 |
| `gear-pair-10-1` | mechanical | 10:1 啮合齿轮副 |

批量校验：`templates/scripts/validate-all.sh`

## 约束

- 单文件自包含，禁止 `import` / `include` 外部路径
- 可调参数放在 SCAD 顶部（`name = 数值;`）
- 提交内置库前运行 `templates/scripts/validate-all.sh`

## API

- `GET /api/templates` — 列表（`tag` / `category` / `scope` 过滤）
- `GET /api/templates/{id}` — 详情含 SCAD
- `POST /api/templates/{id}/apply` — 应用到项目（可新建项目）
- `POST /api/projects/{id}/versions/{v}/save-template` — 另存到用户库
