from __future__ import annotations

from typing import Dict, Any


class TitlePlanner:

    """
    标题策略规划器

    功能：
    1. 提取标题核心产品词
    2. 提取高价值搜索词
    3. 提取标题可使用卖点
    4. 提取兼容信息
    5. 提取标题应该避免的信息

    不生成最终标题
    """

    @staticmethod
    def plan(
        product_knowledge: Dict[str, Any]
    ) -> Dict[str, Any]:

        identity = product_knowledge.get(
            "identity",
            {}
        )

        relationship = product_knowledge.get(
            "relationship",
            {}
        )


        return {

            "main_product":
                TitlePlanner.get_main_product(
                    identity
                ),


            "search_terms":
                TitlePlanner.get_search_terms(
                    product_knowledge
                ),


            "features":
                TitlePlanner.get_features(
                    product_knowledge
                ),


            "compatibility":
                TitlePlanner.get_compatibility(
                    relationship
                ),


            "avoid":
                TitlePlanner.get_avoid_terms(
                    identity
                ),

        }


    # =====================================================
    # 核心产品词
    # =====================================================

    @staticmethod
    def get_main_product(
        identity
    ):

        result = []


        object_name = identity.get(
            "object_name",
            ""
        )


        product_name = identity.get(
            "product_name",
            ""
        )


        value = (
            object_name
            or
            product_name
        )


        if value:

            result.append(
                str(value).strip()
            )


        return result



    # =====================================================
    # 搜索关键词
    # =====================================================

    @staticmethod
    def get_search_terms(
        product_knowledge
    ):

        result = []


        seo = product_knowledge.get(
            "seo",
            {}
        )


        keywords = seo.get(
            "secondary_keywords",
            []
        )


        if isinstance(
            keywords,
            list
        ):

            result.extend(
                keywords[:3]
            )


        classification = (
            product_knowledge.get(
                "feature_classification",
                {}
            )
        )


        functional = classification.get(
            "functional_features",
            []
        )


        if isinstance(
            functional,
            list
        ):

            result.extend(
                functional[:2]
            )


        return TitlePlanner.clean_list(
            result
        )[:5]



    # =====================================================
    # 高价值卖点
    # =====================================================

    @staticmethod
    def get_features(
        product_knowledge
    ):

        result = []


        classification = (
            product_knowledge.get(
                "feature_classification",
                {}
            )
        )


        design = classification.get(
            "design_features",
            []
        )


        functional = classification.get(
            "functional_features",
            []
        )


        if isinstance(
            design,
            list
        ):

            result.extend(
                design[:3]
            )


        if isinstance(
            functional,
            list
        ):

            result.extend(
                functional[:3]
            )


        blocked_features = [

            "start washing machine",

            "protects extruder",

            "enhances heat retention",

            "shaving and grooming",

        ]


        filtered = []


        for item in result:

            text = str(
                item
            ).strip()


            if not text:

                continue


            lower_text = text.lower()


            blocked = False


            for word in blocked_features:

                if word in lower_text:

                    blocked = True

                    break


            if blocked:

                continue


            filtered.append(
                text
            )


        return TitlePlanner.clean_list(
            filtered
        )[:5]



    # =====================================================
    # 兼容品牌
    # =====================================================

    @staticmethod
    def get_compatibility(
        relationship
    ):

        brands = relationship.get(
            "brands",
            []
        )


        if isinstance(
            brands,
            list
        ) and brands:


            return [

                "Compatible with "
                +
                str(
                    brands[0]
                )

            ]


        return []



    # =====================================================
    # 避免进入标题的词
    # =====================================================

    @staticmethod
    def get_avoid_terms(
        identity
    ):

        category = identity.get(
            "category",
            ""
        )


        if not category:

            return []


        avoid = []


        category_lower = (
            str(category)
            .lower()
        )


        if category:

            avoid.append(
                category
            )


        if (
            "parts"
            in
            category_lower
            or
            "appliances"
            in
            category_lower
        ):

            avoid.append(
                category
            )


        return TitlePlanner.clean_list(
            avoid
        )



    # =====================================================
    # 工具
    # =====================================================

    @staticmethod
    def clean_list(
        values
    ):

        result = []

        seen = set()


        for value in values:

            text = str(
                value
            ).strip()


            if not text:

                continue


            key = text.lower()


            if key in seen:

                continue


            seen.add(
                key
            )


            result.append(
                text
            )


        return result
