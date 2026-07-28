from __future__ import annotations

import re


class BulletGenerator:


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
    ]


    @staticmethod
    def generate(profile: dict) -> list:
        """
        Generate Amazon bullet points
        """


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



        product_type = basic.get(
            "product_type",
            "product"
        )


        main_function = basic.get(
            "main_function",
            ""
        )


        brands = compatibility.get(
            "brands",
            []
        )


        models = compatibility.get(
            "models",
            []
        )



        bullets = []



        # 1 Compatibility

        compatibility_text = (
            BulletGenerator
            .compatibility_bullet(
                brands,
                models
            )
        )


        bullets.append(
            compatibility_text
        )



        # 2 Function

        bullets.append(
            BulletGenerator.clean(
                f"Function: Designed to restore the {main_function} function and help replace damaged or worn {product_type} components."
            )
        )



        # 3 Material

        material = attributes.get(
            "material",
            ""
        )


        if material:

            bullets.append(
                BulletGenerator.clean(
                    f"Durable Material: Made from {material} material for reliable daily use and stable performance."
                )
            )

        else:

            bullets.append(
                "Durable Construction: Designed for reliable performance and long-term daily use."
            )



        # 4 Installation

        bullets.append(
            "Easy Installation: Designed as a replacement part. Please follow proper installation steps or seek professional assistance when needed."
        )



        # 5 Purchase reminder

        bullets.append(
            BulletGenerator.clean(
                "Compatibility Check: Please confirm your appliance model number before purchase to ensure proper compatibility."
            )
        )



        return bullets



    @staticmethod
    def compatibility_bullet(
        brands,
        models
    ):


        text = ""


        if brands:

            text += (
                f"Compatible with {brands[0]}"
            )


        else:

            text += (
                "Compatible with selected models"
            )



        if models:


            show_models = models[:4]


            text += (
                " models including "
                +
                ", ".join(show_models)
            )



        text += (
            ". Please check your model number before purchase."
        )


        return text



    @staticmethod
    def clean(text):


        for word in BulletGenerator.BLOCKED_WORDS:


            text = re.sub(

                r"\b"
                +
                re.escape(word)
                +
                r"\b",

                "",

                text,

                flags=re.I

            )


        text = re.sub(
            r"\s+",
            " ",
            text
        )


        return text.strip()
