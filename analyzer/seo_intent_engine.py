
from __future__ import annotations

from typing import Any
import re


IGNORE_WORDS = {
    "compatible",
    "replacement",
    "replace",
    "for",
    "original",
    "oem",
    "official",
    "genuine",
}


def _clean_words(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    return [
        w for w in words
        if w not in IGNORE_WORDS
    ]


def _normalize_product_type(product_type: str) -> str:
    value = product_type.lower()

    replacements = {
        "washing machine part": "washing machine",
        "appliance part": "appliance",
        "printer part": "printer",
        "shaver part": "electric shaver",
    }

    return replacements.get(value, product_type)


def generate_primary_search(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Generate the main search phrase from Product Profile.

    Priority:
    1. Product category
    2. Main function
    3. Remove brand/model/compatibility words
    """

    product_type = profile.get("product_type", "")
    attributes = profile.get("attributes", {})

    functions = (
        attributes.get("functions")
        or attributes.get("function")
        or []
    )

    if isinstance(functions, str):
        functions = [functions]

    category = _normalize_product_type(product_type)

    function_text = ""
    if functions:
        function_text = " ".join(
            _clean_words(functions[0])
        )

    category_words = _clean_words(category)

    result = " ".join(
        category_words + _clean_words(function_text)
    ).strip()

    if not result:
        result = "replacement part"

    return {
        "primary_search": [
            result
        ]
    }
