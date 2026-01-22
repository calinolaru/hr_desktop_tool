import pandas as pd
from core.validation_engine import validate_row

REQUIRED_COLUMNS = [
    "Nume", "Prenume", "CNP", "IBAN",
    "Email", "Functie", "DataAngajare"
]

def load_and_validate_excel(path):
    df = pd.read_excel(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Lipsesc coloane: {missing}")

    all_errors = []

    for index, row in df.iterrows():
        errors = validate_row(row)
        if errors:
            all_errors.append({
                "row": index + 2,  # Excel row number
                "errors": errors
            })

    return df, all_errors
