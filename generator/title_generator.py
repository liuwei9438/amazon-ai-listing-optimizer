from __future__ import annotations

import re


class TitleGenerator:

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
    ]

    @staticmethod
    def generate(profile: dict) -> dict:
        """
        Generate Amazon title from Product Profile
        """

        basic = profile.get("basic_info", {})
        compatibility = profile.get("compatibility", {})
        seo = profile.get("seo", {})

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

        primary_keywords = seo.get(
            "primary_keywords",
            []
        )

        title_parts = []

        # Compatible brand
        if brands:
            title_parts.append(
                f"Compatible with {brands[0]}"
            )

        # SEO keyword priority
        if primary_keywords:
            title_parts.append(
                primary_keywords[0]
            )
        elif main_function:
            title_parts.append(
                main_function
            )

        # Product type
        if product_type:
            title_parts.append(
                product_type
            )

        # Models
        if models:

            if len(models) <= 4:
                title_parts.extend(models)

            else:
                title_parts.extend(models[:3])
                title_parts.append("Series")

        title = " ".join(title_parts)

        title = TitleGenerator.clean_title(title)

        return {
            "title": title,
            "character_count": len(title),
            "validation": {
                "length_ok": len(title) <= 75,
                "compliance_ok": True
            }
        }


    @staticmethod
    def clean_title(text: str) -> str:

        for word in TitleGenerator.BLOCKED_WORDS:
            text = re.sub(
                word,
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
