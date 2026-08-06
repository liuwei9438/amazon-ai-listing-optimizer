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
        """
        Generate Amazon title from Product Knowledge V5.

        Strategy:
        - Product identity first
        - Search intent supplement
        - Model priority for parts
        - Compatibility wording
        - Fact protection
        """


        knowledge = profile.get(
            "product_knowledge",
            {},
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



        title_parts = []



        # =========================
        # Strategy Data
        # =========================

        title_identity_focus = (
            generation_strategy.get(
                "title_identity_focus",
                [],
            )
        )


        title_attribute_focus = (
            generation_strategy.get(
                "title_attribute_focus",
                [],
            )
        )


        title_search_focus = (
            generation_strategy.get(
                "title_search_focus",
                [],
            )
        )


        title_focus = (
            generation_strategy.get(
                "title_focus",
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
        # Model / Part Number
        # 型号零件号
        # =========================


        selected_models = []

        removed_models = []


        title_identifiers = []


        if isinstance(
            title_focus,
            list,
        ):

            title_identifiers.extend(
                title_focus
            )



        for item in title_identifiers:

            if not isinstance(
                item,
                str,
            ):
                continue


            text = item.strip()


            if not text:
                continue


            duplicate = False


            for part in title_parts:

                if text.lower() == str(part).lower():

                    duplicate = True


                    break


            if not duplicate:

                selected_models.append(
                    text
                )



        selected_models = selected_models[:1]


        title_parts.extend(
            selected_models
        )



        # =========================
        # Search Intent
        # 搜索补充
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
                                    if not duplicate:

                    title_parts.append(
                        keyword
                    )

                    break



        # =========================
        # Attribute
        # 高价值属性
        # =========================

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

                    # 属性只添加一个，避免标题堆砌

                    title_parts.append(
                        attribute
                    )

                    break



        # =========================
        # Compatibility Brand
        # 兼容品牌
        # =========================

        brands = relationship.get(
            "brands",
            [],
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
        # Build Title
        # =========================

        title = " ".join(
            [
                str(x)
                for x in title_parts
                if x
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
        text,
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
        text,
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
