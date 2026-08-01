"""
OutputConsole: bottom panel that logs "Loaded file", "Conversion
started/finished", warnings and errors, mirroring the app's logging
output for the user in real time.
"""

from __future__ import annotations

import datetime

from PySide6.QtWidgets import QPlainTextEdit


_LEVEL_COLORS = {
    "DEBUG": "#7f848e",
    "INFO": "#d4d4d4",
    "WARNING": "#e5c07b",
    "ERROR": "#f14c4c",
    "CRITICAL": "#f14c4c",
    "SUCCESS": "#89d185",
}


class OutputConsole(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self.setStyleSheet("background-color: #181818; font-family: Consolas, monospace; font-size: 12px;")

    def log(self, level: str, message: str) -> None:
        color = _LEVEL_COLORS.get(level.upper(), "#d4d4d4")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.appendHtml(
            f'<span style="color:#6a9955;">[{timestamp}]</span> '
            f'<span style="color:{color}; font-weight:bold;">{level.upper()}</span> '
            f'<span style="color:{color};">{_escape(message)}</span>'
        )
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def info(self, message: str) -> None:
        self.log("INFO", message)

    def warning(self, message: str) -> None:
        self.log("WARNING", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)

    def success(self, message: str) -> None:
        self.log("SUCCESS", message)


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
