# core/excel_loader.py
from __future__ import annotations

import pandas as pd
from openpyxl import load_workbook


def _read_header_styles(path: str) -> tuple[list[str], set[str]]:
    """
    Returnează:
      - headers (text header)
      - mandatory_headers (headers care sunt bold în Excel)
    """
    wb = load_workbook(path, read_only=False, data_only=True)
    try:
        ws = wb.active

        headers: list[str] = []
        mandatory_headers: set[str] = set()

        # Header row = 1
        for cell in ws[1]:
            header = str(cell.value).strip() if cell.value is not None else ""
            headers.append(header)

            if cell.font and cell.font.bold and header:
                mandatory_headers.add(header)

        return headers, mandatory_headers
    finally:
        wb.close()


def load_and_validate_excel(path: str):
    """
    Citește Excel și întoarce:
      df, headers, mandatory_headers(bold)
    """
    headers, mandatory_headers = _read_header_styles(path)

    df = pd.read_excel(path)
    df.columns = [str(c).strip() for c in df.columns]

    # headers din pandas pot fi identice dar cu spații — normalizăm la ce are df
    headers = list(df.columns)
    mandatory_headers = {h for h in mandatory_headers if h in df.columns}

    return df, headers, mandatory_headers
