"""
FileManager centralizes all disk I/O so the GUI and batch-conversion
code paths share identical, well-logged behavior -- including the
mandatory ``filename.blade.php.bak`` safety backup created before any
file is overwritten.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from .app_logger import get_logger

log = get_logger("file_manager")


class FileManagerError(Exception):
    pass


class FileManager:
    ENCODING = "utf-8"

    @staticmethod
    def read_file(path: str) -> str:
        p = Path(path)
        if not p.exists():
            raise FileManagerError(f"File not found: {path}")
        try:
            return p.read_text(encoding=FileManager.ENCODING)
        except UnicodeDecodeError:
            log.warning("UTF-8 decode failed for %s, retrying with latin-1", path)
            return p.read_text(encoding="latin-1")

    @staticmethod
    def write_file(path: str, content: str, create_backup: bool = True) -> None:
        p = Path(path)
        if create_backup and p.exists():
            backup_path = Path(str(p) + ".bak")
            backup_path.write_bytes(p.read_bytes())
            log.info("Backup created: %s", backup_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=FileManager.ENCODING)
        log.info("Saved file: %s", path)

    @staticmethod
    def is_blade_file(path: str) -> bool:
        name = Path(path).name.lower()
        return name.endswith(".blade.php")

    @staticmethod
    def find_blade_files(root: str) -> List[Path]:
        root_path = Path(root)
        if not root_path.exists():
            raise FileManagerError(f"Directory not found: {root}")
        return sorted(root_path.rglob("*.blade.php"))

    @staticmethod
    def find_views_directory(project_root: str) -> Path:
        """Prefer resources/views if present (standard Laravel layout)."""
        candidate = Path(project_root) / "resources" / "views"
        return candidate if candidate.exists() else Path(project_root)
