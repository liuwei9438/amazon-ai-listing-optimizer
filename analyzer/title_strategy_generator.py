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

            "product_identity":
                profile.get(
                    "product_identity",
                    {}
                ),

            "basic_info":
                profile.get(
                    "basic_info",
                    {}
                ),

            "title_information":
                profile.get(
                    "title_information",
                    {}
                ),

            "compatibility":
                profile.get(
                    "compatibility",
                    {}
                ),

            "specifications":
                profile.get(
                    "specifications",
                    {}
                ),

            "attributes":
                profile.get(
                    "attributes",
                    {}
                ),

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
                    )
                }

            ],

            response_format={
                "type":
                "json_object"
            }

        )


        try:

            return json.loads(
                response.choices[0]
                .message
                .content
            )

        except Exception as exc:

            raise TitleStrategyError(
                str(exc)
            )
