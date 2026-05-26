import type { ModelPart, PartSourceRef } from "../types/parts";
import { parseModelParams } from "./modelParams";

export type ForgeSources = {
  main: string;
  files: Record<string, string>;
};

export type PartCodeFocus = {
  partId: string;
  partLabel: string;
  shapeVar: string | null;
  snippet: string;
  relatedParamNames: string[];
  sourceFile: string;
  sourceLabel: string;
  highlightLines: { start: number; end: number };
  editableBlock: { start: number; end: number; text: string } | null;
};

const JS_KEYWORDS = new Set([
  "const",
  "let",
  "var",
  "function",
  "return",
  "if",
  "else",
  "for",
  "while",
  "true",
  "false",
  "null",
  "param",
  "new",
  "typeof",
  "undefined",
  "importAssembly",
]);

export function slugifyPartName(name: string): string {
  return (
    name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 48) || "part"
  );
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function lineNumberAt(code: string, offset: number): number {
  return code.slice(0, offset).split("\n").length;
}

function lineRange(code: string, start: number, end: number): { start: number; end: number } {
  return {
    start: lineNumberAt(code, start),
    end: lineNumberAt(code, Math.max(start, end - 1)),
  };
}

function sourceLabel(fileKey: string): string {
  return fileKey === "__main__" ? "model.forge.js" : `src/${fileKey}`;
}

function fileKeyFromRef(ref: PartSourceRef): string {
  if (ref.file === "model.forge.js") return "__main__";
  return ref.file.replace(/^src\//, "");
}

function extractReturnExpression(source: string): { preamble: string; expr: string; returnStart: number } | null {
  const match = source.match(/return\s+([\s\S]+?)\s*;?\s*$/);
  if (!match || match.index == null) return null;
  return {
    preamble: source.slice(0, match.index).trimEnd(),
    expr: match[1].trim().replace(/;\s*$/, ""),
    returnStart: match.index,
  };
}

type ReturnEntry = { name: string; shapeRef: string | null; shapeExpr: string };

function parseReturnEntries(expr: string): ReturnEntry[] {
  const entries: ReturnEntry[] = [];
  const re = /\{\s*name\s*:\s*["']([^"']+)["']\s*,\s*shape\s*:\s*([^,}\n]+)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(expr)) !== null) {
    const shapeExpr = m[2].trim();
    const shapeRef = /^\w+$/.test(shapeExpr) ? shapeExpr : null;
    entries.push({ name: m[1], shapeRef, shapeExpr });
  }
  return entries;
}

function findMatchingEntry(entries: ReturnEntry[], part: ModelPart): ReturnEntry | null {
  return (
    entries.find(
      (entry) =>
        slugifyPartName(entry.name) === part.id ||
        entry.name === part.label ||
        entry.name.toLowerCase() === part.label.toLowerCase(),
    ) ?? null
  );
}

function findStatementEnd(source: string, start: number): number {
  const eqIdx = source.indexOf("=", start);
  const from = eqIdx >= 0 ? eqIdx + 1 : start;
  let depth = 0;
  let inString: string | null = null;

  for (let i = from; i < source.length; i += 1) {
    const ch = source[i];
    if (inString) {
      if (ch === inString && source[i - 1] !== "\\") inString = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === "`") {
      inString = ch;
      continue;
    }
    if (ch === "(" || ch === "[" || ch === "{") depth += 1;
    else if (ch === ")" || ch === "]" || ch === "}") depth -= 1;
    else if (ch === ";" && depth === 0) return i + 1;
  }
  return source.length;
}

function findVariableDefinition(
  source: string,
  varName: string,
): { start: number; end: number; text: string } | null {
  const re = new RegExp(`(?:^|\\n)((?:const|let|var)\\s+${escapeRegExp(varName)}\\s*=)`);
  const m = re.exec(source);
  if (!m) return null;
  const start = m.index + (m[0].startsWith("\n") ? 1 : 0);
  const end = findStatementEnd(source, start);
  return { start, end, text: source.slice(start, end).trim() };
}

function findFunctionDefinition(
  source: string,
  names: string[],
): { start: number; end: number; text: string } | null {
  for (const name of names) {
    const re = new RegExp(`(?:^|\\n)(function\\s+${escapeRegExp(name)}\\s*\\([^)]*\\)\\s*\\{)`);
    const m = re.exec(source);
    if (!m) continue;
    const start = m.index + (m[0].startsWith("\n") ? 1 : 0);
    let depth = 0;
    let inString: string | null = null;
    for (let i = start; i < source.length; i += 1) {
      const ch = source[i];
      if (inString) {
        if (ch === inString && source[i - 1] !== "\\") inString = null;
        continue;
      }
      if (ch === '"' || ch === "'" || ch === "`") {
        inString = ch;
        continue;
      }
      if (ch === "{") depth += 1;
      else if (ch === "}") {
        depth -= 1;
        if (depth === 0) {
          const end = i + 1;
          return { start, end, text: source.slice(start, end).trim() };
        }
      }
    }
  }
  return null;
}

