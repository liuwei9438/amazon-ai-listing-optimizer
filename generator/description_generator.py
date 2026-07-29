from __future__ import annotations


import re



class DescriptionGenerator:



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
        "guaranteed"

    ]



    @staticmethod
    def generate(
        profile: dict,
        highlights: dict,
        bullet_result: dict
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



        models = compatibility.get(
            "models",
            []
        )



        highlight_data = highlights.get(
            "highlights",
            {}
        )



        paragraphs = []



        # =====================
        # Product introduction
        # =====================


        if product_type:

            paragraphs.append(

                f"This {product_type} is designed as a replacement component for compatible equipment."

            )



        # =====================
        # Compatibility
        # =====================


        if models:


            model_text = ", ".join(
                models
            )


            paragraphs.append(

                "Compatible with models: "
                +
                model_text

            )



        # =====================
        # Core function
        # =====================


        function = highlight_data.get(

            "core_function",

            ""

        )


        if function:


            paragraphs.append(

                function

            )



        # =====================
        # Usage
        # =====================


        usage = highlight_data.get(

            "usage",

            ""

        )


        if usage:


            paragraphs.append(

                "Suitable for "
                +
                usage

            )



        # =====================
        # Attributes
        # =====================


        attributes = highlight_data.get(

            "attributes",

            []

        )



        for item in attributes:


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

                    f"{name}: {value}"

                )



        description = "\n\n".join(

            paragraphs

        )



        description = DescriptionGenerator.clean(

            description

        )



        blocked = DescriptionGenerator.check_blocked_words(

            description

        )



        return {


            "description": description,


            "validation": {


                "compliance_ok":

                len(blocked) == 0


            },


            "blocked_words": blocked


        }





    @staticmethod
    def clean(
        text
    ):


        text = re.sub(

            r"\s+",

            " ",

            text

        )


        return text.strip()





    @staticmethod
    def check_blocked_words(
        text
    ):


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


                found.append(word)


        return found
