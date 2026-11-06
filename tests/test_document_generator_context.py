import pandas as pd
import pytest

import core.document_generator as dg


def test_build_context_includes_all_excel_columns_and_fallback(monkeypatch):
    # company.json mocked (nu depindem de fișiere)
    monkeypatch.setattr(dg, "load_company_context", lambda: {"FirmaNume": "ACME SRL", "CUI": "RO123"})

    # simulăm un row din pandas (Series)
    row = pd.Series(
        {
            "Nume": "Popescu",
            "Prenume": "Ion",
            "Email": "   ",          # -> fallback
            "TelefonIntern": None,   # -> fallback
            "Salariu": 5500,         # -> "5500"
        }
    )

    ctx, missing_required, missing_optional = dg.build_context_with_missing(row)

    # required e gol (în modelul tău curent)
    assert missing_required == []

    # toate cheile din Excel există în context
    assert ctx["Nume"] == "Popescu"
    assert ctx["Prenume"] == "Ion"
    assert ctx["Salariu"] == "5500"

    # fallback pentru goale
    assert ctx["Email"] == dg.FALLBACK_VALUE
    assert ctx["TelefonIntern"] == dg.FALLBACK_VALUE

    # company keys sunt adăugate
    assert ctx["FirmaNume"] == "ACME SRL"
    assert ctx["CUI"] == "RO123"

    # missing_optional conține cheile goale
    assert "Email" in missing_optional
    assert "TelefonIntern" in missing_optional


def test_build_context_handles_nan(monkeypatch):
    monkeypatch.setattr(dg, "load_company_context", lambda: {})

    row = pd.Series(
        {
            "Nume": "Ionescu",
            "Prenume": "Maria",
            "DataAngajare": float("nan"),  # NaN
        }
    )

    ctx, _, missing_optional = dg.build_context_with_missing(row)
    assert ctx["DataAngajare"] == dg.FALLBACK_VALUE
    assert "DataAngajare" in missing_optional


def test_sanitize_key_matches_template_placeholder_format():
    assert dg.sanitize_key("E-mail angajator") == "E_mail_angajator"
    assert dg.sanitize_key("1 - Field") == "F_1_Field"
    assert dg.sanitize_key("!!!") == "Field"


def test_load_company_context_rejects_non_object_json(tmp_path, monkeypatch):
    company_path = tmp_path / "company.json"
    company_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(dg, "resource_path", lambda _: company_path)

    with pytest.raises(ValueError, match="obiect JSON"):
        dg.load_company_context()
