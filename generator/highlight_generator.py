from __future__ import annotations


import re



class HighlightGenerator:


    """
    Generate Amazon product highlights.

    Principles:
    - Fact based
    - No invented features
    - No marketing claims
    - Used by bullet and description generator
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
        "top quality"

    ]



    @staticmethod
    def generate(profile: dict):


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



        highlights = {


            "core_function": "",


            "compatibility": "",


            "usage": "",


            "product_facts": []

        }



        # =========================
        # Core Function
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


            highlights["core_function"] = (

                "Replacement component designed to "

                +
                HighlightGenerator.clean(
                    main_function
                )

            )


        elif product_type:


            highlights["core_function"] = (

                "Replacement component for "

                +
                HighlightGenerator.clean(
                    product_type
                )

            )



        # =========================
        # Compatibility
        # =========================


        brands = compatibility.get(
            "brands",
            []
        )


        models = compatibility.get(
            "models",
            []
        )


        if brands and models:


            highlights["compatibility"] = (

                "Compatible with "

                +
                ", ".join(brands)

                +

                " models "

                +

                ", ".join(models)

            )


        elif models:


            highlights["compatibility"] = (

                "Compatible with models "

                +

                ", ".join(models)

            )



        # =========================
        # Usage
        # =========================


        usage = profile.get(
            "usage_scenarios",
            []
        )


        if usage:


            highlights["usage"] = (

                "Suitable for "

                +

                ", ".join(

                    [

                        HighlightGenerator.clean(x)

                        for x in usage

                    ]

                )

            )



        # =========================
        # Facts only
        # =========================


        for key in [

            "quantity",

            "material",

            "color",

            "voltage",

            "power"

        ]:


            value = attributes.get(
                key,
                ""
            )


            if value:


                highlights["product_facts"].append(

                    f"{key}: {value}"

                )



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
    def clean(text):

        if not text:

            return ""

        return str(text).strip()



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


                found.append(word)



        return found
