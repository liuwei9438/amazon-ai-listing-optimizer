from __future__ import annotations

import re
from typing import Any

from .validator import shorten_at_word_boundary


def _clean_fact(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" ,;|")
    if re.fullmatch(r"\d+", text):
        return ""
    return text


def _append_unique(parts: list[str], value: Any) -> None:
    text = _clean_fact(value)
    if text and text.casefold() not in {item.casefold() for item in parts}:
        parts.append(text)


def fallback_short_title(
    analysis: dict[str, Any],
    profile: dict[str, Any],
    keywords: list[str],
) -> str:
    """
    Build Amazon Item Highlights from verified product facts.
    It is not a shortened title and does not mechanically copy brand/model text.
    """
    parts: list[str] = []

    # Highest-value factual highlights first.
    for value in [
        analysis.get("quantity", ""),
        analysis.get("dimensions", ""),
        analysis.get("material", ""),
    ]:
        _append_unique(parts, value)

    for field, limit in [
        ("functions", 4),
        ("structural_features", 3),
        ("usage_scenarios", 2),
        ("factual_selling_points", 3),
    ]:
        for value in (analysis.get(field, []) or [])[:limit]:
            _append_unique(parts, value)

    # Only use localized product keywords when source facts do not provide enough
    # useful highlights. Avoid a single-material or single-product-noun result.
    if len(parts) < 3:
        for value in keywords[:4]:
            _append_unique(parts, value)

    if len(parts) < 2:
        _append_unique(parts, analysis.get("core_product_name", ""))
        _append_unique(parts, analysis.get("product_type", ""))

    return shorten_at_word_boundary(
        ", ".join(parts),
        int(profile["short_limit"]),
    )
