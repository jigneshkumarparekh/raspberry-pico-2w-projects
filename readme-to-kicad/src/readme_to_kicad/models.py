from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


Severity = Literal["info", "warning", "error"]
PinScheme = Literal["physical", "gpio", "signal", "label", "alias"]


@dataclass(frozen=True)
class SourceSpan:
    line: int
    text: str


@dataclass
class Diagnostic:
    severity: Severity
    code: str
    message: str
    source_span: SourceSpan | None = None
    suggested_fix: str | None = None
    blocks_output: bool = False


@dataclass(frozen=True)
class RegistryPin:
    id: str
    number: str
    name: str
    aliases: list[str]
    schemes: list[PinScheme]
    electrical_type: str
    side: Literal["left", "right"] = "right"
    side_order: int | None = None
    shared_net: str | None = None


@dataclass(frozen=True)
class RegistryPart:
    id: str
    aliases: list[str]
    reference_prefix: str
    value: str
    symbol_library_id: str
    pins: list[RegistryPin]


@dataclass
class ComponentInstance:
    id: str
    reference: str
    registry_part_id: str
    display_name: str
    aliases_seen: list[str]
    confidence: float
    source_spans: list[SourceSpan] = field(default_factory=list)


@dataclass
class PinRef:
    component_id: str
    raw_text: str
    scheme: PinScheme
    normalized_pin_id: str
    confidence: float
    source_span: SourceSpan


@dataclass
class Connection:
    from_pin: PinRef
    to_pin: PinRef
    net_name: str
    confidence: float
    status: Literal["resolved", "ambiguous", "unresolved"]
    source_span: SourceSpan


@dataclass
class Circuit:
    project_name: str
    components: list[ComponentInstance]
    connections: list[Connection]
    diagnostics: list[Diagnostic]

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def has_blocking_diagnostics(self) -> bool:
        return any(d.blocks_output for d in self.diagnostics)
