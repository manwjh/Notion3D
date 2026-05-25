# Notion3D 模板库

## 目录

```
templates/builtin/{id}/
  meta.json
  model.forge.js
data/templates/user/{id}/    # 用户另存
```

## 内置模板

| ID | 说明 |
|----|------|
| `hello-assembly` | 5 部件装配 demo |
| `open-enclosure` | 参数化敞口盒 |

## 校验

```bash
bash templates/scripts/validate-all.sh
```

## API

- `GET /api/templates?scope=builtin|user|all`
- `POST /api/templates/{id}/apply`
