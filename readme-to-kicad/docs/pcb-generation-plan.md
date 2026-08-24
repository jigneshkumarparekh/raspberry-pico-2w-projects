# README-to-KiCad PCB Generation Plan

## Summary

Add a v1 path that converts README wiring documentation into a usable KiCad 10
starter PCB project. The existing deterministic README parser and resolver remain
the front end: markdown is parsed into a source-traced `Circuit`, then a new PCB
generation layer converts that circuit into KiCad project, schematic, and board
files.

V1 should generate a starter KiCad project, not a finished routed PCB. The output
target is a KiCad 10 project containing `.kicad_pro`, `.kicad_sch`, and
`.kicad_pcb` files, footprint assignments, placed footprints, a board outline,
netclasses, deterministic labels and zones where safe, and an unrouted ratsnest.
Arbitrary autorouting is explicitly out of scope for v1.

SKiDL should not be the v1 implementation path. SKiDL is a strong optional future
backend for Python circuit descriptions, electrical rules checks, and netlist
generation, but this tool's primary value is README extraction plus native KiCad
project generation.

References:

- [SKiDL README documentation](https://skidl.readthedocs.io/en/latest/readme.html)
- [SKiDL usage documentation](https://skidl.readthedocs.io/en/latest/usage.html)
- [SKiDL GitHub repository](https://github.com/devbisme/skidl)

## Key Changes

- Add a project-generation CLI command while preserving existing `inspect` and
  schematic-only `generate` behavior:

```bash
readme-to-kicad generate-project README.md -o output_dir --profile pico-carrier-v1 --kicad-version 10
```

- Extend the component registry with PCB metadata:
  - KiCad footprint library id
  - footprint value
  - logical-pin to footprint-pad map
  - placement role
  - optional default netclass hints
- Keep old registries readable for schematic-only generation.
- Require complete PCB metadata only when running `generate-project`.
- Add a PCB intent model that converts a resolved `Circuit` into deterministic
  board-level data:
  - components
  - nets
  - footprints
  - footprint placements
  - board outline
  - zones
  - netclasses
- Generate KiCad 10 `.kicad_pro` and `.kicad_pcb` files natively, using the
  existing S-expression writer style and deterministic UUID behavior.
- Reuse the existing hand-built obstacle robot PCB as the v1 reference for board
  size, Pico header placement, TB6612FNG breakout connectors, ultrasonic
  connector, battery and motor headers, silkscreen labels, and netclasses.

## V1 Layout Profile

The first supported profile is `pico-carrier-v1`. It supports the current
obstacle robot component set:

- Raspberry Pi Pico 2W
- TB6612FNG motor driver breakout
- HC-SR04 ultrasonic sensor
- left motor
- right motor
- battery pack

Unsupported components, missing footprint ids, missing pin-to-pad maps, or
unplaceable parts should produce blocking diagnostics for PCB generation. In
`--strict`, any blocking diagnostic returns a nonzero exit status. These
diagnostics must not break schematic-only generation for the same README.

The profile should create placed footprints and board constraints, then leave
routing to KiCad. It may add deterministic GND zones on front and back copper,
but only when those zones are safe for users to fill in KiCad.

## Implementation Details

Data flow:

```text
README markdown
  -> existing parser
  -> existing resolver
  -> Circuit
  -> BoardIntent, using registry PCB metadata and selected layout profile
  -> KiCad schematic, project file, PCB file, and local tables when needed
```

KiCad project output:

- Use KiCad 10 file versions to match the checked-in hand-built robot project.
- Preserve deterministic UUID generation so repeated runs produce stable diffs.
- Generate `Default`, `Power`, and `Motor` netclasses.
- Assign `GND`, `3V3`, `VSYS`, `VM`, and `VBUS` to `Power`.
- Assign motor output nets to `Motor`.
- Keep schematic generation compatible with the current direct `.kicad_sch`
  writer.
- Generate local symbol and footprint tables only when the project cannot rely
  on built-in KiCad library ids.

Board layout behavior:

- Default to an 80 mm x 65 mm robot carrier outline.
- Include the Pico antenna keep-clear notch from the hand-built reference board.
- Place Pico headers, TB6612FNG module headers, ultrasonic header, battery
  header, and motor headers at deterministic coordinates.
- Add connector function labels and orientation markers on silkscreen.
- Add GND zones on front and back copper, but leave them unfilled or safely
  fillable by KiCad.
- Do not perform arbitrary autorouting in v1.

## Registry Metadata

PCB generation should extend each supported part with optional `pcb` data.
Schematic-only generation continues to require only the existing logical symbol
metadata.

Example shape:

```yaml
parts:
  pico_2w:
    value: Raspberry Pi Pico 2W
    symbol:
      library_id: MCU_Module:RaspberryPi_Pico
    pcb:
      footprint:
        library_id: Module:RaspberryPi_Pico
        value: Raspberry Pi Pico 2W
      pin_to_pad:
        gpio0: "1"
        gpio1: "2"
        gnd_3: "3"
      placement_role: controller
      netclass_hints:
        power: [3V3, VSYS, VBUS, GND]
```

Validation should be command-specific:

- `inspect`: no PCB metadata required.
- `generate`: no PCB metadata required.
- `generate-project`: footprint id, footprint value, pin-to-pad map, and
  placement role required for every placed component.

## SKiDL Position

SKiDL describes circuits in Python, connects part pins with nets, runs ERC, and
generates netlists for PCB tools. That makes it useful future infrastructure,
especially for `Circuit -> SKiDL Python -> netlist/ERC` workflows.

For v1, native KiCad project generation is the better fit because:

- The front end is already a deterministic README parser and resolver.
- The required output includes KiCad project and board files, not only a netlist.
- The v1 profile depends on explicit footprint placements and board geometry.
- Keeping generation native avoids adding a Python-circuit backend before the
  KiCad project writer is stable.

Future SKiDL work can add an optional backend after native project generation
exists, primarily for netlist export, ERC checks, and comparison against native
generated connectivity.

## Test Plan

Unit tests:

- Registry validation accepts PCB metadata.
- Registry validation rejects missing footprint ids, footprint values, pin maps,
  and placement roles for `generate-project`.
- Schematic-only generation still accepts registries without PCB metadata.
- `examples/test-readme.md` resolves into a `BoardIntent` with the expected
  component count, net count, netclasses, footprint ids, and placements.
- Generated `.kicad_pcb` files have deterministic UUIDs.
- Generated `.kicad_pcb` files have balanced S-expressions.
- Unsupported components produce blocking diagnostics for PCB generation without
  breaking schematic-only generation.

Golden tests:

- Add a normalized golden snapshot for the obstacle robot starter `.kicad_pcb`.
- Add golden snapshots for generated `.kicad_pro` output.
- Add a golden snapshot for the generated project file list.

Manual acceptance:

```bash
readme-to-kicad generate-project examples/test-readme.md -o /tmp/obstacle-robo --profile pico-carrier-v1 --strict
```

Then open the generated project in KiCad 10 and confirm:

- the schematic loads
- the PCB loads
- all supported footprints are placed
- the ratsnest is visible
- `Default`, `Power`, and `Motor` netclasses exist
- DRC reports no missing-footprint or malformed-board errors

## Assumptions

- V1 targets KiCad 10 because the reference robot PCB uses KiCad 10-era files.
- V1 generates a starter PCB, not a fabrication-ready routed board.
- The first supported profile is the obstacle robot Pico carrier.
- General arbitrary PCB layout is future work.
- SKiDL remains optional future infrastructure rather than a v1 dependency.
