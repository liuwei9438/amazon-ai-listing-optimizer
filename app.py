from __future__ import annotations

import json
import re
import traceback

import pandas as pd
import streamlit as st

from analyzer.product_understanding import (
    ProductUnderstandingEngine,
    UnderstandingError,
)
from analyzer.model_protection import ModelProtection
from analyzer.seo_intent_engine import generate_primary_search
from analyzer.seo_keyword_engine import SEOKeywordEngine
from compliance.brand_protection import protect_text
from core import export_unchanged, integrity_report, read_workbook
from core.product_knowledge import ProductKnowledgeBuilder
from generator.bullet_generator import BulletGenerator
from generator.description_generator import DescriptionGenerator
from generator.highlight_generator import HighlightGenerator
from generator.short_title_generator import ShortTitleGenerator
from generator.title_generator import TitleGenerator
from services.config import get_openai_api_key
from services.listing_exporter import ListingExporter
from services.task_manager import (
    create_task,
    save_status,
    load_status,
)
from services.batch_processor import process_batch
from services.task_worker import start_worker

VERSION = "V2.4.0-Highlight-Pipeline"
BATCH_SIZE = 10
DEBUG_MODE = False
current_task = st.session_state.get(
    "current_task",
    ""
)

def display_highlights(highlight_result) -> None:
    """
    Display Amazon product highlights.
    Supports new list format and old dict format.
    """

    if not highlight_result:
        return


    # 新版 HighlightGenerator 返回 list
    if isinstance(highlight_result, list):

        for item in highlight_result:

            if isinstance(item, str):

                text = item.strip()

                if text:
                    st.write("• " + text)


            elif isinstance(item, dict):

                title = item.get(
                    "title",
                    ""
                )

                content = item.get(
                    "content",
                    ""
                )

                if content:

                    if title:
                        st.write(
                            f"• {title}: {content}"
                        )
                    else:
                        st.write(
                            "• " + content
                        )


    # 兼容旧版本 dict
    elif isinstance(highlight_result, dict):

        highlights = highlight_result.get(
            "highlights",
            []
        )

        for item in highlights:

            if isinstance(item, dict):

                text = (
                    item.get("text")
                    or item.get("content")
                    or ""
                )

            else:

                text = str(item)


            text = str(text).strip()

            if text:
                st.write(
                    "• " + text
                )


def display_generated_content(profile: dict) -> None:
    title_result = profile.get("generated_title", {})
    if title_result.get("title"):
        st.write("### AI生成标题")
        st.write(title_result["title"])
    if "short_title_result" in profile:

        st.write("### AI短标题")

        short_title = profile["short_title_result"].get(
             "short_title",
             ""
        )

    if short_title:

        st.write(
            short_title
        )    

    highlight_result = profile.get("highlight_result", {})
    if highlight_result:
        st.write("### AI商品亮点")
        display_highlights(highlight_result)
    seo_result = profile.get("seo", {})

    if seo_result:

        st.write("### SEO Keywords")

        st.write(
            "**Primary Keywords**"
        )

        for k in seo_result.get(
            "primary_keywords",
            []
        ):
            st.write(
                "• " + k
            )


        st.write(
            "**Secondary Keywords**"
        )

        for k in seo_result.get(
            "secondary_keywords",
            []
        ):
            st.write(
                "• " + k
            )


        st.write(
            "**Model Keywords**"
        )

        for k in seo_result.get(
            "model_keywords",
            []
        ):
            st.write(
                "• " + k
            )


        st.write(
            "**Backend Search Terms**"
        )

        for k in seo_result.get(
            "backend_search_terms",
            []
        ):
            st.write(
                "• " + k
            )

    bullet_result = profile.get("bullet_result", {})
    bullets = bullet_result.get("bullets", [])
    if bullets:
        st.write("### AI生成五点描述")
        for bullet in bullets:
            text = str(bullet).strip()
            if text:
                st.write("• " + text)

    description_result = profile.get("description_result", {})
    description = str(description_result.get("description", "")).strip()
    if description:
        st.write("### AI生成详情描述")
        st.write(description)


st.set_page_config(
    page_title="Amazon AI Listing Optimizer",
    layout="wide",
)

st.title("Amazon AI Listing Optimizer")
st.caption(VERSION)
st.info(
    "本版本基于 AI 商品理解生成商品亮点、标题、五点和详情。"
    "所有内容遵循事实保护规则，不主动添加未确认的材质、参数或功能。"
    "同时保留原文件完整性测试导出。"
)

uploaded = st.file_uploader("上传 Excel", type=["xlsx"])

