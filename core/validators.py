import re

def validate_required(value):
    return value is not None and str(value).strip() != ""

def validate_email(email):
    if not validate_required(email):
        return False
    return re.match(r"^[^@]+@[^@]+\.[^@]+$", str(email)) is not None

def validate_iban(iban):
    if not validate_required(iban):
        return False
    iban = str(iban).replace(" ", "").upper()
    if not iban.startswith("RO") or len(iban) != 24:
        return False
    return True

def validate_cnp(cnp):
    if not validate_required(cnp):
        return False
    cnp = str(cnp)
    if not cnp.isdigit() or len(cnp) != 13:
        return False
    return True
