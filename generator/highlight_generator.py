from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


class HighlightGenerator:
    """
    Amazon Product Highlights Generator V2.4 Final

    目标：
    1. 第一条展示产品核心词(Product Identity)
    2. 后续展示真实卖点(Selling Points)
    3. 不重复标题/短标题
    4. 不生成营销词
    5. 不虚构产品信息
    6. 输出短语式 Highlights

    调用保持:
        HighlightGenerator.generate(profile)
    """


    MAX_HIGHLIGHTS = 5


    BANNED_WORDS = [
        "best",
        "premium",
        "high quality",
        "perfect",
        "professional",
        "original",
        "genuine",
        "official",
        "guaranteed",
        "top",
        "#1",
        "excellent",
        "superior",
    ]


    CATEGORY_BONUS = {

        "accessory": {

            "identity": 100,
            "compatibility": 30,
            "function": 15,
            "specification": 8,
            "material": 5,
            "feature": 5,

        },


        "consumable": {

            "identity": 100,
            "feature": 30,
            "compatibility": 20,
            "package": 15,
            "specification": 10,
            "material": 5,

        },


        "electronics": {

            "identity": 100,
            "feature": 35,
            "function": 20,
            "specification": 15,
            "design": 10,
            "compatibility": 5,

        },


        "tool": {

            "identity": 100,
            "function": 25,
            "material": 20,
            "specification": 15,
            "design": 10,

        },


        "home": {

            "identity": 100,
            "specification": 25,
            "material": 20,
            "design": 15,
            "function": 10,

        },


        "others": {

            "identity":100,

        }

    }



    FEATURE_RULES = [

        (
            r"\bipx\s*7\b",
            "IPX7 Waterproof",
            95
        ),

        (
            r"\bipx\s*6\b",
            "IPX6 Water Resistant",
            90
        ),

        (
            r"\bwaterproof\b",
            "Waterproof Design",
            85
        ),

        (
            r"\bwet\s*(?:&|and)\s*dry\b",
            "Wet & Dry Use",
            95
        ),

        (
            r"\bled\s+display\b",
            "LED Display",
            90
        ),

        (
            r"\bled\s+battery\s+display\b",
            "LED Battery Display",
            95
        ),

        (
            r"\brechargeable\b",
            "Rechargeable Design",
            85
        ),

        (
            r"\bcordless\b",
            "Cordless Design",
            85
        ),

        (
            r"\bwashable\b",
            "Washable Design",
            90
        ),

        (
            r"\bwireless\b",
            "Wireless Design",
            85
        ),

        (
            r"\bfast charging\b",
            "Fast Charging",
            90
        ),

        (
            r"\b6[- ]?in[- ]?1\b",
            "6-in-1 Design",
            90
        ),

        (
            r"\bmulti[- ]?layer filtration\b",
            "Multi-Layer Filtration",
            95
        ),

        (
            r"\bhepa\b",
            "HEPA Filtration",
            95
        ),

        (
            r"\btouch control\b",
            "Touch Control",
            85
        ),

    ]



    @staticmethod
    def generate(profile: Dict) -> List[str]:


        if not isinstance(profile, dict):
            return []


        basic = profile.get(
            "basic_info",
            {}
        ) or {}


        compatibility = profile.get(
            "compatibility",
            {}
        ) or {}


        facts = profile.get(
            "facts",
            {}
        ) or {}


        attributes = profile.get(
            "attributes",
            {}
        ) or {}



        source_text = (
            HighlightGenerator._collect_text(
                profile
            )
        )


        product_type = (
            HighlightGenerator._first(
                basic.get("product_type"),
                basic.get("product_name"),
                ""
            )
        )


        function = (
            HighlightGenerator._first(
                basic.get("main_function"),
                basic.get("core_function"),
                basic.get("function"),
                ""
            )
        )


        category = (
            HighlightGenerator._detect_category(
                product_type,
                function,
                source_text
            )
        )



        candidates = []


        # ==========================
        # 1. Product Identity
        # ==========================

        identity = (
            HighlightGenerator._extract_identity(
                product_type,
                function,
                source_text
            )
        )


        if identity:

            candidates.append({

                "text": identity,

                "type": "identity",

                "score": 1000

            })



        # ==========================
        # 2. Compatibility
        # ==========================

        compatibility_text = (
            HighlightGenerator._extract_compatibility(
                compatibility
            )
        )


        if compatibility_text:

            candidates.append({

                "text": compatibility_text,

                "type":"compatibility",

                "score":900

            })



        # ==========================
        # 3. Features
        # ==========================

        candidates.extend(

            HighlightGenerator._extract_features(
                source_text,
                attributes,
                facts
            )

        )
                # ==========================
        # 4. Function
        # ==========================

        function_highlight = (
            HighlightGenerator._extract_function(
                function,
                identity
            )
        )


        if function_highlight:

            candidates.append({

                "text": function_highlight,

                "type":"function",

                "score":700

            })



        # ==========================
        # 5. Specifications
        # ==========================

        candidates.extend(

            HighlightGenerator._extract_specifications(
                facts,
                attributes
            )

        )



        # ==========================
        # 6. Material
        # ==========================

        material = (
            HighlightGenerator._extract_material(
                facts,
                attributes
            )
        )


        if material:

            candidates.append({

                "text":material,

                "type":"material",

                "score":500

            })



        # ==========================
        # Final Ranking
        # ==========================

        return HighlightGenerator._rank_and_clean(
            candidates,
            category,
            identity
        )



    # =====================================================
    # Identity
    # =====================================================


    @staticmethod
    def _extract_identity(
        product_type,
        function,
        source
    ):

        text = (
            product_type
            +
            " "
            +
            function
        ).lower()



        rules = [

            (
                "electric shaver",
                "Electric Shaver"
            ),

            (
                "shaver",
                "Electric Shaver"
            ),

            (
                "vacuum filter",
                "Vacuum Cleaner Filter"
            ),

            (
                "washing machine start button",
                "Washing Machine Start Button"
            ),

            (
                "start button",
                "Start Button"
            ),

            (
                "printer nozzle",
                "Printer Nozzle"
            ),

            (
                "printhead",
                "Printer Printhead"
            ),

            (
                "filter",
                "Replacement Filter"
            ),

        ]


        for key,value in rules:

            if key in text:

                return value



        clean = HighlightGenerator._clean_phrase(
            product_type
        )


        if clean:

            return HighlightGenerator._title_case(
                clean
            )


        return ""



    # =====================================================
    # Compatibility
    # =====================================================


    @staticmethod
    def _extract_compatibility(
        compatibility
    ):

        if not isinstance(
            compatibility,
            dict
        ):
            return ""


        brands = compatibility.get(
            "brands",
            []
        ) or []


        models = compatibility.get(
            "models",
            []
        ) or []


        if isinstance(
            brands,
            str
        ):

            brands=[brands]


        if isinstance(
            models,
            str
        ):

            models=[models]



        if brands:

            return (
                f"Compatible with {brands[0]} Models"
            )


        if models:

            return (
                "Multiple Model Compatibility"
            )


        return ""



    # =====================================================
    # Features
    # =====================================================


    @staticmethod
    def _extract_features(
        source,
        attributes,
        facts
    ):

        result=[]


        text = (
            source
            +
            " "
            +
            str(attributes)
            +
            " "
            +
            str(facts)
        ).lower()



        for pattern,label,score in HighlightGenerator.FEATURE_RULES:


            if re.search(
                pattern,
                text,
                re.I
            ):


                result.append({

                    "text":label,

                    "type":"feature",

                    "score":score

                })


        return result



    # =====================================================
    # Function
    # =====================================================


    @staticmethod
    def _extract_function(
        function,
        identity
    ):

        if not function:
            return ""


        text = HighlightGenerator._clean_phrase(
            function
        )


        if not text:
            return ""



        if identity:

            identity_words=set(
                identity.lower().split()
            )


            words=set(
                text.lower().split()
            )


            if len(
                identity_words & words
            ) >= 2:

                return ""



        text=text.lower()



        if "replace" in text:

            return "Direct Replacement Design"



        if "shaving" in text:

            return "Wet & Dry Shaving"



        return HighlightGenerator._title_case(
            text
        )



    # =====================================================
    # Specifications
    # =====================================================


    @staticmethod
    def _extract_specifications(
        facts,
        attributes
    ):

        result=[]


        data={}

        data.update(
            facts
            if isinstance(facts,dict)
            else {}
        )

        data.update(
            attributes
            if isinstance(attributes,dict)
            else {}
        )



        quantity = (
            data.get("quantity")
            or data.get("pack")
        )


        if quantity:

            result.append({

                "text":
                f"{quantity} Pack",

                "type":
                "specification",

                "score":
                600

            })



        dimensions = data.get(
            "dimensions"
        )


        if dimensions:

            result.append({

                "text":
                str(dimensions),

                "type":
                "specification",

                "score":
                500

            })


        return result



    # =====================================================
    # Material
    # =====================================================


    @staticmethod
    def _extract_material(
        facts,
        attributes
    ):

        material = ""


        if isinstance(
            facts,
            dict
        ):

            material=facts.get(
                "material",
                ""
            )


        if not material and isinstance(
            attributes,
            dict
        ):

            material=attributes.get(
                "material",
                ""
            )



        if isinstance(
            material,
            dict
        ):

            material=material.get(
                "value",
                ""
            )


        if isinstance(
            material,
            list
        ):

            material=", ".join(
                [
                    str(x)
                    for x in material
                ]
            )


        if material:

            return (
                f"{material} Material"
            )


        return ""



    # =====================================================
    # Ranking
    # =====================================================


    @staticmethod
    def _rank_and_clean(
        candidates,
        category,
        identity
    ):

        bonus = (
            HighlightGenerator.CATEGORY_BONUS.get(
                category,
                {}
            )
        )


        result=[]


        for item in candidates:


            text=item.get(
                "text",
                ""
            ).strip()


            if not text:
                continue



            lower=text.lower()



            if any(
                word in lower
                for word in HighlightGenerator.BANNED_WORDS
            ):
                continue



            score=item.get(
                "score",
                0
            )


            score += bonus.get(
                item.get("type"),
                0
            )



            item["score"]=score



        candidates.sort(
            key=lambda x:x["score"],
            reverse=True
        )



        # identity 永远第一

        if identity:

            final=[identity]

        else:

            final=[]



        for item in candidates:


            text=item["text"]


            if text in final:
                continue



            # 防止身份重复

            if identity:

                if HighlightGenerator._similar(
                    text,
                    identity
                ):
                    continue



            final.append(
                text
            )


            if len(final)>=HighlightGenerator.MAX_HIGHLIGHTS:

                break



        return final



    # =====================================================
    # Helpers
    # =====================================================


    @staticmethod
    def _collect_text(profile):

        values=[]


        def walk(x):

            if isinstance(
                x,
                dict
            ):

                for v in x.values():
                    walk(v)


            elif isinstance(
                x,
                list
            ):

                for v in x:
                    walk(v)


            else:

                values.append(
                    str(x)
                )


        walk(profile)


        return " ".join(values)



    @staticmethod
    def _detect_category(
        product_type,
        function,
        source
    ):


        text=(
            product_type
            +
            " "
            +
            function
            +
            " "
            +
            source
        ).lower()



        if any(
            x in text
            for x in [
                "filter",
                "cartridge",
                "blade"
            ]
        ):
            return "consumable"



        if any(
            x in text
            for x in [
                "shaver",
                "charger",
                "coffee"
            ]
        ):
            return "electronics"



        if any(
            x in text
            for x in [
                "button",
                "switch",
                "part",
                "component"
            ]
        ):
            return "accessory"



        return "others"



    @staticmethod
    def _first(*args):

        for x in args:

            if x:

                return str(x).strip()


        return ""



    @staticmethod
    def _clean_phrase(text):

        text=str(text or "")

        text=re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip(
            " .,:;"
        )



    @staticmethod
    def _title_case(text):

        return " ".join(
            [
                word.capitalize()
                for word in text.split()
            ]
        )



    @staticmethod
    def _similar(
        a,
        b
    ):

        a=set(
            a.lower().split()
        )

        b=set(
            b.lower().split()
        )


        if not a or not b:
            return False


        return len(
            a & b
        ) / min(
            len(a),
            len(b)
        ) >= 0.7
