import pandas as pd

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
