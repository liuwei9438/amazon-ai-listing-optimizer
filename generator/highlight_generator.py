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
            or ""
        ).lower()


        core_function = (
            profile.get("core_function")
            or facts.get("function")
            or ""
        )


        product_category = (
            HighlightGenerator.detect_category(
                product_type,
                core_function
            )
        )


        # =========================
        # 1. 核心功能价值
        # =========================

        if core_function:

            highlights.append(
                {
                    "title": "Function",
                    "content":
                    HighlightGenerator.clean_text(
                        f"Helps restore normal operation by replacing {core_function.lower()}."
                    )
                }
            )

        else:

            highlights.append(
                {
                    "title": "Function",
                    "content":
                    f"Designed as a replacement component for {product_type}."
                }
            )


        # =========================
        # 2. 兼容信息
        # =========================

        brands = compatibility.get(
            "brands",
            []
        ) or []


        models = compatibility.get(
            "models",
            []
        ) or []


        if brands and models:

            model_text = ", ".join(
                models[:5]
            )


            highlights.append(
                {
                    "title": "Compatibility",
                    "content":
                    f"Compatible with {brands[0]} models {model_text}."
                }
            )


        # =========================
        # 3. 根据产品类型生成购买价值
        # =========================


        if product_category == "replacement":


            highlights.append(
                {
                    "title":"Replacement",
                    "content":
                    "Direct replacement design helps replace worn or damaged components without modifying existing equipment."
                }
            )


        elif product_category == "consumable":


            highlights.append(
                {
                    "title":"Replacement",
                    "content":
                    "Designed for regular replacement to help maintain product performance."
                }
            )


        else:


            highlights.append(
                {
                    "title":"Design",
                    "content":
                    "Designed for practical daily use and convenient operation."
                }
            )



        # =========================
        # 4. 材质
        # =========================

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


        # =========================
        # 5. 包装数量
        # =========================


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
            )[:5]

        }



    # =============================
    # 产品分类判断
    # =============================


    @staticmethod
    def detect_category(
        product_type,
        function
    ):


        text = (
            product_type
            +
            " "
            +
            function
        ).lower()



        replacement_words = [

            "replacement",
            "part",
            "button",
            "cover",
            "head",
            "blade",
            "component"

        ]


        consumable_words = [

            "filter",
            "pad",
            "cartridge",
            "bag"

        ]



        for word in consumable_words:

            if word in text:

                return "consumable"



        for word in replacement_words:

            if word in text:

                return "replacement"



        return "general"




    # =============================
    # 文本清理
    # =============================


    @staticmethod
    def clean_text(text):

        forbidden = [

            "best",
            "premium",
            "original",
            "genuine",
            "official",
            "number one"

        ]


        for word in forbidden:

            text = text.replace(
                word,
                ""
            )


        return text.strip()



    @staticmethod
    def clean(items):

        result=[]


        for item in items:


            if not isinstance(
                item,
                dict
            ):

                continue



            title = item.get(
                "title",
                ""
            )


            content = item.get(
                "content",
                ""
            )


            if not content:

                continue



            result.append(
                f"{title}: {content}"
            )



        return result
