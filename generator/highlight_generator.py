from typing import Dict, List


class HighlightGenerator:
    """
    Amazon Product Highlights Generator

    作用：
    从 Product Profile 提取产品核心卖点，
    输出简洁 Amazon Highlights。

    原则：
    - 不扩展事实
    - 不生成营销词
    - 不生成不存在参数
    - 不输出字段标签
    - 优先展示购买决策相关信息
    """


    @staticmethod
    def generate(profile: Dict) -> List[str]:

        highlights = []


        basic = profile.get(
            "basic_info",
            {}
        )


        compatibility = profile.get(
            "compatibility",
            {}
        )


        facts = profile.get(
            "facts",
            {}
        )


        # -----------------------
        # 基础信息
        # -----------------------

        product_type = (
            basic.get("product_type")
            or ""
        )


        function = (
            basic.get("core_function")
            or basic.get("function")
            or basic.get("main_function")
            or basic.get("key_function")
            or profile.get("core_function", "")
            or ""
        )



        # -----------------------
        # 1. 产品功能亮点
        # -----------------------

        if function:

            if product_type:
                clean_function = function.replace(
                    "for washing machine",
                    ""
                ).strip()
                highlights.append(
                    f"Replacement {product_type.lower()} for {clean_function}."
                )

            else:

                highlights.append(
                    f"Replacement component for {function}."
                )



        # -----------------------
        # 2. 兼容型号
        # -----------------------

        brands = compatibility.get(
            "brands",
            []
        )


        models = compatibility.get(
            "models",
            []
        )


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



        # -----------------------
        # 3. 替换价值
        # -----------------------

        highlights.append(
            "Direct replacement component for replacing worn or damaged parts."
        )



        # -----------------------
        # 4. 材质信息
        # -----------------------

        material = facts.get(
            "material",
            ""
        )


        if material:

            highlights.append(
                f"Made of {material} material."
            )



        # -----------------------
        # 合规过滤
        # -----------------------

        banned_words = [

            "best",
            "premium",
            "high quality",
            "perfect",
            "professional",
            "easy",
            "convenient",
            "daily use",
            "practical",
            "original",
            "genuine",
            "official",
            "guaranteed",
            "top",

        ]


        result = []


        for item in highlights:


            text = str(item).strip()


            if not text:
                continue


            lower = text.lower()


            blocked = False


            for word in banned_words:

                if word in lower:

                    blocked = True
                    break


            if not blocked:

                if text not in result:

                    result.append(text)



        # Amazon 商品亮点最多3条
        return result[:3]
