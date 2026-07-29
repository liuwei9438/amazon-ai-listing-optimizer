from __future__ import annotations

import re


class HighlightGenerator:

    """
    Extract Amazon product highlights from Product Profile.

    Principles:
    - Only use confirmed facts
    - No invented specifications
    - No marketing exaggeration
    - Prepare structured data for title/bullet/description
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
        fact_lock = profile.get(
            "fact_lock",
            {}
        )
        seo = profile.get(
            "seo",
            {}
        )


        highlights = {

            "core_function": "",

            "compatibility": "",

            "usage": "",

            "attributes": [],

            "keywords": [],

        }


        # ======================
        # Core Function
        # ======================

        main_function = HighlightGenerator.clean(
            basic.get(
                "main_function",
                ""
            )
        )


        product_type = HighlightGenerator.clean(
            basic.get(
                "product_type",
                ""
            )
        )


        if main_function:

            highlights["core_function"] = (
                HighlightGenerator.normalize_function(
                    main_function,
                    product_type
                )
            )


        # ======================
        # Compatibility
        # ======================

        brands = compatibility.get(
            "brands",
            []
        )

        models = compatibility.get(
            "models",
            []
        )


        brand_text = ""

        if brands:

            brand_text = ", ".join(
                brands
            )


        model_text = ""

        if models:

            model_text = ", ".join(
                models
            )


        if brand_text or model_text:

            text = "Compatible with"

            if brand_text:

                text += f" {brand_text}"


            if model_text:

                text += f" models {model_text}"


            highlights["compatibility"] = text



        # ======================
        # Usage
        # ======================

        usage = profile.get(
            "usage_scenarios",
            []
        )


        if usage:

            highlights["usage"] = (
                ", ".join(
                    [
                        HighlightGenerator.clean(x)
                        for x in usage
                    ]
                )
            )



        # ======================
        # Attributes
        # ======================

        for key in [
            "material",
            "color",
            "quantity",
            "voltage",
            "power",
        ]:

            value = attributes.get(
                key,
                ""
            )


            value = HighlightGenerator.clean(
                value
            )


            if not value:
                continue



            # ======================
            # Fact Protection
            # ======================

            # 材质必须来自事实锁定
            if key == "material":

                confirmed_material = HighlightGenerator.clean(
                    fact_lock.get(
                        "material",
                        ""
                    )
                )


                if not confirmed_material:

                    continue



            highlights["attributes"].append(
                {
                    "name": key,
                    "value": value
                }
            )



        # ======================
        # Keywords
        # ======================

        primary_keywords = seo.get(
            "primary_keywords",
            []
        )

        secondary_keywords = seo.get(
            "secondary_keywords",
            []
        )


        keywords = []

        for item in (
            primary_keywords
            +
            secondary_keywords
        ):

            item = HighlightGenerator.clean(
                item
            )

            if item and item not in keywords:

                keywords.append(
                    item
                )


        highlights["keywords"] = keywords[:10]


        return {

            "highlights": highlights,

            "validation": {

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
    def normalize_function(
        function,
        product_type
    ):


        text = function.lower()


        replacements = {

            "start button power drive":
            "washing machine start button replacement",

            "power button":
            "power button replacement",

        }


        for old,new in replacements.items():

            if old in text:

                return new


        if product_type:

            return (
                function
                +
                " replacement component"
            )


        return function



    @staticmethod
    def clean(text):

        if not text:

            return ""

        return str(text).strip()



    @staticmethod
    def check_blocked_words(
        text
    ):

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
