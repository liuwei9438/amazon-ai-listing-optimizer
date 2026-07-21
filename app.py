from __future__ import annotations

import re

import pandas as pd
import streamlit as st

from core import export_unchanged, integrity_report, read_workbook

VERSION = "V2.2.2-Field-Detector-Stable"

st.set_page_config(page_title="Amazon AI Listing Optimizer", layout="wide")
st.title("Amazon AI Listing Optimizer")
st.caption(VERSION)
st.info(
    "本版本建立稳定字段识别器和 ProductRecord 数据对象，不运行 AI、不优化图片。"
    "导出仍与上传文件字节级一致。"
)

uploaded = st.file_uploader("上传 Excel", type=["xlsx"])

if uploaded is not None:
    try:
        envelope = read_workbook(uploaded.name, uploaded.getvalue())
    except Exception as exc:
        st.error(f"读取失败：{exc}")
        st.stop()

    fields = envelope.fields
    diagnostics = envelope.diagnostics
    st.success(
        f"读取成功：工作表 {envelope.sheet_name}，"
        f"{diagnostics['row_count']} 行，{diagnostics['column_count']} 列。"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("原始列数", diagnostics["column_count"])
    c2.metric("产品记录", diagnostics["record_count"])
    c3.metric("识别字段", diagnostics["matched_field_count"])
    c4.metric("嵌入图片", diagnostics["embedded_image_count"])
    c5.metric("含图片链接记录", diagnostics["records_with_image_urls"])

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
    st.dataframe(pd.DataFrame(report_rows), hide_index=True, use_container_width=True)

    with st.expander(f"未匹配的原始列（{len(diagnostics['unmatched_columns'])}）"):
        if diagnostics["unmatched_columns"]:
            st.write("、".join(diagnostics["unmatched_columns"]))
        else:
            st.success("所有列均已匹配到标准字段。")

    st.subheader("图片识别诊断")
    if fields.images:
        st.success(
            f"图片链接列：{fields.images}；识别方式：{diagnostics['image_detection_method']}；"
            f"含有效图片链接的记录：{diagnostics['records_with_image_urls']}。"
        )
    elif diagnostics["embedded_image_count"]:
        st.success(
            f"未发现图片链接列，但包含 {diagnostics['embedded_image_count']} 个 Excel 嵌入图片对象。"
            "原样导出会保留这些对象。"
        )
    else:
        st.warning(
            "文件中未检测到图片链接列或 Excel 嵌入图片对象。"
            "这通常表示当前上传文件本身没有保存图片信息。"
        )

    st.subheader("ProductRecord 预览")
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
    st.dataframe(pd.DataFrame(record_preview), hide_index=True, use_container_width=True)

    st.subheader("原始数据预览")
    st.dataframe(envelope.dataframe.head(10), use_container_width=True)

    exported = export_unchanged(envelope)
    integrity = integrity_report(envelope, exported)
    st.subheader("导出完整性")
    if integrity["byte_identical"]:
        st.success(f"验证通过：导出文件与原文件完全一致，大小 {integrity['export_size']:,} 字节。")
    else:
        st.error("完整性验证失败，已停止导出。")
        st.stop()

    safe_stem = re.sub(r"\.xlsx$", "", uploaded.name, flags=re.I)
    st.download_button(
        "导出完整性测试文件",
        data=exported,
        file_name=f"{safe_stem}_{VERSION}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
