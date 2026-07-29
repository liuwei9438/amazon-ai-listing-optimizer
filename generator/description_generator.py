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


        items = highlights.get(
            "highlights",
            []
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
        # Highlight details
        # ==========================

        for item in items:


            text = item.get(
                "text",
                ""
            )


            h_type = item.get(
                "type",
                ""
            )


            if not text:

                continue



            if h_type == "compatibility":


                paragraphs.append(

                    DescriptionGenerator.clean(

                        text + "."

                    )

                )


            elif h_type == "function":


                paragraphs.append(

                    DescriptionGenerator.clean(

                        "Function: "
                        +
                        text
                        +
                        "."

                    )

                )


            elif h_type == "usage":


                paragraphs.append(

                    DescriptionGenerator.clean(

                        "Application: "
                        +
                        text
                        +
                        "."

                    )

                )


            else:


                paragraphs.append(

                    DescriptionGenerator.clean(

                        text
                        +
                        "."

                    )

                )



        # ==========================
        # Remove duplicate
        # ==========================


        result = []


        for p in paragraphs:


            if p not in result:

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
