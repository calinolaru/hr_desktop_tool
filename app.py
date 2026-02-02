# app.py
from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from core.license_manager import app_base_dir
from ui.main_window import MainWindow
from core.license_manager import load_and_validate_license, LicenseError
from core.machine_fingerprint import get_machine_fingerprint
from core.license_manager import days_until_expiry
from ui.style import APP_QSS
from PySide6.QtWidgets import QApplication, QMessageBox, QStyleFactory



def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet(APP_QSS)

    try:
        # asigură folder config lângă aplicație
        config_dir = app_base_dir() / "config"
        config_dir.mkdir(exist_ok=True)

        lic = load_and_validate_license()

        days_left = days_until_expiry(lic)

        if lic.license_type == "trial" and days_left is not None:
            if days_left <= 0:
                # deja expirat → n-ar trebui să ajungă aici
                pass
            elif days_left <= 1:
                QMessageBox.warning(
                    None,
                    "Licență Trial",
                    "Licența Trial expiră MÂINE.\n\n"
                    "Contactează furnizorul pentru activare."
                )
            elif days_left <= 3:
                QMessageBox.warning(
                    None,
                    "Licență Trial",
                    f"Licența Trial expiră în {days_left} zile."
                )
            elif days_left <= 7:
                QMessageBox.information(
                    None,
                    "Licență Trial",
                    f"Licența Trial expiră în {days_left} zile."
                )

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
