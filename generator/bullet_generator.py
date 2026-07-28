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
    ]


    @staticmethod
    def generate(profile: dict) -> list:
        """
        Generate Amazon bullet points
        from Product Profile
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

        seo = profile.get(
            "seo",
            {})


        product_type = basic.get(
            "product_type",
            ""
        )


        main_function = basic.get(
            "main_function",
            ""
        )


        brands = compatibility.get(
            "brands",
            []
        )


        models = compatibility.get(
            "models",
            []
        )


        primary_keyword = ""

        keywords = seo.get(
            "primary_keywords",
            []
        )

        if keywords:
            primary_keyword = keywords[0]


        bullets = []


        # Bullet 1
        bullets.append(
            BulletGenerator.clean(
                f"{main_function.capitalize()} designed as a compatible replacement part for {brands[0] if brands else ''} {product_type.lower()}."
            )
        )


        # Bullet 2 - Models
        if models:

            model_text = ", ".join(
                models[:4]
            )

            bullets.append(
                BulletGenerator.clean(
                    f"Compatible with {brands[0] if brands else ''} models {model_text} for replacement use. Please confirm your appliance model before purchase."
                )
            )

        else:

            bullets.append(
                "Please confirm your appliance model before purchase to ensure compatibility."
            )


        # Bullet 3 - Material / Attribute

        material = attributes.get(
            "material",
            ""
        )

        color = attributes.get(
            "color",
            ""
        )


        attribute_parts = []


        if material:
            attribute_parts.append(
                f"Material: {material}"
            )


        if color:
            attribute_parts.append(
                f"Color: {color}"
            )


        if attribute_parts:

            bullets.append(
                BulletGenerator.clean(
                    " ".join(attribute_parts) + "."
                )
            )

        else:

            bullets.append(
                "Designed for replacing worn or damaged parts and helping restore normal appliance operation."
            )


        # Bullet 4 - Installation

        bullets.append(
            BulletGenerator.clean(
                "Designed for straightforward replacement installation. Check the existing part and appliance model before installation."
            )
        )


        # Bullet 5 - Compliance

        bullets.append(
            "Replacement component only. This product is not manufactured or endorsed by the original brand."
        )


        return bullets



    @staticmethod
    def clean(text: str) -> str:


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
