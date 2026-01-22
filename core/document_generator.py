# core/document_generator.py
from __future__ import annotations

from pathlib import Path
from typing import Any
from docxtpl import DocxTemplate


def row_to_context(row: Any) -> dict[str, Any]:
    """
    Transformă un row (pandas Series) în dict pentru docxtpl.
    Cheile trebuie să corespundă cu placeholder-ele din template.
    """
    # Convertim la string unde are sens (HR templates sunt text-heavy)
    def s(x):
        if x is None:
            return ""
        return str(x)

    return {
        "Nume": s(row.get("Nume")),
        "Prenume": s(row.get("Prenume")),
        "CNP": s(row.get("CNP")),
        "IBAN": s(row.get("IBAN")),
        "Email": s(row.get("Email")),
        "Functie": s(row.get("Functie")),
        "DataAngajare": s(row.get("DataAngajare")),
        "NumeComplet": f"{s(row.get('Nume'))} {s(row.get('Prenume'))}".strip(),
    }


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
