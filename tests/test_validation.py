import pandas as pd
import pytest

from core.excel_loader import load_and_validate_excel
from core.validation_engine import parse_salary, validate_row


def test_load_sample_excel_and_validate_signature():
    df, headers, mandatory_headers = load_and_validate_excel("sample_data/angajati.xlsx")

    assert not df.empty
    assert isinstance(headers, list)
    assert isinstance(mandatory_headers, set)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("5.000", 5000.0),
        ("5.000,50", 5000.5),
        ("5000,50", 5000.5),
        ("5 000", 5000.0),
        ("invalid", None),
    ],
)
def test_parse_salary_uses_romanian_number_formats(value, expected):
    assert parse_salary(value) == expected


def test_validate_row_accepts_thousands_separator_salary():
    row = pd.Series({"Nume": "Popescu", "Prenume": "Ana", "Salariu": "5.000"})

    assert "Salariu" not in validate_row(row)
