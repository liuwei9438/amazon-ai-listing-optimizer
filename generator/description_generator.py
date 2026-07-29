from __future__ import annotations

import re


class DescriptionGenerator:


    """
    Generate Amazon product description.

    Rules:
    - Based on verified highlights
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
        "top quality",
        "durable"

    ]



    @staticmethod
    def generate(
        profile: dict,
        highlights: dict
    ) -> dict:


        basic = profile.get(
            "basic_info",
            {}
        )


        highlight_data = highlights.get(
            "highlights",
            {}
        )


        paragraphs = []



        # ==========================
        # Product introduction
        # ==========================

        product_type = basic.get(
            "product_type",
            ""
        )


        if product_type:

            paragraphs.append(

                DescriptionGenerator.clean(

                    f"This product is a {product_type} replacement component."

                )

            )



        # ==========================
        # Core Function
        # ==========================

        core_function = highlight_data.get(
            "core_function",
            ""
        )


        if core_function:

            paragraphs.append(

                DescriptionGenerator.clean(

                    "Function: "
                    +
                    str(core_function)
                    +
                    "."

                )

            )



        # ==========================
        # Compatibility
        # ==========================

        compatibility = highlight_data.get(
            "compatibility",
            ""
        )


        if compatibility:

            paragraphs.append(

                DescriptionGenerator.clean(

                    str(compatibility)
                    +
                    "."

                )

            )



        # ==========================
        # Usage
        # ==========================

        usage = highlight_data.get(
            "usage",
            ""
        )


        if usage:

            paragraphs.append(

                DescriptionGenerator.clean(

                    "Application: "
                    +
                    str(usage)
                    +
                    "."

                )

            )



        # ==========================
        # Attributes
        # ==========================

        attributes = highlight_data.get(
            "attributes",
            []
        )


        if isinstance(attributes, list):

            for item in attributes:


                if isinstance(item, dict):


                    name = item.get(
                        "name",
                        ""
                    )


                    value = item.get(
                        "value",
                        ""
                    )


                    if value:

                        paragraphs.append(

                            DescriptionGenerator.clean(

                                f"{name}: {value}."

                            )

                        )


                else:

                    paragraphs.append(

                        DescriptionGenerator.clean(

                            str(item)

                        )

                    )



        # ==========================
        # Keywords (only if useful)
        # ==========================

        keywords = highlight_data.get(
            "keywords",
            []
        )


        if isinstance(keywords, list) and keywords:


            paragraphs.append(

                DescriptionGenerator.clean(

                    "Keywords: "
                    +
                    ", ".join(
                        keywords[:5]
                    )
                    +
                    "."

                )

            )



        # ==========================
        # Remove duplicate
        # ==========================

        result = []


        for p in paragraphs:


            if p and p not in result:

                result.append(
                    p
                )



        description = "\n\n".join(
            result
        )



        return {


            "description":

            description,


            "validation":

            {

                "compliance_ok":

                len(

                    DescriptionGenerator.check_blocked_words(

                        description

                    )

                ) == 0

            },


            "blocked_words":

            DescriptionGenerator.check_blocked_words(

                description

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
    def check_blocked_words(text):


        found = []


        for word in DescriptionGenerator.BLOCKED_WORDS:


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
