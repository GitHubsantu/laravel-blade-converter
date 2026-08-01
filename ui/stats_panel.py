"""StatsPanel: right-hand dock widget showing conversion statistics."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from core.conversion_report import ConversionReport


class StatsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._labels = {}
        layout = QFormLayout(self)
        layout.setLabelAlignment(Qt.AlignLeft)

        fields = [
            ("forms", "Forms replaced"),
            ("labels", "Labels replaced"),
            ("buttons", "Buttons replaced"),
            ("inputs", "Inputs replaced"),
            ("selects", "Selects replaced"),
            ("textareas", "Textareas replaced"),
            ("checkboxes", "Checkboxes replaced"),
            ("radios", "Radios replaced"),
            ("links", "Links replaced"),
            ("warnings", "Warnings"),
            ("total", "Total replacements"),
        ]
        for key, caption in fields:
            value_label = QLabel("0")
            value_label.setObjectName("StatValue")
            self._labels[key] = value_label
            layout.addRow(caption + ":", value_label)

    def update_report(self, report: ConversionReport) -> None:
        data = report.as_dict()
        mapping = {
            "forms": "Forms replaced",
            "labels": "Labels replaced",
            "buttons": "Buttons replaced",
            "inputs": "Inputs replaced",
            "selects": "Selects replaced",
            "textareas": "Textareas replaced",
            "checkboxes": "Checkboxes replaced",
            "radios": "Radios replaced",
            "links": "Links replaced",
            "warnings": "Warnings",
            "total": "Total replacements",
        }
        for key, report_key in mapping.items():
            self._labels[key].setText(str(data[report_key]))

    def clear(self) -> None:
        for label in self._labels.values():
            label.setText("0")
