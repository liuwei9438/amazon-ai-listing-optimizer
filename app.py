from __future__ import annotations

import json
import re
import pandas as pd
import streamlit as st

from streamlit_autorefresh import st_autorefresh


from core import (
    read_workbook,
    export_unchanged,
    integrity_report,
)

from services.config import get_openai_api_key

from services.task_manager import (
    create_task,
    load_status,
)

from services.result_storage import (
    load_profiles,
)

from services.current_task import (
    save_current_task,
    load_current_task,
)

from services.listing_exporter import (
    ListingExporter,
)


VERSION = "V2.4.3-Worker"


DEBUG_MODE = False



# =====================================================
# 页面配置
# =====================================================

st.set_page_config(
    page_title="Amazon AI Listing Optimizer",
    layout="wide",
)



# =====================================================
# 任务恢复
# =====================================================

current_task = load_current_task()


# =====================================================
# Highlight展示
# =====================================================

def display_highlights(
    highlight_result
):

    if not highlight_result:

        return


    if isinstance(
        highlight_result,
        list
    ):

        for item in highlight_result:

            if isinstance(
                item,
                str
            ):

                st.write(
                    "• " + item
                )

            elif isinstance(
                item,
                dict
            ):

                text = (
                    item.get("content")
                    or
                    item.get("text")
                    or
                    ""
                )

                if text:

                    st.write(
                        "• " + text
                    )



# =====================================================
# 内容展示
# =====================================================

def display_generated_content(
    profile
):

    title = profile.get(
        "generated_title",
        {}
    )


    if title.get(
        "title"
    ):

        st.write(
            "### AI标题"
        )

        st.write(
            title["title"]
        )



    bullet = profile.get(
        "bullet_result",
        {}
    )


    bullets = bullet.get(
        "bullets",
        []
    )


    if bullets:

        st.write(
            "### AI五点"
        )

        for item in bullets:

            st.write(
                "• "
                +
                str(item)
            )



    description = profile.get(
        "description_result",
        {}
    )


    if description.get(
        "description"
    ):

        st.write(
            "### AI详情"
        )

        st.write(
            description["description"]
        )
# =====================================================
# 页面主体
# =====================================================


st.title(
    "Amazon AI Listing Optimizer"
)


st.caption(
    VERSION
)


st.info(
    "基于 AI 商品理解生成标题、五点、详情和商品亮点。"
    "采用 Worker 后台任务模式，避免长任务导致页面阻塞。"
)



# =====================================================
# 上传文件
# =====================================================


uploaded = st.file_uploader(
    "上传 Excel",
    type=[
        "xlsx"
    ]
)



if uploaded is not None:


    try:

        envelope = read_workbook(
            uploaded.name,
            uploaded.getvalue(),
        )


    except Exception as exc:

        st.error(
            f"读取文件失败：{exc}"
        )

        st.stop()



    st.success(
        f"读取成功："
        f"{len(envelope.records)} 个产品"
    )



    # =================================================
    # API KEY
    # =================================================


    saved_api_key = get_openai_api_key()


    manual_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
    )


    api_key = (
        manual_api_key.strip()
        or
        saved_api_key
    )


    model = st.text_input(
        "模型",
        value="gpt-4.1-mini"
    )



    # =================================================
    # 优化模块选择
    # =================================================


    st.subheader(
        "优化内容选择"
    )


    enable_title = st.checkbox(
        "优化标题",
        True
    )


    enable_short_title = st.checkbox(
        "优化短标题",
        True
    )


    enable_highlight = st.checkbox(
        "优化商品亮点",
        True
    )


    enable_bullet = st.checkbox(
        "优化五点描述",
        True
    )


    enable_description = st.checkbox(
        "优化详情描述",
        True
    )


    enable_seo = st.checkbox(
        "优化SEO关键词",
        True
    )



    # =================================================
    # 开始任务
    # =================================================


    if st.button(
        "开始 AI 商品理解",
        type="primary"
    ):


        if not api_key:


            st.error(
                "请输入 OpenAI API Key"
            )


            st.stop()



        task_id = create_task(

            total_products=len(
                envelope.records
            ),

            filename=uploaded.name,

        )



        save_current_task(
            task_id
        )



        options = {


            "title":
                enable_title,


            "short_title":
                enable_short_title,


            "highlight":
                enable_highlight,


            "bullet":
                enable_bullet,


            "description":
                enable_description,


            "seo":
                enable_seo,

        }



        start_worker(

            envelope.records,

            task_id,

            api_key,

            model,

            options,

        )



        st.success(
            f"任务已启动：{task_id}"
        )



        st.info(
            "AI 正在后台运行，可以刷新页面查看状态。"
        )



