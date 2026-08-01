"""SettingsDialog: theme, font size, tab width, and auto-backup toggle."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
)


@dataclass
class AppSettings:
    theme: str = "dark"
    font_size: int = 13
    tab_width: int = 4
    auto_backup: bool = True
    auto_format_on_convert: bool = True


class SettingsDialog(QDialog):
    def __init__(self, parent, settings: AppSettings):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(settings.theme)
        layout.addRow("Theme:", self.theme_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setValue(settings.font_size)
        layout.addRow("Editor font size:", self.font_size_spin)

        self.tab_width_spin = QSpinBox()
        self.tab_width_spin.setRange(2, 8)
        self.tab_width_spin.setValue(settings.tab_width)
        layout.addRow("Indent width:", self.tab_width_spin)

        self.auto_backup_check = QCheckBox("Create .bak backup before saving")
        self.auto_backup_check.setChecked(settings.auto_backup)
        layout.addRow(self.auto_backup_check)

        self.auto_format_check = QCheckBox("Beautify HTML/Blade automatically after conversion")
        self.auto_format_check.setChecked(settings.auto_format_on_convert)
        layout.addRow(self.auto_format_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def result_settings(self) -> AppSettings:
        return AppSettings(
            theme=self.theme_combo.currentText(),
            font_size=self.font_size_spin.value(),
            tab_width=self.tab_width_spin.value(),
            auto_backup=self.auto_backup_check.isChecked(),
            auto_format_on_convert=self.auto_format_check.isChecked(),
        )
