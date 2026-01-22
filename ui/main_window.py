# ui/main_window.py
from __future__ import annotations
from core.error_exporter import export_errors_to_xlsx, default_errors_filename
from pathlib import Path
from core.document_generator import row_to_context, generate_docx_for_employee
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox
)
from core.paths import resource_path
from core.pdf_converter import docx_to_pdf
from core.excel_loader import load_and_validate_excel
from core.version import APP_NAME, APP_VERSION
from PySide6.QtWidgets import QMenuBar



class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HR Desktop Tool - MVP")
        self.resize(900, 600)
        self.setWindowTitle(f"{APP_NAME} - v{APP_VERSION}")

        # Root widget
        root = QWidget()
        self.setCentralWidget(root)

        # State
        self._last_errors = []
        self._last_source_path = None
        self._last_df = None
        self._last_generated_docx_dir = None

        layout = QVBoxLayout(root)

        # Top controls
        top = QHBoxLayout()

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

        self.lbl_status = QLabel("Status: Aștept import Excel…")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)

        #layout
        top.addWidget(self.btn_import)
        top.addWidget(self.btn_export)
        top.addWidget(self.btn_generate)
        top.addWidget(self.lbl_status, 1)
        top.addWidget(self.btn_generate_pdf)

        layout.addLayout(top)

        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.on_about)

        # Error table
        self._last_errors = []
        self._last_source_path = None
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Excel Row", "Field", "Message"])
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table, 1)

        # Keep last import in memory (for Export)
        self._last_errors = []
        self._last_source_path = None


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

        generated = 0
        skipped = 0

        # df index 0 corespunde Excel row 2 (fiindcă header e pe row 1)
        for idx, row in self._last_df.iterrows():
            excel_row = idx + 2
            if excel_row in invalid_excel_rows:
                skipped += 1
                continue

            ctx = row_to_context(row)

            # filename safe (înlocuim caractere dubioase)
            nume = str(ctx.get("Nume", "")).strip().replace("/", "-").replace("\\", "-")
            prenume = str(ctx.get("Prenume", "")).strip().replace("/", "-").replace("\\", "-")
            filename = f"Contract_{nume}_{prenume}_row{excel_row}.docx".replace("  ", " ").strip()

            generate_docx_for_employee(
                template_path=template_path,
                output_dir=out_dir,
                context=ctx,
                filename=filename
            )
            generated += 1

        self._last_generated_docx_dir = out_dir
        self.btn_generate_pdf.setEnabled(generated > 0)

        QMessageBox.information(
            self,
            "Generare DOCX",
            f"Gata.\nGenerate: {generated}\nSărite (cu erori): {skipped}\nFolder: {out_dir}"
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



