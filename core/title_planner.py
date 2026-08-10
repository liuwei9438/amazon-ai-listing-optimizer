from __future__ import annotations

from typing import Dict, Any, List


class TitlePlanner:

    """
    标题策略规划器

    功能：
    1. 分析商品核心身份
    2. 判断标题必须包含的信息
    3. 根据75字符限制排序关键词价值

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

        facts = product_knowledge.get(
            "facts",
            {}
        )

        features = product_knowledge.get(
            "features",
            {}
        )


        return {

            "product_identity":
                TitlePlanner.get_identity(
                    identity
                ),


            "must_include":
                TitlePlanner.get_must_include(
                    identity,
                    relationship
                ),


            "high_value_features":
                TitlePlanner.get_features(
                    features
                ),


            "avoid_terms":[],

        }


    @staticmethod
    def get_identity(identity):

        result=[]


        product_name = identity.get(
            "product_name",
            ""
        )


        category = identity.get(
            "category",
            ""
        )


        if product_name:
            result.append(product_name)


        if category:
            result.append(category)


        return result



    @staticmethod
    def get_must_include(
        identity,
        relationship
    ):

        result=[]


        product_name = identity.get(
            "product_name",
            ""
        )

        if product_name:
            result.append(product_name)


        brands = relationship.get(
            "brands",
            []
        )


        if brands:
            result.append(
                "Compatible with "
                +
                brands[0]
            )


        return result



    @staticmethod
    def get_features(features):

        feature_list = features.get(
            "features",
            []
        )


        return feature_list[:5]
