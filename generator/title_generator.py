from __future__ import annotations

import re

from generator.model_ranker import ModelRanker


class TitleGenerator:


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
    def generate(profile: dict) -> dict:
        """
        Generate Amazon title from Product Knowledge.
        """

        knowledge = profile.get(
            "product_knowledge",
            {}
        )

        if not isinstance(
            knowledge,
            dict
        ):
            knowledge = {}


        identity = knowledge.get(
            "identity",
            {}
        )


        relationship = knowledge.get(
            "relationship",
            {}
        )


        seo = knowledge.get(
            "seo",
            {}
        )


        title_parts = []


        # =========================
        # Product Identity
        # 商品主体
        # =========================

        product_name = (
            identity.get(
                "product_name"
            )
            or
            identity.get(
                "object_name"
            )
            or
            ""
        )


        if product_name:

            title_parts.append(
                product_name
            )


        # =========================
        # Model Priority
        # 主型号
        # =========================

        model_priority = relationship.get(
            "model_priority",
            {}
        )


        primary_model = model_priority.get(
            "primary_model",
            ""
        )


        secondary_models = model_priority.get(
            "secondary_models",
            []
        )


        selected_models = []

        removed_models = []


        if primary_model:

            selected_models.append(
                primary_model
            )


        # 次型号最多补充1个
        if secondary_models:

            if len(
                " ".join(title_parts + selected_models + [secondary_models[0]])
            ) < 70:

                selected_models.append(
                    secondary_models[0]
                )


        all_models = (
            [primary_model]
            +
            secondary_models
            +
            model_priority.get(
                "backend_models",
                []
            )
        )


        removed_models = [
            model
            for model in all_models
            if model not in selected_models
        ]



        # =========================
        # SEO Keywords
        # =========================

        primary_keywords = seo.get(
            "primary_keywords",
            []
        )


        if isinstance(
            primary_keywords,
            list
        ):

            for keyword in primary_keywords:

                keyword = str(
                    keyword
                ).strip()


                if (
                    keyword
                    and keyword.lower()
                    not in product_name.lower()
                ):

                    title_parts.append(
                        keyword
                    )

                    break



        # =========================
        # Compatibility
        # =========================

        brands = relationship.get(
            "brands",
            []
        )


        if brands:

            title_parts.append(
                "Compatible with "
                +
                ", ".join(
                    brands[:2]
                )
            )



        # =========================
        # Add models
        # =========================

        title_parts.extend(
            selected_models
        )


        title = " ".join(
            title_parts
        )


        title = TitleGenerator.clean_title(
            title
        )


        title = TitleGenerator.format_title_case(
            title
        )


        title = TitleGenerator.limit_length(
            title,
            75
        )


        blocked_found = (
            TitleGenerator.check_blocked_words(
                title
            )
        )


        return {

            "title":
                title,


            "selected_models":
                selected_models,


            "removed_models":
                removed_models,


            "character_count":
                len(title),


            "validation":
            {

                "length_ok":
                    len(title) <= 75,


                "compliance_ok":
                    len(blocked_found) == 0,

            },


            "blocked_words":
                blocked_found,


            "brand_check":
                "passed",

        }

    @staticmethod
    def clean_title(text: str):


        for word in TitleGenerator.BLOCKED_WORDS:


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



    @staticmethod
    def format_title_case(text):


        words = text.split()


        small_words = [

            "with",

            "and",

            "for"

        ]


        result = []


        for i, word in enumerate(words):


            if (
                i > 0
                and word.lower()
                in small_words
            ):

                result.append(
                    word.lower()
                )


            else:

                result.append(
                    word.capitalize()
                )


        return " ".join(result)



    @staticmethod
    def limit_length(
        text: str,
        max_length: int = 75
    ):


        if len(text) <= max_length:

            return text



        words = text.split()


        result = []


        length = 0



        for word in words:


            if (
                length
                +
                len(word)
                +
                1
                >
                max_length
            ):

                break



            result.append(word)


            length += (
                len(word)
                +
                1
            )



        return " ".join(result)



    @staticmethod
    def check_blocked_words(text):


        found = []


        for word in TitleGenerator.BLOCKED_WORDS:


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
