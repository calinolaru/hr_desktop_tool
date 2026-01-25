# core/document_generator.py
from __future__ import annotations
import re
from docx import Document
import json
from pathlib import Path
from typing import Any, Tuple
import pandas as pd
from docxtpl import DocxTemplate
from core.template_mapping import TEMPLATE_FIELD_MAPPING, REQUIRED_TEMPLATE_FIELDS

FALLBACK_VALUE = "—"

def row_to_context(row):
    context = {}

    for template_field, source in TEMPLATE_FIELD_MAPPING.items():
        try:
            if callable(source):
                raw_value = source(row)
            else:
                raw_value = row.get(source)
        except Exception:
            raw_value = None

        context[template_field] = normalize_value(raw_value)

    return context

def extract_placeholders_from_docx(docx_path: str | Path) -> set[str]:
    """
    Extrage placeholder-ele de forma {{Field}} din paragrafe + tabele.
    (Suficient pentru template-uri simple; dacă ai cazuri speciale, facem variantă XML.)
    """
    doc = Document(str(docx_path))
    chunks: list[str] = []

    for p in doc.paragraphs:
        chunks.append(p.text)

    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                chunks.append(cell.text)

    text = "\n".join(chunks)
    fields = set(re.findall(r"\{\{\s*([^}]+?)\s*\}\}", text))
    return {f.strip() for f in fields if f.strip()}


def normalize_value(v: Any) -> str:
    try:
        if pd.isna(v):
            return FALLBACK_VALUE
    except Exception:
        pass

    s = str(v).strip()
    return s if s else FALLBACK_VALUE

def generate_docx_for_employee(
    template_path: str | Path,
    output_dir: str | Path,
    context: dict[str, Any],
    filename: str
) -> Path:
    template_path = Path(template_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1) completează context pentru orice placeholder din docx care lipsește
    try:
        placeholders = extract_placeholders_from_docx(template_path)
        for key in placeholders:
            if key not in context:
                context[key] = FALLBACK_VALUE
    except Exception:
        # dacă nu putem citi docx-ul, continuăm cu contextul existent
        pass

    # 2) render + save
    doc = DocxTemplate(str(template_path))
    doc.render(context)

    out_path = output_dir / filename
    doc.save(str(out_path))
    return out_path


def load_company_context() -> dict[str, Any]:
    path = Path("config/company.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def build_context_with_missing(row: Any) -> Tuple[dict[str, Any], list[str], list[str]]:
    """
    Context = toate coloanele din Excel + cheile din company.json.
    Fără required/optional pe template: totul e "optional", iar golurile devin "—".
    """
    context: dict[str, Any] = {}

    # 1) toate coloanele din Excel (dinamic)
    for col in getattr(row, "index", []):
        key = str(col).strip()
        if not key:
            continue
        context[key] = normalize_value(row.get(col))

    # 2) company/static fields
    company_ctx = load_company_context()
    for k, v in company_ctx.items():
        context[k] = normalize_value(v)

    # 3) missing lists (doar informativ)
    missing_required: list[str] = []
    missing_optional: list[str] = sorted([k for k, v in context.items() if v == FALLBACK_VALUE], key=str.lower)

    return context, missing_required, missing_optional