# app.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.style import APP_QSS


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