# =====================================================
# 当前任务状态
# =====================================================


current_task = load_current_task()


profiles = []


if current_task:

    st_autorefresh(
        interval=3000,
        key="task_refresh"
    )


    status = load_status(
        current_task
    )


    profiles = load_profiles(
        current_task
    )

    if status:

        st.subheader(
            "任务状态"
        )


        st.info(
            f"""
状态：
{status.get("status")}

进度：
{status.get("completed")}
/
{status.get("total") or status.get("total_products")}
"""
        )
# =====================================================
# 读取任务结果
# =====================================================


if current_task:

    status = load_status(
        current_task
    )



# =====================================================
# 显示优化结果
# =====================================================


if profiles:


    st.success(
        f"已完成 {len(profiles)} 个产品优化"
    )


    st.subheader(
        "AI优化结果预览"
    )


    # 默认展示前3个，避免页面卡顿

    for index, profile in enumerate(
        profiles[:3]
    ):

        with st.expander(
            f"产品 {index + 1}"
        ):

            display_generated_content(
                profile
            )



    # =================================================
    # 导出 JSON
    # =================================================


    st.download_button(

        "下载 Product Profile JSON",

        data=json.dumps(

            profiles,

            ensure_ascii=False,

            indent=2,

        ).encode(
            "utf-8"
        ),

        file_name=
        "product_profiles_v2.4.3.json",

        mime=
        "application/json",

    )



    # =================================================
    # 导出 Excel
    # =================================================


    st.subheader(
        "AI优化结果导出"
    )


    try:


        optimized_export = ListingExporter.export(

            envelope.dataframe,

            profiles,

        )


        if hasattr(
            optimized_export,
            "getvalue"
        ):

            optimized_data = (
                optimized_export.getvalue()
            )

        else:

            optimized_data = optimized_export



        safe_stem = re.sub(

            r"\.xlsx$",

            "",

            uploaded.name,

            flags=re.I,

        )


        st.download_button(

            "导出 AI 优化结果",

            data=optimized_data,

            file_name=
            f"{safe_stem}_{VERSION}_AI优化结果.xlsx",

            mime=
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

            type="primary",

        )


    except Exception as exc:


        st.error(
            f"生成优化文件失败：{exc}"
        )
# =====================================================
# 原文件完整性测试
# =====================================================


if uploaded is not None:


    st.subheader(
        "原文件完整性导出"
    )


    try:


        unchanged_export = export_unchanged(
            envelope
        )


        integrity = integrity_report(
            envelope,
            unchanged_export,
        )


        if integrity["byte_identical"]:


            st.success(
                "验证通过：原文件完整性保持一致"
            )


            safe_stem = re.sub(

                r"\.xlsx$",

                "",

                uploaded.name,

                flags=re.I,

            )


            st.download_button(

                "导出原文件完整性测试文件",

                data=unchanged_export,

                file_name=
                f"{safe_stem}_{VERSION}_原样导出.xlsx",

                mime=
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

            )


        else:


            st.error(
                "原文件完整性验证失败"
            )


    except Exception as exc:


        st.error(
            f"完整性测试失败：{exc}"
        )
