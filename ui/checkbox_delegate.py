# ui/checkbox_delegate.py
from __future__ import annotations

from PySide6.QtCore import Qt, QEvent, QRect
from PySide6.QtGui import QPainter, QPalette, QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QStyledItemDelegate,
    QStyle,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QApplication,
)


class CenteredCheckBoxDelegate(QStyledItemDelegate):
    """
    Un singur checkbox, centrat.
    - NU desenează checkbox-ul default Qt.
    - Toggle la click (oriunde pe celulă) + SPACE/ENTER.
    - Compatibil cu setData(CheckStateRole) din butoane (model-driven).
    """

    def __init__(self, parent=None, checkbox_size: int = 14):
        super().__init__(parent)
        self.checkbox_size = checkbox_size

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()

        # 1) background + selection, fără indicator default
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        # Scoatem indicatorul default (altfel apar 2 checkbox-uri)
        try:
            opt.features &= ~QStyleOptionViewItem.HasCheckIndicator
        except Exception:
            pass

        opt.text = ""
        opt.icon = QIcon()

        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)

        # 2) checkbox centrat
        checked = index.data(Qt.CheckStateRole) == Qt.Checked

        cb = QStyleOptionButton()
        cb.state |= QStyle.State_Enabled
        cb.state |= QStyle.State_On if checked else QStyle.State_Off

        if option.state & QStyle.State_Selected:
            cb.palette.setColor(QPalette.ButtonText, Qt.white)

        x = option.rect.x() + (option.rect.width() - self.checkbox_size) // 2
        y = option.rect.y() + (option.rect.height() - self.checkbox_size) // 2
        cb.rect = QRect(x, y, self.checkbox_size, self.checkbox_size)

        style.drawControl(QStyle.CE_CheckBox, cb, painter)
        painter.restore()

    def editorEvent(self, event, model, option, index):
        if not (index.flags() & Qt.ItemIsEnabled):
            return False
        if not (index.flags() & Qt.ItemIsUserCheckable):
            return False

        def toggle():
            current = index.data(Qt.CheckStateRole)
            new_state = Qt.Unchecked if current == Qt.Checked else Qt.Checked
            # IMPORTANT: setData pe model (nu pe item) => dataChanged => repaint
            ok = model.setData(index, new_state, Qt.CheckStateRole)
            if ok and option.widget:
                option.widget.viewport().update(option.rect)  # repaint sigur
            return ok

        # Click: toggle oriunde pe celulă (mai UX friendly)
        if event.type() == QEvent.MouseButtonRelease:
            if isinstance(event, QMouseEvent) and event.button() == Qt.LeftButton:
                return toggle()

        # Tastatură
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            return toggle()

        return False
