export type ModelParam = {
  name: string;
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
};

const FORGE_PARAM_RE =
  /param\s*\(\s*["']([^"']+)["']\s*,\s*([\d.]+)(?:\s*,\s*\{\s*min\s*:\s*([\d.]+)\s*,\s*max\s*:\s*([\d.]+)(?:\s*,\s*unit\s*:\s*["']([^"']+)["'])?\s*\})?/g;

function forgeParams(code: string): ModelParam[] {
  const params: ModelParam[] = [];
  let m: RegExpExecArray | null;
  FORGE_PARAM_RE.lastIndex = 0;
  while ((m = FORGE_PARAM_RE.exec(code)) !== null) {
    const value = parseFloat(m[2]);
    const min = m[3] != null ? parseFloat(m[3]) : Math.max(0, value * 0.25);
    const max = m[4] != null ? parseFloat(m[4]) : Math.max(value * 3, 100);
    params.push({
      name: m[1],
      label: m[1],
      value,
      min,
      max,
      unit: m[5] ?? "mm",
    });
  }
  return params;
}

export function parseModelParams(code: string): ModelParam[] {
  return forgeParams(code);
}

export function setModelParam(code: string, name: string, value: number): string {
  const re = new RegExp(
    `(param\\s*\\(\\s*["']${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["']\\s*,\\s*)([\\d.]+)`,
  );
  if (!re.test(code)) return code;
  return code.replace(re, `$1${value}`);
}
