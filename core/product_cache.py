from __future__ import annotations

import hashlib
import json
from typing import Any


def normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    """Normalize listing source for stable duplicate detection.

    SKU, language and image URLs are intentionally excluded. Products with the same
    title/bullets/description/variant facts share one product-analysis cache entry.
    """
    return {
        "title": str(source.get("title", "") or "").strip(),
        "bullet_points": [str(x or "").strip() for x in source.get("bullet_points", []) or []],
        "description": str(source.get("description", "") or "").strip(),
        "color_or_variant": str(source.get("color_or_variant", "") or "").strip(),
    }


def product_fingerprint(source: dict[str, Any]) -> str:
    payload = json.dumps(normalize_source(source), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def result_fingerprint(source: dict[str, Any], language: str, schema: str = "v2.0-p1.4") -> str:
    payload = {
        "schema": schema,
        "language": language,
        "product": normalize_source(source),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
