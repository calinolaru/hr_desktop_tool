# app.py
from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QStyleFactory
from PySide6.QtGui import QIcon

from core.license_manager import (
    LicenseError,
    app_base_dir,
    days_until_expiry,
    load_and_validate_license,
)
from core.machine_fingerprint import get_machine_fingerprint
from core.paths import resource_path
from ui.main_window import MainWindow
from ui.style import APP_QSS


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet(APP_QSS)

    icon_path = resource_path("app.ico")
    app.setWindowIcon(QIcon(str(icon_path)))

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
                    "Licența Trial expiră în cel mult 24 de ore.\n\n"
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

        try:
            out.write_text(machine_id, encoding="utf-8")
            machine_id_details = f"Machine ID este disponibil în fișierul:\n{out.resolve()}"
        except OSError as write_error:
            machine_id_details = (
                f"Nu s-a putut salva fișierul {out}:\n{write_error}\n\n"
                f"Machine ID: {machine_id}"
            )

        QMessageBox.critical(
            None,
            "Licență lipsă / invalidă",
            f"{str(e)}\n\n"
            f"{machine_id_details}\n\n"
            "Trimite Machine ID-ul sau fișierul furnizorului."
        )
        return  # IMPORTANT: nu continua, altfel 'lic' nu există

    w = MainWindow()
    w.setWindowIcon(QIcon(str(icon_path)))
    w._license_info = lic  # type: ignore[attr-defined]
    w.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
