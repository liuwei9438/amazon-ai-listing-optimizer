from __future__ import annotations

import re


class HighlightGenerator:

    """
    Generate Amazon product highlights.

    Rules:
    - Facts only
    - No invented attributes
    - No assumed materials
    - No marketing claims
    - Used by bullet and description generators
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
        "perfect",
        "top quality",
    ]


    @staticmethod
    def generate(profile: dict) -> dict:


        basic = profile.get(
            "basic_info",
            {}
        )

        compatibility = profile.get(
            "compatibility",
            {}
        )

        seo = profile.get(
            "seo",
            {}
        )


        highlights = []


        # =========================
        # 1. Core Function
        # =========================

        main_function = basic.get(
            "main_function",
            ""
        )


        product_type = basic.get(
            "product_type",
            ""
        )


        if main_function:

            highlights.append({

                "type": "function",

                "text":
                HighlightGenerator.clean(
                    main_function
                )

            })


        elif product_type:

            highlights.append({

                "type": "product",

                "text":
                HighlightGenerator.clean(
                    product_type
                )

            })



        # =========================
        # 2. Compatibility
        # =========================

        brands = compatibility.get(
            "brands",
            []
        )

        models = compatibility.get(
            "models",
            []
        )


        if brands or models:


            text = "Compatible with"


            if brands:

                text += " "

                text += ", ".join(
                    brands
                )


            if models:

                text += " models "

                text += ", ".join(
                    models[:5]
                )


            highlights.append({

                "type":
                "compatibility",

                "text":
                text

            })



        # =========================
        # 3. Replacement Purpose
        # =========================

        if product_type:


            highlights.append({

                "type":
                "replacement",

                "text":
                f"Replacement part for {HighlightGenerator.clean(product_type)}"

            })



        # =========================
        # 4. Usage Scenario
        # =========================

        usage = profile.get(
            "usage_scenarios",
            []
        )


        for item in usage[:2]:

            if item:

                highlights.append({

                    "type":
                    "usage",

                    "text":
                    HighlightGenerator.clean(
                        item
                    )

                })



        # =========================
        # 5. SEO Keywords
        # =========================

        keywords = []


        for item in seo.get(
            "primary_keywords",
            []
        ):

            item = HighlightGenerator.clean(
                item
            )

            if item:

                keywords.append(
                    item
                )


        return {


            "highlights":

            highlights,


            "validation":

            {

                "compliance_ok":

                len(

                    HighlightGenerator.check_blocked_words(

                        str(highlights)

                    )

                ) == 0

            },


            "blocked_words":

            HighlightGenerator.check_blocked_words(

                str(highlights)

            )


        }



    @staticmethod
    def clean(text):

        if not text:

            return ""

        return re.sub(

            r"\s+",

            " ",

            str(text)

        ).strip()



    @staticmethod
    def check_blocked_words(text):

        found = []


        for word in HighlightGenerator.BLOCKED_WORDS:


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
