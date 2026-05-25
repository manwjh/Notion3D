"""Parse notion3d:part annotations and render isolated part STLs for element picking."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

PART_COMMENT_RE = re.compile(
    r"^\s*//\s*notion3d:part\s+(\S+)(?:\s+(.*?))?\s*$",
    re.MULTILINE,
)
COLOR_RE = re.compile(
    r'color\s*\(\s*["\']?(#[0-9A-Fa-f]{6}|[#0-9A-Za-z]+)["\']?\s*\)',
    re.IGNORECASE,
)
HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}")

DEFAULT_PART_COLORS = (
    "#E74C3C",
    "#3498DB",
    "#2ECC71",
    "#F39C12",
    "#9B59B6",
    "#1ABC9C",
)


@dataclass(frozen=True)
class ScadPart:
    id: str
    label: str
    color: str
    body: str
    line: int


def _parse_part_meta(part_id: str, rest: str | None, color_hint: str | None, index: int) -> tuple[str, str]:
    label = part_id.replace("_", " ")
    color = color_hint or DEFAULT_PART_COLORS[index % len(DEFAULT_PART_COLORS)]
    if not rest:
        return label, color

    tokens = rest.strip().split()
    label_tokens: list[str] = []
    for token in tokens:
        if HEX_COLOR_RE.fullmatch(token):
            color = token
            continue
        label_tokens.append(token)
    if label_tokens:
        label = " ".join(label_tokens)
    return label, color


def _scan_statement(lines: list[str], start: int) -> tuple[str, int]:
    """Collect OpenSCAD statements until the next notion3d:part comment."""
    chunks: list[str] = []
    depth = 0
    started = False
    i = start
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not started:
            if not stripped or stripped.startswith("//"):
                i += 1
                continue
            if PART_COMMENT_RE.match(raw):
                break
            started = True

        if started and PART_COMMENT_RE.match(raw):
            break

        code_line = raw.split("//", 1)[0]
        for ch in code_line:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth = max(0, depth - 1)
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth = max(0, depth - 1)

        chunks.append(raw.rstrip())
        i += 1
        if started and depth == 0 and stripped.endswith(";"):
            break

    return "\n".join(chunks).strip(), i


def parse_scad_parts(scad_code: str) -> tuple[str, list[ScadPart]]:
    """Return SCAD preamble and annotated parts (empty if none)."""
    matches = list(PART_COMMENT_RE.finditer(scad_code))
    if not matches:
        return scad_code, []

    lines = scad_code.splitlines()
    preamble = scad_code[: matches[0].start()].rstrip()
    parts: list[ScadPart] = []

    for index, match in enumerate(matches):
        part_id = match.group(1)
        rest = (match.group(2) or "").strip() or None
        start_line = scad_code[: match.start()].count("\n")
        body_start = start_line + 1
        body, _ = _scan_statement(lines, body_start)
        if not body:
            continue
        color_hint = None
        color_match = COLOR_RE.search(body)
        if color_match:
            color_hint = color_match.group(1)
            if not color_hint.startswith("#"):
                color_hint = None
        label, color = _parse_part_meta(part_id, rest, color_hint, index)
        parts.append(
            ScadPart(
                id=part_id,
                label=label,
                color=color,
                body=body,
                line=start_line + 1,
            )
        )

    return preamble, parts


def build_part_scad(preamble: str, part: ScadPart) -> str:
    chunks = [preamble.rstrip(), "", f"// notion3d:isolated {part.id}", part.body, ""]
    return "\n".join(chunks)


def parts_manifest(project_id: str, version: int, parts: list[ScadPart]) -> dict:
    return {
        "parts": [
            {
                "id": part.id,
                "label": part.label,
                "color": part.color,
                "stl_url": (
                    f"/api/projects/{project_id}/versions/{version}/parts/{part.id}.stl"
                ),
            }
            for part in parts
        ]
    }


def write_parts_manifest(path: Path, manifest: dict) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
