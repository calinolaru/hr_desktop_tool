# ui/main_window.py
from __future__ import annotations
from core.error_exporter import export_errors_to_xlsx, default_errors_filename
from pathlib import Path
from core.document_generator import row_to_context, generate_docx_for_employee
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog

)
from core.paths import resource_path
from core.pdf_converter import docx_to_pdf
from core.excel_loader import load_and_validate_excel
from core.version import APP_NAME, APP_VERSION
from core.document_generator import build_context_with_missing, generate_docx_for_employee
from ui.template_fields_dialog import TemplateFieldsDialog

import re
from PySide6.QtWidgets import (
    QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox, QToolBar
)
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QSizePolicy, QLabel, QPushButton

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

        warnings_optional_total = set()
        missing_required_total = set()
        skipped_missing_required = 0
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
        generated_files = []

        for idx, row in self._last_df.iterrows():
            excel_row = idx + 2

            if excel_row not in selected_excel_rows:
                continue

            # 1) sari peste rânduri invalide (din validare)
            if excel_row in invalid_excel_rows:
                skipped_validation += 1
                continue

            # 2) construiește context + vezi ce lipsește
            ctx, missing_required, missing_optional = build_context_with_missing(row)

            # 3) dacă lipsesc required template fields -> nu generăm doc
            if missing_required:
                skipped_missing_required += 1
                missing_required_total.update(missing_required)
                continue

            # 4) colectează warnings opționale (non-blocant)
            warnings_optional_total.update(missing_optional)

            # 5) generează doc
            nume = self.safe_name(str(ctx.get("Nume", "")))
            prenume = self.safe_name(str(ctx.get("Prenume", "")))

            prefix = self.doc_prefix_from_template(template_path)
            base = f"{prefix}_{nume}_{prenume}"

            # 1) nume simplu
            candidate = out_path / f"{base}.docx"

            # 2) dacă există deja, adaugă ultimele 4 din CNP
            if candidate.exists():
                cnp = self.safe_name(str(ctx.get("CNP", "")))
                last4 = cnp[-4:] if len(cnp) >= 4 else "0000"
                candidate = out_path / f"{base}_{last4}.docx"

                # 3) dacă și asta există, adaugă _2, _3, ...
                k = 2
                while candidate.exists():
                    candidate = out_path / f"{base}_{last4}_{k}.docx"
                    k += 1

            filename = candidate.name

            generate_docx_for_employee(
                template_path=template_path,
                output_dir=out_dir,
                context=ctx,
                filename=filename
            )

            generated += 1
            generated_files.append(candidate)

        # salvează pentru PDF (respectă batch-ul curent)
        self._last_generated_docx_dir = out_dir
        self._last_generated_docx_files = generated_files

        # enable PDF doar dacă s-a generat ceva
        self.btn_generate_pdf.setEnabled(len(generated_files) > 0)

        # reține lipsurile pt dialogul de câmpuri
        self._last_missing_optional = set(warnings_optional_total)
        self._last_missing_required = set(missing_required_total)

        msg = (
            f"Gata.\n"
            f"Generate: {generated}\n"
            f"Sărite (validare Excel): {skipped_validation}\n"
            f"Sărite (lipsesc câmpuri obligatorii în template): {skipped_missing_required}\n"
            f"Folder: {out_dir}"
        )
        QMessageBox.information(self, "Generare DOCX", msg)

        # Warning non-blocant pentru opționale
        if warnings_optional_total:
            preview = ", ".join(sorted(list(warnings_optional_total))[:12])
            more = "" if len(warnings_optional_total) <= 12 else f" (+{len(warnings_optional_total) - 12} altele)"
            QMessageBox.warning(
                self,
                "Atenție: câmpuri opționale lipsă",
                "Unele câmpuri opționale nu au fost completate și au fost înlocuite cu „—”.\n\n"
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

        try:
            for docx_file in existing:
                pdf_path = pdf_dir / docx_file.with_suffix(".pdf").name
                docx_to_pdf(docx_file, pdf_path)
                generated += 1
        except Exception as e:
            QMessageBox.critical(self, "Eroare PDF", str(e))
            return

        QMessageBox.information(
            self,
            "PDF generate",
            f"Gata.\nPDF-uri generate: {generated}\nFolder: {pdf_dir}"
        )

    def on_about(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        from core.version import APP_NAME, APP_VERSION, APP_COPYRIGHT

        QMessageBox.information(
            self,
            "About",
            f"{APP_NAME}\nVersion: {APP_VERSION}\n{APP_COPYRIGHT}\n\n"
            "MVP: Import Excel → Validare → DOCX/PDF"
        )

    def on_show_template_fields(self) -> None:
        dlg = TemplateFieldsDialog(
            self,
            missing_optional=getattr(self, "_last_missing_optional", set()),
            missing_required=getattr(self, "_last_missing_required", set()),
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








