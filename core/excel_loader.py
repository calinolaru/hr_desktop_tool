from core.validation_engine import validate_row
import pandas as pd

REQUIRED_COLUMNS = ["Nume", "Prenume"]

def load_and_validate_excel(path):
    df = pd.read_excel(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Lipsesc coloane: {missing}")

    # Force as string + cleanup common Excel artifacts
    for col in ["CNP", "IBAN", "Email", "DataAngajare"]:
        if col in df.columns:
            df[col] = df[col].astype("string")

    # Cleanup CNP: remove ".0", spaces, and turn <NA> into empty
    df["CNP"] = (
        df["CNP"]
        .fillna("")
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace(r"\.0$", "", regex=True)
    )

    # Cleanup IBAN
    df["IBAN"] = (
        df["IBAN"]
        .fillna("")
        .str.strip()
        .str.replace(" ", "", regex=False)
    )

    # Cleanup Email
    df["Email"] = df["Email"].fillna("").str.strip()

    all_errors = []
    for index, row in df.iterrows():
        errors = validate_row(row)
        if errors:
            all_errors.append({"row": index + 2, "errors": errors})

    return df, all_errors
