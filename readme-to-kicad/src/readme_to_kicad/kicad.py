from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass

from .models import Circuit, ComponentInstance, Connection, PinRef, RegistryPart, RegistryPin
from .registry import Registry
from .sexpr import SExpr, atom, document


PIN_PITCH = 5.08
PIN_LENGTH = 5.08
SYMBOL_WIDTH = 33.02
MIN_SYMBOL_HEIGHT = 20.32
SYMBOL_VERTICAL_PADDING = 10.16
COLUMN_GAP = 76.2
ROW_GAP = 20.32
POWER_NETS = {"GND", "3V3", "5V", "VBUS", "VSYS", "VM", "VCC"}


@dataclass(frozen=True)
class PlacedPin:
    ref: PinRef
    component: ComponentInstance
    part: RegistryPart
    pin: RegistryPin
    x: float
    y: float
    direction: int


@dataclass(frozen=True)
class SymbolMetrics:
    width: float
    height: float
    left_pins: tuple[RegistryPin, ...]
    right_pins: tuple[RegistryPin, ...]


def generate_schematic(circuit: Circuit, registry: Registry) -> str:
    placements = _component_placements(circuit, registry)
    root_uuid = _stable_uuid(circuit.project_name, "root")
    lib_symbols = [atom("lib_symbols")]
    for component in circuit.components:
        lib_symbols.append(_lib_symbol(registry.parts[component.registry_part_id]))

    body: list[SExpr] = [
        atom("kicad_sch"),
        [atom("version"), 20230121],
        [atom("generator"), "readme-to-kicad"],
        [atom("uuid"), root_uuid],
        [atom("paper"), "A4"],
        lib_symbols,
    ]

    net_counts = _net_counts(circuit.connections)
    emitted_label_stubs: set[tuple[str, str, str]] = set()
    for connection_index, connection in enumerate(circuit.connections, start=1):
        if _should_draw_direct_wire(connection, circuit, registry, placements, net_counts):
            left = _placed_pin(connection.from_pin, circuit, registry, placements)
            right = _placed_pin(connection.to_pin, circuit, registry, placements)
            body.extend(_direct_wire(left, right, connection.net_name, connection_index))
        else:
            for pin_ref in (connection.from_pin, connection.to_pin):
                stub_key = (pin_ref.component_id, pin_ref.normalized_pin_id, connection.net_name)
                if stub_key in emitted_label_stubs:
                    continue
                emitted_label_stubs.add(stub_key)
                placed_pin = _placed_pin(pin_ref, circuit, registry, placements)
                label_x = placed_pin.x + (7.62 if placed_pin.direction == 0 else -7.62)
                body.append(
                    _wire(
                        placed_pin.x,
                        placed_pin.y,
                        label_x,
                        placed_pin.y,
                        connection.net_name,
                        connection_index,
                        pin_ref.component_id,
                        pin_ref.normalized_pin_id,
                    )
                )
                body.append(_label(connection.net_name, label_x, placed_pin.y, placed_pin.direction, pin_ref))

    used_pins = {
        (pin_ref.component_id, pin_ref.normalized_pin_id)
        for connection in circuit.connections
        for pin_ref in (connection.from_pin, connection.to_pin)
    }
    for component in circuit.components:
        part = registry.parts[component.registry_part_id]
        for pin in part.pins:
            if (component.id, pin.id) not in used_pins:
                body.append(_no_connect(component, part, pin, placements))

    for component in circuit.components:
        x, y = placements[component.id]
        body.append(
            _placed_symbol(
                component,
                registry.parts[component.registry_part_id],
                x,
                y,
                circuit.project_name,
                root_uuid,
            )
        )

    body.append([atom("sheet_instances"), [atom("path"), "/", [atom("page"), "1"]]])
    body.append([atom("embedded_fonts"), atom("no")])
    return document(body)


def _component_placements(circuit: Circuit, registry: Registry) -> dict[str, tuple[float, float]]:
    placements: dict[str, tuple[float, float]] = {}
    columns: dict[str, list[ComponentInstance]] = {"left": [], "middle": [], "right": []}
    for component in circuit.components:
        columns[_placement_column(component)].append(component)

    x_positions = {"left": 50.8, "middle": 50.8 + COLUMN_GAP, "right": 50.8 + COLUMN_GAP * 2}
    for column, components in columns.items():
        y_cursor = 50.8
        for component in components:
            height = _symbol_metrics(registry.parts[component.registry_part_id]).height
            placements[component.id] = (x_positions[column], y_cursor + height / 2)
            y_cursor += height + ROW_GAP
    if len(circuit.components) == 2:
        _align_two_component_signal_pins(circuit, registry, placements)
    return placements


