from __future__ import annotations

import json
from typing import Any

from services import OpenAIResponsesClient, AIClientError


class IdentifierClassificationError(RuntimeError):
    pass



class IdentifierClassifier:

    """
    AI Identifier Classifier

    功能:
    - 根据完整产品上下文判断候选标识类型
    - 不依赖固定型号规则
    - 避免尺寸、参数误判为型号

    输出:
    model_number
    part_number
    dimension
    specification
    quantity
    unknown
    """



    SYSTEM_PROMPT = """

You are a product data classification expert.

Your task is to classify candidate identifiers
based on the complete product context.

Do NOT classify only by text format.

Consider:

- product type
- product function
- brand information
- compatibility information
- title
- description
- usage scenario


Each candidate must be classified as one of:

model_number
part_number
dimension
specification
quantity
unknown


Rules:

1. Product models usually identify a specific device/product version.

2. Dimensions must not be classified as models.

3. Values with units such as cm, mm, V, W, kg are usually specifications.

4. Pure numbers without product context should not become models.

5. If uncertain, use unknown.

Return JSON only.

"""



    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1-mini"
    ):

        self.client = OpenAIResponsesClient(
            api_key=api_key,
            model=model,
        )



    def classify(
        self,
        product_context: dict[str, Any],
        candidates: list[str],
    ) -> dict[str, Any]:


        if not candidates:

            return {
                "models": [],
                "part_numbers": [],
                "dimensions": [],
                "specifications": [],
                "unknown": [],
            }



        prompt = {

            "product_context":
                product_context,


            "candidates":
                candidates,

        }



        try:

            result = self.client.create_json(
                self.SYSTEM_PROMPT,
                json.dumps(
                    prompt,
                    ensure_ascii=False,
                ),
                {
                    "type": "object",
                    "properties": {

                        "identifier_results": {

                            "type": "array",

                            "items": {

                                "type": "object",

                                "properties": {

                                    "value":
                                        {
                                        "type":"string"
                                        },

                                    "type":
                                        {
                                        "type":"string"
                                        },

                                    "confidence":
                                        {
                                        "type":"number"
                                        }

                                },

                                "required":[
                                    "value",
                                    "type",
                                    "confidence"
                                ]

                            }

                        }

                    },

                    "required":[
                        "identifier_results"
                    ]

                }
            )


        except AIClientError as exc:

            raise IdentifierClassificationError(
                str(exc)
            ) from exc



        return (
            self.normalize_result(
                result
            )
        )



    @staticmethod
    def normalize_result(
        result: dict[str, Any]
    ) -> dict[str, list[str]]:


        output = {

            "models": [],

            "part_numbers": [],

            "dimensions": [],

            "specifications": [],

            "unknown": [],

        }


        items = result.get(
            "identifier_results",
            []
        )


        if not isinstance(
            items,
            list
        ):

            return output



        for item in items:

            if not isinstance(
                item,
                dict
            ):

                continue


            value = str(
                item.get(
                    "value",
                    ""
                )
            ).strip()


            category = str(
                item.get(
                    "type",
                    ""
                )
            ).lower()



            if not value:

                continue



            if category == "model_number":

                output["models"].append(
                    value
                )


            elif category == "part_number":

                output["part_numbers"].append(
                    value
                )


            elif category == "dimension":

                output["dimensions"].append(
                    value
                )


            elif category == "specification":

                output["specifications"].append(
                    value
                )


            elif category == "quantity":

                output["unknown"].append(
                    value
                )


            else:

                output["unknown"].append(
                    value
                )



        return output
