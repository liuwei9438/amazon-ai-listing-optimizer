class HighlightGenerator:

    @staticmethod
    def generate(profile):

        highlights = []

        basic = profile.get(
            "basic_info",
            {}
        ) or {}

        facts = profile.get(
            "facts",
            {}
        ) or {}

        compatibility = profile.get(
            "compatibility",
            {}
        ) or {}


        product_type = (
            basic.get("product_type")
            or "replacement component"
        )


        core_function = (
            profile.get("core_function")
            or facts.get("function")
            or ""
        )


        # 1 功能价值
        if core_function:

            highlights.append(
                {
                    "title": "Function",
                    "content":
                    f"Restores normal operation by replacing {core_function.lower()}."
                }
            )

        else:

            highlights.append(
                {
                    "title": "Function",
                    "content":
                    f"Replacement component designed for {product_type.lower()}."
                }
            )


        # 2 兼容

        brands = compatibility.get(
            "brands",
            []
        ) or []

        models = compatibility.get(
            "models",
            []
        ) or []


        if brands and models:

            highlights.append(
                {
                    "title": "Compatibility",
                    "content":
                    f"Compatible with {brands[0]} models {', '.join(models[:5])}."
                }
            )


        # 3 替换价值

        highlights.append(
            {
                "title": "Replacement",
                "content":
                "Designed as a replacement solution for worn or damaged components."
            }
        )


        # 4 材质

        material = facts.get(
            "material",
            ""
        )


        if isinstance(material, dict):

            material = material.get(
                "value",
                ""
            )


        if material:

            highlights.append(
                {
                    "title":"Material",
                    "content":
                    f"Made from {material} material."
                }
            )


        # 5 包装数量

        quantity = facts.get(
            "quantity",
            ""
        )


        if quantity:

            highlights.append(
                {
                    "title":"Package",
                    "content":
                    f"Package includes {quantity}."
                }
            )


        return {
            "highlights":
            HighlightGenerator.clean(
                highlights
            )
        }


    @staticmethod
    def clean(items):

        result=[]


        for item in items:

            if not isinstance(
                item,
                dict
            ):
                continue


            title=item.get(
                "title",
                ""
            )

            content=item.get(
                "content",
                ""
            )


            if not content:
                continue


            result.append(
                f"{title}: {content}"
            )


        return result
