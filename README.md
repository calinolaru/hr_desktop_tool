# HR Desktop Tool

Aplicație desktop Windows pentru generarea automată de documente HR (DOCX / PDF)
din fișiere Excel, cu licențiere offline, PC-bound și protecție anti-abuz.

---

## ✨ Funcționalități

- Import fișier Excel (`.xlsx`)
- Citire dinamică a coloanelor (prima linie din Excel)
- Validare date:
  - email
  - CNP
  - salariu (**mandatory**)
- Căutare și filtrare:
  - Nume / Prenume
  - Salariu:
    - `>5000`
    - `<4000`
    - `=6000`
    - interval: `5000-7000`
- Selectare rânduri:
  - selectează valide
  - selectează rândurile filtrate
  - deselectează tot
- Generare documente:
  - Contracte
  - Acte adiționale
  - Orice template DOCX personalizat
- Conversie DOCX → PDF
- Licențiere offline:
  - Trial (cu expirare)
  - Full / Lifetime
  - PC binding (Machine ID)
  - Protecție anti „dat ceasul înapoi”

---

## 📊 Fișier Excel (input)

- Coloanele sunt citite **dinamic** din prima linie
- **Mandatory**:
  - `Nume`
  - `Prenume`
  - `Salariu`
- Restul coloanelor sunt **opționale**
- Celulele goale sunt înlocuite automat cu `—` în documente

---

## 📄 Template DOCX

- Placeholder-ele din Word trebuie să coincidă **exact** cu numele coloanelor din Excel:

```
{{Nume}}
{{Prenume}}
{{Salariu}}
{{Functie}}
```

- Coloană existentă în Excel dar nefolosită → OK  
- Placeholder inexistent în Excel → înlocuit cu `—`  
- Documentul se generează fără erori

---

## 🖥️ Build executabil (.exe)

```bash
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconsole --name HRTool ^
  --add-data "templates;templates" ^
  --add-data "ui;ui" ^
  --add-data "core;core" ^
  app.py
```

Executabilul apare în `dist/HRTool/HRTool.exe`.

---

## 🔐 Licențiere

### Tipuri
- `trial` – cu expirare
- `full` – pe viață (per PC)

### Caracteristici
- Offline
- Legată de PC (Machine ID)
- Semnătură criptografică
- Anti rollback dată sistem

---

## 🆔 Machine ID

La lipsă licență, aplicația generează automat:
```
machine_id.txt
```
Clientul trimite acest fișier furnizorului.

---

## 🧾 Generare licență (furnizor)

```bash
python tools/gen_license.py ^
  --type trial ^
  --company "ACME SRL" ^
  --vat "RO12345678" ^
  --machine "<MACHINE_ID>" ^
  --days 7
```

Rezultat: `license.json`

---

## 📂 Unde se pune licența (client)

```
HRTool/
├─ HRTool.exe
└─ config/
   └─ license.json
```

---

## ℹ️ About

Afișează:
- Tip licență
- Companie
- CUI
- Data expirării (fără oră)
- Zile rămase

---

© HR Desktop Tool – toate drepturile rezervate.
