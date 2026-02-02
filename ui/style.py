# ui/style.py
APP_QSS = """
/* ---------------------------
   Base / Typography
---------------------------- */
QWidget {
    font-family: "Segoe UI";
    font-size: 10.5pt;
    color: #e5e7eb; /* text */
}

QMainWindow {
    background: #0b1220; /* deep navy */
}

/* ---------------------------
   Toolbar
---------------------------- */
QToolBar {
    background: #0f1a2e;
    border: none;
    padding: 6px;
    spacing: 8px;
}

QToolButton {
    background: #13223a;
    color: #e5e7eb;
    border: 1px solid #1f3352;
    border-radius: 10px;
    padding: 8px 12px;
}

QToolButton:hover {
    background: #162a46;
    border-color: #2a4a7a;
}

QToolButton:pressed {
    background: #10223a;
}

QToolButton:disabled {
    background: #0f182a;
    color: #7b8596;
    border: 1px solid #1a2841;
}

/* ---------------------------
   Buttons
---------------------------- */
QPushButton {
    background: #13223a;
    color: #e5e7eb;
    border: 1px solid #1f3352;
    border-radius: 10px;
    padding: 9px 14px;
}

QPushButton:hover {
    background: #162a46;
    border-color: #2a4a7a;
}

QPushButton:pressed {
    background: #10223a;
}

QPushButton:disabled {
    background: #0f182a;
    color: #7b8596;
    border: 1px solid #1a2841;
}

/* ---------------------------
   Labels / Inputs
---------------------------- */
QLabel {
    color: #e5e7eb;
}

QLineEdit {
    background: #0f1a2e;
    color: #e5e7eb;
    border: 1px solid #1f3352;
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: #274a7a; /* selection in text */
    selection-color: #ffffff;
}

QLineEdit:focus {
    border: 1px solid #2a4a7a;
}

/* ---------------------------
   Tabs
---------------------------- */
QTabWidget::pane {
    border: 1px solid #172a44;
    border-radius: 12px;
    background: #0b1220;
}

QTabBar::tab {
    background: #0f1a2e;
    color: #cbd5e1;
    border: 1px solid #172a44;
    border-bottom: none;
    padding: 8px 12px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 6px;
}

QTabBar::tab:selected {
    background: #13223a;
    color: #e5e7eb;
    border-color: #1f3352;
}

QTabBar::tab:hover {
    border-color: #2a4a7a;
}

/* ---------------------------
   Table
---------------------------- */
QTableWidget {
    background: #07101e;   /* darker than window to "sink" */
    color: #e5e7eb;
    gridline-color: #172a44;
    border: 1px solid #172a44;
    border-radius: 12px;
}

QHeaderView::section {
    background: #0f1a2e;
    color: #cbd5e1;
    border: none;
    padding: 10px 10px;
    font-weight: 600;
}

QTableWidget::item {
    padding: 7px;
}

/* Alternating rows (subtle) */
QTableWidget::item:alternate {
    background: #081328;
}

/* Hover on row (subtle, does NOT override invalid red much) */
QTableWidget::item:hover {
    background: #0d1b33;
}

/*
 Selection should be subtle so error rows still stand out.
 We keep it a dark blue tint, not neon/purple.
*/
QTableWidget::item:selected {
    background: #132a4a;  /* subtle navy highlight */
    color: #ffffff;
}

/* For active focus selection (Windows sometimes changes feel) */
QTableWidget::item:selected:active {
    background: #143052;
}

/* ---------------------------
   Scrollbar (optional polish)
---------------------------- */
QScrollBar:vertical {
    background: #0b1220;
    width: 12px;
    margin: 2px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: #1a2b48;
    min-height: 24px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #233a5f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ---------------------------
   StatusBar
---------------------------- */
QStatusBar {
    background: #0f1a2e;
    color: #cbd5e1;
    border-top: 1px solid #172a44;
}
"""