function candidateFunctionNames(part: ModelPart, shapeVar: string | null): string[] {
  const names = new Set<string>();
  if (shapeVar) names.add(shapeVar);
  names.add(slugifyPartName(part.label));
  names.add(slugifyPartName(part.id));
  const compact = part.label.replace(/[^a-zA-Z0-9]/g, "");
  if (compact) {
    names.add(`make${compact.charAt(0).toUpperCase()}${compact.slice(1)}`);
    names.add(`make${compact}`);
  }
  return [...names];
}

function collectIdentifiers(code: string): Set<string> {
  const ids = new Set<string>();
  const re = /\b([a-zA-Z_]\w*)\b/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(code)) !== null) {
    if (!JS_KEYWORDS.has(m[1])) ids.add(m[1]);
  }
  return ids;
}

function relatedParamsForSnippet(code: string, snippet: string): string[] {
  const all = parseModelParams(code);
  return all
    .filter((param) => {
      const re = new RegExp(`param\\s*\\(\\s*["']${escapeRegExp(param.name)}["']`);
      return re.test(snippet);
    })
    .map((param) => param.name);
}

function resolveImportFile(source: string, shapeRef: string | null): string | null {
  if (!shapeRef) return null;
  const re = new RegExp(
    `(?:const|let|var)\\s+${escapeRegExp(shapeRef)}\\s*=\\s*importAssembly\\s*\\(\\s*["']src\\/([^"']+)["']\\s*\\)`,
  );
  const m = re.exec(source);
  return m?.[1] ?? null;
}

function buildFocus(
  source: string,
  fileKey: string,
  part: ModelPart,
  entry: ReturnEntry | null,
  blocks: string[],
  editableBlock: { start: number; end: number; text: string } | null,
  shapeVar: string | null,
): PartCodeFocus {
  const returnSnippet = entry
    ? entry.shapeRef
      ? `{ name: "${entry.name}", shape: ${entry.shapeRef} }`
      : `{ name: "${entry.name}", shape: ${entry.shapeExpr} }`
    : null;

  const snippet =
    blocks.length > 0
      ? returnSnippet
        ? `${blocks.join("\n\n")}\n\n// return 片段\n${returnSnippet}`
        : blocks.join("\n\n")
      : returnSnippet
        ? `// return 片段\n${returnSnippet}`
        : source.trim();

  const highlightStart = editableBlock?.start ?? 0;
  const highlightEnd = editableBlock?.end ?? source.length;
  const combinedCode = source;

  return {
    partId: part.id,
    partLabel: part.label,
    shapeVar,
    snippet,
    relatedParamNames: relatedParamsForSnippet(combinedCode, snippet),
    sourceFile: fileKey,
    sourceLabel: sourceLabel(fileKey),
    highlightLines: lineRange(source, highlightStart, highlightEnd),
    editableBlock,
  };
}

function focusBySourceRef(
  sources: ForgeSources,
  part: ModelPart,
  ref: PartSourceRef,
): PartCodeFocus | null {
  const fileKey = fileKeyFromRef(ref);
  const source = fileKey === "__main__" ? sources.main : sources.files[fileKey];
  if (!source) return null;

  if (ref.symbol) {
    const varDef = findVariableDefinition(source, ref.symbol);
    if (varDef) {
      return buildFocus(source, fileKey, part, null, [varDef.text], varDef, ref.symbol);
    }
    const fnDef = findFunctionDefinition(source, [ref.symbol]);
    if (fnDef) {
      return buildFocus(source, fileKey, part, null, [fnDef.text], fnDef, ref.symbol);
    }
  }

  if (ref.start_line > 0 && ref.end_line >= ref.start_line) {
    const lines = source.split("\n");
    const text = lines.slice(ref.start_line - 1, ref.end_line).join("\n").trim();
    if (text) {
      let offset = 0;
      for (let i = 0; i < ref.start_line - 1; i += 1) offset += lines[i].length + 1;
      const endOffset = offset + text.length;
      return buildFocus(
        source,
        fileKey,
        part,
        null,
        [text],
        { start: offset, end: endOffset, text },
        ref.symbol,
      );
    }
  }

  return focusPartCodeInFile(source, part, fileKey);
}

function collectDefinitionBlocks(preamble: string, shapeVar: string): {
  blocks: string[];
  editableBlock: { start: number; end: number; text: string } | null;
} {
  const blocks: string[] = [];
  const seenVars = new Set<string>();
  let editableBlock: { start: number; end: number; text: string } | null = null;

  function addDefinition(varName: string, primary = false) {
    if (seenVars.has(varName)) return;
    seenVars.add(varName);
    const fnNames = [varName];
    const fnDef = findFunctionDefinition(preamble, fnNames);
    if (fnDef) {
      blocks.push(fnDef.text);
      if (primary) editableBlock = fnDef;
      return;
    }
    const def = findVariableDefinition(preamble, varName);
    if (!def) return;
    blocks.push(def.text);
    if (primary) editableBlock = def;
    for (const dep of collectIdentifiers(def.text)) {
      if (dep !== varName) addDefinition(dep, false);
    }
  }

  addDefinition(shapeVar, true);
  return { blocks, editableBlock };
}

