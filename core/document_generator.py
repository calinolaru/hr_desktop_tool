# core/document_generator.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Tuple

import pandas as pd
from docx import Document
from docxtpl import DocxTemplate

from core.constants import FALLBACK_VALUE as _FALLBACK_VALUE
from core.paths import resource_path

# Backwards-compat (UI/tests)
FALLBACK_VALUE = _FALLBACK_VALUE


def extract_placeholders_from_docx(docx_path: str | Path) -> set[str]:
    """Extract {{Placeholders}} from a DOCX (paragraphs + tables)."""
    doc = Document(str(docx_path))
    chunks: list[str] = [p.text for p in doc.paragraphs]

    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                chunks.append(cell.text)

    text = "\n".join(chunks)
    fields = set(re.findall(r"\{\{\s*([^}]+?)\s*\}\}", text))
    return {f.strip() for f in fields if f.strip()}


def normalize_value(v: Any) -> str:
    """None/NA/empty -> FALLBACK_VALUE, else -> stripped string."""
    try:
        if pd.isna(v):
            return FALLBACK_VALUE
    except Exception:
        pass

    s = str(v).strip()
    return s if s else FALLBACK_VALUE


def load_company_context() -> dict[str, Any]:
    """Load optional company fields from config/company.json (works in PyInstaller too)."""
    path = resource_path("config/company.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_context_with_missing(row: Any) -> Tuple[dict[str, Any], list[str], list[str]]:
    """
    Context = all Excel columns (dynamic) + company.json keys.
    No required/optional template concept.

    Returns:
      context: dict for docxtpl
      missing_required: always []
      missing_optional: keys that became FALLBACK_VALUE (informational only)
    """
    context: dict[str, Any] = {}

    # 1) all Excel columns
    for col in getattr(row, "index", []):
        key = str(col).strip()
        if not key:
            continue
        try:
            context[key] = normalize_value(row.get(col))
        except Exception:
            context[key] = FALLBACK_VALUE

    # 2) company/static fields (optional)
    for k, v in load_company_context().items():
        key = str(k).strip()
        if not key:
            continue
        context[key] = normalize_value(v)

    missing_required: list[str] = []
    missing_optional: list[str] = sorted([k for k, v in context.items() if v == FALLBACK_VALUE], key=str.lower)

    return context, missing_required, missing_optional


def generate_docx_for_employee(
    template_path: str | Path,
    output_dir: str | Path,
    context: dict[str, Any],
    filename: str,
) -> Path:
    """
    Render DOCX template safely:
    - merges company.json automatically (caller context wins)
    - unknown placeholders -> FALLBACK_VALUE
    - empty values -> FALLBACK_VALUE
    """
    template_path = Path(template_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Merge company.json + context (context overrides)
    merged: dict[str, Any] = {}
    for k, v in load_company_context().items():
        merged[str(k).strip()] = normalize_value(v)
    for k, v in (context or {}).items():
        merged[str(k).strip()] = normalize_value(v)

    # Fill any placeholders missing in context
    try:
        placeholders = extract_placeholders_from_docx(template_path)
        for key in placeholders:
            if key not in merged:
                merged[key] = FALLBACK_VALUE
    except Exception:
        pass

    doc = DocxTemplate(str(template_path))
    doc.render(merged)

    out_path = output_dir / filename
    doc.save(str(out_path))
    return out_path

def sanitize_key(name: str) -> str:
    """
    Transformă numele de coloană Excel în placeholder valid pentru Jinja/docxtpl.
    Exemplu: "Nr.Contract" -> "Nr_Contract"
            "E-mail angajator" -> "E_mail_angajator"
    """
    s = (name or "").strip()

    # înlocuiește orice nu e literă/cifră/_ cu _
    s = re.sub(r"[^0-9a-zA-Z_]", "_", s)

    # compactează underscores
    s = re.sub(r"_+", "_", s).strip("_")

    # dacă începe cu cifră, prefix
    if s and s[0].isdigit():
        s = f"col_{s}"

    return s or "col"


def build_dynamic_context_with_missing(
    row: Any,
    col_map: dict[str, str],
) -> Tuple[dict[str, Any], list[str]]:
    """
    context: chei SAFE (placeholder) -> valori
    missing_optional: lista cheilor SAFE care au rezultat fallback (celulă goală)
    """
    ctx: dict[str, Any] = {}
    missing_optional: list[str] = []

    # row e un pandas Series; row.get(original_col) merge
    for original, safe in col_map.items():
        val = row.get(original)

        # normalize + fallback
        if val is None:
            norm = FALLBACK_VALUE
        else:
            # pandas NaN
            try:
                import pandas as pd
                if pd.isna(val):
                    norm = FALLBACK_VALUE
                else:
                    norm = str(val).strip() if str(val).strip() else FALLBACK_VALUE
            except Exception:
                norm = str(val).strip() if str(val).strip() else FALLBACK_VALUE

        ctx[safe] = norm

        if norm == FALLBACK_VALUE:
            missing_optional.append(safe)

    return ctx, missing_optional


def generate_docx_for_employee(
    template_path: str | Path,
    output_dir: str | Path,
    context: dict[str, Any],
    filename: str,
) -> Path:
    template_path = Path(template_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = DocxTemplate(str(template_path))
    doc.render(context)

    out_path = output_dir / filename
    doc.save(str(out_path))
    return out_path