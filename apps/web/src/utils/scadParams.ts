export type ScadParam = {
  name: string;
  value: number;
  lineIndex: number;
};

const ASSIGN_RE = /^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([\d.]+)\s*;\s*(?:\/\/.*)?$/;

/** 解析 SCAD 顶部数值参数（module/difference 之前） */
export function parseScadParams(code: string): ScadParam[] {
  const lines = code.split("\n");
  const params: ScadParam[] = [];
  const stopRe = /^\s*(module|function|difference|union|intersection|minkowski|hull)\s*\(/;

  for (let i = 0; i < lines.length; i++) {
    if (stopRe.test(lines[i])) break;
    const m = lines[i].match(ASSIGN_RE);
    if (m) {
      params.push({ name: m[1], value: parseFloat(m[2]), lineIndex: i });
    }
  }
  return params;
}

export function setScadParam(code: string, name: string, value: number): string {
  const lines = code.split("\n");
  const re = new RegExp(`^(${name}\\s*=\\s*)([\\d.]+)(\\s*;)`);
  for (let i = 0; i < lines.length; i++) {
    if (re.test(lines[i])) {
      lines[i] = lines[i].replace(re, `$1${value}$3`);
      return lines.join("\n");
    }
  }
  return code;
}

export function friendlyParamLabel(name: string): string {
  const map: Record<string, string> = {
    w: "宽度",
    width: "宽度",
    h: "高度",
    height: "高度",
    d: "深度",
    depth: "深度",
    l: "长度",
    length: "长度",
    r: "半径",
    radius: "半径",
    hole_r: "孔半径",
    hole_d: "孔直径",
    wall: "壁厚",
    t: "壁厚",
    thickness: "壁厚",
    teeth: "齿数",
    module_mm: "模数",
    module: "模数",
  };
  return map[name] ?? name;
}
