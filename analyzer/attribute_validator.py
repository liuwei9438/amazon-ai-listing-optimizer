from __future__ import annotations

from typing import Any


VALID_COLORS = {
    "black", "white", "silver", "gray", "grey",
    "red", "blue", "green", "yellow",
    "orange", "pink", "purple", "gold",
    "brown", "beige",
}

VALID_MATERIALS = {
    "abs": "ABS",
    "pp": "PP",
    "pvc": "PVC",
    "aluminum": "Aluminum",
    "aluminium": "Aluminum",
    "metal": "Metal",
    "rubber": "Rubber",
    "silicone": "Silicone",
    "glass": "Glass",
}


def validate_color(attributes: dict[str, Any]) -> dict[str, Any]:
    colors = attributes.get("color", [])

    if not isinstance(colors, list):
        colors = []

    cleaned = []

    for color in colors:
        if not isinstance(color, str):
            continue

        value = color.strip().lower()

        if value in VALID_COLORS:
            cleaned.append(color.strip().capitalize())

    attributes["color"] = list(dict.fromkeys(cleaned))
    return attributes


def validate_material(attributes: dict[str, Any]) -> dict[str, Any]:
    """
    Keep only explicit material names.
    Remove marketing descriptions and unsupported material text.
    """

    materials = attributes.get("material", [])

    if not isinstance(materials, list):
        materials = []

    cleaned = []

    for material in materials:
        if not isinstance(material, str):
            continue

        value = material.strip().lower()

        if value in VALID_MATERIALS:
            cleaned.append(VALID_MATERIALS[value])

    attributes["material"] = list(dict.fromkeys(cleaned))
    return attributes


def validate_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    attributes = validate_color(attributes)
    attributes = validate_material(attributes)

    return attributes
