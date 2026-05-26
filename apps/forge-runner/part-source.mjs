#!/usr/bin/env node
/**
 * Resolve ForgeCAD source location for an assembly part (used by export-parts.mjs).
 */

function slugify(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48) || "part";
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function lineNumberAt(code, offset) {
  return code.slice(0, offset).split("\n").length;
}

export function extractReturnExpression(source) {
  const trimmed = source.trimEnd();
  const returnIdx = trimmed.lastIndexOf("return");
  if (returnIdx === -1) return null;
  const tail = trimmed.slice(returnIdx);
  const match = tail.match(/^return\s+([\s\S]+?)\s*;?\s*$/);
  if (!match) return null;
  return {
    preamble: trimmed.slice(0, returnIdx).trimEnd(),
    expr: match[1].trim().replace(/;\s*$/, ""),
    returnStart: returnIdx,
  };
}

function parseReturnEntries(expr) {
  const entries = [];
  const re = /\{\s*name\s*:\s*["']([^"']+)["']\s*,\s*shape\s*:\s*([^,}\n]+)/g;
  let m;
  while ((m = re.exec(expr)) !== null) {
    const shapeExpr = m[2].trim();
    entries.push({
      name: m[1],
      shapeRef: /^\w+$/.test(shapeExpr) ? shapeExpr : null,
    });
  }
  return entries;
}

function findMatchingEntry(entries, partName, partId) {
  return (
    entries.find(
      (entry) =>
        slugify(entry.name) === partId ||
        entry.name === partName ||
        entry.name.toLowerCase() === partName.toLowerCase(),
    ) ?? null
  );
}

function findStatementEnd(source, start) {
  const eqIdx = source.indexOf("=", start);
  const from = eqIdx >= 0 ? eqIdx + 1 : start;
  let depth = 0;
  let inString = null;
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

function findVariableDefinition(source, varName) {
  const re = new RegExp(`(?:^|\\n)((?:const|let|var)\\s+${escapeRegExp(varName)}\\s*=)`);
  const m = re.exec(source);
  if (!m) return null;
  const start = m.index + (m[0].startsWith("\n") ? 1 : 0);
  const end = findStatementEnd(source, start);
  return { start, end };
}

function findFunctionDefinition(source, names) {
  for (const name of names) {
    const re = new RegExp(`(?:^|\\n)(function\\s+${escapeRegExp(name)}\\s*\\([^)]*\\)\\s*\\{)`);
    const m = re.exec(source);
    if (!m) continue;
    const start = m.index + (m[0].startsWith("\n") ? 1 : 0);
    let depth = 0;
    let inString = null;
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
        if (depth === 0) return { start, end: i + 1 };
      }
    }
  }
  return null;
}

function candidateFunctionNames(partName, partId, shapeVar) {
  const names = new Set();
  if (shapeVar) names.add(shapeVar);
  names.add(slugify(partName));
  names.add(slugify(partId));
  const compact = partName.replace(/[^a-zA-Z0-9]/g, "");
  if (compact) {
    names.add(`make${compact.charAt(0).toUpperCase()}${compact.slice(1)}`);
    names.add(`make${compact}`);
  }
  return [...names];
}

function resolveImportFile(preamble, shapeRef) {
  const re = new RegExp(
    `(?:const|let|var)\\s+${escapeRegExp(shapeRef)}\\s*=\\s*importAssembly\\s*\\(\\s*["']src\\/([^"']+)["']\\s*\\)`,
  );
  const m = re.exec(preamble);
  return m?.[1] ?? null;
}

function resolveBlockInFile(source, partName, partId, shapeRef) {
  const trimmed = source.trim();
  if (!trimmed) return null;

  const ret = extractReturnExpression(trimmed);
  if (!ret) {
    const fnDef = findFunctionDefinition(trimmed, candidateFunctionNames(partName, partId, shapeRef));
    if (fnDef) return { block: fnDef, symbol: shapeRef };
    return { block: { start: 0, end: trimmed.length }, symbol: null };
  }

  const entry = findMatchingEntry(parseReturnEntries(ret.expr), partName, partId);
  if (entry?.shapeRef) {
    let block = findVariableDefinition(ret.preamble, entry.shapeRef);
    if (!block) {
      block = findFunctionDefinition(
        ret.preamble,
        candidateFunctionNames(partName, partId, entry.shapeRef),
      );
    }
    if (block) return { block, symbol: entry.shapeRef };
  }

  if (shapeRef) {
    let block = findVariableDefinition(ret.preamble, shapeRef);
    if (!block) {
      block = findFunctionDefinition(ret.preamble, candidateFunctionNames(partName, partId, shapeRef));
    }
    if (block) return { block, symbol: shapeRef };
  }

  const fnDef = findFunctionDefinition(trimmed, candidateFunctionNames(partName, partId, shapeRef));
  if (fnDef) return { block: fnDef, symbol: shapeRef };

  // Single-shape submodule (typical importAssembly target)
  return { block: { start: 0, end: trimmed.length }, symbol: shapeRef };
}

function toSourceRef(file, source, block, symbol) {
  return {
    file,
    symbol: symbol ?? null,
    start_line: lineNumberAt(source, block.start),
    end_line: lineNumberAt(source, Math.max(block.start, block.end - 1)),
  };
}

/**
 * @param {string} mainSource
 * @param {string} partName
 * @param {string} partId
 * @param {Record<string, string>} [srcFiles]
 */
export function resolvePartSourceRef(mainSource, partName, partId, srcFiles = {}) {
  const trimmed = mainSource.trim();
  if (!trimmed) return null;

  const ret = extractReturnExpression(trimmed);
  if (!ret) return null;

  const entry = findMatchingEntry(parseReturnEntries(ret.expr), partName, partId);
  if (!entry?.shapeRef) return null;

  const importPath = resolveImportFile(ret.preamble, entry.shapeRef);
  if (importPath && srcFiles[importPath]) {
    const subSource = srcFiles[importPath];
    const resolved = resolveBlockInFile(subSource, partName, partId, entry.shapeRef);
    if (resolved) {
      return toSourceRef(`src/${importPath}`, subSource, resolved.block, resolved.symbol);
    }
  }

  let block = findVariableDefinition(ret.preamble, entry.shapeRef);
  if (!block) {
    block = findFunctionDefinition(
      ret.preamble,
      candidateFunctionNames(partName, partId, entry.shapeRef),
    );
  }
  if (!block) return null;

  return toSourceRef("model.forge.js", trimmed, block, entry.shapeRef);
}
