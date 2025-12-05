"""Reusable search bar with scope selector."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QPushButton, QWidget


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

        """self.scope_combo = QComboBox()
        self.scope_combo.addItem("Transaction", "transaction")
        self.scope_combo.addItem("Block", "block")
        self.scope_combo.addItem("Address", "address")
        layout.addWidget(self.scope_combo, 1)"""

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        layout.addWidget(self.input_field, 4)

        self.submit_button = QPushButton("Search")
        self.submit_button.setCursor(Qt.PointingHandCursor)
        self.submit_button.clicked.connect(self._emit_search)
        layout.addWidget(self.submit_button)

    def _emit_search(self) -> None:
        query = self.input_field.text().strip()
        if not query:
            return
        #scope = self.scope_combo.currentData(Qt.UserRole)
        self.search_requested.emit(query)
