# core/excel_loader.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

import pandas as pd

from core.constants import REQUIRED_EXCEL_COLUMNS
from core.validation_engine import validate_row


def load_and_validate_excel(path: str | Path) -> Tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Load Excel + validate rows.

    Rules:
    - Header row defines what fields exist for templates.
    - Only 'Nume' and 'Prenume' are required.
    - All other columns are optional; if filled, we validate format for some known fields.
    """
    path = Path(path)
    df = pd.read_excel(path)

    missing = [c for c in REQUIRED_EXCEL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Lipsesc coloane obligatorii: {missing}")

    # Normalize required columns for UI/search/filenames
    for col in REQUIRED_EXCEL_COLUMNS:
        df[col] = df[col].astype("string").fillna("").str.strip()

    # Normalize common optional fields (only if present)
    if "CNP" in df.columns:
        df["CNP"] = (
            df["CNP"]
            .astype("string")
            .fillna("")
            .str.strip()
            .str.replace(" ", "", regex=False)
            .str.replace(r"\.0$", "", regex=True)
        )

    if "IBAN" in df.columns:
        df["IBAN"] = (
            df["IBAN"]
            .astype("string")
            .fillna("")
            .str.strip()
            .str.replace(" ", "", regex=False)
        )

    if "Email" in df.columns:
        df["Email"] = df["Email"].astype("string").fillna("").str.strip()

    all_errors: list[dict[str, Any]] = []
    for index, row in df.iterrows():
        errors = validate_row(row)
        if errors:
            all_errors.append({"row": index + 2, "errors": errors})  # header=1, first data row=2

    return df, all_errors

