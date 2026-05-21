import type { ToolDef } from "../api/client";

export type { ToolDef };

export const FALLBACK_TOOLS: ToolDef[] = [
  {
    id: "parametric",
    track: "parametric",
    title: "参数化零件",
    description: "立方体、盒子、支架等可编辑几何体，OpenSCAD 参数化建模。",
    available: true,
    sample_prompts: ["20mm 立方体", "40×30×20mm 带孔盒子", "直径 30mm 圆柱"],
  },
  {
    id: "symbolic",
    track: "parametric",
    title: "装饰/地标",
    description: "铁塔、房子、logo 等简化轮廓，适合小尺寸装饰件。",
    available: true,
    sample_prompts: ["简化埃菲尔铁塔，高 100mm", "40×30×25mm 小房子，三角屋顶"],
  },
  {
    id: "name-sign",
    track: "template",
    title: "名牌/字牌",
    description: "大首字母 + 嵌入式姓名，一键生成打印用字牌。",
    available: true,
    sample_prompts: [],
  },
  {
    id: "mesh-character",
    track: "mesh",
    title: "角色/宠物造型",
    description: "卡通、动物、有机造型（mesh AI，即将接入）。",
    available: false,
    sample_prompts: [],
  },
  {
    id: "upload-stl",
    track: "mesh",
    title: "上传模型",
    description: "导入 STL，切片并发送到拓竹（即将支持）。",
    available: false,
    sample_prompts: [],
  },
];

export function getTool(id: string | undefined, tools = FALLBACK_TOOLS): ToolDef | undefined {
  return tools.find((t) => t.id === id);
}
