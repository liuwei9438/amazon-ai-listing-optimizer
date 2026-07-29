from __future__ import annotations

import re


class BulletGenerator:

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
        "high quality",
    ]


    @staticmethod
    def generate(profile: dict) -> list:
        """
        Fact-driven Amazon bullet generator

        Only uses confirmed product facts.
        Does not invent:
        - material
        - durability
        - installation
        - performance
        """

        basic = profile.get(
            "basic_info",
            {}
        )

        compatibility = profile.get(
            "compatibility",
            {}
        )

        attributes = profile.get(
            "attributes",
            {}
        )

        usage = profile.get(
            "usage_scenarios",
            []
        )


        product_type = BulletGenerator.clean_text(
            basic.get("product_type", "")
        )

        main_function = BulletGenerator.clean_text(
            basic.get("main_function", "")
        )


        brands = compatibility.get(
            "brands",
            []
        )

        models = compatibility.get(
            "models",
            []
        )


        bullets = []


        # 1. Product function

        if main_function:

            bullets.append(
                f"{BulletGenerator.title(main_function)}. "
                f"Designed as a compatible replacement component for "
                f"{product_type.lower() if product_type else 'appliance parts'}."
            )


        # 2. Compatibility

        if brands or models:

            brand_text = ""

            if brands:
                brand_text = "Compatible with " + ", ".join(brands)

            model_text = ""

            if models:
                model_text = " models " + ", ".join(models)

            bullets.append(
                f"{brand_text}{model_text}. "
                f"Please confirm your appliance model before purchase."
            )


        # 3. Usage scenario

        if usage:

            usage_text = ", ".join(
                [
                    BulletGenerator.clean_text(x)
                    for x in usage
                    if x
                ]
            )

            if usage_text:

                bullets.append(
                    f"Suitable for {usage_text} when replacement is required."
                )


        # 4. Confirmed attributes only

        attribute_parts = []


        material = attributes.get(
            "material",
            ""
        )

        color = attributes.get(
            "color",
            ""
        )

        quantity = attributes.get(
            "quantity",
            ""
        )


        if material:

            attribute_parts.append(
                f"Material: {material}"
            )


        if color:

            attribute_parts.append(
                f"Color: {color}"
            )


        if quantity:

            attribute_parts.append(
                f"Quantity: {quantity}"
            )


        if attribute_parts:

            bullets.append(
                ". ".join(attribute_parts) + "."
            )


        # 5. Final verification

        bullets.append(
            "Please check the appliance model, part number and product details "
            "before ordering to ensure compatibility."
        )


        # Clean + remove duplicate

        result = []

        for bullet in bullets:

            bullet = BulletGenerator.clean(
                bullet
            )

            if bullet and bullet not in result:

                result.append(
                    bullet
                )


        # Amazon maximum 5 bullets

        return result[:5]


    @staticmethod
    def title(text):

        return text[:1].upper() + text[1:]


    @staticmethod
    def clean_text(text):

        if not text:

            return ""

        return str(text).strip()


    @staticmethod
    def clean(text):

        for word in BulletGenerator.BLOCKED_WORDS:

            text = re.sub(
                r"\b" + re.escape(word) + r"\b",
                "",
                text,
                flags=re.I
            )


        text = re.sub(
            r"\s+",
            " ",
            text
        )


        return text.strip()
