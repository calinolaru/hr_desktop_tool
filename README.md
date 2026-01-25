# HR Desktop Tool

Aplicație desktop pentru generarea automată de documente HR (DOCX / PDF) pe baza unui fișier Excel (.xlsx).
Scopul aplicației este eliminarea muncii repetitive (copy–paste) și reducerea erorilor umane în documentele HR.

---

## Funcționalități principale

- Import fișier Excel (.xlsx)
- Validare date (ex: CNP, IBAN, Email)
- Raport de erori exportabil în Excel
- Listă angajați cu selecție individuală pentru export
- Evidențiere vizuală a rândurilor invalide
- Căutare rapidă după Nume / Prenume
- Generare documente DOCX din template Word
- Conversie DOCX → PDF
- Suport pentru câmpuri dinamice (coloane Excel)
- Fallback automat pentru câmpuri lipsă (`—`)
- Suport pentru mai multe tipuri de documente (contract, act adițional etc.)

---

## Conceptul de date

### Excel = sursa principală de date

- Prima linie din Excel este header-ul
- Fiecare coloană devine automat un câmp utilizabil în template-ul Word
- Nu este necesară configurare suplimentară

### Coloane obligatorii

Fișierul Excel trebuie să conțină obligatoriu:

- `Nume`
- `Prenume`

Acestea sunt folosite pentru:
- identificarea angajaților
- căutare rapidă
- generarea numelui fișierelor

Toate celelalte coloane sunt opționale.

---

## Template DOCX

- Template-urile sunt fișiere Word standard (.docx)
- Câmpurile se scriu sub forma:

{{Nume}}
{{Prenume}}
{{Functie}}
{{OriceAltaColoana}}

### Reguli importante

- Dacă o coloană există în Excel → valoarea este înlocuită
- Dacă o coloană este goală → se folosește fallback `—`
- Dacă un câmp din template NU există în Excel → se folosește fallback `—`
- Documentul se generează fără erori în toate cazurile

---

## Instalare (Developer / local)

### 1. Creează virtual environment

```bash
python -m venv .venv
