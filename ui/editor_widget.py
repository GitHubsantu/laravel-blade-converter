"""
CodeEditor: a QPlainTextEdit subclass that provides the "professional
code editor" experience required by the spec -- line numbers, current
line highlighting, simple bracket matching, auto-indentation, zoom,
and a monospace dark-themed appearance close to VS Code.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from .syntax_highlighter import BladeSyntaxHighlighter

_MATCHING_PAIRS = {"(": ")", "[": "]", "{": "}"}
_CLOSING_CHARS = {")", "]", "}"}


class _LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):
    zoom_changed = Signal(int)
    save_requested = Signal()
    find_requested = Signal()
    replace_requested = Signal()

    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 32

    def __init__(self, parent=None, dark: bool = True):
        super().__init__(parent)
        self._base_font_size = 13
        self._font_size = self._base_font_size
        self._dark = dark

        font = QFont("Consolas, 'Cascadia Mono', 'JetBrains Mono', 'Courier New'")
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(self._font_size)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(QFontMetricsF(font).horizontalAdvance(" ") * 4)

        self._line_number_area = _LineNumberArea(self)
        self.highlighter = BladeSyntaxHighlighter(self.document(), dark=dark)
        self._bracket_selections = []

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

    # ------------------------------------------------------------------
    # Line numbers
    # ------------------------------------------------------------------
    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        space = 12 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def _update_line_number_area_width(self, _new_block_count: int = 0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def paint_line_numbers(self, event) -> None:
        painter = QPainter(self._line_number_area)
        bg = QColor("#252526") if self._dark else QColor("#f3f3f3")
        fg = QColor("#858585") if self._dark else QColor("#8a8a8a")
        current_fg = QColor("#c6c6c6") if self._dark else QColor("#3a3a3a")
        painter.fillRect(event.rect(), bg)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(current_fg if block_number == current_line else fg)
                painter.drawText(
                    0, int(top), self._line_number_area.width() - 8, self.fontMetrics().height(),
                    Qt.AlignRight, number,
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    # ------------------------------------------------------------------
    # Current line highlight + bracket matching
    # ------------------------------------------------------------------
    def _highlight_current_line(self) -> None:
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2a2d2e") if self._dark else QColor("#f0f0f0")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self._bracket_selections = self._match_brackets()
        self.setExtraSelections(extra_selections + self._bracket_selections)

    def _match_brackets(self):
        selections = []
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()
        if not text:
            return selections

        char = text[pos] if pos < len(text) else ""
        prev_char = text[pos - 1] if pos > 0 else ""

        target_pos, match_char, direction = None, None, 1
        if char in _MATCHING_PAIRS:
            target_pos, match_char, direction = pos, char, 1
        elif prev_char in _CLOSING_CHARS:
            target_pos, match_char, direction = pos - 1, prev_char, -1

        if target_pos is None:
            return selections

        open_chars = set(_MATCHING_PAIRS.keys())
        close_chars = set(_MATCHING_PAIRS.values())
        pairs = {**_MATCHING_PAIRS, **{v: k for k, v in _MATCHING_PAIRS.items()}}

        depth = 0
        i = target_pos
        if direction == 1:
            while i < len(text):
                if text[i] == match_char:
                    depth += 1
                elif text[i] == pairs.get(match_char) and text[i] in close_chars:
                    depth -= 1
                    if depth == 0:
                        selections.append(self._make_bracket_selection(target_pos))
                        selections.append(self._make_bracket_selection(i))
                        return selections
                i += 1
        else:
            while i >= 0:
                if text[i] == match_char:
                    depth += 1
                elif text[i] == pairs.get(match_char) and text[i] in open_chars:
                    depth -= 1
                    if depth == 0:
                        selections.append(self._make_bracket_selection(target_pos))
                        selections.append(self._make_bracket_selection(i))
                        return selections
                i -= 1
        return selections

    def _make_bracket_selection(self, pos: int):
        selection = QTextEdit.ExtraSelection()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#3a3d41" if self._dark else "#d0d0d0"))
        fmt.setFontWeight(QFont.Bold)
        cursor = QTextCursor(self.document())
        cursor.setPosition(pos)
        cursor.setPosition(pos + 1, QTextCursor.KeepAnchor)
        selection.cursor = cursor
        selection.format = fmt
        return selection

    # ------------------------------------------------------------------
    # Auto indentation / shortcuts / bracket auto-close
    # ------------------------------------------------------------------
    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_auto_indent()
            return
        if event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
            self.save_requested.emit()
            return
        if event.key() == Qt.Key_F and event.modifiers() & Qt.ControlModifier:
            self.find_requested.emit()
            return
        if event.key() == Qt.Key_H and event.modifiers() & Qt.ControlModifier:
            self.replace_requested.emit()
            return
        if event.modifiers() & Qt.ControlModifier and event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom_in()
            return
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Minus:
            self.zoom_out()
            return
        if event.key() in (Qt.Key_ParenRight, Qt.Key_BracketRight, Qt.Key_BraceRight):
            if self._maybe_skip_closing(event.text()):
                return
        super().keyPressEvent(event)
        if event.text() in _MATCHING_PAIRS:
            self._auto_close_pair(event.text())

    def _maybe_skip_closing(self, char: str) -> bool:
        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()
        if pos < len(text) and text[pos] == char:
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            return True
        return False

    def _auto_close_pair(self, opening: str) -> None:
        closing = _MATCHING_PAIRS.get(opening)
        if not closing:
            return
        cursor = self.textCursor()
        cursor.insertText(closing)
        cursor.movePosition(QTextCursor.Left)
        self.setTextCursor(cursor)

    def _handle_auto_indent(self) -> None:
        cursor = self.textCursor()
        block_text = cursor.block().text()
        leading_ws = ""
        for ch in block_text:
            if ch in (" ", "\t"):
                leading_ws += ch
            else:
                break

        stripped = block_text.strip()
        extra = ""
        if stripped.endswith((">", "{")) or stripped.startswith(
            ("@if", "@foreach", "@for", "@while", "@section", "@switch", "@unless")
        ):
            if not stripped.startswith(("@end", "</")):
                extra = "    "

        cursor.insertText("\n" + leading_ws + extra)
        self.setTextCursor(cursor)

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------
    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def zoom_in(self) -> None:
        self._font_size = min(self.MAX_FONT_SIZE, self._font_size + 1)
        self._apply_font_size()

    def zoom_out(self) -> None:
        self._font_size = max(self.MIN_FONT_SIZE, self._font_size - 1)
        self._apply_font_size()

    def reset_zoom(self) -> None:
        self._font_size = self._base_font_size
        self._apply_font_size()

    def _apply_font_size(self) -> None:
        font = self.font()
        font.setPointSize(self._font_size)
        self.setFont(font)
        self.setTabStopDistance(QFontMetricsF(font).horizontalAdvance(" ") * 4)
        self.zoom_changed.emit(self._font_size)

    # ------------------------------------------------------------------
    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.highlighter = BladeSyntaxHighlighter(self.document(), dark=dark)
        self._highlight_current_line()
