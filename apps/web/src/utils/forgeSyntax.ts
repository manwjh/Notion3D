function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

const KEYWORDS = new Set([
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
  "new",
  "typeof",
  "undefined",
]);

const FORGE_BUILTINS = new Set([
  "param",
  "importAssembly",
  "box",
  "cylinder",
  "sphere",
  "cone",
  "torus",
  "polyline",
  "polygon",
  "extrude",
  "revolve",
  "loft",
  "sweep",
  "union",
  "subtract",
  "intersect",
  "translate",
  "rotate",
  "scale",
  "mirror",
  "color",
  "material",
  "fillet",
  "chamfer",
  "shell",
  "pattern",
  "group",
]);

function wrap(className: string, text: string): string {
  return `<span class="${className}">${text}</span>`;
}

function highlightLine(line: string): string {
  if (!line) return "";

  let rest = line;
  let out = "";

  while (rest.length > 0) {
    let matched = false;

    const comment = rest.match(/^(\/\/.*)$/);
    if (comment) {
      out += wrap("forge-tok-comment", escapeHtml(comment[1]));
      break;
    }

    const ws = rest.match(/^(\s+)/);
    if (ws) {
      out += escapeHtml(ws[1]);
      rest = rest.slice(ws[1].length);
      continue;
    }

    const str =
      rest.match(/^("(?:\\.|[^"\\])*")/) ??
      rest.match(/^('(?:\\.|[^'\\])*')/) ??
      rest.match(/^(`(?:\\.|[^`\\])*`)/);
    if (str) {
      out += wrap("forge-tok-string", escapeHtml(str[1]));
      rest = rest.slice(str[1].length);
      continue;
    }

    const num = rest.match(/^(\d+(?:\.\d+)?)/);
    if (num) {
      out += wrap("forge-tok-number", escapeHtml(num[1]));
      rest = rest.slice(num[1].length);
      continue;
    }

    const ident = rest.match(/^([A-Za-z_]\w*)/);
    if (ident) {
      const word = ident[1];
      const next = rest.slice(word.length);
      if (KEYWORDS.has(word)) {
        out += wrap("forge-tok-keyword", escapeHtml(word));
      } else if (FORGE_BUILTINS.has(word)) {
        out += wrap("forge-tok-builtin", escapeHtml(word));
      } else if (/^\s*\(/.test(next)) {
        out += wrap("forge-tok-fn", escapeHtml(word));
      } else {
        out += wrap("forge-tok-ident", escapeHtml(word));
      }
      rest = next;
      continue;
    }

    out += escapeHtml(rest[0]);
    rest = rest.slice(1);
    matched = true;
    if (!matched) break;
  }

  return out;
}

export function highlightForgeCode(
  code: string,
  highlightLines?: { start: number; end: number } | null,
): string {
  const lines = code.split("\n");
  return lines
    .map((line, index) => {
      const lineNo = index + 1;
      const focused =
        highlightLines != null &&
        lineNo >= highlightLines.start &&
        lineNo <= highlightLines.end;
      const cls = focused ? "forge-line forge-line--focus" : "forge-line";
      return `<span class="${cls}">${highlightLine(line) || "\u200b"}</span>`;
    })
    .join("");
}

export function lineCount(code: string): number {
  if (!code) return 1;
  return code.split("\n").length;
}
