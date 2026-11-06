# ui/main_window.py
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from PySide6.QtCore import QStandardPaths, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QToolButton,
)

from core.paths import resource_path
from core.version import APP_NAME, APP_VERSION
from core.excel_loader import load_and_validate_excel
from core.document_generator import generate_docx_for_employee, sanitize_key
from core.pdf_converter import docx_to_pdf
from core.validation_engine import parse_salary
from ui.template_fields_dialog import TemplateFieldsDialog
from ui.checkbox_delegate import CenteredCheckBoxDelegate

HARD_MANDATORY_HEADERS = {"Nume", "Prenume", "Salariu"}  # regula aplicației


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.resize(1100, 680)
        self.setWindowTitle(f"{APP_NAME} - v{APP_VERSION}")

        # --- State ---
        self._last_df = None

        self._excel_headers: list[str] = []
        self._mandatory_headers: set[str] = set()
        self._col_map: dict[str, str] = {}            # ExcelHeader -> SafePlaceholder
        self._mandatory_safe: set[str] = set()        # set of safe placeholders that are mandatory

        self._last_generated_docx_files: list[Path] = []

        # persist order
        self._column_order_key: str | None = None
        self._saved_column_order: list[str] = []

        # --- Root ---
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # --- Menu ---
        menubar = self.menuBar()
        tools_menu = menubar.addMenu("Tools")
        act_fields = tools_menu.addAction("Câmpuri template")
        act_fields.triggered.connect(self.on_show_template_fields)

        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.on_about)

        # --- Toolbar ---
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(tb)

        self.btn_import = QPushButton("Import Excel (.xlsx)")
        self.btn_import.clicked.connect(self.on_import_excel)

        self.btn_generate = QPushButton("Generează DOCX (selectate)")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self.on_generate_docx)

        self.btn_generate_pdf = QPushButton("Generează PDF")
        self.btn_generate_pdf.setEnabled(False)
        self.btn_generate_pdf.clicked.connect(self.on_generate_pdf)

        tb.addWidget(self.btn_import)
        tb.addWidget(self.btn_generate)
        tb.addWidget(self.btn_generate_pdf)

        tb.addSeparator()

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        self.lbl_counter = QLabel("Selectate: 0 / Total: 0")
        tb.addWidget(self.lbl_counter)

        tb.addSeparator()

        self.btn_select_filtered = QPushButton("Selectează filtrate")
        self.btn_select_filtered.setEnabled(False)
        self.btn_select_filtered.clicked.connect(self.on_select_filtered)
        tb.addWidget(self.btn_select_filtered)

        self.btn_select_all = QPushButton("Selectează tot")
        self.btn_select_all.setEnabled(False)
        self.btn_select_all.clicked.connect(self.on_select_all)
        tb.addWidget(self.btn_select_all)

        self.btn_select_none = QPushButton("Deselectează tot")
        self.btn_select_none.setEnabled(False)
        self.btn_select_none.clicked.connect(self.on_select_none)
        tb.addWidget(self.btn_select_none)

        # --- Tabs ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # --- Tab: Angajați ---
        people_tab = QWidget()
        people_layout = QVBoxLayout(people_tab)

        # --- Search row (wrap) - dropdown coloane + input + clear
        search_wrap = QWidget()
        search_wrap.setObjectName("SearchWrap")
        search_wrap_layout = QHBoxLayout(search_wrap)
        search_wrap_layout.setContentsMargins(8, 8, 8, 8)
        search_wrap_layout.setSpacing(8)

        lbl = QLabel("Caută:")
        search_wrap_layout.addWidget(lbl)

        # Buton "Coloane" (dropdown cu checkbox-uri)
        self.btn_columns = QToolButton()
        self.btn_columns.setText("Coloane: (niciuna)")
        self.btn_columns.setPopupMode(QToolButton.InstantPopup)

        self.columns_menu = QMenu(self)
        self.btn_columns.setMenu(self.columns_menu)
        search_wrap_layout.addWidget(self.btn_columns)

        # Input search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ex: popescu | salariu>5000 | salariu 5000-7000")
        self.search_input.textChanged.connect(self.apply_search_filter)
        search_wrap_layout.addWidget(self.search_input, 1)

        self.btn_clear_search = QPushButton("X")
        self.btn_clear_search.setFixedWidth(32)
        self.btn_clear_search.clicked.connect(lambda: self.search_input.setText(""))
        search_wrap_layout.addWidget(self.btn_clear_search)

        people_layout.addWidget(search_wrap)

        # Table (dinamic)
        self.table_people = QTableWidget(0, 0)
        self.table_people.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_people.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_people.setAlternatingRowColors(True)
        self.table_people.setShowGrid(False)
        self.table_people.verticalHeader().setVisible(False)
        self.table_people.setWordWrap(False)

        # scroll (corect PySide6)
        self.table_people.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_people.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # reorder columns
        hh = self.table_people.horizontalHeader()
        hh.setSectionsMovable(True)
        hh.sectionMoved.connect(self._on_header_section_moved)

        # contor live
        self.table_people.itemChanged.connect(self._on_people_item_changed)

        # după setările tabelului
        self.table_people.setColumnWidth(0, 70)  # un pic mai lat ca să arate bine

        # IMPORTANT: fără edit, doar check
        self.table_people.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_people.setColumnWidth(0, 70)
        self.table_people.setItemDelegateForColumn(0, CenteredCheckBoxDelegate(self.table_people, checkbox_size=14))

        people_layout.addWidget(self.table_people, 1)
        self.tabs.addTab(people_tab, "Tabel Excel")

        # Status label
        self.lbl_status = QLabel("Status: Aștept import Excel…")
        self.lbl_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.lbl_status)

        self.statusBar().showMessage("Ready")

    # ---------------------------
    # Helpers
    # ---------------------------
    def safe_name(self, s: str) -> str:
        s = (s or "").strip()
        for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            s = s.replace(ch, "-")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def doc_prefix_from_template(self, template_path: str) -> str:
        name = Path(template_path).stem
        name = re.sub(r"(template|tmpl|model)$", "", name, flags=re.IGNORECASE).strip("_- ")
        name = name.replace("-", "_").replace(" ", "_").strip("_")
        return name.title().replace("__", "_") or "Document"

    def _make_column_order_key(self, path: str, headers: list[str]) -> str:
        p = Path(path)
        base = f"{p.name}|{'|'.join(headers)}"
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def _column_order_store_path(self) -> Path:
        # lângă exe / în dev: în config
        from core.license_manager import app_base_dir
        d = app_base_dir() / "config"
        d.mkdir(exist_ok=True)
        return d / "column_order.json"

    def _load_saved_column_order(self, key: str) -> list[str]:
        store = self._column_order_store_path()
        if not store.exists():
            return []
        try:
            data = json.loads(store.read_text(encoding="utf-8"))
            return data.get(key, []) or []
        except Exception:
            return []

    def _persist_column_order(self, key: str, order: list[str]) -> None:
        store = self._column_order_store_path()
        data: dict[str, Any] = {}
        if store.exists():
            try:
                data = json.loads(store.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        data[key] = order
        store.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------------------------
    # Import
    # ---------------------------
    def on_import_excel(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Selectează fișierul Excel", "", "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            # IMPORTANT:
            # load_and_validate_excel trebuie să returneze:
            #   df, headers, mandatory_headers
            df, headers, mandatory_headers = load_and_validate_excel(path)

            self._last_df = df
            self._excel_headers = list(headers)
            self._mandatory_headers = set(mandatory_headers or [])

            # hard mandatory always
            self._mandatory_headers |= set(HARD_MANDATORY_HEADERS)

            # col map safe
            self._col_map = {h: sanitize_key(h) for h in self._excel_headers}

            # mandatory safe set
            self._mandatory_safe = {
                self._col_map[h] for h in self._mandatory_headers if h in self._col_map
            }

            # persist reorder key
            self._column_order_key = self._make_column_order_key(path, self._excel_headers)
            self._saved_column_order = self._load_saved_column_order(self._column_order_key)

            # build table columns + populate
            self._setup_people_table_columns()
            self._populate_people_table()

            # rebuild columns dropdown
            self._rebuild_columns_menu()

            # reset search
            if hasattr(self, "search_input"):
                self.search_input.setText("")

            # enable buttons
            self.btn_generate.setEnabled(len(df) > 0)
            self.btn_generate_pdf.setEnabled(False)

            self.btn_select_all.setEnabled(len(df) > 0)
            self.btn_select_none.setEnabled(len(df) > 0)
            self.btn_select_filtered.setEnabled(len(df) > 0)

        except Exception as e:
            QMessageBox.critical(self, "Eroare la import", str(e))
            return

        self.lbl_status.setText(f"Status: Import OK | Rânduri: {len(df)} | Fișier: {path}")

    def _setup_people_table_columns(self) -> None:
        """
        Col0: Export (checkbox)
        Col1: Excel Row
        Rest: TOATE coloanele Excel (în ordinea salvată dacă există)
        """
        headers = list(self._excel_headers)

        # apply saved order
        if self._saved_column_order:
            saved = [h for h in self._saved_column_order if h in headers]
            remaining = [h for h in headers if h not in saved]
            headers = saved + remaining

        self._excel_headers = headers  # actual display order

        table_headers = ["Export", "Excel Row"] + headers
        self.table_people.setColumnCount(len(table_headers))
        self.table_people.setHorizontalHeaderLabels(table_headers)

        hh = self.table_people.horizontalHeader()
        hh.setStretchLastSection(True)
        hh.setSectionsMovable(True)

        # sizing
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # rest: resize-to-contents, last stretch
        for i in range(2, len(table_headers) - 1):
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        if len(table_headers) >= 3:
            hh.setSectionResizeMode(len(table_headers) - 1, QHeaderView.Stretch)

    def _populate_people_table(self) -> None:
        if self._last_df is None:
            self.table_people.setRowCount(0)
            self._update_selection_counter()
            return

        df = self._last_df

        self.table_people.blockSignals(True)
        self.table_people.setSortingEnabled(False)
        self.table_people.setRowCount(len(df))

        for i, (_, row) in enumerate(df.iterrows()):
            excel_row = i + 2

            # Col 0: Export (UN SINGUR checkbox, state ținut în item)
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Unchecked)  # default: totul deselectat
            chk.setTextAlignment(Qt.AlignCenter)
            self.table_people.setItem(i, 0, chk)

            # Col 1: Excel Row
            it_row = QTableWidgetItem(str(excel_row))
            it_row.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            it_row.setTextAlignment(Qt.AlignCenter)
            self.table_people.setItem(i, 1, it_row)

            # Col 2..: coloanele Excel
            for j, col_name in enumerate(self._excel_headers, start=2):
                val = row.get(col_name, "")
                it = QTableWidgetItem("" if val is None else str(val))
                it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table_people.setItem(i, j, it)

        self.table_people.setSortingEnabled(True)
        self.table_people.blockSignals(False)

        self._update_selection_counter()

    # ---------------------------
    # Column reordering persist
    # ---------------------------
    def _on_header_section_moved(self, logicalIndex: int, oldVisualIndex: int, newVisualIndex: int) -> None:
        # blochează mutarea oricărei coloane în primele 2 poziții
        if logicalIndex < 2 or newVisualIndex < 2 or oldVisualIndex < 2:
            hh = self.table_people.horizontalHeader()
            hh.blockSignals(True)
            hh.moveSection(newVisualIndex, oldVisualIndex)  # revert
            hh.blockSignals(False)
            return

        self._save_current_column_order()

    def _save_current_column_order(self) -> None:
        if not self._column_order_key:
            return

        hh = self.table_people.horizontalHeader()

        visual_to_name: dict[int, str] = {}
        for logical in range(self.table_people.columnCount()):
            item = self.table_people.horizontalHeaderItem(logical)
            if not item:
                continue
            name = item.text()
            visual = hh.visualIndex(logical)
            visual_to_name[visual] = name

        ordered = [visual_to_name[v] for v in sorted(visual_to_name.keys())]
        excel_only = [x for x in ordered if x not in ("Export", "Excel Row")]

        self._persist_column_order(self._column_order_key, excel_only)
        self._saved_column_order = list(excel_only)

        # also rebuild menu to match current order
        self._rebuild_columns_menu()

    # ---------------------------
    # Search columns menu
    # ---------------------------
    def _rebuild_columns_menu(self) -> None:
        self.columns_menu.clear()

        if not self._excel_headers:
            self.btn_columns.setEnabled(False)
            self.btn_columns.setText("Coloane: (niciuna)")
            return

        self.btn_columns.setEnabled(True)

        # default: NONE selected
        for col in self._excel_headers:
            act = QAction(col, self.columns_menu)
            act.setCheckable(True)
            act.setChecked(False)
            act.toggled.connect(self._on_columns_changed)
            self.columns_menu.addAction(act)

        self._update_columns_button_text()

    def _get_salary_value(self, row_items: dict[str, str]) -> float | None:
        # încearcă să ia salariul din coloana "Salariu" (case-insensitive)
        for k, v in row_items.items():
            if k.strip().lower() == "salariu":
                return parse_salary(v)
        return None

    def _selected_search_columns(self) -> list[str]:
        if not hasattr(self, "columns_menu"):
            return []
        return [a.text() for a in self.columns_menu.actions() if a.isChecked()]

    # ---------------------------
    # Filtering (text + salary)
    # ---------------------------
    def apply_search_filter(self, text: str) -> None:
        """
        Reguli:
          - separi criteriile prin '|'
          - toate criteriile trebuie să fie adevărate (AND)
          - criteriu text: apare în ORICE coloană selectată
          - criteriu salariu:
              salariu>5000, salariu<=4500, salariu=5000
              salariu 5000-7000
        """
        t = (text or "").strip()
        clauses = [c.strip() for c in t.split("|") if c.strip()]

        # ce coloane folosim pt text search
        selected = self._selected_search_columns()
        selected_lower = {s.lower() for s in selected}

        def row_matches(r: int) -> bool:
            # construim dict header->value din tabelul vizibil (din UI)
            headers = []
            for c in range(self.table_people.columnCount()):
                h = self.table_people.horizontalHeaderItem(c)
                headers.append(h.text() if h else f"col{c}")

            row_items: dict[str, str] = {}
            for c, h in enumerate(headers):
                it = self.table_people.item(r, c)
                row_items[h] = "" if it is None else (it.text() or "")

            # coloanele de căutare (ignorăm primele 2: Export + Excel Row)
            # dacă user a selectat explicit coloane, filtrăm la alea.
            def text_haystack() -> list[str]:
                vals = []
                for c, h in enumerate(headers):
                    if c < 2:
                        continue
                    if selected_lower and h.lower() not in selected_lower:
                        continue
                    vals.append((row_items.get(h) or "").lower())
                return vals

            hay = text_haystack()
            salary_val = self._get_salary_value(row_items)

            for clause in clauses:
                low = clause.lower()

                # --- interval: "salariu 5000-7000" (acceptă și "salariu: 5000-7000")
                m_range = re.match(r"^salariu\s*[: ]\s*([0-9\., ]+)\s*-\s*([0-9\., ]+)\s*$", low)
                if m_range:
                    a = parse_salary(m_range.group(1))
                    b = parse_salary(m_range.group(2))
                    if a is None or b is None or salary_val is None:
                        return False
                    lo2, hi2 = (a, b) if a <= b else (b, a)
                    if not (lo2 <= salary_val <= hi2):
                        return False
                    continue

                # --- comparator: "salariu>=5000"
                m_cmp = re.match(r"^salariu\s*(>=|<=|=|>|<)\s*([0-9\., ]+)\s*$", low)
                if m_cmp:
                    op = m_cmp.group(1)
                    x = parse_salary(m_cmp.group(2))
                    if x is None or salary_val is None:
                        return False
                    if op == ">" and not (salary_val > x): return False
                    if op == "<" and not (salary_val < x): return False
                    if op == ">=" and not (salary_val >= x): return False
                    if op == "<=" and not (salary_val <= x): return False
                    if op == "=" and not (salary_val == x): return False
                    continue

                # --- text clause
                needle = low
                if not needle:
                    continue
                # match dacă apare în ORICE coloană selectată (sau toate dacă none selectate)
                if not any(needle in v for v in hay):
                    return False

            return True

        # aplică hide/show
        self.table_people.blockSignals(True)
        for r in range(self.table_people.rowCount()):
            hide = False
            if clauses:
                hide = not row_matches(r)
            self.table_people.setRowHidden(r, hide)
        self.table_people.blockSignals(False)

        # dacă ai counter, cheamă-l aici
        if hasattr(self, "_update_selection_counter"):
            self._update_selection_counter()

    # ---------------------------
    # Selection
    # ---------------------------
    def _set_all_checks(self, state: Qt.CheckState, *, only_visible: bool = False) -> None:
        model = self.table_people.model()
        self.table_people.blockSignals(True)
        try:
            for r in range(self.table_people.rowCount()):
                if only_visible and self.table_people.isRowHidden(r):
                    continue

                idx = model.index(r, 0)  # col 0 = checkbox
                # setData pe model => delegate vede imediat
                model.setData(idx, state, Qt.CheckStateRole)
        finally:
            self.table_people.blockSignals(False)

        # repaint + counter
        self.table_people.viewport().update()
        self._update_selection_counter()
        self._last_generated_docx_files = []
        self.btn_generate_pdf.setEnabled(False)

    def on_select_none(self) -> None:
        self._set_all_checks(Qt.Unchecked)

    def on_select_all(self) -> None:
        self._set_all_checks(Qt.Checked)

    def on_select_filtered(self) -> None:
        self._set_all_checks(Qt.Checked, only_visible=True)

    def _update_selection_counter(self) -> None:
        total = self.table_people.rowCount()
        selected = 0
        for r in range(total):
            chk = self.table_people.item(r, 0)
            if chk and chk.checkState() == Qt.Checked:
                selected += 1
        self.lbl_counter.setText(f"Selectate: {selected} / Total: {total}")

    def _on_people_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == 0:  # doar checkbox
            self._update_selection_counter()
            self._last_generated_docx_files = []
            self.btn_generate_pdf.setEnabled(False)

    # ---------------------------
    # DOCX generation
    # ---------------------------
    def _row_to_context(self, row: Any) -> tuple[dict[str, Any], set[str]]:
        """
        Context dinamic:
          - chei = SAFE placeholders (din _col_map)
          - valori = din excel (string), fallback '—' dacă lipsesc
        Returnează (ctx, missing_optional_safe)
        """
        ctx: dict[str, Any] = {}
        missing: set[str] = set()

        for excel_name in self._excel_headers:
            safe_key = self._col_map.get(excel_name, sanitize_key(excel_name))
            raw = row.get(excel_name, None)
            val = "" if raw is None else str(raw).strip()
            if not val or val.lower() in ("nan", "<na>", "none"):
                ctx[safe_key] = "—"
                missing.add(safe_key)
            else:
                ctx[safe_key] = val

        return ctx, missing

    def on_generate_docx(self) -> None:
        if self._last_df is None:
            QMessageBox.information(self, "Generare DOCX", "Mai întâi importă un fișier Excel.")
            return

        missing_headers = HARD_MANDATORY_HEADERS - set(self._excel_headers)
        if missing_headers:
            missing = ", ".join(sorted(missing_headers))
            QMessageBox.critical(
                self,
                "Coloane obligatorii lipsă",
                f"Fișierul Excel nu conține coloanele obligatorii: {missing}.",
            )
            return

        # selecția curentă (din item checkstate, NU din cellWidget)
        selected_excel_rows: set[int] = set()
        for r in range(self.table_people.rowCount()):
            item = self.table_people.item(r, 0)  # col 0 = checkbox item
            if item and item.checkState() == Qt.Checked:
                excel_row_item = self.table_people.item(r, 1)
                if excel_row_item:
                    selected_excel_rows.add(int(excel_row_item.text()))

        if not selected_excel_rows:
            QMessageBox.information(self, "Generare DOCX", "Nu ai selectat nicio persoană pentru export.")
            return

        default_template = str(resource_path("templates/contract_template.docx"))
        template_path, _ = QFileDialog.getOpenFileName(
            self, "Selectează template-ul DOCX", default_template, "Word Template (*.docx)"
        )
        if not template_path:
            return
        default_dir = getattr(self, "_last_save_dir", "") or QStandardPaths.writableLocation(
            QStandardPaths.DocumentsLocation)

        out_dir = QFileDialog.getExistingDirectory(
            self,
            "Alege unde să salvezi documentele (DOCX)",
            default_dir
        )
        if not out_dir:
            return

        # ținem minte pentru data viitoare
        self._last_save_dir = out_dir
        out_path = Path(out_dir)

        generated_files: list[Path] = []
        skipped_missing_mandatory = 0
        warnings_optional_total: set[str] = set()
        prefix = self.doc_prefix_from_template(template_path)

        # safe keys for Nume/Prenume (dacă există în excel)
        safe_nume = self._col_map.get("Nume", "Nume")
        safe_prenume = self._col_map.get("Prenume", "Prenume")

        for idx, row in self._last_df.iterrows():
            excel_row = idx + 2
            if excel_row not in selected_excel_rows:
                continue

            ctx, missing_optional = self._row_to_context(row)
            warnings_optional_total |= set(missing_optional)

            # mandatory enforcement (hard + bold)
            missing_mand = [k for k in self._mandatory_safe if ctx.get(k) == "—"]
            if missing_mand:
                skipped_missing_mandatory += 1
                continue

            raw_nume = str(ctx.get(safe_nume, "")).strip()
            raw_prenume = str(ctx.get(safe_prenume, "")).strip()

            nume = self.safe_name(raw_nume) if raw_nume and raw_nume != "—" else f"Row{excel_row}"
            prenume = self.safe_name(raw_prenume) if raw_prenume and raw_prenume != "—" else ""

            base = f"{prefix}_{nume}"
            if prenume:
                base += f"_{prenume}"

            candidate = out_path / f"{base}.docx"

            # dacă există deja, pune sufix incremental
            k = 1
            while candidate.exists():
                candidate = out_path / f"{base}_dup{k}.docx"
                k += 1

            try:
                saved = generate_docx_for_employee(
                    template_path=template_path,
                    output_dir=out_dir,
                    context=ctx,
                    filename=candidate.name
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Eroare generare DOCX",
                    f"Nu am putut genera documentul pentru rândul Excel {excel_row}.\n\n"
                    f"Eroare: {type(e).__name__}: {e}\n\n"
                    "Sugestie: folosește Tools → Câmpuri template și copiază EXACT placeholder-ele safe."
                )
                return

            generated_files.append(Path(saved))

        self._last_generated_docx_files = generated_files
        self.btn_generate_pdf.setEnabled(len(generated_files) > 0)

        QMessageBox.information(
            self,
            "Generare DOCX",
            f"Gata.\n"
            f"Generate: {len(generated_files)}\n"
            f"Sărite (mandatory lipsă): {skipped_missing_mandatory}\n"
            f"Folder: {out_dir}"
        )

        # warning optional (non blocant)
        if warnings_optional_total:
            preview = ", ".join(sorted(list(warnings_optional_total))[:12])
            more = "" if len(warnings_optional_total) <= 12 else f" (+{len(warnings_optional_total) - 12} altele)"
            QMessageBox.warning(
                self,
                "Atenție: câmpuri goale",
                "Unele coloane din Excel nu au fost completate și au fost înlocuite cu „—”.\n\n"
                f"Câmpuri (placeholdere safe): {preview}{more}"
            )

    # ---------------------------
    # PDF generation (same folder as DOCX)
    # ---------------------------
    def on_generate_pdf(self) -> None:
        files = getattr(self, "_last_generated_docx_files", None) or []
        if not files:
            QMessageBox.information(self, "PDF", "Generează mai întâi DOCX pentru selecția curentă.")
            return

        existing: list[Path] = []
        for p in files:
            pp = Path(p)
            if pp.exists():
                existing.append(pp)

        if not existing:
            QMessageBox.information(self, "PDF", "Nu găsesc documentele DOCX generate. Generează din nou DOCX.")
            return

        generated = 0
        failed_files: list[str] = []

        for docx_file in existing:
            try:
                pdf_path = docx_file.with_suffix(".pdf")  # ACELAȘI FOLDER
                docx_to_pdf(docx_file, pdf_path)
                generated += 1
            except Exception as e:
                failed_files.append(f"{docx_file.name}: {e}")

        folder = str(existing[0].parent)

        if not failed_files:
            QMessageBox.information(self, "PDF generate", f"Gata.\nPDF-uri generate: {generated}\nFolder: {folder}")
            return

        preview = "\n".join(failed_files[:8])
        more = "" if len(failed_files) <= 8 else f"\n(+{len(failed_files) - 8} altele)"
        QMessageBox.warning(
            self,
            "PDF generate (cu erori)",
            f"Gata.\nPDF-uri generate: {generated}\nEșuate: {len(failed_files)}\nFolder: {folder}\n\n"
            f"Detalii:\n{preview}{more}"
        )

    # ---------------------------
    # Tools -> Template fields
    # ---------------------------
    def on_show_template_fields(self) -> None:
        if self._last_df is None:
            QMessageBox.information(self, "Câmpuri template", "Mai întâi importă un fișier Excel.")
            return

        dlg = TemplateFieldsDialog(
            parent=self,
            excel_columns=list(self._excel_headers),
            col_map=dict(self._col_map),
            mandatory_headers=set(self._mandatory_headers),
            hard_mandatory=set(HARD_MANDATORY_HEADERS),
        )
        dlg.exec()

    # ---------------------------
    # About
    # ---------------------------
    def on_about(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        from core.version import APP_NAME, APP_VERSION, APP_COPYRIGHT

        lic = getattr(self, "_license_info", None)

        # --- helper formatări ---
        def short_date(iso: str) -> str:
            # ISO: 2026-02-02T19:59:31.359934+00:00  ->  2026-02-02
            try:
                return iso.split("T", 1)[0]
            except Exception:
                return iso

        def status_text(lic) -> str:
            expires = getattr(lic, "expires", None)
            if not expires:
                return "Nelimitată"

            try:
                from core.license_manager import days_until_expiry
                days_left = days_until_expiry(lic)
            except Exception:
                days_left = None

            if days_left is None:
                return f"Expiră la {short_date(str(expires))}"

            if days_left <= 0:
                return "Expirată"
            if days_left == 1:
                return "Expiră mâine"
            return f"{days_left} zile rămase"

        # --- construim HTML minimalist ---
        title = f"<div style='font-size:16px; font-weight:600;'>{APP_NAME}</div>"
        ver = f"<div style='color:#B8BDC7;'>Versiune: {APP_VERSION}</div>"
        copy = f"<div style='color:#B8BDC7;'>{APP_COPYRIGHT}</div>"

        if lic:
            lic_type = str(getattr(lic, "license_type", "")).upper()
            company = str(getattr(lic, "company", "")).strip() or "—"
            vat = str(getattr(lic, "vat", "")).strip() or "—"
            machine = str(getattr(lic, "machine", "")).strip()
            machine_short = (machine[:8] + "…" + machine[-6:]) if len(machine) > 16 else (machine or "—")

            issued = str(getattr(lic, "issued_at", "")).strip()
            expires = getattr(lic, "expires", None)

            issued_short = short_date(issued) if issued else "—"
            expires_short = short_date(str(expires)) if expires else "—"

            status = status_text(lic)

            license_block = f"""
            <div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.10);">
              <div style="font-weight:600; margin-bottom:6px;">Licență</div>
              <table style="width:100%; border-collapse:collapse;">
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Tip</td><td>{lic_type}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Companie</td><td>{company}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">CUI/VAT</td><td>{vat}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Machine</td><td>{machine_short}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Emisă</td><td>{issued_short}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Expiră</td><td>{expires_short}</td></tr>
                <tr><td style="padding:2px 10px 2px 0; color:#B8BDC7;">Status</td><td><b>{status}</b></td></tr>
              </table>
              <div style="margin-top:8px; color:#B8BDC7; font-size:11px;">
                Pentru suport, trimite Machine ID complet (din fișierul <b>machine_id.txt</b>)
              </div>
            </div>
            """
        else:
            license_block = """
            <div style="margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.10); color:#B8BDC7;">
              Licență: — (neîncărcată)
            </div>
            """

        html = f"""
        <div style="min-width:520px;">
          {title}
          {ver}
          {copy}
          {license_block}
        </div>
        """

        QMessageBox.information(self, "About", html)

    def _update_columns_button_text(self) -> None:
        cols = self._selected_search_columns()
        if not cols:
            self.btn_columns.setText("Coloane: (niciuna)")
            return

        shown = ", ".join(cols[:2])
        more = f" +{len(cols) - 2}" if len(cols) > 2 else ""
        self.btn_columns.setText(f"Coloane: {shown}{more}")

    def _on_columns_changed(self) -> None:
        self._update_columns_button_text()
        self.apply_search_filter(self.search_input.text())
