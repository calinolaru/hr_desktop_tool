# core/validation_engine.py
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from core.constants import REQUIRED_EXCEL_COLUMNS
from core.validators import validate_cnp, validate_email, validate_iban, validate_required


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip() == ""


def _parse_date_strict(value: Any) -> bool:
    """
    True dacă value e o dată validă.
    Acceptă:
      - datetime/date (citite automat din Excel)
      - string: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY
    """
    if _is_empty(value):
        return False

    if isinstance(value, (datetime, date)):
        return True

    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            datetime.strptime(s, fmt)
            return True
        except ValueError:
            continue
    return False


def validate_row(row: Any) -> dict[str, str]:
    """
    Only Nume & Prenume are required.
    Optional fields:
      - empty -> OK
      - filled -> validated
    """
    errors: dict[str, str] = {}

    # Required fields
    for col in REQUIRED_EXCEL_COLUMNS:
        val = row.get(col) if hasattr(row, "get") else None
        if not validate_required(val):
            errors[col] = "Lipsă"

    # Optional: DataAngajare (validate only if filled)
    if hasattr(row, "index") and "DataAngajare" in row.index:
        val = row.get("DataAngajare")
        if not _is_empty(val) and not _parse_date_strict(val):
            errors["DataAngajare"] = "Dată invalidă (YYYY-MM-DD, DD.MM.YYYY sau DD/MM/YYYY)"

    # Optional: CNP
    if hasattr(row, "index") and "CNP" in row.index:
        val = row.get("CNP")
        if not _is_empty(val) and not validate_cnp(val):
            errors["CNP"] = "CNP invalid"

    # Optional: IBAN
    if hasattr(row, "index") and "IBAN" in row.index:
        val = row.get("IBAN")
        if not _is_empty(val) and not validate_iban(val):
            errors["IBAN"] = "IBAN invalid"

    # Optional: Email
    if hasattr(row, "index") and "Email" in row.index:
        val = row.get("Email")
        if not _is_empty(val) and not validate_email(val):
            errors["Email"] = "Email invalid"

    return errors
