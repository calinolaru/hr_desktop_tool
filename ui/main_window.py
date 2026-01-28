# ui/main_window.py
from __future__ import annotations
from core.error_exporter import export_errors_to_xlsx, default_errors_filename
from pathlib import Path
from core.document_generator import build_context_with_missing, generate_docx_for_employee
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog
)
from core.paths import resource_path
from core.pdf_converter import docx_to_pdf
from core.excel_loader import load_and_validate_excel
from ui.template_fields_dialog import TemplateFieldsDialog
from core.version import APP_NAME, APP_VERSION, APP_COPYRIGHT
from core.document_generator import load_company_context
from PySide6.QtWidgets import QLineEdit, QHBoxLayout
import re
from PySide6.QtWidgets import (
    QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QToolBar
)
from ui.license_info_dialog import LicenseInfoDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QSizePolicy, QLabel, QPushButton
from PySide6.QtWidgets import QMessageBox

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Window
        self.resize(900, 600)
        self.setWindowTitle(f"{APP_NAME} - v{APP_VERSION}")

        # Root widget
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # --- State (single source of truth) ---
        self._last_missing_optional = set()
        self._last_missing_required = set()
        self._last_errors = []
        self._last_source_path = None
        self._last_df = None
        self._last_generated_docx_dir = None
        self._last_generated_docx_files = []  # list[Path]
        self._last_template_path = None

        # --- Menu ---
        menubar = self.menuBar()

        tools_menu = menubar.addMenu("Tools")
        act_fields = tools_menu.addAction("Câmpuri template")
        act_fields.triggered.connect(self.on_show_template_fields)

        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.on_about)

        # --- Toolbar (top actions) ---
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(tb)

        # Main actions (folosite des)
        self.btn_import = QPushButton("Import Excel (.xlsx)")
        self.btn_import.clicked.connect(self.on_import_excel)

        self.btn_export = QPushButton("Export erori (.xlsx)")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.on_export_errors)

        self.btn_generate = QPushButton("Generează DOCX (selectate)")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self.on_generate_docx)

        self.btn_generate_pdf = QPushButton("Generează PDF")
        self.btn_generate_pdf.setEnabled(False)
        self.btn_generate_pdf.clicked.connect(self.on_generate_pdf)

        tb.addWidget(self.btn_import)
        tb.addWidget(self.btn_export)
        tb.addWidget(self.btn_generate)
        tb.addWidget(self.btn_generate_pdf)

        tb.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # Counter label (Selectate / Valide)
        self.lbl_counter = QLabel("Selectate: 0 / Valide: 0")
        self.lbl_counter.setAlignment(Qt.AlignVCenter)
        tb.addWidget(self.lbl_counter)

        tb.addSeparator()

        # Selection actions (doar astea 2)
        self.btn_select_valid = QPushButton("Selectează valide")
        self.btn_select_valid.setEnabled(False)
        self.btn_select_valid.clicked.connect(self.on_select_valid_only)

        self.btn_select_filtered = QPushButton("Selectează filtrate")
        self.btn_select_filtered.setEnabled(False)
        self.btn_select_filtered.clicked.connect(self.on_select_filtered)

        tb.addWidget(self.btn_select_filtered)

        self.btn_select_none = QPushButton("Deselectează tot")
        self.btn_select_none.setEnabled(False)
        self.btn_select_none.clicked.connect(self.on_select_none)

        tb.addWidget(self.btn_select_valid)
        tb.addWidget(self.btn_select_none)

        # --- Tabs ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # --- Tab: Angajați (select export) ---
        people_tab = QWidget()
        people_layout = QVBoxLayout(people_tab)

        search_row = QHBoxLayout()
        lbl = QLabel("Caută:")
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Caută: nume/prenume sau ex: salariu>5000, salariu=4500, salariu 5000-7000")
        self.txt_search.textChanged.connect(self.apply_search_filter)

        self.btn_clear_search = QPushButton("X")
        self.btn_clear_search.setFixedWidth(28)
        self.btn_clear_search.clicked.connect(lambda: self.txt_search.setText(""))

        search_row.addWidget(lbl)
        search_row.addWidget(self.txt_search, 1)
        search_row.addWidget(self.btn_clear_search)

        people_layout.addLayout(search_row)

        self.table_people = QTableWidget(0, 6)
        self.table_people.setHorizontalHeaderLabels(["Export", "Excel Row", "Nume", "Prenume", "CNP", "Email"])
        self.table_people.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_people.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_people.setAlternatingRowColors(True)
        self.table_people.setShowGrid(False)
        self.table_people.verticalHeader().setVisible(False)

        hhp = self.table_people.horizontalHeader()
        hhp.setStretchLastSection(True)
        hhp.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # checkbox
        hhp.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # excel row
        hhp.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hhp.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hhp.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hhp.setSectionResizeMode(5, QHeaderView.Stretch)

        # contor live când bifezi manual
        self.table_people.itemChanged.connect(self._on_people_item_changed)

        people_layout.addWidget(self.table_people, 1)
        self.tabs.addTab(people_tab, "Angajați")

        # --- Tab: Erori ---
        errors_tab = QWidget()
        errors_layout = QVBoxLayout(errors_tab)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Excel Row", "Field", "Message"])
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        hhe = self.table.horizontalHeader()
        hhe.setStretchLastSection(True)
        hhe.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hhe.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hhe.setSectionResizeMode(2, QHeaderView.Stretch)

        errors_layout.addWidget(self.table, 1)
        self.tabs.addTab(errors_tab, "Erori")

        # Status label (optional)
        self.lbl_status = QLabel("Status: Aștept import Excel…")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.lbl_status)

        # Status bar
        self.statusBar().showMessage("Ready")

    def safe_name(self, s: str) -> str:
        s = (s or "").strip()
        for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            s = s.replace(ch, "-")
        while "  " in s:
            s = s.replace("  ", " ")
        return s

    def doc_prefix_from_template(self, template_path: str) -> str:
        name = Path(template_path).stem  # ex: "contract_template"
        name = re.sub(r"(template|tmpl|model)$", "", name, flags=re.IGNORECASE)
        name = name.replace("-", "_").replace(" ", "_")
        name = name.strip("_")

        # Mapări friendly (opțional)
        mapping = {
            "contract": "Contract",
            "act_aditional": "Act_Aditional",
            "decizie": "Decizie",
        }
        return mapping.get(name.lower(), name.title().replace("__", "_") or "Document")

    def on_import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selectează fișierul Excel",
            "",
            "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            df, errors = load_and_validate_excel(path)

            self._last_df = df
            self._last_errors = errors
            self._last_source_path = path

            self.btn_export.setEnabled(len(errors) > 0)
            self.btn_generate.setEnabled(len(df) > 0)

        except Exception as e:
            QMessageBox.critical(self, "Eroare la import", str(e))
            return

        # Umple tabelul de erori (tab Erori)
        self.populate_errors(errors)

        # Umple tabelul de angajați (tab Angajați) + evidențiere invalid
        self._populate_people_table()

        # re-aplică filtrul curent după repopulare
        if hasattr(self, "search_input"):
            self.apply_search_filter(self.search_input.text())

        self.lbl_status.setText(
            f"Status: Import OK | Rânduri: {len(df)} | Erori: {len(errors)} | Fișier: {path}"
        )

    def _populate_people_table(self) -> None:
        if self._last_df is None:
            self.table_people.setRowCount(0)
            return

        # set de rânduri invalide din validare (Excel row: 2..)
        invalid_excel_rows = {int(e["row"]) for e in (self._last_errors or [])}
        df = self._last_df

        # culori (subtil, nu țipător)
        invalid_bg = QColor("#3a1e1e")  # roșu închis
        invalid_fg = QColor("#ffd6d6")  # text roz-pal (opțional)

        self.table_people.blockSignals(True)
        self.table_people.setSortingEnabled(False)
        self.table_people.setRowCount(len(df))

        for i, (_, row) in enumerate(df.iterrows()):
            excel_row = i + 2
            is_invalid = excel_row in invalid_excel_rows

            # Col 0: checkbox "Export"
            chk = QTableWidgetItem()
            if is_invalid:
                # Rând invalid: checkbox dezactivat
                chk.setFlags(Qt.ItemIsEnabled)  # fără ItemIsUserCheckable
                chk.setCheckState(Qt.Unchecked)
                chk.setToolTip("Rând invalid (are erori). Vezi tab-ul „Erori”.")
            else:
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Checked)
                chk.setToolTip("Selectat pentru export")

            self.table_people.setItem(i, 0, chk)

            # Restul coloanelor (1..5)
            values = [
                str(excel_row),
                str(row.get("Nume", "")),
                str(row.get("Prenume", "")),
                str(row.get("CNP", "")),
                str(row.get("Email", "")),
            ]

            for col, val in enumerate(values, start=1):
                item = QTableWidgetItem(val)
                if is_invalid:
                    item.setToolTip("Rând invalid (are erori). Vezi tab-ul „Erori”.")
                self.table_people.setItem(i, col, item)

            # Evidențiere vizuală pentru rând invalid (toate coloanele)
            if is_invalid:
                for col in range(0, 6):
                    cell = self.table_people.item(i, col)
                    if cell:
                        cell.setBackground(invalid_bg)
                        # opțional: text mai deschis
                        cell.setForeground(invalid_fg)

        self.table_people.setSortingEnabled(True)

        # deblocăm semnalele și actualizăm contorul
        self.table_people.blockSignals(False)
        self._update_selection_counter()

        # activează butoanele de selecție (dacă le ai)
        if hasattr(self, "btn_select_none"):
            self.btn_select_none.setEnabled(True)
        if hasattr(self, "btn_select_valid"):
            self.btn_select_valid.setEnabled(True)
        if hasattr(self, "btn_select_filtered"):
            self.btn_select_filtered.setEnabled(True)

    def on_export_errors(self) -> None:
        if not self._last_errors:
            QMessageBox.information(self, "Export erori", "Nu există erori de exportat.")
            return

        suggested = default_errors_filename()
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează raportul de erori",
            suggested,
            "Excel Files (*.xlsx)"
        )
        if not out_path:
            return

        try:
            saved_path = export_errors_to_xlsx(self._last_errors, out_path)
        except Exception as e:
            QMessageBox.critical(self, "Eroare export", str(e))
            return

        QMessageBox.information(self, "Export erori", f"Raport salvat:\n{saved_path}")

    def populate_errors(self, errors: list[dict]) -> None:
        """
        errors format:
        [
          {"row": 2, "errors": {"CNP": "...", "IBAN": "..."}}
        ]
        We'll show 1 table row per field error for clarity.
        """
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        rows_added = 0
        for entry in errors:
            excel_row = entry.get("row")
            field_errors = entry.get("errors", {})

            for field, msg in field_errors.items():
                self.table.insertRow(rows_added)

                item_row = QTableWidgetItem(str(excel_row))
                item_row.setData(Qt.UserRole, excel_row)  # numeric sorting helper
                item_row.setTextAlignment(Qt.AlignCenter)

                item_field = QTableWidgetItem(str(field))
                item_msg = QTableWidgetItem(str(msg))

                self.table.setItem(rows_added, 0, item_row)
                self.table.setItem(rows_added, 1, item_field)
                self.table.setItem(rows_added, 2, item_msg)

                rows_added += 1

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

    def on_generate_docx(self) -> None:
        if self._last_df is None:
            QMessageBox.information(self, "Generare DOCX", "Mai întâi importă un fișier Excel.")
            return

        # Template default
        default_template = str(resource_path("templates/contract_template.docx"))
        template_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selectează template-ul DOCX",
            default_template,
            "Word Template (*.docx)"
        )
        if not template_path:
            return

        self._last_template_path = template_path

        out_dir = QFileDialog.getExistingDirectory(
            self,
            "Selectează folderul de output pentru DOCX",
            str(Path("output") / "docx")
        )
        if not out_dir:
            return

        out_path = Path(out_dir)

        # rânduri invalide din validare
        invalid_excel_rows = {int(e["row"]) for e in (self._last_errors or [])}

        warnings_optional_total: set[str] = set()
        skipped_validation = 0
        generated = 0

        # selecția din UI
        selected_excel_rows = set()
        for r in range(self.table_people.rowCount()):
            chk = self.table_people.item(r, 0)
            if chk and chk.checkState() == Qt.Checked:
                excel_row = int(self.table_people.item(r, 1).text())
                selected_excel_rows.add(excel_row)

        if not selected_excel_rows:
            QMessageBox.information(self, "Generare DOCX", "Nu ai selectat nicio persoană pentru export.")
            return

        # lista de DOCX generate (pentru PDF)
        generated_files: list[Path] = []

        for idx, row in self._last_df.iterrows():
            excel_row = idx + 2

            if excel_row not in selected_excel_rows:
                continue

            # sari peste rânduri invalide (din validare)
            if excel_row in invalid_excel_rows:
                skipped_validation += 1
                continue

            # context dinamic (toate coloanele) + company.json
            ctx, _missing_required, missing_optional = build_context_with_missing(row)

            # colectăm warnings (coloane lipsă -> fallback "—")
            warnings_optional_total.update(missing_optional)

            # --- nume fișier ---
            # dacă Nume/Prenume lipsesc, folosim excel_row ca fallback ca să nu iasă "—"
            raw_nume = str(ctx.get("Nume", "")).strip()
            raw_prenume = str(ctx.get("Prenume", "")).strip()

            nume = self.safe_name(raw_nume) if raw_nume and raw_nume != "—" else f"Row{excel_row}"
            prenume = self.safe_name(raw_prenume) if raw_prenume and raw_prenume != "—" else ""

            prefix = self.doc_prefix_from_template(template_path)

            base = f"{prefix}_{nume}"
            if prenume:
                base += f"_{prenume}"

            candidate = out_path / f"{base}.docx"

            # dacă există deja, încearcă să distingă cu ultimele 4 din CNP (dacă există)
            if candidate.exists():
                cnp = str(ctx.get("CNP", "")).strip()
                cnp = cnp if cnp and cnp != "—" else ""
                if len(cnp) >= 4:
                    last4 = self.safe_name(cnp[-4:])
                    candidate = out_path / f"{base}_{last4}.docx"

                # dacă și așa există, pune sufix incremental
                k = 1
                while candidate.exists():
                    candidate = out_path / f"{base}_dup{k}.docx"
                    k += 1

            filename = candidate.name

            saved = generate_docx_for_employee(
                template_path=template_path,
                output_dir=out_dir,
                context=ctx,
                filename=filename
            )

            generated += 1
            generated_files.append(saved)

        # salvează pentru PDF (respectă batch-ul curent)
        self._last_generated_docx_dir = out_dir
        self._last_generated_docx_files = generated_files

        # enable PDF doar dacă s-a generat ceva
        self.btn_generate_pdf.setEnabled(len(generated_files) > 0)

        # reține lipsurile pt dialogul de câmpuri (acum sunt doar "coloane goale")
        self._last_missing_optional = set(warnings_optional_total)
        self._last_missing_required = set()  # nu mai există required

        msg = (
            f"Gata.\n"
            f"Generate: {generated}\n"
            f"Sărite (validare Excel): {skipped_validation}\n"
            f"Folder: {out_dir}"
        )
        QMessageBox.information(self, "Generare DOCX", msg)

        # Warning non-blocant pentru câmpuri goale
        if warnings_optional_total:
            preview = ", ".join(sorted(list(warnings_optional_total))[:12])
            more = "" if len(warnings_optional_total) <= 12 else f" (+{len(warnings_optional_total) - 12} altele)"
            QMessageBox.warning(
                self,
                "Atenție: câmpuri goale",
                "Unele coloane din Excel nu au fost completate și au fost înlocuite cu „—”.\n\n"
                f"Câmpuri: {preview}{more}"
            )

    def on_generate_pdf(self) -> None:
        files = getattr(self, "_last_generated_docx_files", None)
        if not files:
            QMessageBox.information(
                self, "PDF",
                "Nu am o listă de documente generate.\n"
                "Generează mai întâi DOCX pentru selecția curentă."
            )
            return

        # păstrează doar fișierele care există (user poate să le fi mutat/șters)
        existing = [Path(p) for p in files if Path(p).exists()]
        if not existing:
            QMessageBox.information(
                self, "PDF",
                "Nu găsesc documentele DOCX generate (au fost mutate/șterse?).\n"
                "Generează din nou DOCX."
            )
            return

        # output pdf folder: lângă docx folder
        docx_dir = existing[0].parent
        pdf_dir = docx_dir.parent / "pdf"
        pdf_dir.mkdir(exist_ok=True)

        generated = 0
        failed = 0
        failed_files = []

        for docx_file in existing:
            try:
                pdf_path = pdf_dir / docx_file.with_suffix(".pdf").name
                docx_to_pdf(docx_file, pdf_path)
                generated += 1
            except Exception as e:
                failed += 1
                failed_files.append(f"{docx_file.name}: {e}")

        if failed == 0:
            QMessageBox.information(
                self,
                "PDF generate",
                f"Gata.\nPDF-uri generate: {generated}\nFolder: {pdf_dir}"
            )
            return

        # dacă au fost erori, arată un sumar + primele N
        preview = "\n".join(failed_files[:8])
        more = "" if len(failed_files) <= 8 else f"\n(+{len(failed_files) - 8} altele)"

        QMessageBox.warning(
            self,
            "PDF generate (cu erori)",
            f"Gata.\nPDF-uri generate: {generated}\nEșuate: {failed}\nFolder: {pdf_dir}\n\n"
            f"Detalii:\n{preview}{more}"
        )

    def on_about(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        from core.version import APP_NAME, APP_VERSION, APP_COPYRIGHT

        lic = getattr(self, "_license_info", None)

        # --- helper formatări ---
        def short_date(iso: str) -> str:
            # ISO: 2026-02-02T19:59:31.359934+00:00  ->  2026-02-02
            try:
                return iso.split("T", 1)[0]
            except Exception:
                return iso

        def status_text(lic) -> str:
            expires = getattr(lic, "expires", None)
            if not expires:
                return "Nelimitată"

            try:
                from core.license_manager import days_until_expiry
                days_left = days_until_expiry(lic)
            except Exception:
                days_left = None

            if days_left is None:
                return f"Expiră la {short_date(str(expires))}"

            if days_left <= 0:
                return "Expirată"
            if days_left == 1:
                return "Expiră mâine"
            return f"{days_left} zile rămase"

        # --- construim HTML minimalist ---
        title = f"<div style='font-size:16px; font-weight:600;'>{APP_NAME}</div>"
        ver = f"<div style='color:#B8BDC7;'>Versiune: {APP_VERSION}</div>"
        copy = f"<div style='color:#B8BDC7;'>{APP_COPYRIGHT}</div>"

        if lic:
            lic_type = str(getattr(lic, "license_type", "")).upper()
            company = str(getattr(lic, "company", "")).strip() or "—"
            vat = str(getattr(lic, "vat", "")).strip() or "—"
            machine = str(getattr(lic, "machine", "")).strip()
            machine_short = (machine[:8] + "…" + machine[-6:]) if len(machine) > 16 else (machine or "—")

            issued = str(getattr(lic, "issued_at", "")).strip()
            expires = getattr(lic, "expires", None)

            issued_short = short_date(issued) if issued else "—"
            expires_short = short_date(str(expires)) if expires else "—"

            status = status_text(lic)

            license_block = f"""
            <div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.10);">
              <div style="font-weight:600; margin-bottom:6px;">Licență</div>
              <table style="width:100%; border-collapse:collapse;">
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Tip</td><td>{lic_type}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Companie</td><td>{company}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">CUI/VAT</td><td>{vat}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Machine</td><td>{machine_short}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Emisă</td><td>{issued_short}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Expiră</td><td>{expires_short}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Status</td><td><b>{status}</b></td></tr>
              </table>
              <div style="margin-top:8px; color:#B8BDC7; font-size:11px;">
                Pentru suport, trimite Machine ID complet (din fișierul <b>machine_id.txt</b>)
              </div>
            </div>
            """
        else:
            license_block = """
            <div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.10); color:#B8BDC7;">
              Licență: — (neîncărcată)
            </div>
            """

        html = f"""
        <div style="min-width:520px;">
          {title}
          {ver}
          {copy}
          {license_block}
        </div>
        """

        QMessageBox.information(self, "About", html)

    def on_show_template_fields(self) -> None:
        if self._last_df is None:
            QMessageBox.information(self, "Câmpuri", "Mai întâi importă un fișier Excel.")
            return

        company_ctx = load_company_context()

        dlg = TemplateFieldsDialog(
            self,
            excel_columns=list(self._last_df.columns),
            company_keys=list(company_ctx.keys()),
        )
        dlg.exec()

    def _set_all_checks(self, state: Qt.CheckState) -> None:
        for r in range(self.table_people.rowCount()):
            item = self.table_people.item(r, 0)
            if item is None:
                continue
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(state)

    def on_select_none(self) -> None:
        self._set_all_checks(Qt.Unchecked)
        self._update_selection_counter()

    def on_select_valid_only(self) -> None:
        self._set_all_checks(Qt.Checked)
        self._update_selection_counter()

    def _update_selection_counter(self) -> None:
        if self.table_people.rowCount() == 0:
            self.lbl_counter.setText("Selectate: 0 / Valide: 0")
            return

        selected = 0
        valid = 0
        for r in range(self.table_people.rowCount()):
            chk = self.table_people.item(r, 0)
            if chk is None:
                continue
            if chk.flags() & Qt.ItemIsUserCheckable:
                valid += 1
                if chk.checkState() == Qt.Checked:
                    selected += 1

        self.lbl_counter.setText(f"Selectate: {selected} / Valide: {valid}")

    def _on_people_item_changed(self, item: QTableWidgetItem) -> None:
        # ne interesează doar checkbox-ul din col 0
        if item.column() != 0:
            return
        self._update_selection_counter()
        self._last_generated_docx_files = []
        self.btn_generate_pdf.setEnabled(False)

    def on_search_people(self, text: str) -> None:
        q = (text or "").strip().lower()

        for r in range(self.table_people.rowCount()):
            # Col 2 = Nume, Col 3 = Prenume (din tabelul tău)
            nume = (self.table_people.item(r, 2).text() if self.table_people.item(r, 2) else "").lower()
            prenume = (self.table_people.item(r, 3).text() if self.table_people.item(r, 3) else "").lower()
            full = f"{nume} {prenume}".strip()

            match = (q in nume) or (q in prenume) or (q in full) if q else True
            self.table_people.setRowHidden(r, not match)

    def _parse_salary_filter(self, text: str):
        """
        Acceptă în search:
          salariu>5000
          salariu>= 5000
          salariu=5000
          salariu<=4500
          salariu< 3000
        Returnează tuple (op, value) sau None.
        """
        t = (text or "").strip().lower().replace(" ", "")
        m = re.search(r"(salariu)(<=|>=|=|<|>)(-?\d+(?:[.,]\d+)?)", t)
        if not m:
            return None
        op = m.group(2)
        val_s = m.group(3).replace(",", ".")
        try:
            val = float(val_s)
        except Exception:
            return None
        return op, val

    def _cell_salary_to_float(self, row_index: int) -> float | None:
        """
        Ia salariul din tabel (coloana 'Salariu' dacă o ai în people table),
        sau din df dacă nu e afișat în tabel.
        Recomand: dacă nu ai coloană Salariu în tabel, citește din self._last_df.
        """
        # VARIANTA 1: dacă ai coloană Salariu în table_people
        # col_salary = ... (index)
        # item = self.table_people.item(row_index, col_salary)
        # s = item.text() if item else ""
        # ...

        # VARIANTA 2 (mai robust): din df
        if self._last_df is None:
            return None
        try:
            salary_raw = self._last_df.iloc[row_index].get("Salariu", None)
        except Exception:
            return None

        # folosește aceeași logică ca în validare (simplificat)
        if salary_raw is None:
            return None
        s = str(salary_raw).strip().replace(" ", "")
        if not s or s.lower() in ("nan", "<na>", "none"):
            return None
        if "." in s and "," in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            if "," in s and "." not in s:
                s = s.replace(",", ".")
            if re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
                s = s.replace(".", "")
        try:
            return float(s)
        except Exception:
            return None

    def _match_salary(self, actual: float | None, flt) -> bool:
        if flt is None:
            return True
        if actual is None:
            return False
        op, val = flt
        if op == ">":
            return actual > val
        if op == ">=":
            return actual >= val
        if op == "<":
            return actual < val
        if op == "<=":
            return actual <= val
        return actual == val

    def apply_search_filter(self, text: str) -> None:
        q = (text or "").strip().lower()

        # detect salariu filter
        salary_filter = self._parse_salary_filter(q)
        salary_range = self._parse_salary_range(q)

        # scoate partea de salariu din text ca să rămână doar nume/prenume
        name_query = re.sub(r"(salariu)\s*(<=|>=|=|<|>)\s*(-?\d+(?:[.,]\d+)?)", "", q).strip()
        name_query = re.sub(r"salariu\s*[: ]\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", "", name_query).strip()

        for r in range(self.table_people.rowCount()):
            nume = (self.table_people.item(r, 2).text() if self.table_people.item(r, 2) else "").lower()
            prenume = (self.table_people.item(r, 3).text() if self.table_people.item(r, 3) else "").lower()

            ok_name = True
            if name_query:
                full = f"{nume} {prenume}".strip()
                ok_name = (name_query in nume) or (name_query in prenume) or (name_query in full)

            sal = self._cell_salary_to_float(r)

            ok_salary = True
            if salary_filter is not None:
                ok_salary = self._match_salary(sal, salary_filter)
            elif salary_range is not None:
                if sal is None:
                    ok_salary = False
                else:
                    lo, hi = salary_range
                    ok_salary = (lo <= sal <= hi)

            self.table_people.setRowHidden(r, not (ok_name and ok_salary))

        if hasattr(self, "_update_counter"):
            self._update_counter()

    def _parse_salary_range(self, text: str):
        """
        Acceptă:
          salariu 5000-7000
          salariu:5000-7000
          5000-7000 (dacă vrei, dar eu îl leg de cuvântul 'salariu' ca să nu fie ambiguu)
        """
        t = (text or "").strip().lower()
        # permite spații, ':' etc
        m = re.search(r"salariu\s*[: ]\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", t)
        if not m:
            return None
        a = float(m.group(1).replace(",", "."))
        b = float(m.group(2).replace(",", "."))
        lo, hi = (a, b) if a <= b else (b, a)
        return (lo, hi)

    def on_select_filtered(self) -> None:
        """
        Bifează pentru export doar rândurile:
          - vizibile (după filtrare)
          - valide (checkbox activ / user-checkable)
        """
        for r in range(self.table_people.rowCount()):
            if self.table_people.isRowHidden(r):
                continue

            chk = self.table_people.item(r, 0)
            if not chk:
                continue

            # Bifează doar dacă e valid (are flag de checkable)
            if chk.flags() & Qt.ItemIsUserCheckable:
                chk.setCheckState(Qt.Checked)

        # dacă ai contor, îl actualizezi
        if hasattr(self, "_update_counter"):
            self._update_counter()












