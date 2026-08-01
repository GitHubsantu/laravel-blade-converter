"""
ThemeManager applies a modern, VS-Code-inspired dark theme (and a
lighter alternative) to the whole QApplication via QPalette + a
targeted stylesheet.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class ThemeManager:
    DARK = "dark"
    LIGHT = "light"

    COLORS_DARK = {
        "bg": "#1e1e1e",
        "bg_alt": "#252526",
        "panel": "#252526",
        "editor_bg": "#1e1e1e",
        "sidebar": "#252526",
        "border": "#3c3c3c",
        "text": "#d4d4d4",
        "text_dim": "#9d9d9d",
        "accent": "#007acc",
        "accent_hover": "#1a8cd8",
        "selection": "#264f78",
        "current_line": "#2a2d2e",
        "console_bg": "#181818",
        "warning": "#e5c07b",
        "error": "#f14c4c",
        "success": "#89d185",
    }

    COLORS_LIGHT = {
        "bg": "#ffffff",
        "bg_alt": "#f3f3f3",
        "panel": "#f3f3f3",
        "editor_bg": "#ffffff",
        "sidebar": "#f3f3f3",
        "border": "#d0d0d0",
        "text": "#1e1e1e",
        "text_dim": "#616161",
        "accent": "#007acc",
        "accent_hover": "#1a8cd8",
        "selection": "#add6ff",
        "current_line": "#f0f0f0",
        "console_bg": "#f7f7f7",
        "warning": "#b58900",
        "error": "#d32f2f",
        "success": "#2e7d32",
    }

    def __init__(self) -> None:
        self.current = self.DARK

    def colors(self) -> dict:
        return self.COLORS_DARK if self.current == self.DARK else self.COLORS_LIGHT

    def apply(self, app: QApplication, theme: str = DARK) -> None:
        self.current = theme
        c = self.colors()
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(c["bg"]))
        palette.setColor(QPalette.WindowText, QColor(c["text"]))
        palette.setColor(QPalette.Base, QColor(c["editor_bg"]))
        palette.setColor(QPalette.AlternateBase, QColor(c["bg_alt"]))
        palette.setColor(QPalette.ToolTipBase, QColor(c["text"]))
        palette.setColor(QPalette.ToolTipText, QColor(c["text"]))
        palette.setColor(QPalette.Text, QColor(c["text"]))
        palette.setColor(QPalette.Button, QColor(c["panel"]))
        palette.setColor(QPalette.ButtonText, QColor(c["text"]))
        palette.setColor(QPalette.BrightText, QColor(c["error"]))
        palette.setColor(QPalette.Highlight, QColor(c["selection"]))
        palette.setColor(QPalette.HighlightedText, QColor(c["text"]))
        app.setPalette(palette)
        app.setStyleSheet(self._stylesheet(c))

    def _stylesheet(self, c: dict) -> str:
        return f"""
        QMainWindow {{ background-color: {c['bg']}; }}
        QWidget {{ color: {c['text']}; font-size: 13px; }}
        QToolBar {{
            background-color: {c['panel']};
            border-bottom: 1px solid {c['border']};
            spacing: 4px;
            padding: 4px;
        }}
        QToolButton {{
            background-color: transparent;
            border-radius: 4px;
            padding: 5px 8px;
            color: {c['text']};
        }}
        QToolButton:hover {{ background-color: {c['accent']}; color: white; }}
        QToolButton:pressed {{ background-color: {c['accent_hover']}; }}
        QStatusBar {{ background-color: {c['accent']}; color: white; }}
        QDockWidget {{ color: {c['text']}; titlebar-close-icon: none; }}
        QDockWidget::title {{
            background-color: {c['panel']};
            padding: 6px;
            border-bottom: 1px solid {c['border']};
        }}
        QTreeView, QListWidget {{
            background-color: {c['sidebar']};
            border: none;
            outline: none;
        }}
        QTreeView::item:selected, QListWidget::item:selected {{
            background-color: {c['selection']};
        }}
        QTabWidget::pane {{ border: 1px solid {c['border']}; top: -1px; }}
        QTabBar::tab {{
            background-color: {c['bg_alt']};
            color: {c['text_dim']};
            padding: 6px 16px;
            border: 1px solid {c['border']};
            border-bottom: none;
        }}
        QTabBar::tab:selected {{
            background-color: {c['editor_bg']};
            color: {c['text']};
            border-top: 2px solid {c['accent']};
        }}
        QPlainTextEdit, QTextEdit {{
            background-color: {c['editor_bg']};
            color: {c['text']};
            border: none;
            selection-background-color: {c['selection']};
        }}
        QLineEdit {{
            background-color: {c['bg_alt']};
            border: 1px solid {c['border']};
            border-radius: 3px;
            padding: 4px 6px;
            color: {c['text']};
        }}
        QLineEdit:focus {{ border: 1px solid {c['accent']}; }}
        QPushButton {{
            background-color: {c['bg_alt']};
            border: 1px solid {c['border']};
            border-radius: 3px;
            padding: 5px 12px;
        }}
        QPushButton:hover {{ background-color: {c['accent']}; color: white; }}
        QPushButton:default {{ background-color: {c['accent']}; color: white; border: none; }}
        QCheckBox {{ spacing: 6px; }}
        QMenuBar {{ background-color: {c['panel']}; }}
        QMenuBar::item:selected {{ background-color: {c['accent']}; color: white; }}
        QMenu {{ background-color: {c['bg_alt']}; border: 1px solid {c['border']}; }}
        QMenu::item:selected {{ background-color: {c['accent']}; color: white; }}
        QScrollBar:vertical {{ background: {c['bg']}; width: 12px; }}
        QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 24px; }}
        QScrollBar::handle:vertical:hover {{ background: {c['accent']}; }}
        QSplitter::handle {{ background-color: {c['border']}; }}
        QLabel#StatValue {{ color: {c['accent']}; font-weight: bold; font-size: 16px; }}
        """
