from __future__ import annotations

import re
from typing import Any, Dict, List


class HighlightGenerator:
    """
    Amazon AI Listing Optimizer
    Highlight Generator V2.4 Stable

    功能:
    1. 提取真实商品卖点
    2. 生成 Amazon 风格 Highlights
    3. 避免标题重复
    4. 避免营销违规词
    5. 保留事实保护
    """

    # Amazon 禁止营销词
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
        "professional",
        "perfect",
        "amazing",
        "top quality",
        "high quality",
        "hot sale",
        "promotion",
        "discount",
        "sale",
    ]


    # 功能关键词
    FEATURE_RULES = {

        "waterproof": [
            "waterproof",
            "water resistant",
            "ipx",
        ],

        "rechargeable": [
            "rechargeable",
            "charging",
            "battery",
            "usb",
        ],

        "wireless": [
            "wireless",
            "cordless",
        ],

        "display": [
            "led display",
            "lcd",
            "display",
        ],

        "portable": [
            "portable",
            "compact",
            "travel",
        ],

        "washable": [
            "washable",
            "washable filter",
        ],

        "compatible": [
            "compatible",
            "replacement",
            "for ",
        ],

        "multifunction": [
            "multi-function",
            "multifunction",
            "6 in 1",
            "5 in 1",
            "4 in 1",
        ],
    }


    # -------------------------
    # 主入口
    # -------------------------

    @classmethod
    def generate(
        cls,
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:

        title = cls._get_title(profile)

        raw_text = cls._collect_text(
            profile
        )


        features = cls._extract_features(
            raw_text
        )


        highlights = []


        for feature in features:

            text = cls._format_feature(
                feature,
                raw_text
            )

            if text:
                highlights.append(text)



        # 添加兼容信息
        compatibility = cls._generate_compatibility(
            profile
        )

        if compatibility:

            highlights.append(
                compatibility
            )



        # 去重
        highlights = cls._remove_duplicate(
            highlights
        )


        # 删除标题重复
        highlights = cls._remove_title_duplicate(
            highlights,
            title
        )


        # 数量控制
        highlights = highlights[:5]


        return {

            "highlights": highlights,

            "short_highlights": [
                x for x in highlights[:3]
            ],

            "keywords": cls._extract_keywords(
                highlights
            )

        }


    # -------------------------
    # 获取标题
    # -------------------------

    @staticmethod
    def _get_title(profile):

        title = (
            profile.get(
                "title",
                ""
            )
            or profile.get(
                "original_title",
                ""
            )
        )

        return str(title)



    # -------------------------
    # 收集文本
    # -------------------------

    @staticmethod
    def _collect_text(profile):

        texts = []


        basic = profile.get(
            "basic_info",
            {}
        )

        for value in basic.values():

            if value:
                texts.append(
                    str(value)
                )



        compatibility = profile.get(
            "compatibility",
            {}
        )

        for key in [
            "brands",
            "models"
        ]:

            value = compatibility.get(
                key,
                []
            )

            if isinstance(value,list):

                texts.extend(
                    [
                        str(x)
                        for x in value
                    ]
                )



        for key in [
            "features",
            "description",
            "bullets",
        ]:

            value = profile.get(
                key,
                ""
            )

            if isinstance(value,list):

                texts.extend(
                    [
                        str(x)
                        for x in value
                    ]
                )

            elif value:

                texts.append(
                    str(value)
                )



        return " ".join(texts)
            # -------------------------
    # 提取功能
    # -------------------------

    @classmethod
    def _extract_features(
        cls,
        text: str
    ) -> List[str]:

        result = []

        text_lower = text.lower()


        for name, keywords in cls.FEATURE_RULES.items():

            for keyword in keywords:

                if keyword in text_lower:

                    result.append(
                        name
                    )

                    break


        return result



    # -------------------------
    # 格式化卖点
    # -------------------------

    @classmethod
    def _format_feature(
        cls,
        feature: str,
        text: str
    ) -> str:


        text_lower = text.lower()


        mapping = {


            "waterproof":
                "Waterproof design for wet and dry use",


            "rechargeable":
                "Rechargeable design for convenient use",


            "wireless":
                "Cordless operation for flexible use",


            "display":
                "LED display for easy status checking",


            "portable":
                "Compact design suitable for travel use",


            "washable":
                "Washable design for easy maintenance",


            "compatible":
                "Compatible replacement design",


            "multifunction":
                "Multiple functions for different usage needs",

        }


        result = mapping.get(
            feature,
            ""
        )


        # 事实检查
        if feature == "waterproof":

            if (
                "ipx" not in text_lower
                and
                "waterproof" not in text_lower
                and
                "water resistant" not in text_lower
            ):
                return ""


        if feature == "rechargeable":

            if (
                "battery" not in text_lower
                and
                "charge" not in text_lower
                and
                "usb" not in text_lower
            ):
                return ""


        if feature == "display":

            if (
                "display" not in text_lower
                and
                "led" not in text_lower
                and
                "lcd" not in text_lower
            ):
                return ""


        return cls._clean_text(
            result
        )



    # -------------------------
    # 兼容信息生成
    # -------------------------

    @staticmethod
    def _generate_compatibility(
        profile
    ):

        compatibility = profile.get(
            "compatibility",
            {}
        )


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


        brand_text = ", ".join(
            brands[:3]
        )


        if models:

            model_text = " ".join(
                models[:4]
            )

            return (
                f"Compatible with {brand_text} "
                f"{model_text}"
            )


        return (
            f"Compatible with {brand_text}"
        )



    # -------------------------
    # 删除标题重复
    # -------------------------

    @staticmethod
    def _remove_title_duplicate(
        items,
        title
    ):

        if not title:

            return items


        title_words = set(
            re.findall(
                r"[a-zA-Z0-9]+",
                title.lower()
            )
        )


        result=[]


        for item in items:

            item_words=set(
                re.findall(
                    r"[a-zA-Z0-9]+",
                    item.lower()
                )
            )


            overlap = len(
                title_words.intersection(
                    item_words
                )
            )


            # 重复超过60%，删除
            if (
                len(item_words)>0
                and
                overlap / len(item_words)
                > 0.6
            ):
                continue


            result.append(
                item
            )


        return result



    # -------------------------
    # 文本清理
    # -------------------------

    @classmethod
    def _clean_text(
        cls,
        text
    ):

        if not text:

            return ""


        result = text


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



    # -------------------------
    # 去重复
    # -------------------------

    @staticmethod
    def _remove_duplicate(
        items
    ):

        result=[]

        seen=set()


        for item in items:

            key=item.lower().strip()


            if key not in seen:

                result.append(
                    item
                )

                seen.add(
                    key
                )


        return result



    # -------------------------
    # SEO关键词
    # -------------------------

    @staticmethod
    def _extract_keywords(
        highlights
    ):

        keywords=[]


        for item in highlights:

            words=re.findall(
                r"[a-zA-Z0-9]+",
                item.lower()
            )


            for word in words:

                if (
                    len(word)>=5
                    and
                    word not in keywords
                ):

                    keywords.append(
                        word
                    )


        return keywords[:10]
