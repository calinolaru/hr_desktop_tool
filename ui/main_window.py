# ui/main_window.py
from __future__ import annotations
from core.error_exporter import export_errors_to_xlsx, default_errors_filename
from pathlib import Path
from core.document_generator import row_to_context, generate_docx_for_employee
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from core.paths import resource_path
from core.pdf_converter import docx_to_pdf
from core.excel_loader import load_and_validate_excel
from core.version import APP_NAME, APP_VERSION
from core.document_generator import build_context_with_missing, generate_docx_for_employee
from ui.template_fields_dialog import TemplateFieldsDialog
from PySide6.QtWidgets import QToolBar
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView


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

        # State (single source of truth)
        self._last_missing_optional = set()
        self._last_missing_required = set()
        self._last_errors = []
        self._last_source_path = None
        self._last_df = None
        self._last_generated_docx_dir = None

        # Toolbar (top actions)
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(tb)

        # Buttons
        self.btn_import = QPushButton("Import Excel (.xlsx)")
        self.btn_import.clicked.connect(self.on_import_excel)

        self.btn_export = QPushButton("Export erori (.xlsx)")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.on_export_errors)

        self.btn_generate = QPushButton("Generează DOCX (rânduri valide)")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self.on_generate_docx)

        self.btn_generate_pdf = QPushButton("Generează PDF")
        self.btn_generate_pdf.setEnabled(False)
        self.btn_generate_pdf.clicked.connect(self.on_generate_pdf)

        self.btn_fields = QPushButton("Câmpuri template")
        self.btn_fields.clicked.connect(self.on_show_template_fields)

        tb.addWidget(self.btn_import)
        tb.addWidget(self.btn_export)
        tb.addWidget(self.btn_generate)
        tb.addWidget(self.btn_generate_pdf)
        tb.addWidget(self.btn_fields)

        # Optional: also keep a label in UI (status bar is primary)
        self.lbl_status = QLabel("Status: Aștept import Excel…")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.lbl_status)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Menu
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.on_about)

        # Error table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Excel Row", "Field", "Message"])
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(True)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Excel Row
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Field
        hh.setSectionResizeMode(2, QHeaderView.Stretch)  # Message

        layout.addWidget(self.table, 1)

    def safe_name(self, s: str) -> str:
        s = (s or "").strip()
        for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            s = s.replace(ch, "-")
        while "  " in s:
            s = s.replace("  ", " ")
        return s

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
            self._last_errors = errors
            self._last_source_path = path
            self.btn_export.setEnabled(len(errors) > 0)
            self._last_df = df
            self.btn_generate.setEnabled(len(df) > 0)  # îl lăsăm activ chiar dacă există erori, va genera doar valide

        except Exception as e:
            QMessageBox.critical(self, "Eroare la import", str(e))
            return

        self.populate_errors(errors)
        self.lbl_status.setText(
            f"Status: Import OK | Rânduri: {len(df)} | Erori: {len(errors)} | Fișier: {path}"
        )

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

        # Template default (poți schimba după)
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

        # errors are like: [{"row": 2, "errors": {...}}, ...]
        # "row" e număr de rând în Excel (header=1, primul data row=2)
        invalid_excel_rows = {int(e["row"]) for e in (self._last_errors or [])}

        warnings_optional_total = set()
        missing_required_total = set()
        skipped_missing_required = 0
        generated = 0
        skipped_validation = 0  # dacă ai deja logica ta de invalid rows

        # ... (invalid_excel_rows calculat ca înainte)

        for idx, row in self._last_df.iterrows():
            excel_row = idx + 2

            # 1) sari peste rânduri invalide (din validare)
            if excel_row in invalid_excel_rows:
                skipped_validation += 1
                continue

            # 2) construiește context + vezi ce lipsește
            ctx, missing_required, missing_optional = build_context_with_missing(row)

            # 3) dacă lipsesc required template fields -> nu generăm doc
            if missing_required:
                skipped_missing_required += 1
                missing_required_total.update(missing_required)  #
                continue

            # 4) colectează warnings opționale (non-blocant)
            for f in missing_optional:
                warnings_optional_total.add(f)

            # 5) generează doc
            nume = self.safe_name(str(ctx.get("Nume", "")))
            prenume = self.safe_name(str(ctx.get("Prenume", "")))

            base = f"Contract_{nume}_{prenume}"
            out_path = Path(out_dir)

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

        self._last_missing_optional = set(warnings_optional_total)
        self._last_missing_required = set(missing_required_total)

        self._last_generated_docx_dir = out_dir
        self.btn_generate_pdf.setEnabled(generated > 0)

        msg = (
            f"Gata.\n"
            f"Generate: {generated}\n"
            f"Sărite (validare Excel): {skipped_validation}\n"
            f"Sărite (lipsesc câmpuri obligatorii în template): {skipped_missing_required}\n"
            f"Folder: {out_dir}"
        )

        QMessageBox.information(self, "Generare DOCX", msg)

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
        if not self._last_generated_docx_dir:
            QMessageBox.information(
                self, "PDF",
                "Mai întâi generează documentele DOCX."
            )
            return

        docx_dir = Path(self._last_generated_docx_dir)
        pdf_dir = docx_dir.parent / "pdf"
        pdf_dir.mkdir(exist_ok=True)

        generated = 0

        try:
            for docx_file in docx_dir.glob("*.docx"):
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



