#!/usr/bin/env python3
"""
Laravel Blade Converter
========================
A PySide6 desktop application that converts legacy LaravelCollective
Blade syntax (Form::, Html::, link_to_route, ...) into native
Laravel 12 Blade/HTML using a proper recursive-descent parser.

Run with:
    python3 main.py
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from core.app_logger import configure_logging, get_logger
from ui.main_window import MainWindow
from ui.theme_manager import ThemeManager
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

log = get_logger("main")
app = QApplication(sys.argv)
app.setWindowIcon(QIcon("assets/icon.ico"))

def main() -> int:
    configure_logging()
    log.info("Starting Laravel Blade Converter")

    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("assets/icon.ico"))
    app.setApplicationName("Laravel Blade Converter")
    app.setOrganizationName("imdevops")

    theme_manager = ThemeManager()
    theme_manager.apply(app, ThemeManager.DARK)

    window = MainWindow(app, theme_manager)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
