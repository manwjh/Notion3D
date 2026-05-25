import {
  friendlyParamLabel,
  parseScadParams,
  setScadParam,
  type ScadParam,
} from "./scadParams";

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

export type SourceBackend = "forge" | "scad";

export function detectSourceBackend(code: string): SourceBackend | null {
  const trimmed = code.trim();
  if (!trimmed) return null;
  if (/\bparam\s*\(/.test(trimmed)) return "forge";
  if (/^\s*[a-zA-Z_][\w]*\s*=\s*[\d.]+/m.test(trimmed)) return "scad";
  if (/\b(module|difference|union)\s*\(/.test(trimmed)) return "scad";
  if (/\b(return|box|cylinder|sphere)\b/.test(trimmed)) return "forge";
  return null;
}

export function backendFromCadBackend(cadBackend: string | null | undefined): SourceBackend {
  if (cadBackend === "openscad_legacy") return "scad";
  return "forge";
}

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

function scadToModelParams(scad: ScadParam[]): ModelParam[] {
  return scad.map((p) => ({
    name: p.name,
    label: friendlyParamLabel(p.name),
    value: p.value,
    min: 0,
    max: Math.max(p.value * 3, 100),
    unit: "mm",
  }));
}

export function parseModelParams(code: string, backend?: SourceBackend | null): ModelParam[] {
  const kind = backend ?? detectSourceBackend(code);
  if (kind === "forge") return forgeParams(code);
  if (kind === "scad") return scadToModelParams(parseScadParams(code));
  return [];
}

export function setModelParam(
  code: string,
  name: string,
  value: number,
  backend?: SourceBackend | null,
): string {
  const kind = backend ?? detectSourceBackend(code);
  if (kind === "forge") {
    const re = new RegExp(
      `(param\\s*\\(\\s*["']${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}["']\\s*,\\s*)([\\d.]+)`,
    );
    if (!re.test(code)) return code;
    return code.replace(re, `$1${value}`);
  }
  return setScadParam(code, name, value);
}
