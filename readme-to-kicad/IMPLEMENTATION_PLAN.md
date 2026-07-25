# README-to-KiCad Implementation Plan

## Summary

Build a Python CLI tool that converts a circuit README into a KiCad 8-compatible `.kicad_sch` schematic. The v1 scope is deliberately narrow: deterministic README parsing, a source-traced intermediate circuit graph, a user-editable component registry, strict diagnostics, and direct schematic generation for a small supported component set.

LLM-assisted extraction is deferred until after the deterministic MVP is stable. The v1 tool should generate schematics only, not PCB layouts.

## Key Changes

- Create a Python package using `pyproject.toml`, `src/` layout, `typer`, `pydantic`, `pyyaml`, `markdown-it-py`, `pytest`, and `ruff`.
- Provide CLI commands:
  - `readme-to-kicad inspect README.md --format json`
  - `readme-to-kicad generate README.md -o project.kicad_sch`
- Add options:
  - `--registry path/to/components.yml`
  - `--project-name name`
  - `--strict`
  - `--dry-run`
  - `--kicad-version 8`
- Exit behavior:
  - validation errors return nonzero
  - warnings return zero by default
  - `--strict` fails on ambiguity, unresolved components, unresolved pins, conflicting connections, and ambiguous power nets

## Implementation Details

- Parse only supported v1 README structures:
  - component lists
  - wiring/connection bullet lists
  - wiring tables with columns such as `From`, `To`, `Component`, `Pin`, `Signal`
  - simple connection prose when it matches documented patterns
- Ignore code blocks and images in v1 unless explicitly marked as wiring data.
- Give explicit wiring tables precedence over prose.
- Treat same-confidence conflicting wiring statements as blocking diagnostics in strict mode.
- Track source spans for every extracted component, pin, and connection.

Use an auditable intermediate model:

```python
ComponentInstance:
  id
  reference
  registry_part_id
  display_name
  aliases_seen
  confidence
  source_spans

PinRef:
  component_id
  raw_text
  scheme: physical | gpio | signal | label | alias
  normalized_pin_id
  confidence
  source_span

Connection:
  from_pin
  to_pin
  net_name
  confidence
  status
  source_span

Diagnostic:
  severity: info | warning | error
  code
  message
  source_span
  suggested_fix
  blocks_output
```

- Keep logical circuit graph connectivity separate from KiCad schematic geometry.
- Never silently collapse Raspberry Pi Pico physical pin numbers and GPIO numbers.
- Normalize power nets only through a controlled map: `3V3`, `3.3V`, `5V`, `VBUS`, `VSYS`, `GND`, `AGND`.
- Unknown modules should fail with diagnostics unless a later explicit generic-connector option is added.

## KiCad Generation

- Generate KiCad 8-compatible `.kicad_sch` S-expression files.
- Use a real S-expression AST/writer with stable formatting, correct string escaping, millimeter units, and fixed numeric precision.
- Generate required schematic sections:
  - `(kicad_sch ...)`
  - `(version ...)`
  - `(generator "readme-to-kicad")`
  - root `(uuid ...)`
  - `(paper ...)`
  - `(lib_symbols ...)`
  - wires, labels, junctions, no-connect markers as needed
  - placed `(symbol ...)` entries with properties, units, BOM/on-board flags, UUIDs, pin UUIDs, and instances data
  - root sheet instance path/page data
- For v1, embed known-good symbol definitions for supported components instead of depending only on the user's KiCad library table.
- Place the controller on the left and modules to the right using deterministic coordinates.
- Use net labels for simple named connections, but ensure generated geometry still creates valid KiCad connectivity.
- Use standards-compliant UUID strings. If deterministic UUIDs are used, validate that KiCad opens and saves the file without destructive churn.

## MVP Component Registry

Create a versioned YAML registry containing:

- Raspberry Pi Pico 2W
- HC-SR04 ultrasonic sensor
- LED
- resistor
- buzzer
- servo

Each registry part should include:

```yaml
schema_version: 1
parts:
  pico_2w:
    aliases: []
    reference_prefix: U
    value: Raspberry Pi Pico 2W
    symbol:
      library_id: ...
      embedded_definition: ...
    pins:
      - id: gpio16
        number: ...
        name: GPIO16
        aliases: [GP16, GPIO16]
        schemes: [gpio, label]
        electrical_type: bidirectional
```

Registry matching should be two-stage:

- Generate ranked candidates from aliases and fuzzy matching.
- Validate candidates against required pins/signals before selecting.
- Emit ranked unresolved candidates instead of guessing.

## Test Plan

Add fixture tests for:

- Explicit component list plus connection bullets.
- Markdown wiring table.
- Simple supported prose.
- Raspberry Pi Pico 2W connected to HC-SR04.
- Ambiguous `pin 16` wording.
- Unknown component.
- Unknown pin.
- Duplicate component references.
- Conflicting wiring statements.
- Power net normalization.
- Registry validation.
- Intermediate JSON golden snapshots.
- `.kicad_sch` golden snapshots.
- S-expression parse/round-trip stability.

Acceptance criteria:

- The Pico 2W plus HC-SR04 README produces a deterministic `.kicad_sch`.
- The schematic opens in KiCad 8 and preferably KiCad 9.
- The extracted intermediate graph matches expected fixture JSON before schematic generation.
- Strict mode fails with stable diagnostic codes for ambiguity and conflicts.
- The tool never invents unresolved components, pins, or connections.
- Generated output remains stable across repeated runs.

## Assumptions

- First deliverable is a CLI tool, not a web app or VS Code extension.
- v1 targets KiCad 8-compatible `.kicad_sch`; KiCad 9 compatibility is tested where available.
- LLM support is intentionally deferred.
- PCB layout generation is out of scope.
- Correctness and inspectability matter more than beautiful schematic layout in v1.
