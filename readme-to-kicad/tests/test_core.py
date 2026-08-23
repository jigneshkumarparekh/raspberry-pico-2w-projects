from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from readme_to_kicad.cli import main
from readme_to_kicad.kicad import (
    _component_placements,
    _pin_endpoint,
    _pin_local_y,
    _symbol_metrics,
    generate_schematic,
)
from readme_to_kicad.models import Circuit, ComponentInstance
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

    def test_obstacle_robo_example_resolves(self) -> None:
        markdown = Path("examples/robo-car-test-circuit.md").read_text(encoding="utf-8")
        circuit = resolve(parse_readme(markdown), Registry.bundled(), "obstacle-robo", strict=True)

        self.assertFalse(circuit.diagnostics)
        self.assertEqual(len(circuit.components), 6)
        self.assertEqual(len(circuit.connections), 19)
        self.assertIn("STBY", [connection.net_name for connection in circuit.connections])
        self.assertIn("BO2", [connection.net_name for connection in circuit.connections])

    def test_pico_2w_registry_has_full_40_pin_header(self) -> None:
        pico = Registry.bundled().parts["pico_2w"]

        self.assertEqual(len(pico.pins), 40)
        self.assertEqual([pin.number for pin in pico.pins], [str(number) for number in range(1, 41)])
        self.assertEqual(sum(1 for pin in pico.pins if pin.side == "left"), 20)
        self.assertEqual(sum(1 for pin in pico.pins if pin.side == "right"), 20)
        self.assertEqual(pico.pins[0].name, "GP0")
        self.assertEqual(pico.pins[-1].name, "VBUS")

    def test_pico_2w_pin_coordinates_follow_physical_header_order(self) -> None:
        registry = Registry.bundled()
        pico = registry.parts["pico_2w"]
        metrics = _symbol_metrics(pico)
        pins = {pin.id: pin for pin in pico.pins}

        self.assertGreater(
            _pin_local_y(pins["gp0"], pico, metrics),
            _pin_local_y(pins["gp15"], pico, metrics),
        )
        self.assertGreater(
            _pin_local_y(pins["vbus"], pico, metrics),
            _pin_local_y(pins["gp16"], pico, metrics),
        )

        component = ComponentInstance(
            id="pico",
            reference="U1",
            registry_part_id="pico_2w",
            display_name="Raspberry Pi Pico 2W",
            aliases_seen=[],
            confidence=1.0,
        )
        circuit = Circuit("pin-order", [component], [], [])
        placements = _component_placements(circuit, registry)

        gp0_y = _pin_endpoint(component, pico, pins["gp0"], placements)[1]
        gp15_y = _pin_endpoint(component, pico, pins["gp15"], placements)[1]
        gp16_y = _pin_endpoint(component, pico, pins["gp16"], placements)[1]
        vbus_y = _pin_endpoint(component, pico, pins["vbus"], placements)[1]

        self.assertLess(gp0_y, gp15_y)
        self.assertLess(vbus_y, gp16_y)

    def test_tb6612fng_registry_matches_breakout_back_view(self) -> None:
        tb = Registry.bundled().parts["tb6612fng"]
        self.assertEqual(len(tb.pins), 16)
        self.assertEqual(
            [pin.id for pin in tb.pins if pin.side == "left"],
            ["pwma", "ain2", "ain1", "stby", "bin1", "bin2", "pwmb", "gnd_left"],
        )
        self.assertEqual(
            [pin.id for pin in tb.pins if pin.side == "right"],
            ["vm", "vcc", "gnd_right_upper", "ao1", "ao2", "bo2", "bo1", "gnd_right_lower"],
        )
        self.assertEqual([pin.side_order for pin in tb.pins if pin.side == "left"], list(range(8)))
        self.assertEqual([pin.side_order for pin in tb.pins if pin.side == "right"], list(range(8)))
        self.assertEqual({pin.name for pin in tb.pins if pin.id in {"ao1", "ao2", "bo1", "bo2"}}, {"AO1", "AO2", "BO1", "BO2"})
        self.assertEqual({pin.shared_net for pin in tb.pins if pin.name == "GND"}, {"GND"})

    def test_tb6612fng_pin_coordinates_follow_explicit_side_order(self) -> None:
        registry = Registry.bundled()
        tb = registry.parts["tb6612fng"]
        metrics = _symbol_metrics(tb)
        pins = {pin.id: pin for pin in tb.pins}
        self.assertEqual(
            [pin.id for pin in metrics.left_pins],
            ["pwma", "ain2", "ain1", "stby", "bin1", "bin2", "pwmb", "gnd_left"],
        )
        self.assertEqual(
            [pin.id for pin in metrics.right_pins],
            ["vm", "vcc", "gnd_right_upper", "ao1", "ao2", "bo2", "bo1", "gnd_right_lower"],
        )
        self.assertGreater(_pin_local_y(pins["pwma"], tb, metrics), _pin_local_y(pins["gnd_left"], tb, metrics))
        self.assertGreater(_pin_local_y(pins["vm"], tb, metrics), _pin_local_y(pins["gnd_right_lower"], tb, metrics))

    def test_tb6612fng_duplicate_gnds_resolve_to_one_physical_pad(self) -> None:
        registry = Registry.bundled()
        markdown = """# GND aliases

## Components

- TB6612FNG motor driver

## Connections

- TB6612FNG GND -> TB6612FNG VCC
"""
        circuit = resolve(parse_readme(markdown), registry, "gnd-aliases", strict=True)
        self.assertFalse(circuit.diagnostics)
        self.assertEqual(circuit.connections[0].from_pin.normalized_pin_id, "gnd_left")
        self.assertEqual(circuit.connections[0].net_name, "GND")

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

    def test_generates_direct_wires_for_simple_signal_nets(self) -> None:
        markdown = """# Direct Wires

## Components

- Raspberry Pi Pico 2W
- HC-SR04 ultrasonic sensor

## Connections

- Pico GPIO17 -> HC-SR04 TRIG
- Pico GPIO16 -> HC-SR04 ECHO
- Pico 3V3 -> HC-SR04 VCC
- Pico GND -> HC-SR04 GND
"""
        circuit = resolve(parse_readme(markdown), Registry.bundled(), "sample", strict=True)

        schematic = generate_schematic(circuit, Registry.bundled())

        label_only_wire_count = len(circuit.connections) * 2
        self.assertLess(schematic.count("(wire"), label_only_wire_count)

    def test_obstacle_robo_schematic_uses_hybrid_routing(self) -> None:
        markdown = Path("examples/robo-car-test-circuit.md").read_text(encoding="utf-8")
        circuit = resolve(parse_readme(markdown), Registry.bundled(), "obstacle-robo", strict=True)

        schematic = generate_schematic(circuit, Registry.bundled())

        self.assertIn('"STBY"', schematic)
        label_only_wire_count = len(circuit.connections) * 2
        self.assertLess(schematic.count("(wire"), label_only_wire_count)
        self.assertIn('"GND"', schematic)
        self.assertIn("(no_connect", schematic)

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
