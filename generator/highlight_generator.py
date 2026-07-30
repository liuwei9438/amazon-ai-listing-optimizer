from __future__ import annotations

import json
import re


class HighlightGenerator:


    def __init__(self, client=None, model="gpt-4.1-mini"):
        self.client = client
        self.model = model



    def generate(self, profile: dict):

        prompt = f"""
You are an Amazon listing optimization expert.

Generate Amazon Product Highlights from the product profile.

The highlights are for Amazon listing display.

Follow this structure:

1. Product Identity
Explain what the product is and what component/item it replaces.

2. Compatibility
Use:
Compatible with + brand + models

3. Core Function
Explain the main function based only on provided information.

4. Replacement Value
Explain replacement purpose or restoring function.

5. Package / Specification
Only include when information exists.


Rules:

- Generate 3-5 bullet points.
- Keep each bullet concise.
- Do not use marketing language.

Forbidden words:

best
premium
original
genuine
official
top
number one
guaranteed
sale
discount

Do not invent:
- material
- performance
- durability
- lifespan
- certification
- warranty

Do not change:
- quantity
- models
- colors
- dimensions

Brand rules:

If brand appears, always use:
Compatible with [brand]

Return JSON only:

{{
"highlights":[
"bullet 1",
"bullet 2",
"bullet 3"
]
}}

Product Profile:

{json.dumps(profile,ensure_ascii=False)}
"""


        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role":"system",
                    "content":
                    "You generate compliant Amazon product highlights."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ],
            temperature=0.2
        )


        content=response.choices[0].message.content.strip()


        return self.clean_result(content)



    def clean_result(self, content):

        """
        兼容:
        1.JSON
        2.list
        3.普通文本
        """

        highlights=[]


        # -------- JSON --------

        try:

            data=json.loads(content)


            if isinstance(data,dict):

                value=data.get(
                    "highlights",
                    []
                )

                if isinstance(value,list):
                    highlights=value


            elif isinstance(data,list):

                highlights=data


        except Exception:
            pass



        # -------- 普通文本 --------

        if not highlights:


            lines=content.split("\n")


            for line in lines:

                line=line.strip()


                line=re.sub(
                    r"^[\-\•\d\.\)]*",
                    "",
                    line
                ).strip()


                if line:
                    highlights.append(line)



        return self.filter_highlights(highlights)



    def filter_highlights(self, highlights):


        banned_words=[

            "best",
            "premium",
            "original",
            "genuine",
            "official",
            "#1",
            "number one",
            "guaranteed",
            "sale",
            "discount"

        ]


        result=[]


        for item in highlights:


            if not isinstance(item,str):
                continue


            text=item.strip()


            if not text:
                continue



            lower=text.lower()


            blocked=False


            for word in banned_words:

                if word in lower:
                    blocked=True
                    break



            if blocked:
                continue



            result.append(text)



        return result[:5]
