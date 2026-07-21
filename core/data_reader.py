from __future__ import annotations

import io

import pandas as pd
from openpyxl import load_workbook

from .field_detector import detect_fields
from .models import WorkbookEnvelope


def read_workbook(filename: str, raw_bytes: bytes) -> WorkbookEnvelope:
    """Read the first visible worksheet without altering the uploaded bytes."""
    if not filename.lower().endswith(".xlsx"):
        raise ValueError("V2.2.1 当前只接受 .xlsx 文件。")

    workbook = load_workbook(io.BytesIO(raw_bytes), read_only=False, data_only=False)
    visible_sheets = [ws.title for ws in workbook.worksheets if ws.sheet_state == "visible"]
    sheet_name = visible_sheets[0] if visible_sheets else workbook.sheetnames[0]

    dataframe = pd.read_excel(io.BytesIO(raw_bytes), sheet_name=sheet_name, dtype=object).fillna("")
    fields, diagnostics = detect_fields(dataframe)

    ws = workbook[sheet_name]
    diagnostics.update(
        {
            "sheet_name": sheet_name,
            "sheet_count": len(workbook.sheetnames),
            "embedded_image_count": len(getattr(ws, "_images", [])),
            "merged_cell_ranges": len(ws.merged_cells.ranges),
            "has_formulas": any(
                isinstance(cell.value, str) and cell.value.startswith("=")
                for row in ws.iter_rows()
                for cell in row
            ),
        }
    )
    workbook.close()

    return WorkbookEnvelope(
        filename=filename,
        raw_bytes=raw_bytes,
        dataframe=dataframe,
        sheet_name=sheet_name,
        fields=fields,
        diagnostics=diagnostics,
    )
