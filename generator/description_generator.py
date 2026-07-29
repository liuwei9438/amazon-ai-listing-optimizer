from __future__ import annotations

import re


class DescriptionGenerator:
    """
    Generate Amazon product description from Product Profile.

    Current version:
    - Uses only confirmed product facts
    - Preserves compatible brands and models
    - Avoids unsupported material, size, package, or performance claims
    - Removes prohibited promotional wording
    """

    BLOCKED_WORDS = [
        "best",
        "best seller",
        "#1",
        "premium",
        "original",
        "genuine",
        "official",
        "authentic",
        "hot sale",
        "discount",
        "promotion",
        "top quality",
        "perfect",
    ]

    @staticmethod
    def generate(profile: dict) -> dict:
        basic = profile.get("basic_info", {})
        compatibility = profile.get("compatibility", {})
        attributes = profile.get("attributes", {})

        product_type = DescriptionGenerator._safe_text(
            basic.get("product_type", "")
        )

        main_function = DescriptionGenerator._safe_text(
            basic.get("main_function", "")
        )

        brands = DescriptionGenerator._clean_list(
            compatibility.get("brands", [])
        )

        models = DescriptionGenerator._clean_list(
            compatibility.get("models", [])
        )

        quantity = attributes.get("quantity", "")
        material = attributes.get("material", "")
        color = attributes.get("color", "")
        dimensions = attributes.get("dimensions", {})
        package_contents = attributes.get("package_contents", [])
        installation = attributes.get("installation", [])

        sections = []

        # 1. Product introduction
        intro = DescriptionGenerator._build_intro(
            product_type=product_type,
            main_function=main_function,
            brands=brands,
        )
        if intro:
            sections.append(intro)

        # 2. Compatibility information
        compatibility_section = DescriptionGenerator._build_compatibility(
            brands=brands,
            models=models,
        )
        if compatibility_section:
            sections.append(compatibility_section)

        # 3. Confirmed attributes only
        attribute_section = DescriptionGenerator._build_attributes(
            quantity=quantity,
            material=material,
            color=color,
            dimensions=dimensions,
            package_contents=package_contents,
        )
        if attribute_section:
            sections.append(attribute_section)

        # 4. Installation information
        installation_section = DescriptionGenerator._build_installation(
            installation=installation
        )
        if installation_section:
            sections.append(installation_section)

        # 5. Purchase reminder
        sections.append(
            "Please verify your appliance model, part number, product appearance, "
            "and required specifications before ordering."
        )

        cleaned_sections = []

        for section in sections:
            cleaned = DescriptionGenerator.clean(section)

            if cleaned and cleaned not in cleaned_sections:
                cleaned_sections.append(cleaned)

        description = "\n\n".join(cleaned_sections)

        return {
            "description": description,
            "sections": cleaned_sections,
            "character_count": len(description),
            "validation": {
                "has_content": bool(description),
                "compliance_ok": not DescriptionGenerator.check_blocked_words(
                    description
                ),
            },
            "blocked_words": DescriptionGenerator.check_blocked_words(
                description
            ),
        }

    @staticmethod
    def _build_intro(
        product_type: str,
        main_function: str,
        brands: list[str],
    ) -> str:
        subject = product_type or "replacement component"

        if main_function:
            function_text = main_function
        else:
            function_text = "replace a worn or damaged component"

        if brands:
            brand_text = f" compatible with {brands[0]} appliances"
        else:
            brand_text = ""

        return (
            f"This {subject.lower()} is designed to {function_text.lower()}"
            f"{brand_text}. It is intended for replacement use when the existing "
            f"component is worn, damaged, or no longer functioning correctly."
        )

    @staticmethod
    def _build_compatibility(
        brands: list[str],
        models: list[str],
    ) -> str:
        if not brands and not models:
            return ""

        parts = []

        if brands:
            parts.append(f"Compatible with {brands[0]}")

        if models:
            parts.append("models " + ", ".join(models))

        return (
            " ".join(parts)
            + ". Please compare the model number and existing part before purchase."
        )

    @staticmethod
    def _build_attributes(
        quantity,
        material,
        color,
        dimensions,
        package_contents,
    ) -> str:
        facts = []

        quantity_text = DescriptionGenerator._format_attribute_value(quantity)
        material_text = DescriptionGenerator._format_attribute_value(material)
        color_text = DescriptionGenerator._format_attribute_value(color)

        if quantity_text:
            facts.append(f"Quantity: {quantity_text}")

        if material_text:
            facts.append(f"Material: {material_text}")

        if color_text:
            facts.append(f"Color: {color_text}")

        dimension_text = DescriptionGenerator._format_dimensions(dimensions)

        if dimension_text:
            facts.append(f"Dimensions: {dimension_text}")

        package_items = DescriptionGenerator._clean_list(package_contents)

        if package_items:
            facts.append("Package contents: " + ", ".join(package_items))

        if not facts:
            return ""

        return ". ".join(facts) + "."

    @staticmethod
    def _build_installation(installation) -> str:
        steps = DescriptionGenerator._clean_list(installation)

        if steps:
            return "Installation information: " + " ".join(steps)

        return (
            "Installation requirements may vary by appliance model. Disconnect the "
            "appliance from power before installation and seek qualified assistance "
            "when necessary."
        )

    @staticmethod
    def _format_dimensions(dimensions) -> str:
        if not isinstance(dimensions, dict):
            return ""

        length = DescriptionGenerator._safe_text(
            dimensions.get("length", "")
        )
        width = DescriptionGenerator._safe_text(
            dimensions.get("width", "")
        )
        height = DescriptionGenerator._safe_text(
            dimensions.get("height", "")
        )
        unit = DescriptionGenerator._safe_text(
            dimensions.get("unit", "")
        )

        values = [value for value in [length, width, height] if value]

        if not values:
            return ""

        dimension_text = " × ".join(values)

        if unit:
            dimension_text += f" {unit}"

        return dimension_text

    @staticmethod
    def _format_attribute_value(value) -> str:
        if isinstance(value, list):
            return ", ".join(DescriptionGenerator._clean_list(value))

        if isinstance(value, dict):
            raw_value = DescriptionGenerator._safe_text(
                value.get("value", "")
            )
            unit = DescriptionGenerator._safe_text(
                value.get("unit", "")
            )

            return " ".join(
                part for part in [raw_value, unit] if part
            )

        return DescriptionGenerator._safe_text(value)

    @staticmethod
    def _clean_list(values) -> list[str]:
        if not isinstance(values, list):
            return []

        result = []
        seen = set()

        for value in values:
            text = DescriptionGenerator._safe_text(value)

            if not text:
                continue

            key = text.lower()

            if key in seen:
                continue

            seen.add(key)
            result.append(text)

        return result

    @staticmethod
    def _safe_text(value) -> str:
        if value is None:
            return ""

        if isinstance(value, (dict, list, tuple, set)):
            return ""

        return str(value).strip()

    @staticmethod
    def clean(text: str) -> str:
        for word in DescriptionGenerator.BLOCKED_WORDS:
            text = re.sub(
                r"\b" + re.escape(word) + r"\b",
                "",
                text,
                flags=re.I,
            )

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" +([,.;:])", r"\1", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def check_blocked_words(text: str) -> list[str]:
        found = []

        for word in DescriptionGenerator.BLOCKED_WORDS:
            if re.search(
                r"\b" + re.escape(word) + r"\b",
                text,
                flags=re.I,
            ):
                found.append(word)

        return found
