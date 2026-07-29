from __future__ import annotations

import pandas as pd
from io import BytesIO


class ListingExporter:


    @staticmethod
    def export(
        original_df,
        profiles
    ):

        rows = []


        for index, profile in enumerate(profiles):

            row = {}


            # =====================
            # 原始字段
            # =====================

            basic = profile.get(
                "basic_info",
                {}
            )


            row["SKU"] = profile.get(
                "sku",
                ""
            )


            row["原标题"] = profile.get(
                "original_title",
                ""
            )


            # =====================
            # AI标题
            # =====================

            title_result = profile.get(
                "generated_title",
                {}
            )


            row["AI标题"] = title_result.get(
                "title",
                ""
            )


            # =====================
            # 商品亮点
            # =====================

            highlight_result = profile.get(
                "highlight_result",
                {}
            )


            highlights = highlight_result.get(
                "highlights",
                {}
            )


            highlight_text = []


            for key,value in highlights.items():

                if isinstance(value,list):

                    highlight_text.extend(
                        value
                    )

                elif value:

                    highlight_text.append(
                        value
                    )


            row["商品亮点"] = "\n".join(
                highlight_text
            )


            # =====================
            # 五点描述
            # =====================

            bullet_result = profile.get(
                "bullet_result",
                {}
            )


            bullets = bullet_result.get(
                "bullets",
                []
            )


            for i in range(5):

                if i < len(bullets):

                    row[
                        f"AI五点{i+1}"
                    ] = bullets[i]

                else:

                    row[
                        f"AI五点{i+1}"
                    ] = ""


            # =====================
            # 详情描述
            # =====================

            description_result = profile.get(
                "description_result",
                {}
            )


            row["AI详情描述"] = description_result.get(
                "description",
                ""
            )


            rows.append(
                row
            )



        result_df = pd.DataFrame(
            rows
        )


        output = BytesIO()


        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            result_df.to_excel(
                writer,
                index=False,
                sheet_name="AI优化结果"
            )


        output.seek(0)


        return output
