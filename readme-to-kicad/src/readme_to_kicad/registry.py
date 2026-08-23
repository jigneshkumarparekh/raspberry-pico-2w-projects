from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from .models import RegistryPart, RegistryPin


class RegistryError(ValueError):
    pass


class Registry:
    def __init__(self, parts: dict[str, RegistryPart]) -> None:
        self.parts = parts

    @classmethod
    def bundled(cls) -> "Registry":
        with resources.files("readme_to_kicad.data").joinpath("components.json").open(
            encoding="utf-8"
        ) as handle:
            return cls.from_mapping(json.load(handle))

    @classmethod
    def from_path(cls, path: Path) -> "Registry":
        if path.suffix.lower() == ".json":
            return cls.from_mapping(json.loads(path.read_text(encoding="utf-8")))
        if path.suffix.lower() in {".yml", ".yaml"}:
            try:
                import yaml  # type: ignore[import-not-found]
            except ModuleNotFoundError as exc:
                raise RegistryError(
                    "YAML registries require PyYAML. Install the package with the 'yaml' extra "
                    "or use a JSON registry file."
                ) from exc
            return cls.from_mapping(yaml.safe_load(path.read_text(encoding="utf-8")))
        raise RegistryError(f"Unsupported registry format: {path}")

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Registry":
        if data.get("schema_version") != 1:
            raise RegistryError("Registry schema_version must be 1.")
        raw_parts = data.get("parts")
        if not isinstance(raw_parts, dict):
            raise RegistryError("Registry must contain a 'parts' mapping.")

        parts: dict[str, RegistryPart] = {}
        for part_id, raw in raw_parts.items():
            pins = [
                RegistryPin(
                    id=str(pin["id"]),
                    number=str(pin["number"]),
                    name=str(pin["name"]),
                    aliases=[str(alias) for alias in pin.get("aliases", [])],
                    schemes=list(pin.get("schemes", ["label"])),
                    electrical_type=str(pin.get("electrical_type", "passive")),
                    side=pin.get("side", "right"),
                    side_order=(int(pin["side_order"]) if "side_order" in pin else None),
                    shared_net=(str(pin["shared_net"]) if pin.get("shared_net") is not None else None),
                )
                for pin in raw.get("pins", [])
            ]
            parts[str(part_id)] = RegistryPart(
                id=str(part_id),
                aliases=[str(alias) for alias in raw.get("aliases", [])],
                reference_prefix=str(raw["reference_prefix"]),
                value=str(raw["value"]),
                symbol_library_id=str(raw["symbol_library_id"]),
                pins=pins,
            )
        return cls(parts)

    def find_part_candidates(self, text: str) -> list[tuple[RegistryPart, str, float]]:
        normalized = normalize(text)
        candidates: list[tuple[RegistryPart, str, float]] = []
        for part in self.parts.values():
            aliases = [part.value, part.id, *part.aliases]
            for alias in aliases:
                alias_norm = normalize(alias)
                if alias_norm and alias_norm in normalized:
                    score = min(1.0, 0.5 + len(alias_norm) / max(len(normalized), 1))
                    candidates.append((part, alias, score))
        candidates.sort(key=lambda item: (item[2], len(item[1])), reverse=True)
        return candidates

    def find_pin_candidates(self, part: RegistryPart, raw_pin: str) -> list[tuple[RegistryPin, str, float]]:
        pin_text = normalize(raw_pin)
        candidates: list[tuple[RegistryPin, str, float]] = []
        for pin in part.pins:
            for alias in [pin.name, pin.id, pin.number, *pin.aliases]:
                alias_norm = normalize(alias)
                if alias_norm and alias_norm == pin_text:
                    candidates.append((pin, alias, 1.0))
                elif alias_norm and alias_norm in pin_text:
                    candidates.append((pin, alias, 0.8))
        candidates.sort(key=lambda item: item[2], reverse=True)
        return candidates


def normalize(text: str) -> str:
    return " ".join(
        "".join(char.lower() if char.isalnum() else " " for char in text).split()
    )
