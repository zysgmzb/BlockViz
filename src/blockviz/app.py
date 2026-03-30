"""Qt application bootstrap for BlockViz."""

from __future__ import annotations

import sys
from typing import TypeAlias

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from . import __version__
from .ui.main_window import MainWindow
from .ui.styles import apply_theme

AppReturnCode: TypeAlias = int


class BlockVizApplication(QApplication):
    """Encapsulates core Qt setup and theme application."""

    def __init__(self) -> None:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        super().__init__(sys.argv)
        self.setApplicationName("BlockViz")
        self.setApplicationVersion(__version__)
        self.setOrganizationName("BlockViz")
        self.setStyle("Fusion")
        apply_theme(self)
        self._main_window: MainWindow | None = None

    def run(self) -> AppReturnCode:
        """Instantiate the main window and start the event loop."""
        self._main_window = MainWindow()
        self._main_window.show()
        return self.exec()
