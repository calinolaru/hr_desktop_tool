from pathlib import Path

from docx import Document

import core.document_generator as dg


def _make_simple_template_docx(path: Path, text: str) -> None:
    doc = Document()
    doc.add_paragraph(text)  # important: într-un singur run (simple)
    doc.save(str(path))


def _read_docx_text(path: Path) -> str:
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs]
    # include și textul din tabele (dacă apar)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def test_generate_docx_fills_unknown_placeholders_with_fallback(tmp_path, monkeypatch):
    # company.json mocked
    monkeypatch.setattr(dg, "load_company_context", lambda: {"FirmaNume": "ACME SRL"})

    template_path = tmp_path / "template.docx"
    out_dir = tmp_path / "out"
    out_file = "doc_test.docx"

    # template conține un câmp existent în context și unul inexistent
    _make_simple_template_docx(
        template_path,
        "Firma={{FirmaNume}} | X={{CampInexistent}} | Nume={{Nume}}"
    )

    context = {
        "Nume": "Popescu",
        # FirmaNume vine din company.json patch-uit
        # CampInexistent nu există -> trebuie să devină "—"
    }

    out_path = dg.generate_docx_for_employee(
        template_path=template_path,
        output_dir=out_dir,
        context=context,
        filename=out_file
    )

    assert out_path.exists()

    text = _read_docx_text(out_path)

    # nu trebuie să rămână placeholder neînlocuit
    assert "{{" not in text
    assert "CampInexistent" not in text  # numele placeholder-ului nu trebuie să apară

    # fallback apare în loc
    assert dg.FALLBACK_VALUE in text

    # și cele existente sunt completate
    assert "ACME SRL" in text
    assert "Popescu" in text


def test_generate_docx_does_not_crash_if_placeholder_extract_fails(tmp_path, monkeypatch):
    """
    Dacă extract_placeholders_from_docx() pică (ex: template corupt),
    funcția ar trebui să continue cu render normal (nu crash).
    """
    monkeypatch.setattr(dg, "extract_placeholders_from_docx", lambda _: (_ for _ in ()).throw(RuntimeError("boom")))

    template_path = tmp_path / "template.docx"
    out_dir = tmp_path / "out"
    out_file = "doc_ok.docx"

    _make_simple_template_docx(template_path, "Nume={{Nume}}")

    out_path = dg.generate_docx_for_employee(
        template_path=template_path,
        output_dir=out_dir,
        context={"Nume": "Test"},
        filename=out_file
    )

    assert out_path.exists()
