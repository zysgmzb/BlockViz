"""Reusable metric cards for the dashboard."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QFont
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget

from ..styles import ACCENT_COLOR, CARD_COLOR, PRIMARY_COLOR, SUBTLE_TEXT_COLOR, TEXT_COLOR
from .icons import get_icon_svg


class InfoCard(QWidget):
    """Displays a KPI-style metric with accent text."""

    def __init__(
        self, title: str, value: str, subtitle: str | None = None, *, accent: str | None = None, icon: str | None = None
    ) -> None:
        super().__init__()
        self.setObjectName("InfoCard")
        self._accent = accent or PRIMARY_COLOR.name()
        self._build_ui(title, value, subtitle, icon_name=icon)

    def _build_ui(self, title: str, value: str, subtitle: str | None, *, icon_name: str | None) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)
        self.setStyleSheet(
            f"""
            QWidget#InfoCard {{
                background-color: {CARD_COLOR.name()};
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }}
            """
        )

        header = QHBoxLayout()
        header.setSpacing(8)
        if svg := get_icon_svg(icon_name):
            icon_widget = QSvgWidget()
            icon_widget.load(QByteArray(svg.encode("utf-8")))
            icon_widget.setFixedSize(28, 28)
            header.addWidget(icon_widget)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {SUBTLE_TEXT_COLOR.name()}; font-weight: 600; letter-spacing: 0.5px;")
        header.addWidget(title_label)
        header.addStretch(1)
        layout.addLayout(header)

        value_label = QLabel(value)
        value_font = QFont("Segoe UI", 22, QFont.Bold)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {self._accent};")
        layout.addWidget(value_label)
        self._value_label = value_label

        if subtitle is not None:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setWordWrap(True)
            subtitle_label.setStyleSheet(f"color: {TEXT_COLOR.name()}; font-size: 12px; opacity: 0.8;")
            layout.addWidget(subtitle_label)
            self._subtitle_label = subtitle_label
        else:
            self._subtitle_label = None

        layout.addStretch(1)

    def update_card(self, *, value: str, subtitle: str | None = None) -> None:
        """Update the card text without rebuilding the widget."""
        self._value_label.setText(value)
        if subtitle is not None:
            if self._subtitle_label is None:
                subtitle_label = QLabel(subtitle)
                subtitle_label.setWordWrap(True)
                subtitle_label.setStyleSheet(f"color: {TEXT_COLOR.name()}; font-size: 12px; opacity: 0.8;")
                self.layout().addWidget(subtitle_label)  # type: ignore[arg-type]
                self._subtitle_label = subtitle_label
            else:
                self._subtitle_label.setText(subtitle)
