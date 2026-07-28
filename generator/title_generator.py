from __future__ import annotations

import re

from generator.seo_scorer import SEOElementScorer
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
    def format_title_case(text):

        words = text.split()

        small_words = [
            "with",
            "and",
            "for"
        ]

        result = []

        for i, w in enumerate(words):

            # 型号保护
            if any(
                c.isdigit()
                for c in w
            ):
                result.append(w)

            elif i > 0 and w.lower() in small_words:

                result.append(
                    w.lower()
                )

            else:

                result.append(
                    w.capitalize()
                )

        return " ".join(result)



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

        seo = profile.get(
            "seo",
            {}
        )


        product_type = basic.get(
            "product_type",
            ""
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


        # 型号排序
        if models:

            models = ModelRanker.rank(
                models
            )


        primary_keywords = seo.get(
            "primary_keywords",
            []
        )


        title_parts = []


        # =========================
        # 主关键词
        # =========================

        main_keyword = ""


        if primary_keywords:

            main_keyword = primary_keywords[0]

        elif main_function:

            main_keyword = main_function



        # 避免重复产品词

        if product_type:

            product_words = (
                product_type.lower()
                .split()
            )

            keyword_words = (
                main_keyword.lower()
                .split()
            )


            overlap = len(
                set(product_words)
                &
                set(keyword_words)
            )


            if overlap == 0:

                main_keyword = (
                    main_keyword
                    +
                    " "
                    +
                    product_type
                )



        if main_keyword:

            title_parts.append(
                main_keyword
            )



        # =========================
        # Compatible brand
        # =========================

        if brands:

            title_parts.append(
                f"Compatible with {brands[0]}"
            )



        # =========================
        # 型号选择
        # =========================

        selected_models = []

        removed_models = []


        if models:


            for model in models:


                test_title = (
                    " ".join(title_parts)
                    +
                    " "
                    +
                    " ".join(selected_models)
                    +
                    " "
                    +
                    model
                )


                if len(test_title) <= 75:

                    selected_models.append(
                        model
                    )

                else:

                    removed_models.append(
                        model
                    )



        title_parts.extend(
            selected_models
        )



        title = " ".join(
            title_parts
        )



        # 标题格式化

        title = (
            TitleGenerator
            .format_title_case(title)
        )


        title = title.strip()



        # 清理违规词

        title = (
            TitleGenerator
            .clean_title(title)
        )



        # 75字符限制

        title = (
            TitleGenerator
            .limit_length(
                title,
                75
            )
        )



        blocked_found = (
            TitleGenerator
            .check_blocked_words(title)
        )



        return {

            "title": title,


            "selected_models":
                selected_models,


            "removed_models":
                removed_models,


            "character_count":
                len(title),


            "validation": {

                "length_ok":
                    len(title) <= 75,


                "compliance_ok":
                    len(blocked_found) == 0

            },


            "blocked_words":
                blocked_found,


            "brand_check":
                "passed"

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


            result.append(
                word
            )


            length += (
                len(word)
                +
                1
            )



        return " ".join(
            result
        )



    @staticmethod
    def check_blocked_words(
        text: str
    ):


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

                found.append(
                    word
                )


        return found