def _lib_symbol(part: RegistryPart) -> SExpr:
    metrics = _symbol_metrics(part)
    symbol_body: list[SExpr] = [
        atom("symbol"),
        part.symbol_library_id,
        [atom("pin_names"), [atom("offset"), 1.016]],
        [atom("exclude_from_sim"), atom("no")],
        [atom("in_bom"), atom("yes")],
        [atom("on_board"), atom("yes")],
        _property("Reference", part.reference_prefix, 0, -metrics.height / 2 - 5.08, 0),
        _property("Value", part.value, 0, metrics.height / 2 + 5.08, 0),
        [atom("symbol"), f"{_symbol_name(part)}_0_1", _rectangle(metrics.width, metrics.height)],
    ]
    for pin in part.pins:
        symbol_body[-1].append(_symbol_pin(pin, part, metrics))
    return symbol_body


def _rectangle(width: float, height: float) -> SExpr:
    return [
        atom("rectangle"),
        [atom("start"), -width / 2, -height / 2],
        [atom("end"), width / 2, height / 2],
        [atom("stroke"), [atom("width"), 0.254], [atom("type"), atom("default")]],
        [atom("fill"), [atom("type"), atom("background")]],
    ]


def _symbol_pin(pin: RegistryPin, part: RegistryPart, metrics: SymbolMetrics) -> SExpr:
    y = _pin_local_y(pin, part, metrics)
    if pin.side == "left":
        x = -metrics.width / 2 - PIN_LENGTH
        rotation = 0
    else:
        x = metrics.width / 2 + PIN_LENGTH
        rotation = 180
    return [
        atom("pin"),
        atom(_pin_electrical_type(pin.electrical_type)),
        atom("line"),
        [atom("at"), x, y, rotation],
        [atom("length"), PIN_LENGTH],
        [atom("name"), pin.name, [atom("effects"), [atom("font"), [atom("size"), 1.27, 1.27]]]],
        [atom("number"), pin.number, [atom("effects"), [atom("font"), [atom("size"), 1.27, 1.27]]]],
    ]


def _placed_symbol(
    component: ComponentInstance,
    part: RegistryPart,
    x: float,
    y: float,
    project_name: str,
    root_uuid: str,
) -> SExpr:
    symbol: list[SExpr] = [
        atom("symbol"),
        [atom("lib_id"), part.symbol_library_id],
        [atom("at"), x, y, 0],
        [atom("unit"), 1],
        [atom("exclude_from_sim"), atom("no")],
        [atom("in_bom"), atom("yes")],
        [atom("on_board"), atom("yes")],
        [atom("dnp"), atom("no")],
        [atom("uuid"), _stable_uuid(component.id, "symbol")],
        _property("Reference", component.reference, x, y - 12.7, 0),
        _property("Value", part.value, x, y + 12.7, 0),
    ]
    for pin in part.pins:
        symbol.append([atom("pin"), pin.number, [atom("uuid"), _stable_uuid(component.id, "pin", pin.id)]])
    symbol.append(
        [
            atom("instances"),
            [
                atom("project"),
                project_name,
                [
                    atom("path"),
                    f"/{root_uuid}",
                    [atom("reference"), component.reference],
                    [atom("unit"), 1],
                ],
            ],
        ]
    )
    return symbol


def _symbol_name(part: RegistryPart) -> str:
    return part.symbol_library_id.split(":", 1)[-1]


def _property(name: str, value: str, x: float, y: float, rotation: int) -> SExpr:
    return [
        atom("property"),
        name,
        value,
        [atom("at"), x, y, rotation],
        [atom("effects"), [atom("font"), [atom("size"), 1.27, 1.27]]],
    ]


def _wire(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    net_name: str,
    index: int,
    *uuid_parts: object,
) -> SExpr:
    return [
        atom("wire"),
        [atom("pts"), [atom("xy"), x1, y1], [atom("xy"), x2, y2]],
        [atom("stroke"), [atom("width"), 0], [atom("type"), atom("default")]],
        [atom("uuid"), _stable_uuid("wire", net_name, index, x1, y1, x2, y2, *uuid_parts)],
    ]


def _label(name: str, x: float, y: float, direction: int, pin_ref: PinRef) -> SExpr:
    return [
        atom("label"),
        name,
        [atom("at"), x, y, direction],
        [atom("effects"), [atom("font"), [atom("size"), 1.27, 1.27]]],
        [atom("uuid"), _stable_uuid("label", pin_ref.component_id, pin_ref.normalized_pin_id, name)],
    ]


def _no_connect(
    component: ComponentInstance,
    part: RegistryPart,
    pin: RegistryPin,
    placements: dict[str, tuple[float, float]],
) -> SExpr:
    x, y, _direction = _pin_endpoint(component, part, pin, placements)
    return [
        atom("no_connect"),
        [atom("at"), x, y],
        [atom("uuid"), _stable_uuid("no_connect", component.id, pin.id)],
    ]


def _placed_pin(
    ref: PinRef,
    circuit: Circuit,
    registry: Registry,
    placements: dict[str, tuple[float, float]],
) -> PlacedPin:
    component = next(component for component in circuit.components if component.id == ref.component_id)
    part = registry.parts[component.registry_part_id]
    pin = next(pin for pin in part.pins if pin.id == ref.normalized_pin_id)
    x, y, direction = _pin_endpoint(component, part, pin, placements)
    return PlacedPin(ref, component, part, pin, x, y, direction)


