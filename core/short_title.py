from __future__ import annotations

from typing import Any

from .validator import shorten_at_word_boundary


def fallback_short_title(analysis: dict[str, Any], profile: dict[str, Any], keywords: list[str]) -> str:
    parts: list[str] = []
    product_type = str(analysis.get("product_type", "") or "").strip()
    material = str(analysis.get("material", "") or "").strip()
    if keywords:
        parts.append(keywords[0])
    elif product_type:
        parts.append(product_type)
    if material:
        parts.append(material)
    return shorten_at_word_boundary(" ".join(parts), int(profile["short_limit"]))
