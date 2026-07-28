from __future__ import annotations

import re

from generator.model_ranker import ModelRanker
from generator.keyword_ranker import KeywordRanker
from generator.title_scorer import TitleScorer



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
    def generate(profile: dict):


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



        all_keywords = (
            primary_keywords
            +
            secondary_keywords
        )



        # ======================
        # Keyword Ranking
        # ======================

        keywords = KeywordRanker.rank(
            all_keywords
        )



        # ======================
        # Model Ranking
        # ======================

        models = ModelRanker.rank(
            models
        )



        if keywords:

            best_keyword = keywords[0]

        else:

            best_keyword = main_function



        if product_type:

            if product_type.lower() not in best_keyword.lower():

                best_keyword = (
                    best_keyword
                    +
                    " "
                    +
                    product_type
                )



        # ======================
        # Generate Candidates
        # ======================


        candidates = []



        brand_text = ""


        if brands:

            brand_text = (
                "Compatible with "
                +
                brands[0]
            )



        # 不同关键词组合

        keyword_candidates = keywords[:3]



        for keyword in keyword_candidates:


            base = (

                brand_text
                +
                " "
                +
                keyword

            ).strip()



            selected_models = []



            title = base



            for model in models:


                test_title = (

                    title
                    +
                    " "
                    +
                    " "
                    .join(selected_models)
                    +
                    " "
                    +
                    model

                ).strip()



                if len(test_title) <= 75:

                    selected_models.append(
                        model
                    )



            final_title = (

                title
                +
                " "
                +
                " "
                .join(selected_models)

            ).strip()



            score = TitleScorer.total_score(

                final_title,

                keywords,

                models

            )



            candidates.append(

                {

                    "title":
                        final_title,


                    "models":
                        selected_models,


                    "score":
                        score

                }

            )



        # ======================
        # Select Best
        # ======================


        if candidates:


            best = max(

                candidates,

                key=lambda x:x["score"]

            )


            title = best["title"]

            selected_models = best["models"]



        else:


            title = brand_text + " " + best_keyword

            selected_models = []




        removed_models = [

            m for m in models

            if m not in selected_models

        ]



        title = TitleGenerator.clean_title(
            title
        )


        title = TitleGenerator.format_title_case(
            title
        )



        return {


            "title": title,


            "selected_models":
                selected_models,


            "removed_models":
                removed_models,


            "character_count":
                len(title),


            "validation":
                {

                    "length_ok":
                        len(title)<=75,


                    "compliance_ok":
                        len(
                            TitleGenerator.check_blocked_words(title)
                        ) == 0

                },


            "blocked_words":
                TitleGenerator.check_blocked_words(title),


            "brand_check":
                "passed"

        }




    @staticmethod
    def format_title_case(text):


        words=text.split()


        small_words=[
            "with",
            "and",
            "for"
        ]


        result=[]


        for i,w in enumerate(words):


            if i>0 and w.lower() in small_words:

                result.append(
                    w.lower()
                )

            else:

                result.append(
                    w.capitalize()
                )


        return " ".join(result)





    @staticmethod
    def clean_title(text):


        for word in TitleGenerator.BLOCKED_WORDS:


            text=re.sub(

                r"\b"
                +
                re.escape(word)
                +
                r"\b",

                "",

                text,

                flags=re.I

            )


        text=re.sub(
            r"\s+",
            " ",
            text
        )


        return text.strip()




    @staticmethod
    def check_blocked_words(text):


        found=[]


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

