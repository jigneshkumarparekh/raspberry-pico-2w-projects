from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from readme_to_kicad.cli import main
from readme_to_kicad.kicad import generate_schematic
from readme_to_kicad.parser import parse_readme
from readme_to_kicad.registry import Registry
from readme_to_kicad.resolver import resolve


SAMPLE = """# Test Circuit

## Components

- Raspberry Pi Pico 2W
- HC-SR04 ultrasonic sensor

## Connections

- Pico GPIO16 -> HC-SR04 TRIG
- Pico GPIO17 -> HC-SR04 ECHO
- Pico 3V3 -> HC-SR04 VCC
- Pico GND -> HC-SR04 GND
"""


class CoreTests(unittest.TestCase):
    def test_resolves_sample_readme(self) -> None:
        circuit = resolve(parse_readme(SAMPLE), Registry.bundled(), "sample", strict=True)

        self.assertFalse(circuit.diagnostics)
        self.assertEqual([component.reference for component in circuit.components], ["U1", "U2"])
        self.assertEqual([connection.net_name for connection in circuit.connections], ["TRIG", "ECHO", "3V3", "GND"])

    def test_ambiguous_pico_pin_blocks_in_strict_mode(self) -> None:
        markdown = """# Ambiguous

## Components

- Raspberry Pi Pico 2W
- HC-SR04

## Connections

- Pico pin 16 -> HC-SR04 TRIG
"""
        circuit = resolve(parse_readme(markdown), Registry.bundled(), "ambiguous", strict=True)

        self.assertTrue(circuit.has_blocking_diagnostics)
        self.assertEqual(circuit.diagnostics[0].code, "ambiguous_pin_scheme")

    def test_markdown_wiring_table(self) -> None:
        markdown = """# Table Circuit

## Components

- Raspberry Pi Pico 2W
- HC-SR04

## Wiring

| From | To |
| --- | --- |
| Pico GPIO16 | HC-SR04 TRIG |
"""
        circuit = resolve(parse_readme(markdown), Registry.bundled(), "table", strict=True)

        self.assertFalse(circuit.diagnostics)
        self.assertEqual(len(circuit.connections), 1)
        self.assertEqual(circuit.connections[0].net_name, "TRIG")

    def test_conflicting_connection_blocks_in_strict_mode(self) -> None:
        markdown = """# Conflict

## Components

- Raspberry Pi Pico 2W
- HC-SR04

## Connections

- Pico GPIO16 -> HC-SR04 TRIG
- Pico GPIO16 -> HC-SR04 ECHO
"""
        circuit = resolve(parse_readme(markdown), Registry.bundled(), "conflict", strict=True)

        self.assertTrue(circuit.has_blocking_diagnostics)
        self.assertIn("conflicting_connection", [diagnostic.code for diagnostic in circuit.diagnostics])

    def test_generates_deterministic_schematic(self) -> None:
        circuit = resolve(parse_readme(SAMPLE), Registry.bundled(), "sample", strict=True)

        first = generate_schematic(circuit, Registry.bundled())
        second = generate_schematic(circuit, Registry.bundled())

        self.assertEqual(first, second)
        self.assertIn('(kicad_sch', first)
        self.assertIn('(lib_symbols', first)
        self.assertIn('"readme-to-kicad"', first)
        self.assertIn('"TRIG"', first)
        self.assertIn("(no_connect", first)
        self.assertTrue(_balanced_parentheses(first))

    def test_cli_inspect_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(SAMPLE, encoding="utf-8")

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main(["inspect", str(readme), "--strict"])

        self.assertEqual(exit_code, 0)
        self.assertIn('"connections"', buffer.getvalue())

    def test_cli_generate_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            output = Path(directory) / "project.kicad_sch"
            readme.write_text(SAMPLE, encoding="utf-8")

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                exit_code = main(["generate", str(readme), "-o", str(output), "--strict"])

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertIn("(kicad_sch", output.read_text(encoding="utf-8"))
            self.assertIn("wrote", buffer.getvalue())

def _balanced_parentheses(text: str) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0 and not in_string


if __name__ == "__main__":
    unittest.main()
