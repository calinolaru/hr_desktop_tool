# app.py
from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from core.license_manager import app_base_dir
from ui.main_window import MainWindow
from core.license_manager import load_and_validate_license, LicenseError
from core.machine_fingerprint import get_machine_fingerprint
from ui.style import APP_QSS


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    try:
        # asigură folder config lângă aplicație
        config_dir = app_base_dir() / "config"
        config_dir.mkdir(exist_ok=True)

        lic = load_and_validate_license()

    except LicenseError as e:
        machine_id = get_machine_fingerprint()

        # machine_id.txt LÂNGĂ EXE
        out = app_base_dir() / "machine_id.txt"

        # scrie DOAR dacă nu există
        if not out.exists():
            try:
                out.write_text(machine_id, encoding="utf-8")
            except Exception:
                pass

        QMessageBox.critical(
            None,
            "Licență lipsă / invalidă",
            f"{str(e)}\n\n"
            "Machine ID este disponibil în fișierul:\n"
            f"{out.resolve()}\n\n"
            "Trimite acest fișier furnizorului."
        )
        return  # IMPORTANT: nu continua, altfel 'lic' nu există

    w = MainWindow()
    w._license_info = lic  # type: ignore[attr-defined]
    w.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
