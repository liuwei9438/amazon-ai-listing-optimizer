
from __future__ import annotations

import re
from typing import Any


COLOR_LIST = {
    "black", "white", "silver", "gray", "grey",
    "red", "blue", "green", "yellow",
    "orange", "pink", "purple", "gold",
    "brown", "beige"
}


MATERIAL_LIST = {
    "abs": "ABS",
    "plastic": "Plastic",
    "pp": "PP",
    "pvc": "PVC",
    "aluminum": "Aluminum",
    "aluminium": "Aluminum",
    "metal": "Metal",
    "rubber": "Rubber",
    "silicone": "Silicone",
    "glass": "Glass",
}


def _text_from_record(record: Any) -> str:
    values = []

    for key in [
        "title",
        "description",
        "details",
        "material",
        "color",
    ]:
        value = getattr(record, key, "")
        if value:
            values.append(str(value))

    bullets = getattr(record, "bullets", [])
    if isinstance(bullets, list):
        values.extend(str(x) for x in bullets)

    return " ".join(values)


def extract_quantity(text: str) -> dict[str, str]:
    match = re.search(
        r"\b(\d+)\s*(pack|packs|pcs|pieces|piece|set|sets)\b",
        text,
        re.IGNORECASE,
    )

    if match:
        return {
            "value": match.group(1),
            "unit": match.group(2),
        }

    return {
        "value": "",
        "unit": "",
    }


def extract_material(text: str) -> list[str]:
    result = []
    lower = text.lower()

    for key, value in MATERIAL_LIST.items():
        if key in lower:
            result.append(value)

    return list(dict.fromkeys(result))


def extract_color(text: str) -> list[str]:
    result = []

    words = re.findall(r"\b[a-zA-Z]+\b", text)

    for word in words:
        if word.lower() in COLOR_LIST:
            result.append(word.capitalize())

    return list(dict.fromkeys(result))


def extract_basic_attributes(record: Any) -> dict[str, Any]:
    """
    Task 3.1A:
    Standalone attribute extraction.

    Current scope:
    - quantity
    - material
    - color

    Only extracts explicit text facts.
    Does not guess from images.
    """

    text = _text_from_record(record)

    return {
        "quantity": extract_quantity(text),
        "material": extract_material(text),
        "color": extract_color(text),
    }
