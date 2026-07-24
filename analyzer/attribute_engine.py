
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

    for key in ["title", "description", "details", "material", "color"]:
        value = getattr(record, key, "")
        if value:
            values.append(str(value))

    bullets = getattr(record, "bullets", [])
    if isinstance(bullets, list):
        values.extend(str(x) for x in bullets)

    return " ".join(values)


def extract_quantity(text: str):
    match = re.search(r"\b(\d+)\s*(pack|packs|pcs|pieces|piece|set|sets)\b", text, re.I)
    if match:
        return {"value": match.group(1), "unit": match.group(2)}
    return {"value": "", "unit": ""}


def extract_material(text: str):
    result = []
    lower = text.lower()
    for key, value in MATERIAL_LIST.items():
        if key in lower:
            result.append(value)
    return list(dict.fromkeys(result))


def extract_color(text: str):
    result = []
    for word in re.findall(r"\b[a-zA-Z]+\b", text):
        if word.lower() in COLOR_LIST:
            result.append(word.capitalize())
    return list(dict.fromkeys(result))


def _extract_value_unit(text: str, units):
    pattern = r"(?<![A-Za-z])(\d+(?:\.\d+)?)\s*(" + "|".join(units) + r")\b"
    match = re.search(pattern, text, re.I)
    if match:
        return {
            "value": match.group(1),
            "unit": match.group(2).upper()
        }
    return {"value": "", "unit": ""}


def extract_voltage(text: str):
    return _extract_value_unit(text, ["V", "volt", "volts"])


def extract_power(text: str):
    return _extract_value_unit(text, ["W", "watt", "watts"])


def extract_dimensions(text: str):
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*(mm|cm|inch|in)?",
        text,
        re.I,
    )

    if match:
        return {
            "length": match.group(1),
            "width": match.group(2),
            "height": match.group(3),
            "unit": match.group(4) or ""
        }

    return {
        "length": "",
        "width": "",
        "height": "",
        "unit": ""
    }


def extract_package_contents(text: str):
    """
    Extract only explicitly stated package contents.
    Does not infer accessories from product type.
    """

    results = []

    patterns = [
        r"(?:package includes|package contains|includes|contents include)[:\s]+([^\n.]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            content = match.group(1)
            parts = re.split(r",|;|\n", content)
            for part in parts:
                item = part.strip()
                if item:
                    results.append(item)

    return list(dict.fromkeys(results))


def extract_basic_attributes(record: Any):
    text = _text_from_record(record)

    return {
        "quantity": extract_quantity(text),
        "material": extract_material(text),
        "color": extract_color(text),
        "voltage": extract_voltage(text),
        "power": extract_power(text),
        "dimensions": extract_dimensions(text),
        "package_contents": extract_package_contents(text),
    }
