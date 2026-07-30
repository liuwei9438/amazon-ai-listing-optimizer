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
        # 1. 产品功能
        # -----------------------

        function = (
            basic.get("core_function")
            or basic.get("function")
            or basic.get("main_function")
            or basic.get("key_function")
            or profile.get("core_function", "")
            or ""
        )


        if function:

            highlights.append(
                f"Replacement component designed for {function}."
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


        if brands and models:

            model_text = ", ".join(
                models[:5]
            )

            highlights.append(
                f"Compatible with {brands[0]} models {model_text}."
            )


        elif models:

            model_text = ", ".join(
                models[:5]
            )

            highlights.append(
                f"Compatible with specified models {model_text}."
            )



        # -----------------------
        # 3. 产品类型
        # -----------------------

        product_type = (
            basic.get("product_type")
            or ""
        )


        if product_type:

            highlights.append(
                f"Replacement part for {product_type} applications."
            )



        # -----------------------
        # 4. 材质
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
        # 清理
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

        ]


        result = []


        for item in highlights:

            text = item.strip()


            if not text:
                continue


            lower = text.lower()


            blocked = False


            for word in banned_words:

                if word in lower:
                    blocked = True
                    break


            if not blocked:

                result.append(text)



        # 最大3条
        return result[:3]