def _pin_endpoint(
    component: ComponentInstance,
    part: RegistryPart,
    pin: RegistryPin,
    placements: dict[str, tuple[float, float]],
) -> tuple[float, float, int]:
    metrics = _symbol_metrics(part)
    cx, cy = placements[component.id]
    y = cy - _pin_local_y(pin, part, metrics)
    if pin.side == "left":
        return cx - metrics.width / 2 - PIN_LENGTH, y, 180
    return cx + metrics.width / 2 + PIN_LENGTH, y, 0


def _pin_y(index: int, total: int) -> float:
    return ((total - 1) / 2 - index) * PIN_PITCH


def _symbol_metrics(part: RegistryPart) -> SymbolMetrics:
    left_pins = _ordered_side_pins(part, "left")
    right_pins = _ordered_side_pins(part, "right")
    max_side_count = max(len(left_pins), len(right_pins), 1)
    height = max(MIN_SYMBOL_HEIGHT, (max_side_count - 1) * PIN_PITCH + SYMBOL_VERTICAL_PADDING)
    return SymbolMetrics(SYMBOL_WIDTH, height, left_pins, right_pins)


def _pin_local_y(pin: RegistryPin, part: RegistryPart, metrics: SymbolMetrics) -> float:
    side_pins = metrics.left_pins if pin.side == "left" else metrics.right_pins
    index = side_pins.index(pin)
    if pin.side_order is None and pin.side != "left":
        index = len(side_pins) - 1 - index
    return _pin_y(index, len(side_pins))


def _ordered_side_pins(part: RegistryPart, side: str) -> tuple[RegistryPin, ...]:
    pins = [pin for pin in part.pins if pin.side == side]
    if any(pin.side_order is not None for pin in pins):
        # Explicit ordering is top-to-bottom. A part may mix ordered and legacy
        # pins, so declaration order remains the deterministic tie-breaker.
        ordered = sorted(
            enumerate(pins),
            key=lambda item: (
                item[1].side_order is None,
                item[1].side_order if item[1].side_order is not None else 0,
                item[0],
            ),
        )
        return tuple(pin for _index, pin in ordered)
    return tuple(pins)


def _placement_column(component: ComponentInstance) -> str:
    part_id = component.registry_part_id
    if "pico" in part_id:
        return "left"
    if part_id in {"left_dc_motor", "right_dc_motor", "battery_pack"}:
        return "right"
    return "middle"


def _net_counts(connections: list[Connection]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for connection in connections:
        counts[connection.net_name] += 1
    return counts


def _should_draw_direct_wire(
    connection: Connection,
    circuit: Circuit,
    registry: Registry,
    placements: dict[str, tuple[float, float]],
    net_counts: dict[str, int],
) -> bool:
    if net_counts[connection.net_name] != 1 or connection.net_name in POWER_NETS:
        return False
    left = _placed_pin(connection.from_pin, circuit, registry, placements)
    right = _placed_pin(connection.to_pin, circuit, registry, placements)
    return left.direction != right.direction and abs(left.y - right.y) < 0.001


def _direct_wire(left: PlacedPin, right: PlacedPin, net_name: str, index: int) -> list[SExpr]:
    first, second = (left, right) if left.x <= right.x else (right, left)
    label_x = (first.x + second.x) / 2
    label_y = first.y
    label_rotation = 0
    return [
        _wire(first.x, first.y, second.x, second.y, net_name, index, "direct"),
        _label(net_name, label_x, label_y, label_rotation, left.ref),
    ]


def _align_two_component_signal_pins(
    circuit: Circuit,
    registry: Registry,
    placements: dict[str, tuple[float, float]],
) -> None:
    source, target = circuit.components
    desired_target_y: list[float] = []
    for connection in circuit.connections:
        if connection.net_name in POWER_NETS:
            continue
        if connection.from_pin.component_id == source.id and connection.to_pin.component_id == target.id:
            source_ref = connection.from_pin
            target_ref = connection.to_pin
        elif connection.to_pin.component_id == source.id and connection.from_pin.component_id == target.id:
            source_ref = connection.to_pin
            target_ref = connection.from_pin
        else:
            continue
        source_pin = _placed_pin(source_ref, circuit, registry, placements)
        target_part = registry.parts[target.registry_part_id]
        target_pin = next(pin for pin in target_part.pins if pin.id == target_ref.normalized_pin_id)
        target_local_y = _pin_local_y(target_pin, target_part, _symbol_metrics(target_part))
        desired_target_y.append(source_pin.y + target_local_y)
    if desired_target_y:
        x, _old_y = placements[target.id]
        placements[target.id] = (x, sum(desired_target_y) / len(desired_target_y))


def _pin_electrical_type(value: str) -> str:
    allowed = {
        "input",
        "output",
        "bidirectional",
        "tri_state",
        "passive",
        "free",
        "unspecified",
        "power_in",
        "power_out",
        "open_collector",
        "open_emitter",
        "no_connect",
    }
    return value if value in allowed else "passive"


def _stable_uuid(*parts: object) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "readme-to-kicad:" + ":".join(map(str, parts))))
