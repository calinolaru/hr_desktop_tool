# HR Desktop Tool – Ghid de utilizare

Această aplicație permite generarea rapidă de documente HR (contracte, acte adiționale, adeverințe etc.)
pentru unul sau mai mulți angajați, pe baza unui fișier Excel (.xlsx).

---

## 1. Cerințe minime

- Sistem de operare: Windows
- Generarea DOCX nu necesită Microsoft Office.
- Generarea PDF necesită Microsoft Word instalat.
- Pentru editarea fișierului Excel se poate folosi:
  - Microsoft Excel
  - Google Sheets
  - LibreOffice

---

## 2. Structura fișierului Excel (.xlsx)

### 2.1 Regula de bază (IMPORTANT)

- Prima linie din Excel reprezintă header-ul (titlurile coloanelor)
- Numele coloanelor devin automat câmpuri disponibile în documente

---

### 2.2 Coloane obligatorii

Pentru generare, fișierul Excel trebuie să conțină:

- Nume
- Prenume
- Salariu

Coloanele marcate bold în header sunt, de asemenea, obligatorii. Dacă un astfel
de câmp lipsește sau este gol, documentul pentru rândul respectiv nu se generează.
Email-ul și CNP-ul nu sunt validate automat.

Exemplu nume fișier:
Contract_Popescu_Ion.docx

---

### 2.3 Coloane opționale

Orice altă coloană este opțională și poate fi adăugată liber.

Exemple:
- CNP
- Email
- TelefonIntern
- Functie
- Salariu
- DataAngajare
- ManagerDirect
- OriceAltaColoana

Toate aceste coloane pot fi utilizate în documente fără configurare suplimentară.

---

## 3. Utilizarea coloanelor Excel în documente Word (DOCX)

### 3.1 Regula de bază

Placeholder-ele folosesc numele safe afișate în **Tools → Câmpuri template**.
Spațiile și semnele de punctuație devin `_`; de exemplu,
coloana `E-mail angajator` devine `{{E_mail_angajator}}`.

Exemple:

{{Nume}}
{{Prenume}}
{{Salariu}}
{{Functie}}

Exemplu concret:
- Coloană Excel: `TelefonIntern`
- În document Word: `{{TelefonIntern}}`

---

### 3.2 Ce se întâmplă dacă un câmp NU este completat

Dacă:
- o celulă este goală în Excel
- sau coloana există dar nu are valoare

Aplicația va înlocui automat câmpul cu:

—

Pentru câmpurile opționale, documentul se generează normal. Dacă lipsește un
câmp obligatoriu (`Nume`, `Prenume`, `Salariu` sau o coloană bold), acel rând
este omis la generare.

---

### 3.3 Ce se întâmplă dacă documentul conține un câmp inexistent

Exemplu:
{{CampInexistent}}

Comportament:
- nu apare eroare
- documentul se generează normal
- câmpul este înlocuit automat cu:

—

---

## 4. Importul fișierului Excel

1. Apasă butonul „Import Excel (.xlsx)”
2. Selectează fișierul dorit
3. Aplicația:
   - încarcă datele
   - citește header-ele bold pentru a determina câmpuri obligatorii
   - nu validează automat formatul email-ului sau CNP-ului

---

## 5. Tab-ul „Angajați”

În acest tab:
- fiecare rând reprezintă un angajat
- există o coloană „Export” (checkbox)

### 5.1 Căutare rapidă

Poți alege coloanele căutate din butonul „Coloane”. Criteriile de salariu acceptă,
de exemplu, `salariu>5000` și `salariu 5000-7000`; separă criterii multiple cu `|`.

Lista se filtrează instant, fără scroll.

---

## 6. Selectarea angajaților

- Poți selecta manual una sau mai multe persoane
- „Selectează tot” bifează toate rândurile
- „Selectează filtrate” bifează doar rândurile vizibile după căutare
- Verificarea câmpurilor obligatorii se face la generare; rândurile incomplete sunt omise

---

## 7. Generarea documentelor DOCX

1. Apasă „Generează DOCX”
2. Selectează template-ul Word (.docx)
3. Selectează folderul de output

Documentele se generează doar pentru:
- angajații selectați
- angajații care au toate câmpurile obligatorii completate

---

### 7.1 Numele fișierelor generate

Format standard:
TipDocument_Nume_Prenume.docx

Exemplu:
Contract_Popescu_Ion.docx

Dacă există nume duplicate, aplicația adaugă automat un sufix pentru diferențiere.

---

## 8. Generarea PDF

După generarea DOCX:
1. Apasă „Generează PDF”
2. PDF-urile se creează doar pentru documentele generate în ultima operație
3. PDF-urile sunt salvate lângă fișierele DOCX (necesită Microsoft Word)

---

## 9. Câmpuri disponibile

Butonul „Câmpuri template” afișează:
- toate coloanele citite din fișierul Excel
- scopul este informativ (nu necesită configurare)

---

## 10. Recomandări

- Nu modifica structura Excel-ului după import
- Folosește denumiri clare pentru coloane
- Evită caractere speciale în header
- Testează întâi pe 1–2 angajați

---

© HR Desktop Tool – Documentație
