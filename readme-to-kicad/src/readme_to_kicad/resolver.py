from __future__ import annotations

from collections import Counter

from .models import (
    Circuit,
    ComponentInstance,
    Connection,
    Diagnostic,
    PinRef,
    RegistryPart,
    SourceSpan,
)
from .parser import ParsedReadme
from .registry import Registry, normalize


POWER_NETS = {
    "3v3": "3V3",
    "3 3v": "3V3",
    "3v3 out": "3V3",
    "5v": "5V",
    "vbus": "VBUS",
    "vsys": "VSYS",
    "gnd": "GND",
    "ground": "GND",
    "agnd": "AGND",
}


def resolve(parsed: ParsedReadme, registry: Registry, project_name: str, strict: bool) -> Circuit:
    diagnostics: list[Diagnostic] = []
    components: dict[str, ComponentInstance] = {}
    references = Counter()

    for raw_component, span in parsed.components:
        candidate = _best_part(raw_component, registry)
        if not candidate:
            diagnostics.append(
                Diagnostic(
                    "error" if strict else "warning",
                    "unknown_component",
                    f"Could not match component '{raw_component}' to the registry.",
                    span,
                    "Add the component to the registry or use a supported alias.",
                    blocks_output=strict,
                )
            )
            continue
        part, alias, confidence = candidate
        _ensure_component(components, references, part, raw_component, alias, confidence, span)

    connections: list[Connection] = []
    for raw_connection in parsed.connections:
        left = _resolve_pin_endpoint(
            raw_connection.left, raw_connection.span, registry, components, references, diagnostics, strict
        )
        right = _resolve_pin_endpoint(
            raw_connection.right, raw_connection.span, registry, components, references, diagnostics, strict
        )
        if left is None or right is None:
            continue
        net_name = _net_name(left, right, registry, len(connections) + 1)
        connections.append(
            Connection(
                from_pin=left,
                to_pin=right,
                net_name=net_name,
                confidence=min(left.confidence, right.confidence, raw_connection.confidence),
                status="resolved",
                source_span=raw_connection.span,
            )
        )

    _detect_conflicts(connections, diagnostics, strict)
    return Circuit(project_name, list(components.values()), connections, diagnostics)


def _best_part(text: str, registry: Registry) -> tuple[RegistryPart, str, float] | None:
    candidates = registry.find_part_candidates(text)
    return candidates[0] if candidates else None


def _ensure_component(
    components: dict[str, ComponentInstance],
    references: Counter[str],
    part: RegistryPart,
    display_name: str,
    alias: str,
    confidence: float,
    span: SourceSpan,
) -> ComponentInstance:
    existing = next(
        (component for component in components.values() if component.registry_part_id == part.id),
        None,
    )
    if existing:
        if alias not in existing.aliases_seen:
            existing.aliases_seen.append(alias)
        if all(existing_span.line != span.line for existing_span in existing.source_spans):
            existing.source_spans.append(span)
        return existing

    references[part.reference_prefix] += 1
    reference = f"{part.reference_prefix}{references[part.reference_prefix]}"
    instance = ComponentInstance(
        id=_instance_id(part.id, references[part.reference_prefix]),
        reference=reference,
        registry_part_id=part.id,
        display_name=display_name,
        aliases_seen=[alias],
        confidence=confidence,
        source_spans=[span],
    )
    components[instance.id] = instance
    return instance


def _resolve_pin_endpoint(
    endpoint: str,
    span: SourceSpan,
    registry: Registry,
    components: dict[str, ComponentInstance],
    references: Counter[str],
    diagnostics: list[Diagnostic],
    strict: bool,
) -> PinRef | None:
    part_match = _best_part(endpoint, registry)
    if not part_match:
        diagnostics.append(
            Diagnostic(
                "error" if strict else "warning",
                "unknown_endpoint_component",
                f"Could not identify a component in endpoint '{endpoint}'.",
                span,
                "Use '<component> <pin>' such as 'Pico GPIO16'.",
                blocks_output=strict,
            )
        )
        return None

    part, alias, part_confidence = part_match
    component = _ensure_component(components, references, part, part.value, alias, part_confidence, span)
    raw_pin = _remove_alias(endpoint, alias)
    ambiguity = _ambiguous_plain_pin(raw_pin, part)
    if ambiguity:
        diagnostics.append(
            Diagnostic(
                "error" if strict else "warning",
                "ambiguous_pin_scheme",
                f"'{endpoint}' is ambiguous: specify GPIO, label, or physical pin explicitly.",
                span,
                "Use wording like 'Pico GPIO16' or 'Pico physical pin 21'.",
                blocks_output=strict,
            )
        )
        return None

    pin_match = _resolve_pin(part, raw_pin)
    if not pin_match:
        diagnostics.append(
            Diagnostic(
                "error" if strict else "warning",
                "unknown_pin",
                f"Could not match pin '{raw_pin or endpoint}' on {part.value}.",
                span,
                "Use a pin name or alias from the registry.",
                blocks_output=strict,
            )
        )
        return None

    pin, scheme, confidence = pin_match
    return PinRef(component.id, raw_pin, scheme, pin.id, min(confidence, part_confidence), span)


