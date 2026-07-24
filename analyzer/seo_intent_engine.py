
from __future__ import annotations

from typing import Any
import re


IGNORE_WORDS = {
    "compatible",
    "compatiblewith",
    "for",
    "function",
    "power",
    "drive",
    "button",
    "part",
    "replacement",
    "replace",
}


CATEGORY_MAP = {
    "washing machine part": "washing machine",
    "washing machine": "washing machine",
    "printer part": "printer",
    "printer": "printer",
    "shaver part": "electric shaver",
    "shaver": "electric shaver",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text).lower())


def _clean_function(text: str) -> list[str]:
    words = _words(text)

    result = []
    for word in words:
        if word in IGNORE_WORDS:
            continue
        result.append(word)

    return result


def _normalize_category(value: str) -> str:
    value = str(value).lower().strip()

    for key, result in CATEGORY_MAP.items():
        if key in value:
            return result

    return value


def generate_primary_search(profile: dict[str, Any]) -> dict[str, Any]:
    """
    Generate Amazon-style primary search phrase.

    Structure:
    product category + core function

    Brand/model/compatibility information should be handled
    by secondary search, not primary search.
    """

    basic_info = profile.get("basic_info", {})
    attributes = profile.get("attributes", {})

    product_type = (
        profile.get("product_type")
        or basic_info.get("product_type")
        or ""
    )

    category = _normalize_category(product_type)

    functions = (
        attributes.get("functions")
        or attributes.get("function")
        or []
    )

    if isinstance(functions, str):
        functions = [functions]

    function_text = " ".join(functions)

    function_words = _clean_function(function_text)

    # Special handling for common compound entities
    if "start" in function_words and "button" in function_words:
        function_phrase = "start button"
    elif "print" in function_words and "head" in function_words:
        function_phrase = "print head"
    elif "head" in function_words:
        function_phrase = "head"
    else:
        function_phrase = " ".join(function_words[:3])

    result = " ".join(
        part for part in [category, function_phrase]
        if part
    ).strip()

    if not result:
        result = "replacement part"

    return {
        "primary_search": [
            result
        ]
    }
