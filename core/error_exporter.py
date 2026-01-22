# core/error_exporter.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import pandas as pd


@dataclass(frozen=True)
class FlatError:
    excel_row: int
    field: str
    message: str


def flatten_errors(errors: list[dict]) -> list[FlatError]:
    """
    Input format:
      [{"row": 2, "errors": {"CNP": "...", "IBAN": "..."}}]
    Output: one FlatError per field.
    """
    out: list[FlatError] = []
    for entry in errors:
        row = int(entry.get("row"))
        field_errors = entry.get("errors", {}) or {}
        for field, msg in field_errors.items():
            out.append(FlatError(excel_row=row, field=str(field), message=str(msg)))
    return out


def export_errors_to_xlsx(errors: list[dict], out_path: str | Path) -> Path:
    flat = flatten_errors(errors)
    df = pd.DataFrame([e.__dict__ for e in flat], columns=["excel_row", "field", "message"])
    out_path = Path(out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # index=False ca sa nu ai coloana 0,1,2...
    df.to_excel(out_path, index=False)
    return out_path


def default_errors_filename() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"errors_{ts}.xlsx"
