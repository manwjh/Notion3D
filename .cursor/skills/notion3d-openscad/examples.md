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

---

## A 类：10:1 啮合齿轮副

**Prompt**：`设计一对齿轮，转速比 10:1`

策略：

- 齿数比 10:100（或 12:120 等），`module_mm` 参数化
- **渐开线齿廓** + 按中心距**啮合装配**（预览区应看到两齿轮咬合，不是分开摆放）
- 禁止简单梯形 polygon 近似齿形（会导致非封闭网格、预览像圆环）
- 大齿数时 `module_mm >= 1.5`，否则 3D 预览看不清齿

```openscad
module_mm = 1.5;
teeth_1 = 10;
teeth_2 = 100;
thickness = 8;
bore_d = 5;
hub_d = 14;
hub_h = 5;
pressure_angle = 20;
backlash = 0.08;
$fn = 48;

center_distance = module_mm * (teeth_1 + teeth_2) / 2;

function involute_pt(r_base, t) = [
  r_base * (cos(t) + t * sin(t)),
  r_base * (sin(t) - t * cos(t))
];

module tooth_space_2d(z) {
  m = module_mm;
  pa = pressure_angle;
  r_pitch = m * z / 2;
  r_base = r_pitch * cos(pa);
  r_outer = r_pitch + m;
  r_root = max(m * 0.8, r_pitch - 1.25 * m - backlash / 2);
  t_outer = sqrt(pow(r_outer / r_base, 2) - 1);
  t_root = sqrt(pow(max(r_root, r_base + 0.01) / r_base, 2) - 1);
  n = 10;
  half_angle = 360 / z / 4;
  flank = [
    for (i = [0:n])
      let(t = t_root + (t_outer - t_root) * i / n)
      involute_pt(r_base, t)
  ];
  root_pt = [r_root * cos(-half_angle), r_root * sin(-half_angle)];
  poly = concat(
    [root_pt],
    flank,
    [for (p = flank) [p[0], -p[1]]],
    [[r_root * cos(half_angle), r_root * sin(half_angle)]]
  );
  polygon(points = poly);
}

module gear_blank_2d(z) {
  m = module_mm;
  pa = pressure_angle;
  r_pitch = m * z / 2;
  r_root = max(m * 0.8, r_pitch - 1.25 * m - backlash / 2);
  union() {
    circle(r = r_root, $fn = z * 6);
    for (i = [0:z - 1])
      rotate([0, 0, i * 360 / z])
        tooth_space_2d(z);
  }
}

module spur_gear(z) {
  difference() {
    union() {
      linear_extrude(height = thickness)
        gear_blank_2d(z);
      if (hub_d > bore_d)
        cylinder(d = hub_d, h = hub_h, $fn = 48);
    }
    translate([0, 0, -0.5])
      cylinder(d = bore_d, h = thickness + hub_h + 1, $fn = 48);
  }
}

spur_gear(teeth_1);

translate([center_distance, 0, 0])
  rotate([0, 0, 180 / teeth_2])
    spur_gear(teeth_2);
```

**助手回复**：说明齿数、模数、中心距；给出 **web_url**；预览区应显示啮合状态。
