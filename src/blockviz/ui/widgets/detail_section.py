"""Reusable section for displaying key-value details."""

from __future__ import annotations

from typing import Iterable, Sequence

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from ..styles import CARD_COLOR, SUBTLE_TEXT_COLOR, TEXT_COLOR


class DetailSection(QFrame):
    """Displays a titled list of key-value pairs in a card layout."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title
        self._grid = QGridLayout()
        self._grid.setColumnStretch(1, 1)
        self._grid.setHorizontalSpacing(18)
        self._grid.setVerticalSpacing(10)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {CARD_COLOR.name()};
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.06);
            }}
            """
        )

        title_label = QLabel(self._title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 700; color: white; letter-spacing: 0.5px;")
        layout.addWidget(title_label)
        layout.addLayout(self._grid)

    def update_rows(self, rows: Sequence[tuple[str, str]] | Iterable[tuple[str, str]]) -> None:
        """Replace the contents with new rows."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for idx, (key, value) in enumerate(rows):
            key_label = QLabel(key)
            key_label.setStyleSheet(
                f"color: {SUBTLE_TEXT_COLOR.name()}; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;"
            )
            value_label = QLabel(value)
            value_label.setWordWrap(True)
            value_label.setStyleSheet(f"color: {TEXT_COLOR.name()}; font-family: 'Cascadia Code', 'Consolas';")
            self._grid.addWidget(key_label, idx, 0)
            self._grid.addWidget(value_label, idx, 1)
