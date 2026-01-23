# core/document_generator.py
from __future__ import annotations

from pathlib import Path
from typing import Any
from docxtpl import DocxTemplate
from core.template_mapping import TEMPLATE_FIELD_MAPPING
import json


def row_to_context(row):
    context = {}

    for template_field, source in TEMPLATE_FIELD_MAPPING.items():
        if callable(source):
            context[template_field] = source(row)
        else:
            value = row.get(source, "")
            context[template_field] = "" if value is None else str(value)

    return context

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

def load_company_context():
    path = Path("config/company.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))