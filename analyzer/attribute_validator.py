from __future__ import annotations

from typing import Any


VALID_COLORS = {
    "black", "white", "silver", "gray", "grey",
    "red", "blue", "green", "yellow",
    "orange", "pink", "purple", "gold",
    "brown", "beige",
}


def validate_color(attributes: dict[str, Any]) -> dict[str, Any]:
    """
    Keep only explicit standard colors.
    Remove product names, marketing words, and model numbers.
    """

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


def validate_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    """
    Current scope:
    - color validation

    Future scope:
    - material
    - quantity
    - electrical parameters
    """

    return validate_color(attributes)