if uploaded is not None:
    upload_key = f"{uploaded.name}:{len(uploaded.getvalue())}"

    if st.session_state.get("upload_key") != upload_key:
        st.session_state["upload_key"] = upload_key
        st.session_state["profiles"] = []

    try:
        envelope = read_workbook(
            uploaded.name,
            uploaded.getvalue(),
        )
    except Exception as exc:
        import traceback
        st.error(
            f"读取失败: {exc}"
        )
        st.code(
            traceback.format_exc()
        )
        st.stop()

    fields = envelope.fields
    diagnostics = envelope.diagnostics

    st.success(
        f"读取成功：工作表 {envelope.sheet_name}，"
        f"{diagnostics['row_count']} 行，"
        f"{diagnostics['column_count']} 列。"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("原始列数", diagnostics["column_count"])
    c2.metric("产品记录", diagnostics["record_count"])
    c3.metric("识别字段", diagnostics["matched_field_count"])
    c4.metric("嵌入图片", diagnostics["embedded_image_count"])
    c5.metric("含图片链接记录", diagnostics["records_with_image_urls"])
    if DEBUG_MODE:
        st.subheader("字段识别报告")
    
        report_rows = []
        for label, value in fields.as_dict().items():
            if isinstance(value, tuple):
                display_value = "、".join(value)
            else:
                display_value = value or ""
    
            report_rows.append(
                {
                    "标准字段": label,
                    "识别结果": display_value or "未识别",
                    "状态": "✓ 已识别" if display_value else "× 未识别",
                }
            )
    
        st.dataframe(
            pd.DataFrame(report_rows),
            hide_index=True,
            use_container_width=True,
        )

    with st.expander(
        f"未匹配的原始列（{len(diagnostics['unmatched_columns'])}）"
    ):
        if diagnostics["unmatched_columns"]:
            st.write("、".join(diagnostics["unmatched_columns"]))
        else:
            st.success("所有列均已匹配到标准字段。")
    if DEBUG_MODE:
        st.subheader("图片识别诊断")
    
        if fields.images:
            st.success(
                f"图片链接列：{fields.images}；"
                f"识别方式：{diagnostics['image_detection_method']}；"
                f"含有效图片链接的记录："
                f"{diagnostics['records_with_image_urls']}。"
            )
        elif diagnostics["embedded_image_count"]:
            st.success(
                f"未发现图片链接列，但包含 "
                f"{diagnostics['embedded_image_count']} 个 Excel 嵌入图片对象。"
                "原样导出会保留这些对象。"
            )
        else:
            st.warning(
                "文件中未检测到图片链接列或 Excel 嵌入图片对象。"
                "这通常表示当前上传文件本身没有保存图片信息。"
            )
    
    if DEBUG_MODE:

        st.subheader("ProductRecord 预览")
    
        ...

    record_preview = []
    for record in envelope.records[:10]:
        record_preview.append(
            {
                "Excel行": record.row_number,
                "SKU": record.sku,
                "父SKU": record.parent_sku,
                "标题": record.title,
                "五点数量": len(record.bullets),
                "图片数量": len(record.image_urls),
                "语言": record.language,
            }
        )

    st.dataframe(
        pd.DataFrame(record_preview),
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("AI Product Understanding")
    st.caption(
        "建议先分析 1–5 个代表产品，确认商品理解、事实保护、"
        "标题、商品亮点、五点和详情结果。"
    )

    saved_api_key = get_openai_api_key()

    if saved_api_key:
        st.success(
            "✅ 已从 Streamlit Secrets 或系统环境变量读取 OpenAI API Key。"
        )
    else:
        st.warning(
            "⚠ 未检测到已保存的 OpenAI API Key，可在下方临时输入。"
        )

    manual_api_key = st.text_input(
        "OpenAI API Key（可留空，默认读取 Secrets）",
        type="password",
        help=(
            "优先读取 Streamlit Secrets 或系统环境变量；"
            "手动输入仅用于当前会话。"
        ),
    )

    api_key = manual_api_key.strip() or saved_api_key
    model = st.text_input("模型", value="gpt-4.1-mini")
    st.subheader("优化内容选择")
    
    enable_title = st.checkbox(
        "优化标题",
        value=True
    )
    
    enable_short_title = st.checkbox(
        "优化短标题",
        value=True
    )
    
    enable_highlight = st.checkbox(
        "优化商品亮点",
        value=True
    )
    
    enable_bullet = st.checkbox(
        "优化五点描述",
        value=True
    )
    
    enable_description = st.checkbox(
        "优化详情描述",
        value=True
    )
    
    enable_seo = st.checkbox(
        "优化SEO关键词",
        value=True
    )
    record_count = len(envelope.records)

    st.info(
        f"当前文件共有 {record_count} 个产品，"
        f"将全部进行 AI 优化。"
    )

    if st.button("开始 AI 商品理解", type="primary"):
        if not api_key.strip():
            st.error("请先填写 OpenAI API Key。")
        else:
        
            task_id = create_task(
                total_products=len(envelope.records),
                filename=uploaded.name,
            )
        
        
            st.session_state["current_task"] = task_id
        
        
            st.success(
                f"任务创建成功：{task_id}"
            )
        options = {

            "title": enable_title,
        
            "short_title": enable_short_title,
        
            "highlight": enable_highlight,
        
            "bullet": enable_bullet,
        
            "description": enable_description,
        
            "seo": enable_seo,
        
        }
        
        start_worker(

            envelope.records,
        
            task_id,
        
            api_key,
        
            model,
        
            options,
        
        )
        
        
        st.success(
            f"任务已启动:{task_id}"
        )
        
        
        st.session_state["profiles"] = profiles
    
        if profiles:
            st.download_button(
                "下载 Product Profile JSON",
                data=json.dumps(
                    profiles,
                    ensure_ascii=False,
                    indent=2,
                ).encode("utf-8"),
                file_name="product_profiles_v2.4.0.json",
                mime="application/json",
            )
    
            st.subheader("AI优化结果导出")
    
            try:
                optimized_export = ListingExporter.export(
                    envelope.dataframe,
                    profiles,
                )
    
                if hasattr(optimized_export, "getvalue"):
                    optimized_data = optimized_export.getvalue()
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
                    file_name=f"{safe_stem}_{VERSION}_AI优化结果.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    type="primary",
                )
            except Exception as exc:
                st.error(f"生成 AI 优化结果文件失败：{exc}")
    
        st.subheader("原文件完整性导出")
    
        unchanged_export = export_unchanged(envelope)
        integrity = integrity_report(
            envelope,
            unchanged_export,
        )
    
        if integrity["byte_identical"]:
            st.success(
                "验证通过：原样导出文件与上传文件完全一致，"
                f"大小 {integrity['export_size']:,} 字节。"
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
                file_name=f"{safe_stem}_{VERSION}_原样导出.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
        else:
            st.error("原文件完整性验证失败，已停止原样导出。")
