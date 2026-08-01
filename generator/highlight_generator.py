from __future__ import annotations

import re
from typing import Any, Dict, List


class HighlightGenerator:
    """
    Amazon AI Listing Optimizer

    Highlight Generator V2.4.1 Stable

    优化：
    - Amazon 转化型卖点
    - 产品用途优先
    - 兼容信息降权
    - Short Highlight独立生成
    - 事实保护
    """


    BANNED_WORDS = [

        "best",
        "best seller",
        "bestseller",
        "#1",
        "number one",

        "premium",
        "original",
        "genuine",
        "official",

        "perfect",
        "amazing",
        "professional",

        "top quality",
        "high quality",

        "sale",
        "discount",
        "promotion"

    ]


    PRODUCT_TYPE_RULES = {


        "replacement_part": [

            "button",
            "switch",
            "cover",
            "replacement",
            "part",
            "handle",
            "housing"

        ],


        "filter": [

            "filter",
            "hepa",
            "filtration"

        ],


        "electronic": [

            "battery",
            "charging",
            "display",
            "wireless",
            "electric"

        ],


        "grooming": [

            "shaver",
            "trimmer",
            "razor"

        ]

    }



    FEATURE_RULES = {


        "waterproof": [

            "waterproof",
            "water resistant",
            "ipx"

        ],


        "rechargeable": [

            "rechargeable",
            "battery",
            "usb charging"

        ],


        "wireless": [

            "wireless",
            "cordless"

        ],


        "display": [

            "led display",
            "lcd display",
            "display"

        ],


        "multifunction": [

            "multi-function",
            "multifunction",
            "6 in 1",
            "5 in 1",
            "4 in 1"

        ],


        "portable": [

            "portable",
            "compact",
            "travel"

        ]

    }



    # ==========================
    # 主入口
    # ==========================

    @classmethod
    def generate(
        cls,
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:


        text = cls.collect_text(
            profile
        )


        product_type = cls.detect_product_type(
            text
        )


        features = cls.extract_features(
            text
        )


        highlights = []


        # 1. 产品用途卖点
        usage = cls.generate_usage(
            product_type,
            profile
        )


        if usage:

            highlights.append(
                usage
            )


        # 2. 功能卖点

        for feature in features:

            item = cls.feature_text(
                feature
            )


            if item:

                highlights.append(
                    item
                )


        # 3. 兼容信息最后加入

        compatibility = cls.generate_compatibility(
            profile
        )


        if compatibility:

            highlights.append(
                compatibility
            )


        highlights = cls.clean_list(
            highlights
        )


        highlights = cls.limit_highlights(
            highlights
        )


        short_highlights = cls.generate_short(
            features,
            product_type
        )


        return {


            "highlights": highlights,


            "short_highlights": short_highlights,


            "keywords": cls.extract_keywords(
                highlights
            )

        }
            # ==========================
    # 产品类型判断
    # ==========================

    @classmethod
    def detect_product_type(
        cls,
        text: str
    ) -> str:


        text_lower = text.lower()


        for product_type, words in cls.PRODUCT_TYPE_RULES.items():

            for word in words:

                if word in text_lower:

                    return product_type


        return "general"



    # ==========================
    # 收集产品文本
    # ==========================

    @staticmethod
    def collect_text(
        profile
    ) -> str:


        texts = []


        # 基础信息

        basic_info = profile.get(
            "basic_info",
            {}
        )


        if isinstance(
            basic_info,
            dict
        ):

            for value in basic_info.values():

                if value:

                    texts.append(
                        str(value)
                    )



        # 标题

        for key in [
            "title",
            "original_title"
        ]:

            value = profile.get(
                key,
                ""
            )

            if value:

                texts.append(
                    str(value)
                )



        # Features

        features = profile.get(
            "features",
            []
        )


        if isinstance(
            features,
            list
        ):

            texts.extend(
                [
                    str(x)
                    for x in features
                ]
            )

        elif features:

            texts.append(
                str(features)
            )



        # Bullet

        bullets = profile.get(
            "bullets",
            []
        )


        if isinstance(
            bullets,
            list
        ):

            texts.extend(
                [
                    str(x)
                    for x in bullets
                ]
            )



        # Compatibility

        compatibility = profile.get(
            "compatibility",
            {}
        )


        if isinstance(
            compatibility,
            dict
        ):

            for key in [
                "brands",
                "models"
            ]:

                values = compatibility.get(
                    key,
                    []
                )


                if isinstance(
                    values,
                    list
                ):

                    texts.extend(
                        [
                            str(x)
                            for x in values
                        ]
                    )



        return " ".join(
            texts
        )



    # ==========================
    # 功能提取
    # ==========================

    @classmethod
    def extract_features(
        cls,
        text
    ) -> List[str]:


        result=[]


        text_lower = text.lower()


        for name, keywords in cls.FEATURE_RULES.items():


            for keyword in keywords:


                if keyword in text_lower:

                    result.append(
                        name
                    )

                    break



        return result



    # ==========================
    # 产品用途生成
    # ==========================

    @classmethod
    def generate_usage(
        cls,
        product_type,
        profile
    ):


        if product_type == "replacement_part":


            return (
                "Replacement part designed "
                "to restore normal device operation"
            )


        if product_type == "filter":


            return (
                "Replacement filter designed "
                "for regular maintenance"
            )


        if product_type == "grooming":


            return (
                "Designed for convenient "
                "daily grooming needs"
            )


        if product_type == "electronic":


            return (
                "Designed for convenient "
                "daily use"
            )


        return ""



    # ==========================
    # 功能描述
    # ==========================

    @staticmethod
    def feature_text(
        feature
    ):


        mapping = {


            "waterproof":
                "Waterproof design supports wet and dry use",


            "rechargeable":
                "Rechargeable design for convenient operation",


            "wireless":
                "Cordless operation for flexible use",


            "display":
                "LED display for easy status checking",


            "multifunction":
                "Multiple functions for different usage needs",


            "portable":
                "Compact design suitable for travel use"

        }


        return mapping.get(
            feature,
            ""
        )



    # ==========================
    # 兼容信息
    # ==========================

    @staticmethod
    def generate_compatibility(
        profile
    ):


        compatibility = profile.get(
            "compatibility",
            {}
        )


        if not isinstance(
            compatibility,
            dict
        ):

            return ""



        brands = compatibility.get(
            "brands",
            []
        )


        models = compatibility.get(
            "models",
            []
        )


        if not brands:

            return ""



        brand = brands[0]



        if len(models) > 3:


            model_text = (
                " ".join(
                    models[:2]
                )
                +
                " and more models"
            )


        else:


            model_text = " ".join(
                models
            )



        if model_text:


            return (
                f"Compatible with {brand} "
                f"{model_text}"
            )


        return (
            f"Compatible with {brand}"
        )
            # ==========================
    # Highlight数量控制
    # ==========================

    @staticmethod
    def limit_highlights(
        highlights
    ):


        result=[]


        for item in highlights:


            if not item:
                continue


            if item not in result:

                result.append(
                    item
                )


            if len(result) >= 5:

                break



        return result



    # ==========================
    # Short Highlights生成
    # ==========================

    @classmethod
    def generate_short(
        cls,
        features,
        product_type
    ):


        result=[]


        mapping={


            "waterproof":
                "Waterproof Design",


            "rechargeable":
                "Rechargeable",


            "wireless":
                "Cordless Operation",


            "display":
                "LED Display",


            "multifunction":
                "Multi Function",


            "portable":
                "Portable Design"

        }



        for feature in features:


            value = mapping.get(
                feature,
                ""
            )


            if value:

                result.append(
                    value
                )



        # 如果没有功能关键词
        # 根据产品类型补充

        if not result:


            if product_type == "replacement_part":

                result.append(
                    "Replacement Part"
                )


            elif product_type == "filter":

                result.append(
                    "Replacement Filter"
                )


            elif product_type == "grooming":

                result.append(
                    "Daily Grooming"
                )


        return result[:5]



    # ==========================
    # 文本清理
    # ==========================

    @classmethod
    def clean_list(
        cls,
        items
    ):


        result=[]


        for item in items:


            item = cls.clean_text(
                item
            )


            if not item:

                continue


            if item.lower() not in [
                x.lower()
                for x in result
            ]:

                result.append(
                    item
                )



        return result



    @classmethod
    def clean_text(
        cls,
        text
    ):


        if not text:

            return ""



        result = str(text)



        for word in cls.BANNED_WORDS:


            result = re.sub(
                word,
                "",
                result,
                flags=re.I
            )



        result = re.sub(
            r"\s+",
            " ",
            result
        )



        return result.strip()



    # ==========================
    # SEO关键词
    # ==========================

    @staticmethod
    def extract_keywords(
        highlights
    ):


        keywords=[]


        for item in highlights:


            words = re.findall(
                r"[a-zA-Z0-9]+",
                item.lower()
            )


            for word in words:


                if (
                    len(word) >= 5
                    and
                    word not in keywords
                ):

                    keywords.append(
                        word
                    )



        return keywords[:10]
