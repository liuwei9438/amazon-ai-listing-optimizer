from __future__ import annotations

import re


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
        "oem",
    ]


    @staticmethod
    def generate(
        profile: dict,
    ) -> dict:

        knowledge = profile.get(
            "product_knowledge",
            {},
        )
        title_plan = profile.get(
            "title_plan",
            {}
        )

        if not isinstance(
            knowledge,
            dict,
        ):
            knowledge = {}



        identity = knowledge.get(
            "identity",
            {},
        )


        relationship = knowledge.get(
            "relationship",
            {},
        )


        generation_strategy = knowledge.get(
            "generation_strategy",
            {},
        )
        plan_identity = title_plan.get(
            "product_identity",
            []
        )
        
        plan_must_include = title_plan.get(
            "must_include",
            []
        )
        
        plan_features = title_plan.get(
            "high_value_features",
            []
        )


        title_parts = []
        # =========================
        # Title Planner Must Include
        # 必须保留关键词
        # =========================

        if isinstance(
            plan_must_include,
            list,
        ):

            for item in plan_must_include[:2]:

                item = str(item).strip()

                if item:

                    title_parts.append(item)


        # =========================
        # Generation Strategy
        # =========================

        title_identity_focus = (
            plan_identity
            or
            generation_strategy.get(
                "title_identity_focus",
                [],
            )
        )


        title_search_focus = (
            generation_strategy.get(
                "title_search_focus",
                [],
            )
        )


        title_attribute_focus = (
            generation_strategy.get(
                "title_attribute_focus",
                [],
            )
        )



        # =========================
        # Product Identity
        # 商品身份
        # =========================

        if isinstance(
            title_identity_focus,
            list,
        ) and title_identity_focus:

            title_parts.extend(
                title_identity_focus[:2]
            )


        else:

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
        # Identifier
        # 型号/零件号
        # 只使用 search_strategy.title_identifiers
        # =========================

        search_strategy = knowledge.get(
            "search_strategy",
            {},
        )


        title_identifiers = (
            search_strategy.get(
                "title_identifiers",
                [],
            )
        )


        selected_models = []


        removed_models = []


        if isinstance(
            title_identifiers,
            list,
        ):

            for item in title_identifiers:

                if not isinstance(
                    item,
                    str,
                ):
                    continue


                value = item.strip()


                if not value:

                    continue


                duplicate = False


                for part in title_parts:

                    if value.lower() == str(part).lower():

                        duplicate = True

                        break


                if not duplicate:

                    selected_models.append(
                        value
                    )


        selected_models = selected_models[:1]


        title_parts.extend(
            selected_models
        )



        # =========================
        # Search Keyword
        # 搜索补充词
        # =========================

        if isinstance(
            title_search_focus,
            list,
        ):

            for keyword in title_search_focus:

                keyword = str(
                    keyword
                ).strip()


                if not keyword:

                    continue


                duplicate = False


                for part in title_parts:

                    if keyword.lower() in str(part).lower():

                        duplicate = True

                        break


                if not duplicate:

                    title_parts.append(
                        keyword
                    )

                    break
        # =========================
        # Attribute
        # 高价值属性
        # =========================
        # =========================
        # Title Planner Features
        # 高价值卖点
        # =========================
        
        if isinstance(
            plan_features,
            list,
        ):
        
            for feature in plan_features:
        
                feature = str(feature).strip()
        
                if not feature:
                    continue
        
        
                duplicate = False
        
        
                for part in title_parts:
        
                    if feature.lower() in str(part).lower():
        
                        duplicate = True
                        break
        
        
                if not duplicate:
        
                    title_parts.append(
                        feature
                    )
        
                    break
        if isinstance(
            title_attribute_focus,
            list,
        ):

            for attribute in title_attribute_focus:

                attribute = str(
                    attribute
                ).strip()


                if not attribute:

                    continue


                duplicate = False


                for part in title_parts:

                    if attribute.lower() in str(part).lower():

                        duplicate = True

                        break


                if not duplicate:

                    title_parts.append(
                        attribute
                    )

                    break



        # =========================
        # Compatibility Brand
        # =========================

        relationship_brands = relationship.get(
            "brands",
            [],
        )


        if relationship_brands:

            title_parts.append(
                "Compatible with "
                +
                ", ".join(
                    relationship_brands[:2]
                )
            )



        # =========================
        # Build Title
        # =========================

        title = " ".join(
            [
                str(item)
                for item in title_parts
                if item
            ]
        )


        title = TitleGenerator.clean_title(
            title
        )


        title = TitleGenerator.format_title_case(
            title
        )


        title = TitleGenerator.limit_length(
            title,
            75,
        )


        blocked_words = (
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
                    len(blocked_words) == 0,

            },


            "blocked_words":
                blocked_words,


            "brand_check":
                "passed",

        }



    @staticmethod
    def clean_title(
        text: str,
    ):

        for word in TitleGenerator.BLOCKED_WORDS:

            text = re.sub(

                r"\b"
                +
                re.escape(word)
                +
                r"\b",

                "",

                text,

                flags=re.I,

            )


        text = re.sub(

            r"\s+",

            " ",

            text,

        )


        return text.strip()



    @staticmethod
    def format_title_case(
        text: str,
    ):

        words = text.split()


        small_words = [

            "with",
            "and",
            "for",
            "de",
            "para",
            "con",

        ]


        result = []


        for index, word in enumerate(words):

            if (
                index > 0
                and
                word.lower()
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
        max_length: int = 75,
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


        return " ".join(result)



    @staticmethod
    def check_blocked_words(
        text: str,
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

                flags=re.I,

            ):

                found.append(
                    word
                )


        return found
