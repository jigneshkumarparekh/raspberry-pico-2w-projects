#!/usr/bin/env python3
"""Reset the robot carrier PCB to a clean placement-only layout."""

from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "kicad" / "obstacle_avoiding_robo"
PCB_PATH = PROJECT_DIR / "obstacle_avoiding_robo.kicad_pcb"
PRO_PATH = PROJECT_DIR / "obstacle_avoiding_robo.kicad_pro"
KICAD_FOOTPRINTS = Path(
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
)


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def vec(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


def set_fp_position(
    board: pcbnew.BOARD,
    ref: str,
    x: float,
    y: float,
    angle: float = 0,
) -> None:
    footprint = board.FindFootprintByReference(ref)
    if footprint is None:
        raise RuntimeError(f"Missing footprint {ref}")
    footprint.SetPosition(vec(x, y))
    footprint.SetOrientationDegrees(angle)


def replace_footprint(
    board: pcbnew.BOARD,
    ref: str,
    library: str,
    name: str,
) -> None:
    old = board.FindFootprintByReference(ref)
    if old is None:
        raise RuntimeError(f"Missing footprint {ref}")

    new = pcbnew.FootprintLoad(str(KICAD_FOOTPRINTS / f"{library}.pretty"), name)
    if new is None:
        raise RuntimeError(f"Unable to load footprint {library}:{name}")

    new.SetReference(ref)
    new.SetValue(old.GetValue())
    new.SetPath(old.GetPath())
    new.SetSheetfile(old.GetSheetfile())
    new.SetSheetname(old.GetSheetname())
    new.SetFPIDAsString(f"{library}:{name}")

    for pad in new.Pads():
        old_pad = old.FindPadByNumber(pad.GetNumber())
        if old_pad is None:
            raise RuntimeError(f"Missing {ref} pad {pad.GetNumber()}")
        pad.SetNet(old_pad.GetNet())

    board.Delete(old)
    board.Add(new)


def add_line(
    board: pcbnew.BOARD,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    layer: int = pcbnew.Edge_Cuts,
) -> None:
    line = pcbnew.PCB_SHAPE(board)
    line.SetShape(pcbnew.SHAPE_T_SEGMENT)
    line.SetStart(vec(x1, y1))
    line.SetEnd(vec(x2, y2))
    line.SetLayer(layer)
    line.SetWidth(mm(0.1))
    board.Add(line)


def add_rect(
    board: pcbnew.BOARD,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    layer: int = pcbnew.F_SilkS,
) -> None:
    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(vec(x1, y1))
    rect.SetEnd(vec(x2, y2))
    rect.SetLayer(layer)
    rect.SetWidth(mm(0.15))
    board.Add(rect)


def add_text(
    board: pcbnew.BOARD,
    text: str,
    x: float,
    y: float,
    size: float = 1.0,
    angle: float = 0,
    layer: int = pcbnew.F_SilkS,
) -> None:
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(vec(x, y))
    item.SetTextSize(vec(size, size))
    item.SetTextThickness(mm(0.15 if size >= 1.0 else 0.12))
    item.SetTextAngleDegrees(angle)
    item.SetLayer(layer)
    board.Add(item)


def add_zone(board: pcbnew.BOARD, layer: int) -> None:
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNetCode(board.GetNetcodeFromNetname("/GND"))
    zone.SetLocalClearance(mm(0.2))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(mm(0.3))
    zone.SetThermalReliefSpokeWidth(mm(0.4))

    polygon = pcbnew.VECTOR_VECTOR2I()
    for point in (vec(1.0, 1.0), vec(79.0, 1.0), vec(79.0, 64.0), vec(1.0, 64.0)):
        polygon.append(point)
    zone.AddPolygon(polygon)
    zone.SetFillFlag(layer, False)
    board.Add(zone)


def add_pin_labels(
    board: pcbnew.BOARD,
    ref: str,
    labels: tuple[str, ...],
    x: float,
) -> None:
    footprint = board.FindFootprintByReference(ref)
    if footprint is None:
        raise RuntimeError(f"Missing footprint {ref}")
    for pin, label in enumerate(labels, start=1):
        pad = footprint.FindPadByNumber(str(pin))
        add_text(board, label, x, pcbnew.ToMM(pad.GetPosition().y), 0.8)


def set_reference(
    board: pcbnew.BOARD,
    ref: str,
    x: float,
    y: float,
    visible: bool = True,
) -> None:
    footprint = board.FindFootprintByReference(ref)
    if footprint is None:
        raise RuntimeError(f"Missing footprint {ref}")
    field = footprint.Reference()
    field.SetPosition(vec(x, y))
    field.SetTextAngleDegrees(0)
    field.SetVisible(visible)


def reset_board() -> None:
    board = pcbnew.LoadBoard(str(PCB_PATH))

    for track in list(board.GetTracks()):
        board.Delete(track)

    for drawing in list(board.GetDrawings()):
        board.Delete(drawing)

    for index in reversed(range(board.GetAreaCount())):
        board.Delete(board.GetArea(index))

    socket_library = "Connector_PinSocket_2.54mm"
    socket_name = "PinSocket_1x08_P2.54mm_Vertical"
    replace_footprint(board, "J3", socket_library, socket_name)
    replace_footprint(board, "J4", socket_library, socket_name)

    placements = {
        "J1": (24.00, 14.37, 0),
        # J2.1 is Pico physical pin 21 at the antenna end.
        "J2": (41.78, 62.63, 180),
        # ROB-14450 is rotated so logic faces the Pico and power faces the edge.
        "J3": (65.74, 21.05, 180),
        "J4": (50.50, 21.05, 180),
        "J5": (74.00, 15.50, 180),
        "J6": (74.00, 6.50, 0),
        "J7": (74.00, 25.00, 0),
        "J8": (7.00, 55.00, 0),
    }
    for ref, (x, y, angle) in placements.items():
        set_fp_position(board, ref, x, y, angle)

    set_reference(board, "J3", 66.5, 24.0)
    set_reference(board, "J4", 49.7, 24.0)
    set_reference(board, "J1", 24.0, 11.3)
    set_reference(board, "J2", 41.78, 11.3)
    for ref in ("J5", "J6", "J7"):
        set_reference(board, ref, 0, 0, False)

    add_line(board, 0, 0, 80, 0)
    add_line(board, 80, 0, 80, 65)
    add_line(board, 80, 65, 39.89, 65)
    add_line(board, 39.89, 65, 39.89, 55)
    add_line(board, 39.89, 55, 25.89, 55)
    add_line(board, 25.89, 55, 25.89, 65)
    add_line(board, 25.89, 65, 0, 65)
    add_line(board, 0, 65, 0, 0)

    add_text(board, "PICO 2 W - USB END", 32.89, 8.7, 0.9)
    add_text(board, "PIN 1", 19.5, 14.37, 0.8)
    add_text(board, "PIN 40", 37.5, 15.8, 0.8)
    add_text(board, "PICO 2 W 51x21mm", 31.8, 34.0, 0.8, 90)
    add_text(board, "ROWS 17.78mm", 34.0, 34.0, 0.8, 90)
    add_text(board, "ANTENNA - KEEP CLEAR", 32.89, 53.2, 0.8)
    add_line(board, 22.39, 13.0, 43.39, 13.0, pcbnew.F_SilkS)
    add_line(board, 22.39, 13.0, 22.39, 64.0, pcbnew.F_SilkS)
    add_line(board, 43.39, 13.0, 43.39, 64.0, pcbnew.F_SilkS)
    add_line(board, 22.39, 64.0, 25.89, 64.0, pcbnew.F_SilkS)
    add_line(board, 39.89, 64.0, 43.39, 64.0, pcbnew.F_SilkS)

    # SparkFun's board is 20.32 mm square with rows 15.24 mm apart.
    add_rect(board, 47.96, 2.00, 68.28, 22.32)
    add_text(board, "TB6612FNG ROB-14450", 58.12, 25.7, 0.8)
    add_text(board, "MODULE ROTATED 180", 58.12, 27.5, 0.8)
    add_pin_labels(
        board,
        "J3",
        ("VM", "VCC", "GND", "AO1", "AO2", "BO2", "BO1", "GND"),
        70.0,
    )
    add_pin_labels(
        board,
        "J4",
        ("PWMA", "AIN2", "AIN1", "STBY", "BIN1", "BIN2", "PWMB", "GND"),
        46.0,
    )

    add_text(board, "J6 RIGHT", 78.2, 7.8, 0.8, 90)
    add_text(board, "J5 LEFT", 78.2, 14.2, 0.8, 90)
    add_text(board, "J7 BAT", 78.2, 26.3, 0.8, 90)
    add_text(board, "+", 70.5, 25.0, 0.8)
    add_text(board, "GND", 70.0, 27.54, 0.8)
    add_text(board, "ULTRASONIC", 7.0, 52.2, 0.8)
    for index, label in enumerate(("VCC", "TRIG", "ECHO", "GND")):
        add_text(board, label, 3.2, 55.0 + index * 2.54, 0.8)

    add_zone(board, pcbnew.F_Cu)
    add_zone(board, pcbnew.B_Cu)

    pcbnew.SaveBoard(str(PCB_PATH), board)


def update_project_netclasses() -> None:
    data = json.loads(PRO_PATH.read_text())
    data.setdefault("net_settings", {})
    data["net_settings"]["classes"] = [
        {
            "bus_width": 12,
            "clearance": 0.2,
            "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2,
            "line_style": 0,
            "microvia_diameter": 0.3,
            "microvia_drill": 0.1,
            "name": "Default",
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
            "track_width": 0.25,
            "via_diameter": 0.8,
            "via_drill": 0.4,
            "wire_width": 6,
        },
        {
            "bus_width": 12,
            "clearance": 0.2,
            "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2,
            "line_style": 0,
            "microvia_diameter": 0.3,
            "microvia_drill": 0.1,
            "name": "Power",
            "pcb_color": "rgba(194, 0, 0, 0.000)",
            "schematic_color": "rgba(194, 0, 0, 0.000)",
            "track_width": 0.8,
            "via_diameter": 1.0,
            "via_drill": 0.5,
            "wire_width": 6,
        },
        {
            "bus_width": 12,
            "clearance": 0.2,
            "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2,
            "line_style": 0,
            "microvia_diameter": 0.3,
            "microvia_drill": 0.1,
            "name": "Motor",
            "pcb_color": "rgba(132, 0, 255, 0.000)",
            "schematic_color": "rgba(132, 0, 255, 0.000)",
            "track_width": 0.8,
            "via_diameter": 1.0,
            "via_drill": 0.5,
            "wire_width": 6,
        },
    ]
    data["net_settings"]["net_colors"] = {}
    data["net_settings"]["netclass_assignments"] = {
        "/3V3": "Power",
        "/GND": "Power",
        "/VSYS_VM_3xAA": "Power",
        "/AO1_LEFT_MOTOR": "Motor",
        "/AO2_LEFT_MOTOR": "Motor",
        "/BO1_RIGHT_MOTOR": "Motor",
        "/BO2_RIGHT_MOTOR": "Motor",
    }
    data["net_settings"].setdefault("meta", {"version": 0})
    PRO_PATH.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    reset_board()
    update_project_netclasses()
