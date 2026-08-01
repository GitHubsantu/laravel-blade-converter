"""
FindReplaceDialog: a non-modal Find / Find & Replace panel wired up
to Ctrl+F and Ctrl+H, supporting Find Next, Replace, Replace All and
"Highlight all" matches in the active CodeEditor.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

import logging

log = logging.getLogger("blade_converter.find_replace")


class FindReplaceDialog(QDialog):
    def __init__(self, parent, get_editor_callable, show_replace: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Find & Replace" if show_replace else "Find")
        self.setWindowFlag(Qt.Tool, True)
        self.setModal(False)
        self._get_editor = get_editor_callable
        self._build_ui(show_replace)

    def _build_ui(self, show_replace: bool) -> None:
        layout = QVBoxLayout(self)

        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        self.find_input.returnPressed.connect(self.find_next)
        find_row.addWidget(self.find_input)
        layout.addLayout(find_row)

        self.replace_row_widget = QWidgetRow = QHBoxLayout()
        self.replace_label = QLabel("Replace:")
        self.replace_input = QLineEdit()
        QWidgetRow.addWidget(self.replace_label)
        QWidgetRow.addWidget(self.replace_input)
        layout.addLayout(QWidgetRow)

        options_row = QHBoxLayout()
        self.case_checkbox = QCheckBox("Match case")
        self.highlight_checkbox = QCheckBox("Highlight all")
        self.highlight_checkbox.toggled.connect(self.highlight_all)
        options_row.addWidget(self.case_checkbox)
        options_row.addWidget(self.highlight_checkbox)
        layout.addLayout(options_row)

        buttons_row = QHBoxLayout()
        self.find_next_btn = QPushButton("Find Next")
        self.find_next_btn.clicked.connect(self.find_next)
        buttons_row.addWidget(self.find_next_btn)

        if show_replace:
            self.replace_btn = QPushButton("Replace")
            self.replace_btn.clicked.connect(self.replace_one)
            buttons_row.addWidget(self.replace_btn)

            self.replace_all_btn = QPushButton("Replace All")
            self.replace_all_btn.clicked.connect(self.replace_all)
            buttons_row.addWidget(self.replace_all_btn)
        else:
            self.replace_label.hide()
            self.replace_input.hide()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        buttons_row.addWidget(close_btn)
        layout.addLayout(buttons_row)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setMinimumWidth(360)

    def set_replace_visible(self, visible: bool) -> None:
        self.replace_label.setVisible(visible)
        self.replace_input.setVisible(visible)
        if hasattr(self, "replace_btn"):
            self.replace_btn.setVisible(visible)
            self.replace_all_btn.setVisible(visible)
        self.setWindowTitle("Find & Replace" if visible else "Find")

    def _flags(self) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self.case_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        return flags

    def find_next(self) -> None:
        editor = self._get_editor()
        if editor is None:
            return
        query = self.find_input.text()
        if not query:
            return
        found = editor.find(query, self._flags())
        if not found:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)
            found = editor.find(query, self._flags())
        self.status_label.setText("Found" if found else "No matches found")

    def replace_one(self) -> None:
        editor = self._get_editor()
        if editor is None:
            return
        cursor = editor.textCursor()
        if cursor.hasSelectedText() and cursor.selectedText() == self.find_input.text():
            cursor.insertText(self.replace_input.text())
            editor.setTextCursor(cursor)
        self.find_next()

    def replace_all(self) -> None:
        editor = self._get_editor()
        if editor is None:
            return
        query = self.find_input.text()
        replacement = self.replace_input.text()
        if not query:
            return
        content = editor.toPlainText()
        count = content.count(query) if self.case_checkbox.isChecked() else content.lower().count(query.lower())
        if self.case_checkbox.isChecked():
            new_content = content.replace(query, replacement)
        else:
            import re
            new_content = re.sub(re.escape(query), lambda m: replacement, content, flags=re.IGNORECASE)
        editor.setPlainText(new_content)
        self.status_label.setText(f"Replaced {count} occurrence(s)")

    def highlight_all(self, enabled: bool) -> None:
        editor = self._get_editor()
        if editor is None:
            return
        if not enabled:
            editor.setExtraSelections([])
            return
        query = self.find_input.text()
        if not query:
            return
        selections = []
        cursor = QTextCursor(editor.document())
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#515c6a"))
        flags = self._flags()
        while True:
            cursor = editor.document().find(query, cursor, flags)
            if cursor.isNull():
                break
            sel = QTextEdit.ExtraSelection()
            sel.cursor = cursor
            sel.format = fmt
            selections.append(sel)
        editor.setExtraSelections(selections)
