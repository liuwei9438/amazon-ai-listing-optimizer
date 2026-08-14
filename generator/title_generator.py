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
            {}
        )
        
        
        title_strategy = profile.get(
            "title_strategy",
            {}
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

        
        plan_title_attributes = title_plan.get(
            "title_attributes",
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

        strategy_core_product = (
            title_strategy.get(
                "core_product",
                ""
            )
        )
        
        
        strategy_title_identity = []
        
        
        if strategy_core_product:
        
            strategy_title_identity.append(
                strategy_core_product
            )
        
        
        title_identity_focus = (
            strategy_title_identity
            or
            plan_identity
            or
            generation_strategy.get(
                "title_identity_focus",
                [],
            )
        )
        

        title_search_focus = (
            strategy_search_terms
            or
            plan_search_terms
        )

        strategy_must_include = (
            title_strategy.get(
                "must_include",
                []
            )
        )
        
        
        strategy_optional_include = (
            title_strategy.get(
                "optional_include",
                []
            )
        )
        
        
        title_attribute_focus = (
            strategy_must_include
            or
            plan_title_attributes
            or
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

            identity_added = 0


            for item in title_identity_focus:
            
            
                item = str(item).strip()
            
            
                if not item:
            
                    continue
            
            
                # 分类词不要进入标题
                if item.lower() in [
                    "personal care",
                    "personal care appliances",
                    "washing machine parts",
                    "3d printer parts",
                ]:
            
                    continue
            
            
                if not TitleGenerator.has_semantic_overlap(
                    item,
                    title_parts
                ):
                
                    title_parts.append(item)
            
            
                identity_added += 1
            
            
                if identity_added >= 1:
            
                    break


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

                if len(value) <= 2:
                
                    continue
                
                
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


                    if TitleGenerator.has_semantic_overlap(
                        value,
                        title_parts,
                    ):
                
                        continue
                
                
                
                    selected_models.append(
                        value
                    )


        selected_models = selected_models[:1]
        
        
        title_parts.extend(
            selected_models
        )

        
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
        
        
                if attribute.lower() in [
                    x.lower()
                    for x in TitleGenerator.IGNORED_ATTRIBUTES
                ]:
        
                    continue
        
        
                if not attribute:
        
                    continue
        
        
                duplicate = TitleGenerator.has_semantic_overlap(
                    attribute,
                    title_parts,
                )
                if not duplicate:

                    title_parts.append(
                        attribute
                    )
        # =========================
        # Optional Include
        # =========================
        
        if isinstance(
            strategy_optional_include,
            list,
        ):
        
            for item in strategy_optional_include:
        
                item = str(item).strip()
        
                if not item:
                    continue
        
        
                if TitleGenerator.has_semantic_overlap(
                    item,
                    title_parts,
                ):
                    continue
        
        
                title_parts.append(item)
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


                duplicate = TitleGenerator.has_semantic_overlap(
                    attribute,
                    title_parts,
                )
                
                
                if not duplicate:
                
                    title_parts.append(
                        attribute
                    )


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
        # Compatibility Brand
        # =========================

        relationship_brands = (
            title_strategy.get(
                "compatibility_priority",
                []
            )
            or
            plan_compatibility
        )


        protected_compatibility = []


        if relationship_brands:

            for item in relationship_brands:

                text = str(
                    item
                ).strip()


                if text:

                    protected_compatibility.append(
                        text
                    )

                    title_parts.append(
                        text
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


        # =========================
        # Final Attribute Filter
        # 删除材质等低价值词
        # =========================
        
        final_parts = []
        
        
        for part in title_parts:
        
            blocked = False
        
        
            for attr in TitleGenerator.IGNORED_ATTRIBUTES:
        
                if str(part).lower() == attr.lower():
        
                    blocked = True
        
                    break
        
        
            if not blocked:
        
                final_parts.append(part)
        
        
        
        title_parts = final_parts
        
        
        
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
      
        title_parts = (
            TitleGenerator.compress_title_parts(
                title_parts,
                75,
                title_attribute_focus,
            )
        )


        protected_parts = (
            TitleGenerator.protect_compatibility_phrases(
                title_parts
            )
        )
        
        
        title = " ".join(
            [
                str(item)
                for item in protected_parts
                if item
            ]
        )
        
        title = title.replace(
            "_",
            " "
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


    # =====================================================
    # 语义重复检测
    # 防止 Button / Cover / Shaver 等核心词重复
    # =====================================================

    @staticmethod
    def has_semantic_overlap(
        new_text,
        existing_parts,
    ):

        if not new_text:
            return False


        if not existing_parts:
            return False



        def extract_words(text):

            words = re.findall(
                r"[a-zA-Z0-9]+",
                str(text).lower()
            )


            ignore_words = {

                "compatible",
                "with",
                "for",
                "and",
                "the",

            }


            result = set()


            for word in words:

                # 太短词忽略
                if len(word) <= 2:
                    continue


                if word in ignore_words:
                    continue


                result.add(word)


            return result



        new_words = extract_words(
            new_text
        )


        if not new_words:

            return False



        for old in existing_parts:


            old_words = extract_words(
                old
            )


            overlap = (
                new_words
                &
                old_words
            )


            # 一个核心词重复即可认为可能重复
            if overlap:

                return True



        return False
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
    def compress_title_parts(
        parts,
        max_length=75,
        priority_parts=None,
    ):

        if len(
            " ".join(parts)
        ) <= max_length:

            return parts



        result = []


        # 第一优先级：
        # 产品身份

        for part in parts:

            if len(result) == 0:

                result.append(
                    part
                )



        # 第二优先级：
        # 型号

        for part in parts:

            text = str(
                part
            )


            if re.search(
                r"[A-Za-z]+\d+",
                text
            ):

                if text not in result:

                    result.append(
                        text
                    )
        # 第三优先级：
        # 标题高价值属性

        if priority_parts:

            for part in priority_parts:

                if part in parts:

                    if part not in result:

                        result.append(
                            part
                        )


        # 第四优先级：
        # Compatible with 品牌

        for part in parts:

            if "Compatible with" in str(part):

                if part not in result:

                    result.append(
                        part
                    )



        # 第五优先级：
        # 其他卖点

        for part in parts:

            if part not in result:

                if len(
                    " ".join(result+[part])
                ) <= max_length:

                    result.append(
                        part
                    )



        return result
    @staticmethod
    def protect_compatibility_phrases(
        parts
    ):

        protected = []

        for part in parts:

            text = str(part)

            if text.startswith(
                "Compatible with"
            ):

                protected.append(
                    text.replace(
                        " ",
                        "_",
                    )
                )

            else:

                protected.append(
                    text
                )

        return protected
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
