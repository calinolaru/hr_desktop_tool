# ui/template_fields_dialog.py
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
)


class TemplateFieldsDialog(QDialog):
    def __init__(
        self,
        parent=None,
        excel_columns: list[str] | None = None,
        col_map: dict[str, str] | None = None,
        mandatory_headers: set[str] | None = None,
        hard_mandatory: set[str] | None = None,
    ):
        super().__init__(parent)

        self.setWindowTitle("Câmpuri template (Mandatory / Optional)")
        self.resize(860, 560)

        excel_columns = excel_columns or []
        col_map = col_map or {}
        mandatory_headers = set(mandatory_headers or [])
        hard_mandatory = set(hard_mandatory or set())

        # Mandatory final = bold headers + hard mandatory
        mandatory_final = set(mandatory_headers) | set(hard_mandatory)

        layout = QVBoxLayout(self)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Coloană Excel", "Tip", "Placeholder DOCX (safe)"])
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
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # sort: mandatory first, then optional
        def sort_key(col: str):
            is_req = col in mandatory_final
            group = 0 if is_req else 1
            return (group, col.lower())

        cols_sorted = sorted(excel_columns, key=sort_key)
        table.setRowCount(len(cols_sorted))

        for r, excel_name in enumerate(cols_sorted):
            is_req = excel_name in mandatory_final

            tip = "Mandatory" if is_req else "Optional"
            placeholder = col_map.get(excel_name, excel_name)

            it_excel = QTableWidgetItem(excel_name)
            it_tip = QTableWidgetItem(tip)
            it_ph = QTableWidgetItem(f"{{{{{placeholder}}}}}")

            # make mandatory visually stronger
            if is_req:
                f = it_excel.font()
                f.setBold(True)
                it_excel.setFont(f)
                it_tip.setFont(f)
                it_ph.setFont(f)

                it_excel.setToolTip("Mandatory: dacă lipsește, documentul NU se generează pentru acel rând.")
                it_tip.setToolTip("Mandatory")
            else:
                it_excel.setToolTip("Optional: dacă lipsește, se înlocuiește cu „—” și documentul se generează.")
                it_tip.setToolTip("Optional")

            it_ph.setToolTip("Copiază exact în DOCX (docxtpl): {{Placeholder}}")

            table.setItem(r, 0, it_excel)
            table.setItem(r, 1, it_tip)
            table.setItem(r, 2, it_ph)

        layout.addWidget(table)

        btn_close = QPushButton("Închide")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
