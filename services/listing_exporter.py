from __future__ import annotations

import json
from io import BytesIO

import pandas as pd


class ListingExporter:
    """
    Amazon AI Listing Optimizer

    Listing Exporter V2.4 Stable

    功能:
    - AI结果合并
    - 保留原Excel结构
    - 支持Highlight新版结构
    - 稳定导出xlsx
    """

    # =========================
    # 安全转换
    # =========================

    @staticmethod
    def safe_value(value):

        if value is None:
            return ""


        if isinstance(value, list):

            return "\n".join(
                [
                    str(x)
                    for x in value
                    if x
                ]
            )


        if isinstance(value, dict):

            return json.dumps(
                value,
                ensure_ascii=False
            )


        return str(value)



    # =========================
    # 获取字段
    # =========================

    @staticmethod
    def get_generated(profile):


        title = (
            profile
            .get("generated_title", {})
            .get(
                "title",
                ""
            )
        )


        short_title = (
            profile
            .get(
                "short_title_result",
                {}
            )
            .get(
                "short_title",
                ""
            )
        )


        highlight = profile.get(
            "highlight_result",
            {}
        )


        # 新版
        if isinstance(
            highlight,
            dict
        ):

            highlights = highlight.get(
                "highlights",
                []
            )

            short_highlights = highlight.get(
                "short_highlights",
                []
            )


        # 兼容旧版
        elif isinstance(
            highlight,
            list
        ):

            highlights = highlight
            short_highlights = highlight[:3]


        else:

            highlights=[]
            short_highlights=[]



        bullets = (
            profile
            .get(
                "bullet_result",
                {}
            )
            .get(
                "bullets",
                []
            )
        )


        description = (
            profile
            .get(
                "description_result",
                {}
            )
            .get(
                "description",
                ""
            )
        )


        return {

            "AI Title": title,

            "AI Short Title": short_title,

            "AI Highlights":
                highlights,

            "AI Short Highlights":
                short_highlights,

            "AI Bullet Points":
                bullets,

            "AI Description":
                description,

        }



    # =========================
    # 查找SKU
    # =========================

    @staticmethod
    def find_sku(profile):

        return (

            profile.get(
                "sku"
            )

            or

            profile.get(
                "product",
                {}
            )
            .get(
                "sku",
                ""
            )

        )



    # =========================
    # 主导出
    # =========================

    @classmethod
    def export(
        cls,
        dataframe,
        profiles
    ):


        df = dataframe.copy()



        export_rows=[]


        for index, profile in enumerate(
            profiles
        ):

            if not profile:
                continue


            generated = cls.get_generated(
                profile
            )


            export_rows.append(
                generated
            )



        if not export_rows:

            raise ValueError(
                "没有可导出的AI优化结果"
            )



        ai_df = pd.DataFrame(
            [
                {
                    k: cls.safe_value(v)
                    for k,v in row.items()
                }

                for row in export_rows
            ]
        )



        # 保留原数据

        result = pd.concat(
            [
                df.reset_index(drop=True),

                ai_df.reset_index(drop=True)

            ],

            axis=1
        )



        output = BytesIO()


        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            result.to_excel(
                writer,
                index=False,
                sheet_name="AI Optimized"
            )



        output.seek(0)


        return output
