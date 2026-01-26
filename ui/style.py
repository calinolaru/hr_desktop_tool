# ui/style.py
APP_QSS = """
QWidget {
    font-family: Segoe UI;
    font-size: 10.5pt;
}

QMainWindow {
    background: #0f1115;
}

QToolBar {
    background: #151923;
    border: none;
    padding: 6px;
    spacing: 8px;
}

QToolButton {
    background: #1e2433;
    color: #e7e9ee;
    border: 1px solid #2a3245;
    border-radius: 10px;
    padding: 8px 12px;
}

QToolButton:hover {
    background: #242c3f;
}

QToolButton:disabled {
    background: #141a25;
    color: #6b7280;
    border: 1px solid #1f2635;
}

QPushButton {
    background: #1e2433;
    color: #e7e9ee;
    border: 1px solid #2a3245;
    border-radius: 10px;
    padding: 10px 14px;
}

QPushButton:hover {
    background: #242c3f;
}

QPushButton:disabled {
    background: #141a25;
    color: #6b7280;
    border: 1px solid #1f2635;
}

QLabel {
    color: #e7e9ee;
}

QLineEdit {
    background: #121623;
    color: #e7e9ee;
    border: 1px solid #2a3245;
    border-radius: 10px;
    padding: 8px 10px;
}

QTableWidget {
    background: #0f1115;
    color: #e7e9ee;
    gridline-color: #20283a;
    border: 1px solid #20283a;
    border-radius: 12px;
}

QHeaderView::section {
    background: #151923;
    color: #cbd5e1;
    border: none;
    padding: 10px;
    font-weight: 600;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background: #24304a;
}

QStatusBar {
    background: #151923;
    color: #cbd5e1;
    border-top: 1px solid #20283a;
}
"""
