# HRTool

**HRTool** is a Windows desktop application designed for HR teams to automate the processing of employee data from Excel files. It validates data, reports errors clearly, and generates professional documents (DOCX and PDF) only for valid entries.

---

## ✨ Key Features

* **Excel Import (.xlsx)** – Load employee data from a predefined Excel template
* **Data Validation** – Automatic checks for:

  * CNP (length, digits, Excel formatting issues)
  * IBAN (basic structure)
  * Email format
  * Required fields
* **Error Reporting**

  * On-screen table with row / field / message
  * Export error report to Excel (.xlsx)
* **Document Generation**

  * Generate one **DOCX per valid employee** from a Word template
  * Generate **PDF files automatically** from DOCX (via Microsoft Word)
* **Safe Workflow**

  * Rows with errors are skipped
  * Only valid data produces documents

---

## 🧩 Typical Workflow

1. HR prepares an Excel file with employee data
2. Import the Excel file into HRTool
3. Review validation errors (if any)
4. Export error report (optional)
5. Fix errors in Excel
6. Generate DOCX documents for valid rows
7. Generate PDF documents

---

## 📁 Expected Excel Format

The Excel file **must contain the following columns** (exact names):

* `Nume`
* `Prenume`
* `CNP`
* `IBAN`
* `Email`
* `Functie`
* `DataAngajare`

### ⚠️ Important Excel Notes

* Columns **CNP** and **IBAN must be formatted as TEXT**, not Number
* Otherwise Excel may convert values to scientific notation (e.g. `1.99E+12`)

---

## 📝 Word Template

The DOCX template must contain placeholders using this syntax:

```
{{Nume}}
{{Prenume}}
{{NumeComplet}}
{{CNP}}
{{IBAN}}
{{Email}}
{{Functie}}
{{DataAngajare}}
```

Example text in template:

> Subsemnatul/a **{{NumeComplet}}**, CNP **{{CNP}}**, angajat pe funcția **{{Functie}}** începând cu **{{DataAngajare}}**.

---

## 🖨️ PDF Generation Requirements

To generate PDF files:

* **Microsoft Word must be installed** on the machine
* Conversion is done automatically via Word (COM automation)

If Word is not installed, DOCX generation will still work.

---

## 💻 System Requirements

* Windows 10 / 11
* Microsoft Word (for PDF export)
* No Python installation required for end users

---

## 📦 Application Distribution

HRTool is distributed as a Windows executable:

```
HRTool/
├── HRTool.exe
└── _internal/
```

To run the application:

1. Extract the folder
2. Double-click `HRTool.exe`

---

## 🔒 Source Code & Licensing

* Source code is private
* End users receive only the compiled executable
* Custom licensing / trial mechanisms can be added if required

---

## 🚀 Status

This project is an MVP focused on real HR workflows and automation. The application is stable, production-ready, and designed to be extended with additional validations and document types.

---

## 📞 Support

For issues related to:

* Excel formatting
* Validation errors
* Document templates

Please ensure the input data follows the documented format before reporting issues.

---

© 2026 HRTool

