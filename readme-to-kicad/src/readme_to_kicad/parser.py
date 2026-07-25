from __future__ import annotations

import re
from dataclasses import dataclass

from .models import SourceSpan


@dataclass(frozen=True)
class RawConnection:
    left: str
    right: str
    span: SourceSpan
    confidence: float = 1.0


@dataclass(frozen=True)
class ParsedReadme:
    components: list[tuple[str, SourceSpan]]
    connections: list[RawConnection]


SECTION_COMPONENTS = {"component", "components", "parts", "bom", "bill of materials"}
SECTION_CONNECTIONS = {"connection", "connections", "wiring", "wire", "pin connections"}
CONNECTOR_RE = re.compile(
    r"\s*(?:->|=>|-->| connected to | connects to | goes to | to )\s*",
    flags=re.IGNORECASE,
)


def parse_readme(markdown: str) -> ParsedReadme:
    components: list[tuple[str, SourceSpan]] = []
    connections: list[RawConnection] = []
    current_section: str | None = None
    in_code_block = False
    table_headers: list[str] | None = None

    lines = markdown.splitlines()
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        span = SourceSpan(line=index, text=line)

        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        heading = _heading_text(stripped)
        if heading is not None:
            current_section = heading
            table_headers = None
            continue

        if _is_table_separator(stripped):
            continue

        if "|" in stripped and current_section in SECTION_CONNECTIONS:
            headers_or_row = _split_table_row(stripped)
            if not headers_or_row:
                continue
            if table_headers is None:
                table_headers = [_normalize_header(cell) for cell in headers_or_row]
                continue
            row = dict(zip(table_headers, headers_or_row, strict=False))
            raw_connection = _connection_from_table(row, span)
            if raw_connection:
                connections.append(raw_connection)
            continue

        bullet = _bullet_text(stripped)
        if bullet and current_section in SECTION_COMPONENTS:
            components.append((bullet, span))
            continue
        if bullet and current_section in SECTION_CONNECTIONS:
            raw_connection = _connection_from_text(bullet, span, confidence=1.0)
            if raw_connection:
                connections.append(raw_connection)
            continue

        if current_section in SECTION_CONNECTIONS or "connected" in stripped.lower():
            raw_connection = _connection_from_text(stripped.rstrip("."), span, confidence=0.75)
            if raw_connection:
                connections.append(raw_connection)

    return ParsedReadme(components=components, connections=connections)


def _heading_text(line: str) -> str | None:
    if not line.startswith("#"):
        return None
    return line.lstrip("#").strip().lower()


def _bullet_text(line: str) -> str | None:
    if line.startswith(("- ", "* ")):
        return line[2:].strip()
    match = re.match(r"^\d+\.\s+(.*)$", line)
    return match.group(1).strip() if match else None


def _split_table_row(line: str) -> list[str]:
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    return [cell for cell in cells if cell]


def _is_table_separator(line: str) -> bool:
    marker = line.replace("|", "").replace(":", "").replace(" ", "").strip()
    return bool(marker) and set(marker) <= {"-"}


def _normalize_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", header.lower()).strip("_")


def _connection_from_table(row: dict[str, str], span: SourceSpan) -> RawConnection | None:
    if "from" in row and "to" in row:
        return RawConnection(row["from"], row["to"], span)
    left_component = row.get("component") or row.get("from_component")
    left_pin = row.get("pin") or row.get("from_pin")
    right_component = row.get("connected_component") or row.get("to_component")
    right_pin = row.get("connected_pin") or row.get("to_pin")
    if left_component and left_pin and right_component and right_pin:
        return RawConnection(f"{left_component} {left_pin}", f"{right_component} {right_pin}", span)
    return None


def _connection_from_text(text: str, span: SourceSpan, confidence: float) -> RawConnection | None:
    parts = CONNECTOR_RE.split(text, maxsplit=1)
    if len(parts) != 2:
        return None
    left, right = parts[0].strip(), parts[1].strip()
    if not left or not right:
        return None
    return RawConnection(left, right, span, confidence)
