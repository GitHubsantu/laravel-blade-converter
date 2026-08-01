"""Statistics/report object produced by ConverterEngine.convert()."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConversionReport:
    file_name: str = ""
    forms_replaced: int = 0
    labels_replaced: int = 0
    buttons_replaced: int = 0
    inputs_replaced: int = 0
    selects_replaced: int = 0
    textareas_replaced: int = 0
    checkboxes_replaced: int = 0
    radios_replaced: int = 0
    links_replaced: int = 0
    warnings: List[str] = field(default_factory=list)

    @property
    def total_replacements(self) -> int:
        return (
            self.forms_replaced
            + self.labels_replaced
            + self.buttons_replaced
            + self.inputs_replaced
            + self.selects_replaced
            + self.textareas_replaced
            + self.checkboxes_replaced
            + self.radios_replaced
            + self.links_replaced
        )

    def bump(self, key: str, amount: int = 1) -> None:
        current = getattr(self, key, None)
        if current is None:
            raise AttributeError(f"Unknown report field: {key}")
        setattr(self, key, current + amount)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: "ConversionReport") -> None:
        self.forms_replaced += other.forms_replaced
        self.labels_replaced += other.labels_replaced
        self.buttons_replaced += other.buttons_replaced
        self.inputs_replaced += other.inputs_replaced
        self.selects_replaced += other.selects_replaced
        self.textareas_replaced += other.textareas_replaced
        self.checkboxes_replaced += other.checkboxes_replaced
        self.radios_replaced += other.radios_replaced
        self.links_replaced += other.links_replaced
        self.warnings.extend(other.warnings)

    def as_dict(self) -> Dict[str, int]:
        return {
            "Forms replaced": self.forms_replaced,
            "Labels replaced": self.labels_replaced,
            "Buttons replaced": self.buttons_replaced,
            "Inputs replaced": self.inputs_replaced,
            "Selects replaced": self.selects_replaced,
            "Textareas replaced": self.textareas_replaced,
            "Checkboxes replaced": self.checkboxes_replaced,
            "Radios replaced": self.radios_replaced,
            "Links replaced": self.links_replaced,
            "Warnings": len(self.warnings),
            "Total replacements": self.total_replacements,
        }