export function focusPartCodeInFile(
  source: string,
  part: ModelPart,
  fileKey: string,
): PartCodeFocus | null {
  const trimmed = source.trim();
  if (!trimmed) return null;

  const ret = extractReturnExpression(trimmed);
  if (!ret) {
    if (fileKey !== "__main__") {
      const fnDef = findFunctionDefinition(trimmed, candidateFunctionNames(part, null));
      if (fnDef) {
        return buildFocus(trimmed, fileKey, part, null, [fnDef.text], fnDef, null);
      }
      const whole = { start: 0, end: trimmed.length, text: trimmed };
      return buildFocus(trimmed, fileKey, part, null, [trimmed], whole, null);
    }
    return null;
  }

  const entry = findMatchingEntry(parseReturnEntries(ret.expr), part);
  if (!entry) {
    if (fileKey !== "__main__") {
      const fnDef = findFunctionDefinition(trimmed, candidateFunctionNames(part, null));
      if (fnDef) {
        return buildFocus(trimmed, fileKey, part, null, [fnDef.text], fnDef, null);
      }
    }
    return null;
  }

  if (entry.shapeRef) {
    const { blocks, editableBlock } = collectDefinitionBlocks(ret.preamble, entry.shapeRef);
    return buildFocus(trimmed, fileKey, part, entry, blocks, editableBlock, entry.shapeRef);
  }

  const inlineStart = ret.returnStart;
  const inlineEnd = trimmed.length;
  const inlineText = trimmed.slice(inlineStart).trim();
  return buildFocus(
    trimmed,
    fileKey,
    part,
    entry,
    [inlineText],
    { start: inlineStart, end: inlineEnd, text: inlineText },
    null,
  );
}

export function focusPartInSources(sources: ForgeSources, part: ModelPart): PartCodeFocus | null {
  if (part.source_ref) {
    const fromRef = focusBySourceRef(sources, part, part.source_ref);
    if (fromRef) return fromRef;
  }

  const mainFocus = focusPartCodeInFile(sources.main, part, "__main__");
  if (mainFocus?.shapeVar) {
    const importFile = resolveImportFile(sources.main, mainFocus.shapeVar);
    if (importFile && sources.files[importFile]) {
      const subSource = sources.files[importFile];
      const subFocus =
        focusPartCodeInFile(subSource, part, importFile) ??
        buildFocus(
          subSource,
          importFile,
          part,
          null,
          [subSource.trim()],
          { start: 0, end: subSource.length, text: subSource.trim() },
          mainFocus.shapeVar,
        );
      return subFocus;
    }
  }
  if (mainFocus) return mainFocus;

  for (const [fileKey, fileSource] of Object.entries(sources.files)) {
    const focus = focusPartCodeInFile(fileSource, part, fileKey);
    if (focus) return focus;
  }

  return null;
}

/** @deprecated Use focusPartInSources */
export function focusPartCode(code: string, part: ModelPart): PartCodeFocus | null {
  return focusPartInSources({ main: code, files: {} }, part);
}

export function replaceRange(code: string, start: number, end: number, replacement: string): string {
  return code.slice(0, start) + replacement + code.slice(end);
}

export function applyPartBlockEdit(
  sources: ForgeSources,
  focus: PartCodeFocus,
  newBlockText: string,
): ForgeSources {
  if (!focus.editableBlock) return sources;
  const trimmed = newBlockText.trim();
  if (!trimmed) return sources;

  if (focus.sourceFile === "__main__") {
    return {
      main: replaceRange(
        sources.main,
        focus.editableBlock.start,
        focus.editableBlock.end,
        trimmed,
      ),
      files: sources.files,
    };
  }

  const prev = sources.files[focus.sourceFile] ?? "";
  return {
    main: sources.main,
    files: {
      ...sources.files,
      [focus.sourceFile]: replaceRange(prev, focus.editableBlock.start, focus.editableBlock.end, trimmed),
    },
  };
}

export function resolvePartSourceRef(
  mainSource: string,
  partName: string,
  partId: string,
  srcFiles: Record<string, string> = {},
): PartSourceRef | null {
  const part: ModelPart = {
    id: partId,
    label: partName,
    color: "#000000",
    stl_url: "",
  };
  const focus = focusPartInSources({ main: mainSource, files: srcFiles }, part);
  if (!focus) return null;
  return {
    file: focus.sourceLabel,
    symbol: focus.shapeVar,
    start_line: focus.highlightLines.start,
    end_line: focus.highlightLines.end,
  };
}
