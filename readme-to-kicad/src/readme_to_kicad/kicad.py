from __future__ import annotations

import uuid
from dataclasses import dataclass

from .models import Circuit, ComponentInstance, PinRef, RegistryPart, RegistryPin
from .registry import Registry
from .sexpr import SExpr, atom, document


@dataclass(frozen=True)
class PlacedPin:
    ref: PinRef
    component: ComponentInstance
    part: RegistryPart
    pin: RegistryPin
    x: float
    y: float
    direction: int


def generate_schematic(circuit: Circuit, registry: Registry) -> str:
    placements = _component_placements(circuit)
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

    for connection_index, connection in enumerate(circuit.connections, start=1):
        for pin_ref in (connection.from_pin, connection.to_pin):
            placed_pin = _placed_pin(pin_ref, circuit, registry, placements)
            label_x = placed_pin.x + (7.62 if placed_pin.direction == 0 else -7.62)
            body.append(_wire(placed_pin.x, placed_pin.y, label_x, placed_pin.y, connection.net_name, connection_index))
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


def _component_placements(circuit: Circuit) -> dict[str, tuple[float, float]]:
    placements: dict[str, tuple[float, float]] = {}
    controllers = [c for c in circuit.components if "pico" in c.registry_part_id]
    others = [c for c in circuit.components if c not in controllers]
    y = 76.2
    for index, component in enumerate(controllers):
        placements[component.id] = (50.8, y + index * 45.72)
    for index, component in enumerate(others):
        placements[component.id] = (127.0, y + index * 35.56)
    return placements


def _lib_symbol(part: RegistryPart) -> SExpr:
    height = max(15.24, len(part.pins) * 5.08 + 5.08)
    width = 25.4
    symbol_body: list[SExpr] = [
        atom("symbol"),
        part.symbol_library_id,
        [atom("pin_names"), [atom("offset"), 1.016]],
        [atom("exclude_from_sim"), atom("no")],
        [atom("in_bom"), atom("yes")],
        [atom("on_board"), atom("yes")],
        _property("Reference", part.reference_prefix, 0, -height / 2 - 5.08, 0),
        _property("Value", part.value, 0, height / 2 + 5.08, 0),
        [atom("symbol"), f"{_symbol_name(part)}_0_1", _rectangle(width, height)],
    ]
    for index, pin in enumerate(part.pins):
        symbol_body[-1].append(_symbol_pin(pin, index, part.pins, width))
    return symbol_body


def _rectangle(width: float, height: float) -> SExpr:
    return [
        atom("rectangle"),
        [atom("start"), -width / 2, -height / 2],
        [atom("end"), width / 2, height / 2],
        [atom("stroke"), [atom("width"), 0.254], [atom("type"), atom("default")]],
        [atom("fill"), [atom("type"), atom("background")]],
    ]


def _symbol_pin(pin: RegistryPin, index: int, pins: list[RegistryPin], width: float) -> SExpr:
    y = _pin_y(index, len(pins))
    if pin.side == "left":
        x = -width / 2 - 5.08
        rotation = 0
    else:
        x = width / 2 + 5.08
        rotation = 180
    return [
        atom("pin"),
        atom(_pin_electrical_type(pin.electrical_type)),
        atom("line"),
        [atom("at"), x, y, rotation],
        [atom("length"), 5.08],
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
        symbol.append([atom("pin"), pin.number, [atom("uuid"), _stable_uuid(component.id, "pin", pin.number)]])
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


def _wire(x1: float, y1: float, x2: float, y2: float, net_name: str, index: int) -> SExpr:
    return [
        atom("wire"),
        [atom("pts"), [atom("xy"), x1, y1], [atom("xy"), x2, y2]],
        [atom("stroke"), [atom("width"), 0], [atom("type"), atom("default")]],
        [atom("uuid"), _stable_uuid("wire", net_name, index, x1, y1, x2, y2)],
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
    pin_index = part.pins.index(pin)
    symbol_width = 25.4
    cx, cy = placements[component.id]
    y = cy - _pin_y(pin_index, len(part.pins))
    if pin.side == "left":
        return cx - symbol_width / 2 - 5.08, y, 180
    return cx + symbol_width / 2 + 5.08, y, 0


def _pin_y(index: int, total: int) -> float:
    return (index - (total - 1) / 2) * 5.08


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
