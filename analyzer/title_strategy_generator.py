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


        product_context = {

            # 产品身份
            "product_identity":
                profile.get(
                    "product_identity",
                    {}
                ),


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
