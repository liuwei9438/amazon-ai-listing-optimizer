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


        # ==========================================
        # 优先使用 Product Knowledge
        # 因为它经过结构化整理
        # 避免直接使用原始身份字段造成污染
        # ==========================================

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


        product_identity = (
            knowledge_identity
            if knowledge_identity
            else
            profile.get(
                "product_identity",
                {}
            )
        )


        product_context = {


            # 产品身份
            "product_identity":
                product_identity,


            # Product Knowledge
            # 提供完整商品理解
            "product_knowledge":
                product_knowledge,


            # 基础信息
            "basic_info":
                profile.get(
                    "basic_info",
                    {}
                ),


            # 标题相关信息
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


            # 规格参数
            "specifications":
                profile.get(
                    "specifications",
                    {}
                ),


            # 产品属性
            "attributes":
                profile.get(
                    "attributes",
                    {}
                ),


            # 事实锁定
            # 防止AI遗漏数量、型号、尺寸等事实
            "fact_lock":
                profile.get(
                    "fact_lock",
                    {}
                ),


            # SEO信息
            "seo":
                profile.get(
                    "seo",
                    {}
                ),

        }


        response = client.chat.completions.create(

            model=model,


            messages=[

                {
                    "role": "system",

                    "content":
                        TITLE_STRATEGY_SYSTEM_PROMPT,
                },


                {
                    "role": "user",

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
