from __future__ import annotations

import json
import re
from dataclasses import asdict

import pandas as pd
import streamlit as st

from analyzer import analyze_records, validate_analysis
from core import export_unchanged, integrity_report, read_workbook

VERSION = "V2.2.3-Product-Analyzer-Modular"

st.set_page_config(page_title="Amazon AI Listing Optimizer", layout="wide")
st.title("Amazon AI Listing Optimizer")
st.caption(VERSION)
st.info(
    "本版本新增独立 analyzer/ 产品理解模块与事实校验模块。"
    "不生成标题、不修改 Excel、不运行图片优化；core/ 与 image/ 保持 V2.2.2 原样。"
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

    with st.expander("查看字段识别报告"):
        report_rows = []
        for label, value in fields.as_dict().items():
            display_value = "、".join(value) if isinstance(value, tuple) else (value or "")
            report_rows.append({
                "标准字段": label,
                "识别结果": display_value or "未识别",
                "状态": "✓ 已识别" if display_value else "× 未识别",
            })
        st.dataframe(pd.DataFrame(report_rows), hide_index=True, use_container_width=True)

    st.subheader("Product Analyzer（产品理解）")
    max_records = st.number_input(
        "本次分析产品数量",
        min_value=1,
        max_value=max(1, len(envelope.records)),
        value=min(10, max(1, len(envelope.records))),
        step=1,
    )

    if st.button("开始产品识别", type="primary"):
        analyses = analyze_records(envelope.records[: int(max_records)])
        st.session_state["product_analyses"] = analyses

    analyses = st.session_state.get("product_analyses", ())
    if analyses:
        rows = []
        json_rows = []
        error_count = 0
        warning_count = 0
        for analysis in analyses:
            report = validate_analysis(analysis)
            error_count += sum(issue.severity == "error" for issue in report.issues)
            warning_count += sum(issue.severity == "warning" for issue in report.issues)
            rows.append({
                "Excel行": analysis.row_number,
                "SKU": analysis.sku,
                "产品类型": analysis.product_type,
                "品牌": analysis.brand,
                "兼容品牌": "、".join(analysis.compatible_brands),
                "兼容型号": "、".join(analysis.compatible_models),
                "材质": analysis.material,
                "颜色": analysis.color,
                "数量": analysis.quantity,
                "尺寸": analysis.dimensions,
                "重量": analysis.weight,
                "使用场景": "、".join(analysis.applications),
                "关键词": "、".join(analysis.keywords),
                "事实校验": "通过" if report.passed else "失败",
                "警告": "；".join(issue.message for issue in report.issues),
            })
            item = analysis.as_dict()
            item["validation"] = report.as_dict()
            json_rows.append(item)

        m1, m2, m3 = st.columns(3)
        m1.metric("已分析", len(analyses))
        m2.metric("事实错误", error_count)
        m3.metric("人工检查警告", warning_count)
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        st.download_button(
            "导出产品理解 JSON",
            data=json.dumps(json_rows, ensure_ascii=False, indent=2),
            file_name="product_analysis_v223.json",
            mime="application/json",
        )

        with st.expander("查看第一条识别证据"):
            st.json(asdict(analyses[0]))

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
    )
