from __future__ import annotations

import re


class ShortTitleGenerator:


    """
    Generate Amazon short title.

    Purpose:
    - Compact product summary
    - Keyword focused
    - Human readable

    Rules:
    - No invented features
    - No marketing words
    - Brand compatibility protected
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
        "discount",
        "promotion",
        "perfect"

    ]



    @staticmethod
    def generate(
        profile: dict
    ) -> dict:


        basic = profile.get(
            "basic_info",
            {}
        )

        compatibility = profile.get(
            "compatibility",
            {}
        )


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


        parts = []


        # ======================
        # Core Product
        # ======================

        if main_function:

            parts.append(
                ShortTitleGenerator.clean(
                    main_function
                )
            )


        elif product_type:

            parts.append(
                product_type
            )



        # ======================
        # Replacement Keyword
        # ======================

        if product_type:

            if "replacement" not in str(
                product_type
            ).lower():

                parts.append(
                    "Replacement"
                )



        # ======================
        # Compatibility
        # ======================

        if brands:

            brand_text = ", ".join(
                brands[:2]
            )

            parts.append(

                "Compatible with "
                +
                brand_text

            )



        title = " ".join(
            parts
        )


        title = ShortTitleGenerator.clean(
            title
        )


        title = ShortTitleGenerator.remove_blocked_words(
            title
        )


        return {

            "short_title": title,

            "validation": {

                "compliance_ok":

                len(
                    ShortTitleGenerator.check_blocked_words(
                        title
                    )
                ) == 0

            },

            "blocked_words":

            ShortTitleGenerator.check_blocked_words(
                title
            )

        }



    @staticmethod
    def clean(text):

        text = str(text)

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()



    @staticmethod
    def remove_blocked_words(
        text
    ):

        for word in ShortTitleGenerator.BLOCKED_WORDS:

            text = re.sub(

                re.escape(word),

                "",

                text,

                flags=re.I

            )


        return ShortTitleGenerator.clean(
            text
        )



    @staticmethod
    def check_blocked_words(
        text
    ):

        found = []

        for word in ShortTitleGenerator.BLOCKED_WORDS:

            if re.search(

                r"\b"
                +
                re.escape(word)
                +
                r"\b",

                text,

                flags=re.I

            ):

                found.append(
                    word
                )


        return found
