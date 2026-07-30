from __future__ import annotations

import re


class HighlightGenerator:

    """
    Generate Amazon product highlight structure.

    Output:
    - short_title
    - product_highlights
    - core_function
    - compatibility
    - usage
    - product_facts

    Rules:
    - Facts only
    - No invented specifications
    - No marketing exaggeration
    - Compatible wording protected
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


        if not isinstance(
            compatibility,
            dict
        ):

            compatibility = {}



        if not isinstance(
            attributes,
            dict
        ):

            attributes = {}



        highlights = {


            "short_title": "",


            "product_highlights": [],


            "core_function": "",


            "compatibility": "",


            "usage": "",


            "product_facts": []

        }



        # =========================
        # Basic information
        # =========================


        product_type = HighlightGenerator.clean(

            basic_info.get(
                "product_type",
                ""
            )

        )


        main_function = HighlightGenerator.clean(

            basic_info.get(
                "main_function",
                ""
            )

        )



        # =========================
        # Core Function
        # =========================


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
        # Short Title
        # =========================


        short_parts = []


        if main_function:

            short_parts.append(

                main_function

            )


        elif product_type:

            short_parts.append(

                product_type

            )



        if short_parts:


            highlights["short_title"] = (

                " ".join(short_parts)

                +

                " Replacement"

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
        # Usage
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
        # Product Highlights
        # =========================


        if highlights["core_function"]:


            highlights["product_highlights"].append(
                {
                    "title":
                    "Replacement Function",
                    "content":
                    "Designed to replace "
                    +
                    main_function
                }
            )



        if highlights["compatibility"]:


            highlights["product_highlights"].append(

                {

                    "title":
                    "Compatibility",


                    "content":
                    highlights["compatibility"]

                }

            )



        if highlights["usage"]:


            highlights["product_highlights"].append(

                {

                    "title":
                    "Application",


                    "content":
                    highlights["usage"]

                }

            )



        # =========================
        # Product Facts
        # =========================


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
            value = HighlightGenerator.extract_attribute(
                value
            )

            value = HighlightGenerator.clean(

                value

            )


            if value:


                highlights["product_facts"].append(

                    {

                        "name":
                        key,


                        "value":
                        value

                    }

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

                )

                == 0

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
    def extract_attribute(value):
        if isinstance(value, dict):
            return value.get(
                "value",
                ""
            )
        return str(value)


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
