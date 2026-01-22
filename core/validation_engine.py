from core.validators import (
    validate_required,
    validate_email,
    validate_iban,
    validate_cnp
)

def validate_row(row):
    errors = {}

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
