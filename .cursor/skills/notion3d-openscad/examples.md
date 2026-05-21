# Notion3D 建模示例

## A 类：30mm 立方体

**Prompt**：`20mm 立方体`

```openscad
$fn = 32;
size = 20;
cube([size, size, size], center = true);
```

**助手回复**：已生成立方体，边长 20mm，可在左侧预览并导出 STL。

---

## A 类：带孔盒子

**Prompt**：`40×30×20mm 盒子，中心通孔直径 10mm`

策略：`difference()` + 略高的 subtract 圆柱；`wall` 参数化。

---

## B 类：埃菲尔铁塔

**Prompt**：`搞个埃菲尔铁塔`

策略：

- 分类 B：lattice 四腿 + 平台 + 尖塔，总高约 80–120mm
- `$fn` 48，`wall = 1.6`
- **必须** multi-preview 验证
- 回复加：「简化装饰造型，非精细地标还原」

---

## C 类：卡通兔子（应拒绝并改写）

**Prompt**：`帮我画一只卡通兔子，独眼`

**不要**生成复杂 organic mesh 近似。

**建议回复**：

> OpenSCAD 适合几何体，不适合卡通角色。你可以试试：
> - 「25mm 兔子轮廓剪影徽章，厚 3mm」（B 类 2D extrude）
> - 「30mm 立方体」作为底座测试

---

## 迭代修改

**Prompt**：`把边长改成 40mm`（已有 cube SCAD）

在 Bridge 中会传入 `existing_scad`；只改参数或对应 `cube([...])`，输出**完整**文件。
