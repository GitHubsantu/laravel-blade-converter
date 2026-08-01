"""
MainWindow: assembles the full Laravel Blade Converter desktop UI --
toolbar, left file explorer, center VS-Code-like editor (Original /
Converted tabs), bottom output console, right statistics panel, find
& replace, settings, single-file and batch-folder conversion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStyle,
    QTabWidget,
    QToolBar,
    QWidget,
    QVBoxLayout,
)

from core.app_logger import get_logger, attach_gui_handler
from core.blade_formatter import BladeFormatter
from core.conversion_report import ConversionReport
from core.converter_engine import ConverterEngine
from core.file_manager import FileManager, FileManagerError

from .editor_widget import CodeEditor
from .file_explorer import FileExplorer
from .find_replace_dialog import FindReplaceDialog
from .output_console import OutputConsole
from .settings_dialog import AppSettings, SettingsDialog
from .stats_panel import StatsPanel
from .theme_manager import ThemeManager

log = get_logger("main_window")


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication, theme_manager: ThemeManager):
        super().__init__()
        self.app = app
        self.theme_manager = theme_manager
        self.settings = AppSettings()

        self.engine = ConverterEngine()
        self.formatter = BladeFormatter(indent_size=self.settings.tab_width)
        self.current_file_path: Optional[str] = None
        self.last_report: Optional[ConversionReport] = None

        self.setWindowTitle("Laravel Blade Converter")
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.resize(1400, 900)

        self._build_docks()
        self._build_central_widget()
        self._build_toolbar()
        self._build_menu()
        self._build_find_dialogs()

        attach_gui_handler(self._on_log_record)
        self.output_console.info("Laravel Blade Converter ready.")

    # ------------------------------------------------------------------
    def _build_central_widget(self) -> None:
        self.tabs = QTabWidget()
        self.original_editor = CodeEditor(dark=self.theme_manager.current == ThemeManager.DARK)
        self.converted_editor = CodeEditor(dark=self.theme_manager.current == ThemeManager.DARK)

        self.tabs.addTab(self.original_editor, "Original")
        self.tabs.addTab(self.converted_editor, "Converted")

        self.original_editor.save_requested.connect(self.save_file)
        self.converted_editor.save_requested.connect(self.save_file)
        self.original_editor.find_requested.connect(self.show_find_dialog)
        self.converted_editor.find_requested.connect(self.show_find_dialog)
        self.original_editor.find_requested.connect(lambda: None)
        self.original_editor.replace_requested.connect(self.show_replace_dialog)
        self.converted_editor.replace_requested.connect(self.show_replace_dialog)

        self.setCentralWidget(self.tabs)

    def _build_docks(self) -> None:
        # Left: file explorer
        self.file_explorer = FileExplorer()
        self.file_explorer.file_activated.connect(self.open_specific_file)
        self.file_explorer.files_dropped.connect(self._on_files_dropped)
        left_dock = QDockWidget("File Explorer", self)
        left_dock.setWidget(self.file_explorer)
        left_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.LeftDockWidgetArea, left_dock)
        self.left_dock = left_dock

        # Right: statistics
        self.stats_panel = StatsPanel()
        right_dock = QDockWidget("Statistics", self)
        right_dock.setWidget(self.stats_panel)
        right_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, right_dock)
        self.right_dock = right_dock

        # Bottom: output console
        self.output_console = OutputConsole()
        bottom_dock = QDockWidget("Output Console", self)
        bottom_dock.setWidget(self.output_console)
        bottom_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.BottomDockWidgetArea, bottom_dock)
        self.bottom_dock = bottom_dock

        self.resizeDocks([left_dock], [260], Qt.Horizontal)
        self.resizeDocks([right_dock], [260], Qt.Horizontal)
        self.resizeDocks([bottom_dock], [180], Qt.Vertical)

    def _icon(self, standard_pixmap) -> QIcon:
        return self.style().standardIcon(standard_pixmap)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        style = self.style()

        act_open = QAction(self._icon(QStyle.SP_DialogOpenButton), "Open File", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self.open_file)
        toolbar.addAction(act_open)

        act_save = QAction(self._icon(QStyle.SP_DialogSaveButton), "Save", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self.save_file)
        toolbar.addAction(act_save)

        act_save_as = QAction(self._icon(QStyle.SP_DriveFDIcon), "Save As", self)
        act_save_as.setShortcut(QKeySequence.SaveAs)
        act_save_as.triggered.connect(self.save_file_as)
        toolbar.addAction(act_save_as)

        toolbar.addSeparator()

        act_undo = QAction(self._icon(QStyle.SP_ArrowBack), "Undo", self)
        act_undo.setShortcut(QKeySequence.Undo)
        act_undo.triggered.connect(lambda: self._active_editor().undo())
        toolbar.addAction(act_undo)

        act_redo = QAction(self._icon(QStyle.SP_ArrowForward), "Redo", self)
        act_redo.setShortcut(QKeySequence.Redo)
        act_redo.triggered.connect(lambda: self._active_editor().redo())
        toolbar.addAction(act_redo)

        toolbar.addSeparator()

        act_find = QAction(self._icon(QStyle.SP_FileDialogContentsView), "Find", self)
        act_find.setShortcut(QKeySequence.Find)
        act_find.triggered.connect(self.show_find_dialog)
        toolbar.addAction(act_find)

        act_replace = QAction(self._icon(QStyle.SP_FileDialogDetailedView), "Replace", self)
        act_replace.setShortcut(QKeySequence.Replace)
        act_replace.triggered.connect(self.show_replace_dialog)
        toolbar.addAction(act_replace)

        act_find_replace = QAction(self._icon(QStyle.SP_DialogResetButton), "Find & Replace", self)
        act_find_replace.triggered.connect(self.show_replace_dialog)
        toolbar.addAction(act_find_replace)

        toolbar.addSeparator()

        act_convert = QAction(self._icon(QStyle.SP_MediaPlay), "Convert", self)
        act_convert.setShortcut("Ctrl+R")
        act_convert.triggered.connect(self.convert_current)
        toolbar.addAction(act_convert)

        toolbar.addSeparator()

        act_zoom_in = QAction(self._icon(QStyle.SP_ArrowUp), "Zoom In", self)
        act_zoom_in.setShortcut(QKeySequence.ZoomIn)
        act_zoom_in.triggered.connect(lambda: self._active_editor().zoom_in())
        toolbar.addAction(act_zoom_in)

        act_zoom_out = QAction(self._icon(QStyle.SP_ArrowDown), "Zoom Out", self)
        act_zoom_out.setShortcut(QKeySequence.ZoomOut)
        act_zoom_out.triggered.connect(lambda: self._active_editor().zoom_out())
        toolbar.addAction(act_zoom_out)

        toolbar.addSeparator()

        act_settings = QAction(self._icon(QStyle.SP_FileDialogListView), "Settings", self)
        act_settings.triggered.connect(self.open_settings)
        toolbar.addAction(act_settings)

        self.toolbar = toolbar

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("Open File...", self.open_file, QKeySequence.Open)
        file_menu.addAction("Save", self.save_file, QKeySequence.Save)
        file_menu.addAction("Save As...", self.save_file_as, QKeySequence.SaveAs)
        file_menu.addSeparator()
        file_menu.addAction("Batch Convert Folder...", self.batch_convert_folder)
        file_menu.addAction("Export Converted To...", self.export_converted)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction("Undo", lambda: self._active_editor().undo(), QKeySequence.Undo)
        edit_menu.addAction("Redo", lambda: self._active_editor().redo(), QKeySequence.Redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Find...", self.show_find_dialog, QKeySequence.Find)
        edit_menu.addAction("Find & Replace...", self.show_replace_dialog, QKeySequence.Replace)

        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction("Zoom In", lambda: self._active_editor().zoom_in(), QKeySequence.ZoomIn)
        view_menu.addAction("Zoom Out", lambda: self._active_editor().zoom_out(), QKeySequence.ZoomOut)
        view_menu.addAction("Reset Zoom", lambda: self._active_editor().reset_zoom())
        view_menu.addSeparator()
        view_menu.addAction("Toggle Dark / Light Theme", self.toggle_theme)
        view_menu.addSeparator()
        view_menu.addAction("Toggle File Explorer", self.left_dock.toggleViewAction().trigger)
        view_menu.addAction("Toggle Statistics", self.right_dock.toggleViewAction().trigger)
        view_menu.addAction("Toggle Output Console", self.bottom_dock.toggleViewAction().trigger)

        tools_menu = menu_bar.addMenu("&Tools")
        tools_menu.addAction("Convert", self.convert_current, "Ctrl+R")
        tools_menu.addAction("Settings...", self.open_settings)

        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("About", self.show_about)

    def _build_find_dialogs(self) -> None:
        self.find_dialog = FindReplaceDialog(self, self._active_editor, show_replace=False)
        self.replace_dialog = FindReplaceDialog(self, self._active_editor, show_replace=True)

    # ------------------------------------------------------------------
    # Editor helpers
    # ------------------------------------------------------------------
    def _active_editor(self) -> CodeEditor:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, CodeEditor) else self.original_editor

    def show_find_dialog(self) -> None:
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.find_input.setFocus()

    def show_replace_dialog(self) -> None:
        self.replace_dialog.show()
        self.replace_dialog.raise_()
        self.replace_dialog.find_input.setFocus()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------
    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Blade File", str(Path.home()),
            "Blade files (*.blade.php);;PHP files (*.php);;All files (*.*)",
        )
        if path:
            self.open_specific_file(path)

    def open_specific_file(self, path: str) -> None:
        try:
            content = FileManager.read_file(path)
        except FileManagerError as exc:
            self.output_console.error(str(exc))
            QMessageBox.critical(self, "Error", str(exc))
            return

        self.current_file_path = path
        self.original_editor.setPlainText(content)
        self.converted_editor.setPlainText("")
        self.file_explorer.set_current_file(path)
        self.tabs.setCurrentWidget(self.original_editor)
        self.stats_panel.clear()
        self.output_console.info(f"Loaded file: {path}")
        self.setWindowTitle(f"Laravel Blade Converter - {Path(path).name}")

    def _on_files_dropped(self, paths: list) -> None:
        blade_files = [p for p in paths if FileManager.is_blade_file(p)] or paths
        if blade_files:
            self.open_specific_file(blade_files[0])
            if len(blade_files) > 1:
                self.output_console.info(f"{len(blade_files)} files dropped; opened the first one.")

    def save_file(self) -> None:
        if not self.current_file_path:
            self.save_file_as()
            return
        self._write_to(self.current_file_path)

    def save_file_as(self) -> None:
        default = self.current_file_path or str(Path.home() / "converted.blade.php")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Blade File", default, "Blade files (*.blade.php);;All files (*.*)"
        )
        if path:
            self.current_file_path = path
            self._write_to(path)

    def export_converted(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Converted File", str(Path.home() / "converted.blade.php"),
            "Blade files (*.blade.php);;All files (*.*)",
        )
        if path:
            try:
                FileManager.write_file(path, self.converted_editor.toPlainText(), create_backup=self.settings.auto_backup)
                self.output_console.success(f"Exported converted file to: {path}")
            except Exception as exc:
                self.output_console.error(f"Export failed: {exc}")
                QMessageBox.critical(self, "Export failed", str(exc))

    def _write_to(self, path: str) -> None:
        content = self.converted_editor.toPlainText() or self.original_editor.toPlainText()
        try:
            FileManager.write_file(path, content, create_backup=self.settings.auto_backup)
            self.output_console.success(f"Saved: {path}")
        except Exception as exc:
            self.output_console.error(f"Save failed: {exc}")
            QMessageBox.critical(self, "Save failed", str(exc))

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    def convert_current(self) -> None:
        content = self.original_editor.toPlainText()
        if not content.strip():
            self.output_console.warning("Nothing to convert -- open a Blade file first.")
            return

        file_name = Path(self.current_file_path).name if self.current_file_path else "<unsaved>"
        self.output_console.info(f"Conversion started for {file_name}")
        try:
            result = self.engine.convert(content, file_name)
            output = result.converted_text
            if self.settings.auto_format_on_convert:
                output = self.formatter.format(output)
        except Exception as exc:
            log.exception("Conversion crashed")
            self.output_console.error(f"Conversion failed: {exc}")
            QMessageBox.critical(self, "Conversion failed", str(exc))
            return

        self.converted_editor.setPlainText(output)
        self.last_report = result.report
        self.stats_panel.update_report(result.report)
        for warning in result.report.warnings:
            self.output_console.warning(warning)
        self.output_console.success(
            f"Conversion finished: {result.report.total_replacements} replacement(s), "
            f"{len(result.report.warnings)} warning(s)"
        )
        self.tabs.setCurrentWidget(self.converted_editor)

    def batch_convert_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Laravel Project or Views Folder", str(Path.home()))
        if not folder:
            return

        try:
            views_dir = FileManager.find_views_directory(folder)
            files = FileManager.find_blade_files(str(views_dir))
        except FileManagerError as exc:
            self.output_console.error(str(exc))
            return

        if not files:
            self.output_console.warning(f"No .blade.php files found under {views_dir}")
            return

        self.output_console.info(f"Batch conversion started: {len(files)} file(s) under {views_dir}")
        total_report = ConversionReport()
        converted_count = 0
        skipped: list = []

        for file_path in files:
            try:
                content = FileManager.read_file(str(file_path))
                result = self.engine.convert(content, file_path.name)
                output = result.converted_text
                if self.settings.auto_format_on_convert:
                    output = self.formatter.format(output)
                FileManager.write_file(str(file_path), output, create_backup=self.settings.auto_backup)
                total_report.merge(result.report)
                converted_count += 1
                self.output_console.info(
                    f"Converted {file_path.relative_to(views_dir)} "
                    f"({result.report.total_replacements} replacement(s))"
                )
            except Exception as exc:
                skipped.append(str(file_path))
                self.output_console.error(f"Skipped {file_path}: {exc}")

        self.stats_panel.update_report(total_report)
        self.output_console.success(
            f"Batch conversion finished: {converted_count} converted, {len(skipped)} skipped, "
            f"{total_report.total_replacements} total replacement(s), {len(total_report.warnings)} warning(s)"
        )
        QMessageBox.information(
            self, "Batch Conversion Report",
            f"Converted: {converted_count}\nSkipped: {len(skipped)}\n"
            f"Total replacements: {total_report.total_replacements}\n"
            f"Warnings: {len(total_report.warnings)}\n\n"
            f"A `.bak` backup was created for every overwritten file." if self.settings.auto_backup else
            f"Converted: {converted_count}\nSkipped: {len(skipped)}\n"
            f"Total replacements: {total_report.total_replacements}\nWarnings: {len(total_report.warnings)}",
        )

    # ------------------------------------------------------------------
    # Settings / theme
    # ------------------------------------------------------------------
    def open_settings(self) -> None:
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec():
            self.settings = dialog.result_settings()
            self.formatter = BladeFormatter(indent_size=self.settings.tab_width)
            self.theme_manager.apply(self.app, self.settings.theme)
            dark = self.settings.theme == ThemeManager.DARK
            self.original_editor.set_dark(dark)
            self.converted_editor.set_dark(dark)
            for editor in (self.original_editor, self.converted_editor):
                font = editor.font()
                font.setPointSize(self.settings.font_size)
                editor.setFont(font)
            self.output_console.info("Settings updated.")

    def toggle_theme(self) -> None:
        new_theme = ThemeManager.LIGHT if self.theme_manager.current == ThemeManager.DARK else ThemeManager.DARK
        self.settings.theme = new_theme
        self.theme_manager.apply(self.app, new_theme)
        dark = new_theme == ThemeManager.DARK
        self.original_editor.set_dark(dark)
        self.converted_editor.set_dark(dark)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Laravel Blade Converter",
            "Laravel Blade Converter\n\n"
            "Converts LaravelCollective Blade syntax into native Laravel 12 Blade/HTML.\n\n"
            "Developer\n"
            "imdevops\n\n"
            "GitHub\n"
            "https://github.com/GitHubsantu\n\n"
            "Built with PySide6."
        )

    # ------------------------------------------------------------------
    def _on_log_record(self, level: str, message: str) -> None:
        # Bridge the shared Python logging output into the Output Console.
        self.output_console.log(level, message)
