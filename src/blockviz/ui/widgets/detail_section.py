"""Reusable section for displaying key-value details."""

from __future__ import annotations

from typing import Iterable, Sequence

from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from .. import styles


class DetailSection(QFrame):
    """Displays a titled list of key-value pairs in a card layout."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title
        self._title_label: QLabel | None = None
        self._rows: list[tuple[str, str]] = []
        self._grid = QGridLayout()
        self._grid.setColumnStretch(1, 1)
        self._grid.setHorizontalSpacing(14)
        self._grid.setVerticalSpacing(10)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        self.setStyleSheet(
            """
            QFrame {
                background: transparent;
                border: none;
            }
            """
        )

        self._title_label = QLabel(self._title.upper())
        layout.addWidget(self._title_label)
        layout.addLayout(self._grid)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        if self._title_label is not None:
            self._title_label.setStyleSheet(
                f"color: {styles.TEXT_COLOR.name()}; font-size: 12px; font-weight: 800; letter-spacing: 1px;"
            )
        if self._rows:
            self.update_rows(self._rows)

    def update_rows(self, rows: Sequence[tuple[str, str]] | Iterable[tuple[str, str]]) -> None:
        """Replace the contents with new rows."""
        self._rows = list(rows)
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for idx, (key, value) in enumerate(self._rows):
            key_label = QLabel(key.upper())
            key_label.setStyleSheet(
                f"color: {styles.SUBTLE_TEXT_COLOR.name()}; font-size: 9px; font-weight: 800; letter-spacing: 1.1px;"
            )
            value_label = QLabel(value)
            value_label.setWordWrap(True)
            value_label.setStyleSheet(
                f"color: {styles.TEXT_COLOR.name()}; font-size: 11px; font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas'; line-height: 1.3;"
            )
            self._grid.addWidget(key_label, idx, 0)
            self._grid.addWidget(value_label, idx, 1)
