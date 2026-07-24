
from __future__ import annotations

import re
from typing import Any


PROHIBITED_TERMS = {
    "original",
    "genuine",
    "official",
    "oem",
    "authentic",
    "best seller",
    "#1",
    "premium quality",
}

DEFAULT_BRANDS = {
    "LG",
    "Dyson",
    "Epson",
    "Samsung",
    "Bosch",
    "Philips",
    "Whirlpool",
}


def remove_prohibited_terms(text: str) -> str:
    result = text

    for term in PROHIBITED_TERMS:
        result = re.sub(
            rf"\b{re.escape(term)}\b",
            "",
            result,
            flags=re.IGNORECASE,
        )

    return re.sub(r"\s+", " ", result).strip()


def ensure_compatible_expression(
    text: str,
    brands: list[str] | None = None,
) -> dict[str, Any]:
    brands = brands or list(DEFAULT_BRANDS)

    cleaned = remove_prohibited_terms(text)

    detected = [
        brand
        for brand in brands
        if re.search(rf"\b{re.escape(brand)}\b", cleaned, re.IGNORECASE)
    ]

    changes = []

    if detected and not re.search(
        r"compatible\s+with",
        cleaned,
        re.IGNORECASE,
    ):
        brand_text = ", ".join(detected)

        cleaned = (
            re.sub(
                r"^for\s+",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            + f" Compatible with {brand_text} models"
        )

        changes.append("Added compatibility wording")

    if cleaned != text:
        changes.append("Removed prohibited terms")

    return {
        "text": cleaned.strip(),
        "changes": changes,
        "risk": "low" if not detected or "Compatible with" in cleaned else "review",
        "detected_brands": detected,
    }


def protect_text(
    text: str,
    detected_brands: list[str] | None = None,
) -> dict[str, Any]:
    return ensure_compatible_expression(text, detected_brands)
