"""
ui/about_dialog.py

Modern, dark-themed About dialog for Laravel Blade Converter.

This module is self-contained and does not modify any existing
application logic. It only needs to be imported and invoked from
the main window's show_about() method.
"""

import os
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

# Try to import the app version from the main package if it exists.
# Falls back gracefully if APP_VERSION is not defined anywhere.
try:
    from main import APP_VERSION  # type: ignore
except Exception:
    APP_VERSION = "1.0.0"


GITHUB_URL = "https://github.com/GitHubsantu"


def resource_path(relative_path: str) -> str:
    """
    Resolve a resource path that works both when running from source
    (python main.py) and when packaged with PyInstaller (onefile/onedir).
    """
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path is None:
        # Running from source: resolve relative to the project root
        # (two levels up from this file: ui/about_dialog.py -> project root)
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
    return os.path.join(base_path, relative_path)


class AboutDialog(QDialog):
    """A modern, dark-themed, professional About dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("About - Laravel Blade Converter")
        self.setFixedSize(500, 350)
        self.setModal(True)

        # Window icon (assets/icon.ico)
        icon_path = resource_path(os.path.join("assets", "icon.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._build_ui()
        self._apply_styles()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(10)

        # --- Logo (top center) -----------------------------------------
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_pixmap = self._load_logo_pixmap()
        if logo_pixmap is not None:
            logo_label.setPixmap(logo_pixmap)
        root_layout.addWidget(logo_label)

        # --- App name -----------------------------------------------------
        name_label = QLabel("Laravel Blade Converter")
        name_label.setObjectName("appNameLabel")
        name_label.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(name_label)

        # --- Version --------------------------------------------------
        version_text = APP_VERSION if APP_VERSION else "Unknown"
        version_label = QLabel(f"Version {version_text}")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(version_label)

        # --- Description ------------------------------------------------
        description_label = QLabel(
            "Converts LaravelCollective Blade syntax into native Laravel Blade."
        )
        description_label.setObjectName("descriptionLabel")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        root_layout.addWidget(description_label)

        # --- Separator ----------------------------------------------------
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separatorLine")
        root_layout.addWidget(separator)

        # --- Developer section -------------------------------------------
        developer_title = QLabel("Developer")
        developer_title.setObjectName("developerTitleLabel")
        developer_title.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(developer_title)

        developer_name = QLabel("imdevops")
        developer_name.setObjectName("developerNameLabel")
        developer_name.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(developer_name)

        # --- GitHub link (clickable, no setOpenExternalLinks) -------------
        github_label = QLabel(f'<a href="{GITHUB_URL}">{GITHUB_URL}</a>')
        github_label.setObjectName("githubLabel")
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setTextFormat(Qt.RichText)
        github_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        github_label.setCursor(Qt.PointingHandCursor)
        # Intercept the link click manually and open via QDesktopServices.
        github_label.linkActivated.connect(self._open_github)
        root_layout.addWidget(github_label)

        # --- Copyright ------------------------------------------------
        copyright_label = QLabel("© 2026 imdevops")
        copyright_label.setObjectName("copyrightLabel")
        copyright_label.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(copyright_label)

        root_layout.addStretch(1)

        # --- Buttons ----------------------------------------------------
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        visit_github_button = QPushButton("Visit GitHub")
        visit_github_button.setObjectName("visitGithubButton")
        visit_github_button.setCursor(Qt.PointingHandCursor)
        visit_github_button.clicked.connect(self._open_github)

        close_button = QPushButton("Close")
        close_button.setObjectName("closeButton")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.close)

        button_row.addStretch(1)
        button_row.addWidget(visit_github_button)
        button_row.addWidget(close_button)
        button_row.addStretch(1)

        root_layout.addLayout(button_row)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _load_logo_pixmap(self):
        """Load assets/icon.png, falling back to assets/icon.ico, scaled to 96x96."""
        png_path = resource_path(os.path.join("assets", "icon.png"))
        ico_path = resource_path(os.path.join("assets", "icon.ico"))

        candidate_path = None
        if os.path.exists(png_path):
            candidate_path = png_path
        elif os.path.exists(ico_path):
            candidate_path = ico_path

        if candidate_path is None:
            return None

        pixmap = QPixmap(candidate_path)
        if pixmap.isNull():
            return None

        return pixmap.scaled(
            96,
            96,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

    def _open_github(self, *_args):
        """Open the GitHub URL in the user's default browser."""
        QDesktopServices.openUrl(QUrl(GITHUB_URL))

    # ------------------------------------------------------------------ #
    # Styling
    # ------------------------------------------------------------------ #
    def _apply_styles(self):
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1f26;
                border-radius: 12px;
            }

            QLabel {
                color: #e6e6e6;
                background: transparent;
            }

            #appNameLabel {
                font-size: 20pt;
                font-weight: bold;
                color: #ffffff;
            }

            #versionLabel {
                font-size: 11pt;
                color: #9aa0a6;
            }

            #descriptionLabel {
                font-size: 10pt;
                color: #c7c9cc;
                padding: 4px 10px;
            }

            #separatorLine {
                background-color: #33343d;
                max-height: 1px;
                border: none;
                margin: 6px 0px;
            }

            #developerTitleLabel {
                font-size: 10pt;
                font-weight: bold;
                color: #b6b8bd;
            }

            #developerNameLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #ffffff;
            }

            #githubLabel {
                font-size: 10pt;
            }

            #githubLabel a {
                color: #4da3ff;
                text-decoration: underline;
            }

            #copyrightLabel {
                font-size: 9pt;
                color: #7a7d85;
            }

            QPushButton {
                background-color: #2b2d36;
                color: #ffffff;
                border: 1px solid #3c3f4a;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 10pt;
            }

            QPushButton:hover {
                background-color: #363944;
                border: 1px solid #4da3ff;
            }

            QPushButton:pressed {
                background-color: #23252c;
            }

            #visitGithubButton {
                background-color: #2f6fed;
                border: 1px solid #2f6fed;
            }

            #visitGithubButton:hover {
                background-color: #4d84f5;
                border: 1px solid #4d84f5;
            }

            #visitGithubButton:pressed {
                background-color: #275ecb;
            }
            """
        )