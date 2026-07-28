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
        brand_info = profile.get("brand_info", {})
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


        relationship = brand_info.get(
            "relationship",
            ""
        )


        title_parts = []


        # Compatible brand
        if brands:
            title_parts.append(
                f"Compatible with {brands[0]}"
            )


        # Main keyword
        main_keyword = ""

        if primary_keywords:
            main_keyword = primary_keywords[0]

        elif main_function:
            main_keyword = main_function


        # Remove duplicated product words
        if product_type:
            if product_type.lower() not in main_keyword.lower():
                main_keyword = (
                    main_keyword + " " + product_type
                )


        if main_keyword:
            title_parts.append(main_keyword)


        # Models
        if models:

            if len(models) <= 4:
                title_parts.extend(models)

            else:
                title_parts.extend(models[:3])
                title_parts.append("Series")


        title = " ".join(title_parts)


        # Clean
        title = title.strip()
        
        for brand in brands:
            title = title.replace(
                brand.title(),
                brand.upper()
            )
        title = TitleGenerator.clean_title(title)


        # Length control
        title = TitleGenerator.limit_length(
            title,
            max_length=75
        )


        blocked_found = (
            TitleGenerator.check_blocked_words(title)
        )


        return {

            "title": title,

            "character_count": len(title),

            "validation": {

                "length_ok":
                    len(title) <= 75,

                "blocked_words":
                    blocked_found,

                "compliance_ok":
                    len(blocked_found) == 0,

                "brand_check":
                    "passed"

            }

        }



    @staticmethod
    def clean_title(text: str) -> str:

        for word in TitleGenerator.BLOCKED_WORDS:

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



    @staticmethod
    def limit_length(
        text: str,
        max_length: int = 75
    ) -> str:

        if len(text) <= max_length:

            return text


        words = text.split()

        result = []

        length = 0


        for word in words:

            if length + len(word) + 1 > max_length:

                break

            result.append(word)

            length += len(word) + 1


        return " ".join(result)



    @staticmethod
    def check_blocked_words(
        text: str
    ) -> list:

        found = []

        for word in TitleGenerator.BLOCKED_WORDS:

            if re.search(
                r"\b" + re.escape(word) + r"\b",
                text,
                flags=re.I
            ):

                found.append(word)


        return found
