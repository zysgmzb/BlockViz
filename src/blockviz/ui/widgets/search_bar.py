"""Reusable search bar with scope selector."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from ..styles import accent_button_stylesheet


class SearchBar(QWidget):
    """Includes scope selector, text input and trigger button."""

    search_requested = Signal(str)

    def __init__(self, placeholder: str = "Enter hash / address...") -> None:
        super().__init__()
        self._build_ui(placeholder)

    def _build_ui(self, placeholder: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        layout.addWidget(self.input_field, 4)

        self.submit_button = QPushButton("⌕ Search")
        self.submit_button.setCursor(Qt.PointingHandCursor)
        self.submit_button.clicked.connect(self._emit_search)
        layout.addWidget(self.submit_button)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.submit_button.setStyleSheet(accent_button_stylesheet())

    def _emit_search(self) -> None:
        query = self.input_field.text().strip()
        if not query:
            return
        self.search_requested.emit(query)
