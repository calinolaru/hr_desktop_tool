# core/pdf_converter.py
from __future__ import annotations
from pathlib import Path
import win32com.client


def docx_to_pdf(docx_path: str | Path, pdf_path: str | Path | None = None) -> Path:
    docx_path = Path(docx_path).resolve()

    if pdf_path is None:
        pdf_path = docx_path.with_suffix(".pdf")
    else:
        pdf_path = Path(pdf_path).resolve()

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False

    try:
        doc = word.Documents.Open(str(docx_path))
        # 17 = wdFormatPDF
        doc.SaveAs(str(pdf_path), FileFormat=17)
        doc.Close(False)
    finally:
        word.Quit()

    return pdf_path
