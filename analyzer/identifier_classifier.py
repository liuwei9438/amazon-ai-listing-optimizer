from __future__ import annotations

import json
from typing import Any

from services import (
    OpenAIResponsesClient,
    AIClientError,
)


class IdentifierClassificationError(RuntimeError):
    pass



class IdentifierClassifier:

    """
    Identifier Classifier V1.1 Stable

    作用:
    根据完整商品上下文，
    判断候选标识属于:

    - model_number
    - part_number
    - dimension
    - specification
    - quantity
    - unknown

    注意:
    不直接修改 Product Profile。
    只提供分类结果。
    """



    CLASSIFICATION_TYPES = [

        "model_number",

        "part_number",

        "dimension",

        "specification",

        "quantity",

        "unknown",

    ]



    SYSTEM_PROMPT = """

You are a product data classification expert.

Your task is to classify candidate identifiers
using the complete product context.

Do NOT judge only by string format.

Consider:

- product name
- product type
- main function
- brand information
- compatibility information
- title
- description


Classify each candidate into exactly one category:

model_number:
A product/device model identifier.

part_number:
A manufacturer or replacement part identifier.

dimension:
A size measurement.

specification:
A technical specification such as voltage, power, capacity.

quantity:
A count value.

unknown:
Cannot determine safely.


Important:

- Pure numbers are usually not models unless product context strongly supports it.
- Values with units are usually specifications or dimensions.
- Dimensions must not become models.
- If uncertain, use unknown.

Return JSON only.

"""



    RESPONSE_SCHEMA = {

        "type": "object",

        "additionalProperties": False,

        "properties": {

            "identifier_results": {

                "type": "array",

                "items": {

                    "type": "object",

                    "additionalProperties": False,

                    "properties": {

                        "value": {

                            "type": "string"

                        },


                        "type": {

                            "type": "string",

                            "enum": [
                                "model_number",
                                "part_number",
                                "dimension",
                                "specification",
                                "quantity",
                                "unknown",
                            ]

                        },


                        "confidence": {

                            "type": "number"

                        }

                    },

                    "required": [

                        "value",

                        "type",

                        "confidence"

                    ]

                }

            }

        },

        "required": [

            "identifier_results"

        ]

    }



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

                "identifier_results": []

            }



        payload = {

            "product_context":
                product_context,


            "candidates":
                candidates,

        }



        try:

            result = self.client.create_json(

                self.SYSTEM_PROMPT,

                json.dumps(

                    payload,

                    ensure_ascii=False,

                ),

                self.RESPONSE_SCHEMA,

            )


        except AIClientError as exc:

            raise IdentifierClassificationError(

                str(exc)

            ) from exc



        return self.normalize_result(
            result
        )



    @staticmethod
    def normalize_result(
        result: dict[str, Any]
    ) -> dict[str, Any]:


        if not isinstance(
            result,
            dict
        ):

            return {

                "identifier_results": []

            }



        items = result.get(

            "identifier_results",

            []

        )



        cleaned = []



        if not isinstance(
            items,
            list
        ):

            items = []



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

                    "unknown"

                )

            ).lower()



            confidence = item.get(

                "confidence",

                0

            )



            if not value:

                continue



            if category not in IdentifierClassifier.CLASSIFICATION_TYPES:

                category = "unknown"



            cleaned.append(

                {

                    "value": value,

                    "type": category,

                    "confidence": confidence,

                }

            )



        return {

            "identifier_results": cleaned

        }
        
