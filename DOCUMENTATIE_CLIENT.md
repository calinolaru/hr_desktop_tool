# HR Desktop Tool – Ghid de utilizare

Această aplicație permite generarea rapidă de documente HR (contracte, acte adiționale, adeverințe etc.)
pentru unul sau mai mulți angajați, pe baza unui fișier Excel (.xlsx).

---

## 1. Cerințe minime

- Sistem de operare: Windows
- Aplicația funcționează fără Microsoft Office instalat
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

Fișierul Excel trebuie să conțină obligatoriu:

- Nume
- Prenume

Aceste coloane sunt folosite pentru:
- identificarea angajaților
- căutare rapidă în aplicație
- generarea automată a numelui fișierelor

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

Numele coloanei din Excel se folosește identic în documentul Word,
între acolade duble.

Exemple:

{{Nume}}
{{Prenume}}
{{Salariu}}
{{Functie}}

Exemplu concret:
- Coloană Excel: TelefonIntern
- În document Word: {{TelefonIntern}}

---

### 3.2 Ce se întâmplă dacă un câmp NU este completat

Dacă:
- o celulă este goală în Excel
- sau coloana există dar nu are valoare

Aplicația va înlocui automat câmpul cu:

—

Documentul se generează normal, fără erori.

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
   - validează câmpurile (Email, CNP etc.)
   - afișează eventualele erori într-un tab separat

---

## 5. Tab-ul „Angajați”

În acest tab:
- fiecare rând reprezintă un angajat
- există o coloană „Export” (checkbox)

### 5.1 Rânduri invalide

- Rândurile cu date incorecte sunt evidențiate vizual
- Aceste rânduri nu pot fi selectate pentru export
- Detaliile apar în tab-ul „Erori”

---

### 5.2 Căutare rapidă

Poți căuta după:
- Nume
- Prenume
- Nume + Prenume

Lista se filtrează instant, fără scroll.

---

## 6. Selectarea angajaților

- Poți selecta manual una sau mai multe persoane
- Butonul „Selectează valide” bifează automat doar rândurile fără erori
- Rândurile invalide nu pot fi selectate

---

## 7. Generarea documentelor DOCX

1. Apasă „Generează DOCX”
2. Selectează template-ul Word (.docx)
3. Selectează folderul de output

Documentele se generează doar pentru:
- angajații selectați
- angajații cu date valide

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
3. PDF-urile sunt salvate într-un folder separat

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
