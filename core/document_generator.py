# core/document_generator.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Tuple

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

def normalize_value(value: Any) -> str:
    if value is None:
        return FALLBACK_VALUE
    s = str(value).strip()
    if s == "" or s.lower() in ("nan", "none", "<na>"):
        return FALLBACK_VALUE
    return s

def generate_docx_for_employee(template_path: str | Path, output_dir: str | Path, context: dict[str, Any], filename: str) -> Path:
    template_path = Path(template_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

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
    Returns:
      context: dict for docxtpl
      missing_required: list of required template fields that ended up fallback
      missing_optional: list of optional template fields that ended up fallback
    """
    context: dict[str, Any] = {}

    # 1) employee-based fields (excel + computed)
    for template_field, source in TEMPLATE_FIELD_MAPPING.items():
        try:
            raw_value = source(row) if callable(source) else row.get(source)
        except Exception:
            raw_value = None
        context[template_field] = normalize_value(raw_value)

    # 2) company/static fields
    company_ctx = load_company_context()
    for k, v in company_ctx.items():
        context[k] = normalize_value(v)

    # 3) detect missing (fallback) fields
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for field in TEMPLATE_FIELD_MAPPING.keys():
        if context.get(field) == FALLBACK_VALUE:
            if field in REQUIRED_TEMPLATE_FIELDS:
                missing_required.append(field)
            else:
                missing_optional.append(field)

    return context, missing_required, missing_optional