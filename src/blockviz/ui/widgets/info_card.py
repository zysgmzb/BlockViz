"""Reusable metric cards for the dashboard."""

from __future__ import annotations

from PySide6.QtCore import QByteArray
from PySide6.QtGui import QFont
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget

from .. import styles
from .icons import get_icon_svg


class InfoCard(QWidget):
    """Displays a KPI-style metric with accent text."""

    def __init__(
        self, title: str, value: str, subtitle: str | None = None, *, accent: str | None = None, icon: str | None = None
    ) -> None:
        super().__init__()
        self.setObjectName("InfoCard")
        self._accent_override = accent
        self._icon_shell: QWidget | None = None
        self._title_label: QLabel | None = None
        self._subtitle_label: QLabel | None = None
        self._build_ui(title, value, subtitle, icon_name=icon)

    def _build_ui(self, title: str, value: str, subtitle: str | None, *, icon_name: str | None) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        if svg := get_icon_svg(icon_name):
            self._icon_shell = QWidget()
            self._icon_shell.setFixedSize(32, 32)
            shell_layout = QVBoxLayout(self._icon_shell)
            shell_layout.setContentsMargins(5, 5, 5, 5)
            icon_widget = QSvgWidget()
            icon_widget.load(QByteArray(svg.encode("utf-8")))
            icon_widget.setFixedSize(20, 20)
            shell_layout.addWidget(icon_widget)
            header.addWidget(self._icon_shell)
        self._title_label = QLabel(title.upper())
        header.addWidget(self._title_label)
        header.addStretch(1)
        layout.addLayout(header)

        value_label = QLabel(value)
        value_label.setFont(QFont("Inter", 20, QFont.Bold))
        layout.addWidget(value_label)
        self._value_label = value_label

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
            self._subtitle_label = subtitle_label

        layout.addStretch(1)
        self.refresh_theme()

    def refresh_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget#InfoCard {
                background: rgba(255, 255, 255, 0.02);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.035);
            }
            """
        )
        if self._icon_shell is not None:
            self._icon_shell.setStyleSheet("background: rgba(255,255,255,0.02); border: none; border-radius: 16px;")
        if self._title_label is not None:
            self._title_label.setStyleSheet(
                f"color: {styles.SUBTLE_TEXT_COLOR.name()}; font-size: 10px; font-weight: 800; letter-spacing: 1.6px;"
            )
        self._value_label.setStyleSheet(f"color: {(self._accent_override or styles.PRIMARY_COLOR.name())};")
        if self._subtitle_label is not None:
            self._subtitle_label.setStyleSheet(
                f"color: {styles.TEXT_COLOR.name()}; font-size: 12px; line-height: 1.4; opacity: 0.75;"
            )

    def update_card(self, *, value: str, subtitle: str | None = None) -> None:
        """Update the card text without rebuilding the widget."""
        self._value_label.setText(value)
        if subtitle:
            if self._subtitle_label is None:
                subtitle_label = QLabel(subtitle)
                subtitle_label.setWordWrap(True)
                self.layout().addWidget(subtitle_label)  # type: ignore[arg-type]
                self._subtitle_label = subtitle_label
            else:
                self._subtitle_label.setText(subtitle)
                self._subtitle_label.show()
        elif self._subtitle_label is not None:
            self._subtitle_label.hide()
        self.refresh_theme()
