# ui/license_info_dialog.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QGridLayout
)
from PySide6.QtCore import Qt

from core.license_manager import LicenseInfo


class LicenseInfoDialog(QDialog):
    def __init__(self, lic: LicenseInfo, parent=None):
        super().__init__(parent)

        self.setWindowTitle("License Information")
        self.resize(420, 260)

        layout = QVBoxLayout(self)

        title = QLabel("License Information")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)

        def add_row(row: int, label: str, value: str):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel(value)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)

        add_row(0, "License type:", lic.license_type.upper())
        add_row(1, "Company:", lic.company)
        add_row(2, "VAT / CUI:", lic.vat)
        add_row(3, "Machine ID:", lic.machine)

        if lic.expires:
            add_row(4, "Expires:", lic.expires)
            add_row(5, "Status:", "ACTIVE" if lic.expires else "ACTIVE")
        else:
            add_row(4, "Expires:", "—")
            add_row(5, "Status:", "ACTIVE (Lifetime)")

        layout.addLayout(grid)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)
