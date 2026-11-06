# HR Desktop Tool

Aplicație desktop Windows pentru generarea automată de documente HR (DOCX / PDF)
din fișiere Excel, cu licențiere offline, PC-bound și protecție anti-abuz.

---

## ✨ Funcționalități

- Import fișier Excel (`.xlsx`)
- Citire dinamică a coloanelor (prima linie din Excel)
- Verificare la generare pentru câmpuri obligatorii (`Nume`, `Prenume`, `Salariu`
  și coloanele marcate bold în header-ul Excel)
- Email-ul și CNP-ul nu sunt validate automat
- Căutare și filtrare:
  - orice coloană sau coloane alese din „Coloane”
  - `salariu>5000`, `salariu<=4000`, `salariu=6000`
  - interval: `salariu 5000-7000`
  - criterii multiple separate cu `|`
- Selectare rânduri:
  - selectează tot
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
- **Obligatorii la generare**:
  - `Nume`
  - `Prenume`
  - `Salariu`
- Coloanele marcate bold în header sunt, de asemenea, obligatorii.
- Câmpurile obligatorii lipsă opresc generarea documentului pentru rândul respectiv.
- Restul coloanelor sunt **opționale**; email-ul și CNP-ul nu sunt validate automat.
- Celulele opționale goale sunt înlocuite automat cu `—`; rândurile cu valori obligatorii lipsă nu sunt generate.

---

## 📄 Template DOCX

- Placeholder-ele trebuie să folosească numele safe afișate în **Tools → Câmpuri template**.
  Spațiile și semnele de punctuație devin `_`, iar numele care începe cu o cifră primește prefixul `F_`.
  De exemplu, coloana `E-mail angajator` devine `{{E_mail_angajator}}`.

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
python tools/license_gen.py ^
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
