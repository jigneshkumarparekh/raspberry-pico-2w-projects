# README-to-KiCad

`readme-to-kicad` is a CLI tool that reads a circuit README, extracts supported
components and wiring statements, and writes a KiCad `.kicad_sch` schematic.

## Setup

From the project directory, create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, use:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the package and its development dependencies in the active virtual
environment:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

You only need to install the dependencies once for this virtual environment.
After deactivating it, reactivate it with `source .venv/bin/activate` and
continue working. Reinstall dependencies only if you recreate `.venv`, change
the project dependencies, or move to another machine or environment.

The runtime package has no required third-party dependencies. If YAML support
is needed, install the optional dependency as well:

```bash
python -m pip install -e ".[yaml]"
```

## Usage

Inspect the extracted circuit graph:

```bash
readme-to-kicad inspect examples/pico_hcsr04.md --format json
```

Generate a schematic:

```bash
readme-to-kicad generate examples/pico_hcsr04.md -o pico_hcsr04.kicad_sch
```

You can also run the module directly:

```bash
python -m readme_to_kicad generate examples/pico_hcsr04.md -o pico_hcsr04.kicad_sch
```

Run the test suite with:

```bash
python -m pytest
```

The v1 parser supports component lists, connection bullet lists, markdown wiring
tables, and simple connection prose. Ambiguous pin references are diagnosed
instead of guessed.
