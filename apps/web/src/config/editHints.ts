/** 语义部位 — 普通人改模型时用，无需 3D 点选 */
export const EDIT_REGIONS = [
  { id: "whole", label: "整体", prefix: "整体" },
  { id: "top", label: "顶部", prefix: "顶部" },
  { id: "bottom", label: "底部", prefix: "底部" },
  { id: "hole", label: "孔", prefix: "孔" },
  { id: "wall", label: "壁/侧面", prefix: "侧面壁厚" },
  { id: "edge", label: "边缘/圆角", prefix: "边缘圆角" },
] as const;

/** 有模型后的快捷修改建议（点击填入输入框） */
export const EDIT_HINTS = [
  "孔加大一点",
  "整体缩小 10%",
  "壁厚加厚到 2mm",
  "顶部加圆角",
  "高度增加 5mm",
] as const;

export type EditRegionId = (typeof EDIT_REGIONS)[number]["id"];
