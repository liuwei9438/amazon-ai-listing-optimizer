from __future__ import annotations

import re
from typing import Any

from .validator import shorten_at_word_boundary


def _clean_fact(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" ,;|")
    if re.fullmatch(r"\d+", text):
        return ""
    return text


def fallback_short_title(analysis: dict[str, Any], profile: dict[str, Any], keywords: list[str]) -> str:
    """Build Item Highlights from verified facts, not from a truncated title."""
    parts: list[str] = []

    # Quantity/size/material/function/scene/selling point order follows the
    # user's operational requirement for Amazon Item Highlights.
    priority_fields = [
        analysis.get("quantity", ""),
        analysis.get("dimensions", ""),
        analysis.get("material", ""),
        *(analysis.get("functions", []) or [])[:4],
        *(analysis.get("usage_scenarios", []) or [])[:3],
        *(analysis.get("factual_selling_points", []) or [])[:4],
    ]

    for value in priority_fields:
        text = _clean_fact(value)
        if text and text.casefold() not in {x.casefold() for x in parts}:
            parts.append(text)

    # Localized keywords are preferable to the English product type for
    # non-English fallbacks.
    for value in keywords[:4]:
        text = _clean_fact(value)
        if text and text.casefold() not in {x.casefold() for x in parts}:
            parts.append(text)

    if not parts:
        product_type = _clean_fact(analysis.get("product_type", ""))
        if product_type:
            parts.append(product_type)

    return shorten_at_word_boundary(", ".join(parts), int(profile["short_limit"]))
