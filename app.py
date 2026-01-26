# app.py
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from core.license_manager import load_and_validate_license, LicenseError
from core.machine_fingerprint import get_machine_fingerprint
from ui.style import APP_QSS


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    try:
        lic = load_and_validate_license()
    except LicenseError as e:
        machine_id = get_machine_fingerprint()

        # 1) Print în consolă (copy-paste ușor)
        print("\n=== HR TOOL MACHINE ID ===")
        print(machine_id)
        print("==========================\n")

        # 2) Popup informativ
        QMessageBox.critical(
            None,
            "Licență",
            f"{str(e)}\n\n"
            "Machine ID (copie din consolă / terminal):\n"
            f"{machine_id}\n\n"
            "Tip: Rulează aplicația din PowerShell/CMD ca să poți copia din terminal."
        )
        return

    w = MainWindow()
    # opțional: ținem licența pe fereastră (About/status)
    w._license_info = lic  # type: ignore[attr-defined]
    w.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
