from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .product_cache import product_fingerprint


def group_duplicate_sources(items: Iterable[tuple[Any, dict[str, Any]]]) -> dict[str, list[tuple[Any, dict[str, Any]]]]:
    """Group identical source products before AI analysis/generation.

    This is deterministic deduplication, not an OpenAI batch endpoint. It avoids
    duplicate calls while preserving each source row/SKU in the final spreadsheet.
    """
    groups: dict[str, list[tuple[Any, dict[str, Any]]]] = defaultdict(list)
    for key, source in items:
        groups[product_fingerprint(source)].append((key, source))
    return dict(groups)
