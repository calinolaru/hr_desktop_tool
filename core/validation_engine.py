# core/validation_engine.py
from __future__ import annotations

import re
from typing import Any


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    s = str(v).strip()
    if s == "":
        return True
    # pandas NaN
    try:
        import pandas as pd
        return pd.isna(v)
    except Exception:
        return False


def parse_salary(v: Any) -> float | None:
    if _is_empty(v):
        return None
    s = str(v).strip().replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif re.fullmatch(r"[+-]?\d{1,3}(?:\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except Exception:
        return None


def validate_row(row: Any, mandatory_headers: set[str] | None = None) -> dict[str, str]:
    """
    Return dict: field -> error message
    """
    mandatory_headers = mandatory_headers or set()

    errors: dict[str, str] = {}

    # mandatory by rule
    must_have = {"Nume", "Prenume", "Salariu"} | set(mandatory_headers)

    for col in must_have:
        if col in row.index:
            if _is_empty(row.get(col)):
                errors[col] = "Câmp obligatoriu (marcat mandatory)."
        else:
            errors[col] = "Coloană obligatorie lipsă din Excel."

    # Salary format validation (dacă există)
    if "Salariu" in row.index:
        val = row.get("Salariu")
        if not _is_empty(val):
            if parse_salary(val) is None:
                errors["Salariu"] = "Salariu invalid (trebuie numeric)."

    return errors
