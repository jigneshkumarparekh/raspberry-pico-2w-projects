from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Atom:
    value: str | int | float


SExpr = Atom | str | int | float | list["SExpr"]


def atom(value: str | int | float) -> Atom:
    return Atom(value)


def render(expr: SExpr, indent: int = 0) -> str:
    if isinstance(expr, Atom):
        return _atom(str(expr.value))
    if isinstance(expr, str):
        return _quote(expr)
    if isinstance(expr, int):
        return str(expr)
    if isinstance(expr, float):
        return f"{expr:.4f}".rstrip("0").rstrip(".")
    if not expr:
        return "()"

    if _is_flat(expr):
        return "(" + " ".join(render(item, indent) for item in expr) + ")"

    child_indent = indent + 2
    rendered = [render(expr[0], indent)]
    for item in expr[1:]:
        rendered.append("\n" + " " * child_indent + render(item, child_indent))
    return "(" + "".join(rendered) + ")"


def document(expr: SExpr) -> str:
    return render(expr) + "\n"


def _is_flat(items: Iterable[SExpr]) -> bool:
    return all(not isinstance(item, list) for item in items)


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _atom(value: str) -> str:
    return value
