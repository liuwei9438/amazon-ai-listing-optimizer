import json


class HighlightGenerator:

    @staticmethod
    def generate(profile):
        """
        Amazon 商品亮点生成器

        目标：
        - 生成购买决策信息
        - 不生成标题
        - 不堆关键词
        - 不输出JSON结构
        - 不输出空属性
        """

        highlights = []

        basic = profile.get("basic_info", {}) or {}
        facts = profile.get("facts", {}) or {}
        compatibility = profile.get("compatibility", {}) or {}

        product_type = (
            basic.get("product_type")
            or "replacement component"
        )

        core_function = (
            profile.get("core_function")
            or facts.get("function")
            or ""
        )

        # 1. 功能价值
        if core_function:
            highlights.append(
                {
                    "title": "Replacement Function",
                    "content":
                        f"Designed to replace {core_function.lower()}."
                }
            )

        else:
            highlights.append(
                {
                    "title": "Replacement Function",
                    "content":
                        f"Designed as a replacement component for {product_type.lower()}."
                }
            )


        # 2. 兼容信息
        brands = compatibility.get("brands", []) or []
        models = compatibility.get("models", []) or []

        if brands and models:

            brand_text = brands[0]

            model_text = ", ".join(
                models[:5]
            )

            highlights.append(
                {
                    "title": "Compatibility",
                    "content":
                        f"Compatible with {brand_text} models {model_text}."
                }
            )


        # 3. 材质
        material = (
            facts.get("material")
            or ""
        )

        if isinstance(material, dict):
            material = material.get("value", "")

        if material and material.lower() not in [
            "unknown",
            "none",
            "null",
            "[]",
            "{}"
        ]:
            highlights.append(
                {
                    "title": "Material",
                    "content":
                        f"Made of {material} material."
                }
            )


        # 4. 使用场景
        application = (
            facts.get("application")
            or ""
        )

        if application:
            highlights.append(
                {
                    "title": "Application",
                    "content": application
                }
            )


        return HighlightGenerator.clean(highlights)


    @staticmethod
    def clean(items):

        result = []

        for item in items:

            if not isinstance(item, dict):
                continue

            title = item.get("title", "")
            content = item.get("content", "")

            if not content:
                continue


            # 清理异常字符
            if isinstance(content, (dict, list)):
                continue


            text = str(content).strip()


            if text in [
                "",
                "[]",
                "{}",
                "None",
                "unknown"
            ]:
                continue


            result.append(
                f"{title}: {text}"
            )


        return result
