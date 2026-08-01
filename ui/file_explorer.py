"""
FileExplorer: left-hand dock panel. Shows a filesystem tree rooted at
the currently opened project/folder (or the last opened file's
directory), supports drag & drop of ``.blade.php`` files onto the
window, and highlights the currently active file.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, Signal
from PySide6.QtWidgets import QFileSystemModel, QTreeView, QVBoxLayout, QWidget, QLabel


class FileExplorer(QWidget):
    file_activated = Signal(str)
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.current_file_label = QLabel("No file loaded")
        self.current_file_label.setStyleSheet("padding: 6px; font-weight: bold;")
        self.current_file_label.setWordWrap(True)
        layout.addWidget(self.current_file_label)

        self.model = QFileSystemModel()
        self.model.setNameFilters(["*.blade.php", "*.php", "*.html"])
        self.model.setNameFilterDisables(False)
        self.model.setRootPath(str(Path.home()))

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(Path.home())))
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self._on_double_clicked)
        layout.addWidget(self.tree)

    def set_root(self, path: str) -> None:
        self.tree.setRootIndex(self.model.index(path))

    def set_current_file(self, path: str) -> None:
        self.current_file_label.setText(Path(path).name)
        self.current_file_label.setToolTip(path)
        self.set_root(str(Path(path).parent))

    def _on_double_clicked(self, index) -> None:
        path = self.model.filePath(index)
        if Path(path).is_file():
            self.file_activated.emit(path)

    # ------------------------------------------------------------------
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        paths = [p for p in paths if p]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