def _remove_alias(endpoint: str, alias: str) -> str:
    normalized_alias = normalize(alias)
    words = endpoint.split()
    for length in range(len(words), 0, -1):
        for start in range(0, len(words) - length + 1):
            phrase = " ".join(words[start : start + length])
            if normalize(phrase) == normalized_alias:
                remaining = [*words[:start], *words[start + length :]]
                return " ".join(remaining).strip(" :-")
    return endpoint.replace(alias, "", 1).strip(" :-")


def _ambiguous_plain_pin(raw_pin: str, part: RegistryPart) -> bool:
    text = normalize(raw_pin)
    if part.id != "pico_2w":
        return False
    return bool(text.startswith("pin ") and "physical" not in text and "gpio" not in text and "gp" not in text)


def _resolve_pin(part: RegistryPart, raw_pin: str):
    text = normalize(raw_pin)
    if text.startswith("physical pin "):
        wanted = text.removeprefix("physical pin ").strip()
        for pin in part.pins:
            if pin.number == wanted:
                return pin, "physical", 1.0
    if text.startswith("gpio "):
        text = text.replace("gpio ", "gpio", 1)
    if text.startswith("gp "):
        text = text.replace("gp ", "gp", 1)
    candidates = Registry({"part": part}).find_pin_candidates(part, text)
    if candidates:
        shared_nets = {pin.shared_net for pin, _alias, _confidence in candidates}
        if len(shared_nets) == 1 and None not in shared_nets:
            # Multiple physical pads can intentionally expose one logical net
            # (for example the three GND pads on a breakout). Resolve the
            # logical reference to the first physical pad in stable side order.
            candidates = sorted(
                candidates,
                key=lambda item: (
                    item[0].side,
                    item[0].side_order if item[0].side_order is not None else 10**9,
                    item[0].id,
                ),
            )[:1]
    for pin, _alias, confidence in candidates:
        scheme = _scheme_for(text, pin.schemes)
        return pin, scheme, confidence
    return None


def _scheme_for(text: str, schemes: list[str]) -> str:
    if text.startswith(("gp", "gpio")) and "gpio" in schemes:
        return "gpio"
    if "signal" in schemes:
        return "signal"
    if "label" in schemes:
        return "label"
    return schemes[0] if schemes else "alias"


def _net_name(left: PinRef, right: PinRef, registry: Registry, index: int) -> str:
    left_pin = _pin_for_ref(left, registry)
    right_pin = _pin_for_ref(right, registry)
    for pin in (left_pin, right_pin):
        power = POWER_NETS.get(normalize(pin.name))
        if power:
            return power
    for pin in (right_pin, left_pin):
        if pin.electrical_type in {"input", "output", "bidirectional"}:
            return normalize(pin.name).replace(" ", "_").upper()
    return f"NET_{index}"


def _pin_for_ref(ref: PinRef, registry: Registry):
    component_part_id = ref.component_id.rsplit("_", 1)[0]
    part = registry.parts[component_part_id]
    return next(pin for pin in part.pins if pin.id == ref.normalized_pin_id)


def _detect_conflicts(connections: list[Connection], diagnostics: list[Diagnostic], strict: bool) -> None:
    seen: dict[tuple[str, str], str] = {}
    for connection in connections:
        for pin in (connection.from_pin, connection.to_pin):
            key = (pin.component_id, pin.normalized_pin_id)
            existing = seen.get(key)
            if existing and existing != connection.net_name:
                diagnostics.append(
                    Diagnostic(
                        "error" if strict else "warning",
                        "conflicting_connection",
                        f"{pin.component_id}.{pin.normalized_pin_id} is connected to both "
                        f"{existing} and {connection.net_name}.",
                        pin.source_span,
                        "Keep only one intended connection or name the shared net explicitly.",
                        blocks_output=strict,
                    )
                )
            seen[key] = connection.net_name


def _instance_id(part_id: str, index: int) -> str:
    return f"{part_id}_{index}"
