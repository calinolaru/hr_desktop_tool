from core.validators import (
    validate_required,
    validate_email,
    validate_iban,
    validate_cnp
)
from datetime import datetime, date
import pandas as pd


def _parse_date_strict(value) -> bool:
    """
    True dacă valoarea reprezintă o dată validă.
    Acceptă:
      - datetime / date (citit automat din Excel)
      - string: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY
    """
    if value is None:
        return False

    # pandas NA
    try:
        if pd.isna(value):
            return False
    except Exception:
        pass

    # date native (Excel)
    if isinstance(value, (datetime, date)):
        return True

    s = str(value).strip()
    if not s:
        return False

    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            datetime.strptime(s, fmt)
            return True
        except ValueError:
            continue

    return False

def validate_row(row):
    errors = {}

    # --- DataAngajare ---
    val = row.get("DataAngajare")

    # e gol?
    try:
        is_empty = pd.isna(val) or str(val).strip() == ""
    except Exception:
        is_empty = str(val).strip() == ""

    if not is_empty:
        # completat -> trebuie să fie valid
        if not _parse_date_strict(val):
            errors["DataAngajare"] = (
                "Dată invalidă (format acceptat: YYYY-MM-DD sau DD.MM.YYYY)"
            )
    else:
        # gol -> eroare doar dacă e obligatoriu
        if "DataAngajare" in REQUIRED_COLUMNS:
            errors["DataAngajare"] = "Lipsă (obligatoriu)"

    if not validate_required(row["Nume"]):
        errors["Nume"] = "Lipsă"

    if not validate_required(row["Prenume"]):
        errors["Prenume"] = "Lipsă"

    if not validate_cnp(row["CNP"]):
        errors["CNP"] = "CNP invalid"

    if not validate_iban(row["IBAN"]):
        errors["IBAN"] = "IBAN invalid"

    if not validate_email(row["Email"]):
        errors["Email"] = "Email invalid"

    return errors
