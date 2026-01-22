from core.excel_loader import load_and_validate_excel

df, errors = load_and_validate_excel("sample_data/angajati.xlsx")

print("Erori găsite:")
for e in errors:
    print(e)
