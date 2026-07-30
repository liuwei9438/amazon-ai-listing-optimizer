from __future__ import annotations

import re


class HighlightGenerator:

    """
    Generate Amazon product highlights.

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


        if not isinstance(basic_info, dict):
            basic_info = {}


        if not isinstance(compatibility, dict):
            compatibility = {}


        if not isinstance(attributes, dict):
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
        # Basic Information
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

                "Designed to replace "

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


        if product_type:

            short_parts.append(
                product_type
            )


        elif main_function:

            short_parts.append(
                main_function
            )



        if compatibility.get("brands"):

            brand = compatibility.get(
                "brands"
            )


            if isinstance(brand, list):

                brand = brand[0]

            short_parts.append(
                "Compatible with " + str(brand)
            )



        if short_parts:

            highlights["short_title"] = (

                " ".join(short_parts)

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



        if isinstance(brands, str):

            brands = [
                brands
            ]


        if isinstance(models, str):

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


        if isinstance(usage, str):

            usage = [
                usage
            ]



        if usage:

            usage_text = ", ".join(

                [

                    HighlightGenerator.clean(x)

                    for x in usage

                    if x

                ]

            )


            if usage_text:

                highlights["usage"] = (

                    "Suitable for "

                    +

                    usage_text

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
                    highlights["core_function"]

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


        fact_mapping = [

            ("material", "Material"),

            ("quantity", "Quantity"),

            ("color", "Color"),

            ("dimensions", "Dimensions"),

            ("voltage", "Voltage"),

            ("power", "Power")

        ]



        for key, title in fact_mapping:


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
                        title,

                        "value":
                        value

                    }

                )


                # 商品亮点只加入有价值事实

                if key in [

                    "material",
                    "dimensions"

                ]:


                    highlights["product_highlights"].append(

                        {

                            "title":
                            title,

                            "content":
                            f"Made of {value}."

                        }

                    )



        # 最多保留5条商品亮点

        highlights["product_highlights"] = (

            highlights["product_highlights"][:5]

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
    def extract_attribute(value):


        if isinstance(value, dict):

            return value.get(
                "value",
                ""
            )


        if isinstance(value, list):

            return ", ".join(

                [

                    str(x)

                    for x in value

                    if x

                ]

            )


        return str(value)



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
