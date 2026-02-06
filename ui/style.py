# ui/style.py
APP_QSS = r"""
/* =========================================================
   HRTool Dark Navy (Win10/Win11 friendly)
   - selection: subtle (no purple)
   - invalid rows (red) remain visible
   - nicer scrollbars
   - checkbox column centered
========================================================= */

/* ---------- Base / Typography ---------- */
QWidget {
    font-family: "Segoe UI";
    font-size: 10.5pt;
    color: #e5e7eb;
}
QMainWindow {
    background-color: #0b1220; /* deep navy */
}

/* ---------- Toolbar ---------- */
QToolBar {
    background: #0f1a2e;
    border: none;
    padding: 6px;
    spacing: 8px;
}

/* ---------- Buttons ---------- */
QToolButton, QPushButton {
    background: #13223a;
    color: #e5e7eb;
    border: 1px solid #1f3352;
    border-radius: 10px;
    padding: 8px 12px;
}
QToolButton:hover, QPushButton:hover {
    background: #162a46;
    border-color: #2a4a7a;
}
QToolButton:pressed, QPushButton:pressed {
    background: #10223a;
}
QToolButton:disabled, QPushButton:disabled {
    background: #0f182a;
    color: #7b8596;
    border: 1px solid #1a2841;
}

/* Dropdown menu for columns */
QMenu {
    background: #0f1a2e;
    color: #e5e7eb;
    border: 1px solid #1f3352;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 10px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: #162a46;
}
QMenu::separator {
    height: 1px;
    background: #1f3352;
    margin: 6px 4px;
}

/* ---------- Labels / Inputs ---------- */
QLabel { color: #e5e7eb; }

QLineEdit {
    background: #0f1a2e;
    color: #e5e7eb;
    border: 1px solid #1f3352;
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: #1d355a;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #2a4a7a;
}

/* ---------- Tabs (aligned + joined corners) ---------- */
QTabWidget::pane {
    border: 1px solid #172a44;
    border-radius: 12px;
    background: #0b1220;
    top: -1px;
}
QTabWidget::tab-bar {
    left: 8px; /* mută tab-urile spre stânga/dreapta */
}
QTabBar::tab {
    background: #0f1a2e;
    color: #cbd5e1;
    border: 1px solid #172a44;
    border-bottom: none;
    padding: 7px 12px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 6px;
    margin-top: 6px;
}
QTabBar::tab:selected {
    background: #13223a;
    color: #e5e7eb;
    border-color: #1f3352;
}
QTabBar::tab:hover {
    border-color: #2a4a7a;
}

/* ---------- Table ---------- */
QTableWidget {
    background: #07101e;
    color: #e5e7eb;
    gridline-color: #172a44;
    border: 1px solid #172a44;
    border-radius: 12px;
    selection-background-color: #10253f;  /* backup for Win */
    selection-color: #ffffff;
}
QHeaderView::section {
    background: #0f1a2e;
    color: #cbd5e1;
    border: none;
    padding: 10px;
    font-weight: 600;
}
QTableWidget::item {
    padding: 7px;
}

/* alternare subtilă (fără mov) */
QTableWidget::item:alternate {
    background: #081328;
}

/* hover subtil */
QTableWidget::item:hover {
    background: #0d1b33;
}

/* SELECTIE: subtilă (ca să vezi roșul de invalid) */
QTableWidget::item:selected {
    background: #10243e;
    color: #e5e7eb;
}

QTableWidget::item:selected:active {
    background: #122a4a;
}


/* checkbox column centering */
QTableView::indicator {
    width: 14px;
    height: 14px;
}
QTableView::indicator:unchecked {
    border: 1px solid #2a3b5c;
    background: #0b1220;
    border-radius: 3px;
}
QTableView::indicator:checked {
    border: 1px solid #2a4a7a;
    background: #2a4a7a;
    border-radius: 3px;
}

/* ---------- Scrollbars (Win10/Win11 friendly) ---------- */
QScrollBar:horizontal {
    height: 12px;
    background: #0b1220;
    border: 1px solid #162033;
    border-radius: 6px;
    margin: 0px 10px 0px 10px;
}
QScrollBar::handle:horizontal {
    background: #2b3a55;
    border: 1px solid #324363;
    border-radius: 6px;
    min-width: 40px;
}
QScrollBar::handle:horizontal:hover {
    background: #33476a;
    border-color: #3a527a;
}
QScrollBar:vertical {
    width: 12px;
    background: #0b1220;
    border: 1px solid #162033;
    border-radius: 6px;
    margin: 10px 0px 10px 0px;
}
QScrollBar::handle:vertical {
    background: #2b3a55;
    border: 1px solid #324363;
    border-radius: 6px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover {
    background: #33476a;
    border-color: #3a527a;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    width: 0px; height: 0px;
    background: transparent;
    border: none;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

/* ---------- StatusBar ---------- */
QStatusBar {
    background: #0f1a2e;
    color: #cbd5e1;
    border-top: 1px solid #172a44;
}
"""
