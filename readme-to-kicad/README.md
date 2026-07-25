# README-to-KiCad

`readme-to-kicad` is a CLI tool that reads a circuit README, extracts supported
components and wiring statements, and writes a KiCad `.kicad_sch` schematic.

## Usage

Inspect the extracted circuit graph:

```bash
python3 -m readme_to_kicad inspect examples/pico_hcsr04.md --format json
```

Generate a schematic:

```bash
python3 -m readme_to_kicad generate examples/pico_hcsr04.md -o pico_hcsr04.kicad_sch
```

The v1 parser supports component lists, connection bullet lists, markdown wiring
tables, and simple connection prose. Ambiguous pin references are diagnosed
instead of guessed.
