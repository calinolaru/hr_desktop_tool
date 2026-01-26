# ui/template_fields_dialog.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class TemplateFieldsDialog(QDialog):
    """
    Shows available fields for templating:
      - Excel columns (from loaded .xlsx)
      - Optional company.json keys
    """

    def __init__(
        self,
        parent=None,
        excel_columns: list[str] | None = None,
        company_keys: list[str] | None = None,
    ):
        super().__init__(parent)

        self.setWindowTitle("Câmpuri disponibile (Excel + Setări firmă)")
        self.resize(800, 520)

        excel_columns = list(excel_columns or [])
        company_keys = list(company_keys or [])

        layout = QVBoxLayout(self)

        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Câmp", "Sursă"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.ElideRight)

        hh = table.horizontalHeader()
        hh.setStretchLastSection(True)
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        rows = [(c, "Excel") for c in excel_columns] + [(k, "Setări firmă") for k in company_keys]
        rows.sort(key=lambda x: (0 if x[1] == "Excel" else 1, x[0].lower()))

        table.setRowCount(len(rows))
        for i, (field, source) in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(field))
            table.setItem(i, 1, QTableWidgetItem(source))

        layout.addWidget(table)

        btn_close = QPushButton("Închide")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
