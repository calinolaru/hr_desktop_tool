import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from ui.main_window import MainWindow


def test_search_uses_the_columns_selected_in_the_menu():
    app = QApplication.instance() or QApplication([])
    assert app is not None
    window = MainWindow()
    window._excel_headers = ["Name", "Department"]
    window._rebuild_columns_menu()

    table = window.table_people
    table.setColumnCount(4)
    table.setRowCount(2)
    table.setHorizontalHeaderLabels(["Export", "Excel Row", "Name", "Department"])
    rows = [
        ("", "1", "Alice", "HR"),
        ("", "2", "Bob", "Alice team"),
    ]
    for row_index, values in enumerate(rows):
        for column_index, value in enumerate(values):
            table.setItem(row_index, column_index, QTableWidgetItem(value))

    window.columns_menu.actions()[1].setChecked(True)
    window.apply_search_filter("Alice")

    assert table.isRowHidden(0)
    assert not table.isRowHidden(1)
    window.close()


def test_generation_rejects_missing_required_columns(monkeypatch):
    app = QApplication.instance() or QApplication([])
    assert app is not None
    window = MainWindow()
    window._last_df = object()
    window._excel_headers = ["Name"]
    messages = []
    monkeypatch.setattr(
        "ui.main_window.QMessageBox.critical",
        lambda *args: messages.append(args[-1]),
    )

    window.on_generate_docx()

    assert len(messages) == 1
    assert "Nume" in messages[0]
    assert "Prenume" in messages[0]
    assert "Salariu" in messages[0]
    window.close()
