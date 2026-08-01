"""
BladeSyntaxHighlighter provides VS-Code-like coloring for the mixed
Blade / HTML / inline-PHP content shown in the editor: HTML tags &
attributes, Blade directives (@if, @foreach, ...), echo blocks
({{ }} / {!! !!}), Blade comments, strings and PHP variables.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Bold)
    if italic:
        f.setFontItalic(True)
    return f


class BladeSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, dark: bool = True):
        super().__init__(document)
        self._rules = []
        self._build_rules(dark)

        # Multi-line Blade comment state id
        self._comment_state = 1

    def _build_rules(self, dark: bool) -> None:
        tag_color = "#569cd6" if dark else "#0000ff"
        attr_color = "#9cdcfe" if dark else "#994500"
        string_color = "#ce9178" if dark else "#a31515"
        directive_color = "#c586c0" if dark else "#af00db"
        echo_color = "#4ec9b0" if dark else "#267f99"
        comment_color = "#6a9955" if dark else "#008000"
        variable_color = "#9cdcfe" if dark else "#001080"
        number_color = "#b5cea8" if dark else "#098658"

        self._rules = [
            (QRegularExpression(r"</?[a-zA-Z][a-zA-Z0-9:-]*"), _fmt(tag_color, bold=True)),
            (QRegularExpression(r"\b[a-zA-Z-]+(?==)"), _fmt(attr_color)),
            (QRegularExpression(r'"[^"]*"'), _fmt(string_color)),
            (QRegularExpression(r"'[^']*'"), _fmt(string_color)),
            (QRegularExpression(r"@\w+"), _fmt(directive_color, bold=True)),
            (QRegularExpression(r"\$[a-zA-Z_][a-zA-Z0-9_]*"), _fmt(variable_color)),
            (QRegularExpression(r"\b\d+\.?\d*\b"), _fmt(number_color)),
        ]
        self._echo_format = _fmt(echo_color)
        self._comment_format = _fmt(comment_color, italic=True)
        self._directive_format = _fmt(directive_color, bold=True)

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

        # {{ }} and {!! !!} echo blocks (single line, simple case)
        for m in re.finditer(r"\{\{.*?\}\}|\{!!.*?!!\}", text):
            self.setFormat(m.start(), m.end() - m.start(), self._echo_format)

        # Multi-line Blade comments {{-- ... --}}
        self.setCurrentBlockState(0)
        start_expr = "{{--"
        end_expr = "--}}"

        start_index = 0
        if self.previousBlockState() != self._comment_state:
            start_index = text.find(start_expr)

        while start_index >= 0:
            end_index = text.find(end_expr, start_index)
            if end_index == -1:
                self.setCurrentBlockState(self._comment_state)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + len(end_expr)
            self.setFormat(start_index, comment_length, self._comment_format)
            start_index = text.find(start_expr, start_index + comment_length)
