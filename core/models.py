from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class FieldMap:
    title: str | None = None
    short_title: str | None = None
    description: str | None = None
    images: str | None = None
    sku: str | None = None
    language: str | None = None
    bullets: tuple[str, ...] = ()


@dataclass
class WorkbookEnvelope:
    """Immutable source workbook plus a tabular view used by later modules.

    V2.2.1 deliberately exports ``raw_bytes`` unchanged. This guarantees that
    columns, formulas, formatting, hyperlinks and embedded images are not lost
    while the new modular pipeline is being established.
    """

    filename: str
    raw_bytes: bytes
    dataframe: pd.DataFrame
    sheet_name: str
    fields: FieldMap
    diagnostics: dict[str, Any] = field(default_factory=dict)
