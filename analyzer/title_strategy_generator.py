from __future__ import annotations

import json

from openai import OpenAI

from .title_strategy_prompt import (
    TITLE_STRATEGY_SYSTEM_PROMPT,
)


class TitleStrategyError(Exception):
    pass


class TitleStrategyGenerator:

    @staticmethod
    def generate(
        profile: dict,
        api_key: str,
        model="gpt-4.1-mini",
    ):

        client = OpenAI(
            api_key=api_key
        )


        # =================================================
        # 产品身份整理
        #
        # 目标：
        # 给AI提供干净的产品身份信息
        # 避免卖家名称、系列名称污染标题判断
        # =================================================

        raw_identity = (
            profile.get(
                "product_identity",
                {}
            )
        )


        product_knowledge = (
            profile.get(
                "product_knowledge",
                {}
            )
        )


        knowledge_identity = (
            product_knowledge.get(
                "identity",
                {}
            )
            if isinstance(
                product_knowledge,
                dict
            )
            else {}
        )


        # 不直接发送：
        # product_name
        # object_name
        #
        # 因为这些字段可能包含：
        # 卖家命名、系列名称、营销名称

        identity_candidates = {

            # AI需要判断的真实产品身份
            "title_product_identity":
                raw_identity.get(
                    "title_product_identity",
                    ""
                ),


            # 买家搜索表达
            # 可能包含场景，需要AI过滤
            "buyer_search_identity":
                raw_identity.get(
                    "buyer_search_identity",
                    ""
                ),


            # 产品类型
            "product_type":
                knowledge_identity.get(
                    "product_type",
                    ""
                ),


            # 类目
            "category":
                raw_identity.get(
                    "category",
                    ""
                ),

        }


        product_context = {


            # 产品身份候选
            "product_identity_candidates":
                identity_candidates,


            # 产品知识
            # 保留用于理解功能和特征
            "product_knowledge":
                product_knowledge,


            # 基础信息
            "basic_info":
                profile.get(
                    "basic_info",
                    {}
                ),


            # 标题信息
            # 包含高价值卖点
            "title_information":
                profile.get(
                    "title_information",
                    {}
                ),


            # 兼容信息
            "compatibility":
                profile.get(
                    "compatibility",
                    {}
                ),


            # 规格
            "specifications":
                profile.get(
                    "specifications",
                    {}
                ),


            # 属性
            "attributes":
                profile.get(
                    "attributes",
                    {}
                ),


            # 事实锁定
            "fact_lock":
                profile.get(
                    "fact_lock",
                    {}
                ),


            # SEO
            "seo":
                profile.get(
                    "seo",
                    {}
                ),


            # 标题限制
            "title_constraints":
                {
                    "marketplace":
                        "Amazon",

                    "max_title_length":
                        75,

                    "objective":
                        "maximize purchase-relevant information within the title limit",
                },

        }


        response = client.chat.completions.create(

            model=model,


            messages=[

                {
                    "role":
                        "system",

                    "content":
                        TITLE_STRATEGY_SYSTEM_PROMPT,
                },


                {
                    "role":
                        "user",

                    "content":
                        json.dumps(
                            product_context,
                            ensure_ascii=False,
                            indent=2,
                        ),
                },

            ],


            response_format={
                "type":
                    "json_object"
            },

        )


        try:

            result = json.loads(
                response.choices[0]
                .message
                .content
            )


            return result


        except Exception as exc:

            raise TitleStrategyError(
                f"Title strategy parse failed: {exc}"
            )
