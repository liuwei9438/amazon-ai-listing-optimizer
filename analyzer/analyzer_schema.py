from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProductAnalysis:
    row_number: int
    sku: str = ""
    product_type: str = ""
    brand: str = ""
    compatible_brands: tuple[str, ...] = ()
    compatible_models: tuple[str, ...] = ()
    material: str = ""
    color: str = ""
    quantity: str = ""
    dimensions: str = ""
    weight: str = ""
    applications: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    evidence: dict[str, tuple[str, ...]] = field(default_factory=dict)
    source_text: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    severity: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    issues: tuple[ValidationIssue, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [asdict(issue) for issue in self.issues],
        }
