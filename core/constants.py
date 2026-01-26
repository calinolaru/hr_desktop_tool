# core/constants.py
from __future__ import annotations

# Doar acestea sunt obligatorii în Excel
REQUIRED_EXCEL_COLUMNS: list[str] = ["Nume", "Prenume"]

# Fallback standard pentru câmpuri lipsă / goale
FALLBACK_VALUE: str = "—"
