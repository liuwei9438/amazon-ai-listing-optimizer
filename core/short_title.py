from __future__ import annotations

from typing import Any

from .validator import shorten_at_word_boundary


def fallback_short_title(analysis: dict[str, Any], profile: dict[str, Any], keywords: list[str]) -> str:
    """Build a safe Amazon Item Highlights fallback from verified facts only."""
    parts: list[str] = []
    priority_fields = [
        analysis.get("quantity", ""),
        analysis.get("material", ""),
        *(analysis.get("functions", []) or [])[:3],
        *(analysis.get("usage_scenarios", []) or [])[:2],
        *(analysis.get("factual_selling_points", []) or [])[:3],
        analysis.get("dimensions", ""),
    ]
    product_type = str(analysis.get("product_type", "") or "").strip()
    if product_type:
        parts.append(product_type)
    for value in priority_fields:
        text = str(value or "").strip()
        if text and text.casefold() not in {x.casefold() for x in parts}:
            parts.append(text)
    if len(parts) < 3:
        for kw in keywords[:4]:
            text = str(kw or "").strip()
            if text and text.casefold() not in {x.casefold() for x in parts}:
                parts.append(text)
    return shorten_at_word_boundary(", ".join(parts), int(profile["short_limit"]))
