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
        # 不直接把原始identity全部交给AI
        # 避免品牌名、用户群体、场景污染
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


        identity_candidates = {

            "product_name":
                raw_identity.get(
                    "name",
                    ""
                ),


            "title_product_identity":
                raw_identity.get(
                    "title_product_identity",
                    ""
                ),


            "buyer_search_identity":
                raw_identity.get(
                    "buyer_search_identity",
                    ""
                ),


            "knowledge_product_type":
                knowledge_identity.get(
                    "product_type",
                    ""
                ),


            "knowledge_object_name":
                knowledge_identity.get(
                    "object_name",
                    ""
                ),


            "category":
                raw_identity.get(
                    "category",
                    ""
                ),

        }


        # =================================================
        # 构造Title Strategy输入
        # =================================================

        product_context = {


            # 产品身份候选
            # 让AI判断，而不是直接相信某一个字段
            "product_identity_candidates":
                identity_candidates,


            # 商品知识
            "product_knowledge":
                product_knowledge,


            # 基础信息
            "basic_info":
                profile.get(
                    "basic_info",
                    {}
                ),


            # 标题信息
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


            # 标题约束
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
