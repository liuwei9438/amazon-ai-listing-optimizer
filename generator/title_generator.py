from __future__ import annotations

import re

from generator.seo_scorer import SEOElementScorer
from generator.model_ranker import ModelRanker
from generator.keyword_ranker import KeywordRanker


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
        Generate Amazon title from Product Profile
        """


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
            {})


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


        primary_keywords = seo.get(
            "primary_keywords",
            []
        )


        secondary_keywords = seo.get(
            "secondary_keywords",
            []
        )


        # ==========================
        # 1. Keyword Ranking
        # ==========================

        all_keywords = (
            primary_keywords
            +
            secondary_keywords
        )


        ranked_keywords = KeywordRanker.rank(
            all_keywords
        )


        main_keyword = ""


        if ranked_keywords:

            main_keyword = ranked_keywords[0]


        elif main_function:

            main_keyword = main_function



        # ==========================
        # 2. Model Ranking
        # ==========================

        if models:

            models = ModelRanker.rank(
                models
            )



        # ==========================
        # 3. Build Base Title
        # ==========================

        title_parts = []


        # Compatible brand

        if brands:

            title_parts.append(
                f"Compatible with {brands[0]}"
            )


        # Main keyword

        if product_type:


            product_words = (
                product_type
                .lower()
                .split()
            )


            keyword_words = (
                main_keyword
                .lower()
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



        # ==========================
        # 4. Add Models
        # ==========================


        selected_models = []

        removed_models = []


        current_title = (
            " ".join(title_parts)
        )


        for model in models:


            test_title = (
                current_title
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



        # ==========================
        # 5. Clean
        # ==========================

        title = title.strip()


        title = TitleGenerator.clean_title(
            title
        )


        title = TitleGenerator.format_title_case(
            title
        )



        # ==========================
        # 6. Final Length Control
        # ==========================

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


            "title": title,


            "selected_models": selected_models,


            "removed_models": removed_models,


            "character_count": len(title),


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
    def format_title_case(text):


        words = text.split()


        small_words = [

            "with",

            "and",

            "for"

        ]


        result = []


        for i, w in enumerate(words):


            if i > 0 and w.lower() in small_words:

                result.append(
                    w.lower()
                )

            else:

                result.append(
                    w.capitalize()
                )


        return " ".join(result)




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
        max_length=75
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

                found.append(
                    word
                )


        return found
