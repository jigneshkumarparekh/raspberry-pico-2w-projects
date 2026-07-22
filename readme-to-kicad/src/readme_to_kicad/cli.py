from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .kicad import generate_schematic
from .parser import parse_readme
from .registry import Registry, RegistryError
from .resolver import resolve


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    try:
        return args.handler(args)
    except RegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def inspect_command(args: argparse.Namespace) -> int:
    circuit, _registry = _build_circuit(args)
    print(json.dumps(circuit.to_dict(), indent=2))
    return 1 if circuit.has_blocking_diagnostics else 0


def generate_command(args: argparse.Namespace) -> int:
    circuit, registry = _build_circuit(args)
    if args.dry_run:
        print(json.dumps(circuit.to_dict(), indent=2))
        return 1 if circuit.has_blocking_diagnostics else 0
    if circuit.has_blocking_diagnostics:
        _print_diagnostics(circuit.diagnostics)
        return 1
    output = generate_schematic(circuit, registry)
    args.output.write_text(output, encoding="utf-8")
    _print_diagnostics(circuit.diagnostics)
    print(f"wrote {args.output}")
    return 0


def _build_circuit(args: argparse.Namespace):
    registry = Registry.from_path(args.registry) if args.registry else Registry.bundled()
    markdown = args.readme.read_text(encoding="utf-8")
    project_name = args.project_name or args.readme.stem
    parsed = parse_readme(markdown)
    circuit = resolve(parsed, registry, project_name, args.strict)
    return circuit, registry


def _print_diagnostics(diagnostics) -> None:
    for diagnostic in diagnostics:
        location = f":{diagnostic.source_span.line}" if diagnostic.source_span else ""
        print(
            f"{diagnostic.severity}{location}: {diagnostic.code}: {diagnostic.message}",
            file=sys.stderr if diagnostic.severity == "error" else sys.stdout,
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="readme-to-kicad")
    subcommands = parser.add_subparsers(dest="command")

    inspect_parser = subcommands.add_parser("inspect", help="print the extracted circuit graph")
    _add_common_arguments(inspect_parser)
    inspect_parser.add_argument("--format", choices=["json"], default="json")
    inspect_parser.set_defaults(handler=inspect_command)

    generate_parser = subcommands.add_parser("generate", help="generate a KiCad schematic")
    _add_common_arguments(generate_parser)
    generate_parser.add_argument("-o", "--output", type=Path, required=True)
    generate_parser.add_argument("--dry-run", action="store_true")
    generate_parser.add_argument("--kicad-version", choices=["8"], default="8")
    generate_parser.set_defaults(handler=generate_command)

    return parser


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("readme", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--project-name")
    parser.add_argument("--strict", action="store_true")
