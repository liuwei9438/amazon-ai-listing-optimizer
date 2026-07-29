from __future__ import annotations

import re


class HighlightGenerator:

    """
    Generate Amazon product highlights.

    Purpose:
    - Create structured product highlights
    - Used by BulletGenerator and DescriptionGenerator

    Rules:
    - Facts only
    - No invented specifications
    - No marketing claims
    - No prohibited words
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
    def generate(profile: dict) -> dict:


        basic_info = profile.get(
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


        #
        # Compatibility compatibility fix
        #

        if isinstance(
            compatibility,
            str
        ):

            compatibility = {

                "brands": [
                    compatibility
                ],

                "models": []

            }


        if not isinstance(
            compatibility,
            dict
        ):

            compatibility = {}



        highlights = {


            "core_function": "",


            "compatibility": "",


            "usage": "",


            "product_facts": []

        }



        # =========================
        # Core Function
        # =========================


        main_function = HighlightGenerator.clean(

            basic_info.get(
                "main_function",
                ""
            )

        )


        product_type = HighlightGenerator.clean(

            basic_info.get(
                "product_type",
                ""
            )

        )



        if main_function:


            highlights["core_function"] = (

                "Replacement component designed to "

                +

                main_function

            )


        elif product_type:


            highlights["core_function"] = (

                "Replacement component for "

                +

                product_type

            )



        # =========================
        # Compatibility
        # =========================


        brands = compatibility.get(

            "brands",

            []

        )


        models = (

            compatibility.get(

                "models",

                []

            )

            or

            compatibility.get(

                "compatible_models",

                []

            )

        )



        if isinstance(
            brands,
            str
        ):

            brands = [
                brands
            ]


        if isinstance(
            models,
            str
        ):

            models = [
                models
            ]



        brands = [

            HighlightGenerator.clean(x)

            for x in brands

            if x

        ]


        models = [

            HighlightGenerator.clean(x)

            for x in models

            if x

        ]



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


        elif brands:


            highlights["compatibility"] = (

                "Compatible with "

                +

                ", ".join(brands)

            )



        # =========================
        # Usage Scenario
        # =========================


        usage = profile.get(

            "usage_scenarios",

            []

        )


        if isinstance(
            usage,
            str
        ):

            usage = [

                usage

            ]



        if usage:


            highlights["usage"] = (

                "Suitable for "

                +

                ", ".join(

                    [

                        HighlightGenerator.clean(x)

                        for x in usage

                        if x

                    ]

                )

            )



        # =========================
        # Product Facts
        # =========================


        if not isinstance(
            attributes,
            dict
        ):

            attributes = {}



        for key in [

            "quantity",

            "material",

            "color",

            "voltage",

            "power",

            "dimensions"

        ]:


            value = attributes.get(

                key,

                ""

            )


            value = HighlightGenerator.clean(

                value

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

                )

                ==

                0


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
