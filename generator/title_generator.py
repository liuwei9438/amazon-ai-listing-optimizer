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


    IGNORED_ATTRIBUTES = [
        "PP",
        "ABS",
        "plastic",
        "metal",
        "stainless steel",
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
            "main_product",
            []
        )
        
        
        plan_search_terms = title_plan.get(
            "search_terms",
            []
        )
        
        
        plan_features = title_plan.get(
            "features",
            []
        )
        
        
        plan_compatibility = title_plan.get(
            "compatibility",
            []
        )
        
        
        plan_avoid = title_plan.get(
            "avoid",
            [])


        title_parts = []    

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
        

        title_search_focus = plan_search_terms

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
        def is_valid_model(value):
        
            value = str(value).strip()
        
        
            # 功能参数，不是型号
            blocked_patterns = [
                r"^\d+D$",
                r"^\d+-in-\d+$",
                r"^IPX\d+$",
            ]
        
        
            for pattern in blocked_patterns:
        
                if re.match(
                    pattern,
                    value,
                    re.I
                ):
        
                    return False
        
        
            return True

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
                if not is_valid_model(value):
                
                    continue

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


                    words = keyword.lower().split()
                
                
                    existing_text = " ".join(
                        [
                            str(x).lower()
                            for x in title_parts
                        ]
                    )
                
                
                    overlap = 0
                
                
                    for word in words:
                
                        if word in existing_text:
                
                            overlap += 1
                
                
                
                    if overlap < len(words) * 0.7:
                
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
                if attribute.lower() in [
                    x.lower()
                    for x in TitleGenerator.IGNORED_ATTRIBUTES
                ]:
                
                    continue

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

        relationship_brands = plan_compatibility


        if relationship_brands:
        
            title_parts.extend(
                relationship_brands
            )


        # =========================
        # Build Title
        # =========================
        clean_parts = []
        
        
        for part in title_parts:
        
            skip = False
        
        
            for avoid in plan_avoid:
        
                if str(avoid).lower() in str(part).lower():
        
                    skip = True
        
                    break
        
        
            if not skip:
        
                clean_parts.append(part)
        
        
        
        title_parts = clean_parts
        unique_parts = []


        for item in title_parts:
        
            exists = False
        
        
            for old in unique_parts:
        
                if str(item).lower() == str(old).lower():
        
                    exists = True
        
                    break
        
        
            if not exists:
        
                unique_parts.append(item)
        
        
        title_parts = unique_parts
      
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
