from typing import Dict, List


class HighlightGenerator:
    """
    Amazon Product Highlights Generator

    规则：
    - 基于 Product Profile 生成
    - 不再次调用 AI
    - 不改变事实
    - 不生成营销词
    - 适用于不同产品类型
    """


    BANNED_WORDS = [
        "best",
        "premium",
        "high quality",
        "perfect",
        "professional",
        "original",
        "genuine",
        "official",
        "guaranteed",
        "top",
        "#1",
    ]


    @staticmethod
    def generate(profile: Dict) -> List[str]:

        highlights = []


        basic = profile.get(
            "basic_info",
            {}
        ) or {}


        compatibility = profile.get(
            "compatibility",
            {}
        ) or {}


        facts = profile.get(
            "facts",
            {}
        ) or {}


        product_type = str(
            basic.get(
                "product_type",
                ""
            )
        ).strip()


        function = str(
            basic.get(
                "main_function",
                ""
            )
            or basic.get(
                "core_function",
                ""
            )
            or ""
        ).strip()



        # ==========================
        # 1. 产品身份 + 核心功能
        # ==========================

        if product_type and function:

            clean_function = (
                HighlightGenerator.remove_repeat_words(
                    function,
                    product_type
                )
            )

            highlights.append(
                f"Replacement {product_type.lower()} for {clean_function}."
            )


        elif product_type:

            highlights.append(
                f"Replacement component for {product_type.lower()}."
            )


        elif function:

            highlights.append(
                f"Replacement component for {function}."
            )



        # ==========================
        # 2. 兼容信息
        # ==========================

        brands = compatibility.get(
            "brands",
            []
        ) or []


        models = compatibility.get(
            "models",
            []
        ) or []


        if models:


            model_text = ", ".join(
                models[:5]
            )


            if brands:

                highlights.append(
                    f"Compatible with {brands[0]} models {model_text}."
                )

            else:

                highlights.append(
                    f"Compatible with models {model_text}."
                )



        # ==========================
        # 3. 替换价值
        # 根据产品类型动态表达
        # ==========================

        if product_type:

            text = product_type.lower()


            if any(
                word in text
                for word in [
                    "filter",
                    "cartridge"
                ]
            ):

                highlights.append(
                    "Designed for replacing used filter components during maintenance."
                )


            elif any(
                word in text
                for word in [
                    "head",
                    "blade"
                ]
            ):

                highlights.append(
                    "Designed for replacing worn components during regular use."
                )


            else:

                highlights.append(
                    "Direct replacement component for worn or damaged parts."
                )



        # ==========================
        # 4. 材质
        # ==========================

        material = facts.get(
            "material",
            ""
        )


        if isinstance(material, dict):

            material = material.get(
                "value",
                ""
            )


        if isinstance(material, list):

            material = ", ".join(
                [
                    str(x)
                    for x in material
                    if x
                ]
            )


        if material:

            highlights.append(
                f"Made of {material} material."
            )



        # ==========================
        # 清理
        # ==========================

        return HighlightGenerator.clean(
            highlights
        )



    @staticmethod
    def remove_repeat_words(
        function,
        product_type
    ):

        result = function


        product_words = product_type.lower().split()


        for word in product_words:

            if len(word) > 3:

                result = result.replace(
                    word,
                    ""
                )


        return " ".join(
            result.split()
        )



    @staticmethod
    def clean(items):

        result = []


        for item in items:

            if not item:
                continue


            text = str(
                item
            ).strip()


            if not text:
                continue



            lower = text.lower()


            blocked = False


            for word in HighlightGenerator.BANNED_WORDS:

                if word in lower:

                    blocked = True
                    break



            if blocked:
                continue



            if text not in result:

                result.append(
                    text
                )



        # 商品亮点最多5条
        return result[:5]
