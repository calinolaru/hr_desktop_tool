# ui/main_window.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox
)

from core.excel_loader import load_and_validate_excel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HR Desktop Tool - MVP")
        self.resize(900, 600)

        # Root widget
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        # Top controls
        top = QHBoxLayout()
        self.btn_import = QPushButton("Import Excel (.xlsx)")
        self.btn_import.clicked.connect(self.on_import_excel)

        self.lbl_status = QLabel("Status: Aștept import Excel…")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)

        top.addWidget(self.btn_import)
        top.addWidget(self.lbl_status, 1)

        layout.addLayout(top)

        # Error table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Excel Row", "Field", "Message"])
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.table, 1)

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
        except Exception as e:
            QMessageBox.critical(self, "Eroare la import", str(e))
            return

        self.populate_errors(errors)
        self.lbl_status.setText(
            f"Status: Import OK | Rânduri: {len(df)} | Erori: {len(errors)} | Fișier: {path}"
        )

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
