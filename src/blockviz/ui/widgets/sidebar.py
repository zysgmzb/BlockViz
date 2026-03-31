"""Navigation sidebar with network selector."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...core.config import AppConfig
from ..styles import accent_button_stylesheet, nav_button_stylesheet, sidebar_card_stylesheet, status_pill_stylesheet
from .icons import build_icon


class Sidebar(QWidget):
    """Left-hand navigation and RPC controls."""

    network_changed = Signal(str)
    nav_selected = Signal(str)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._nav_buttons: dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setFixedWidth(244)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        brand_card = QFrame()
        brand_card.setStyleSheet(sidebar_card_stylesheet())
        brand_layout = QVBoxLayout(brand_card)
        brand_layout.setContentsMargins(16, 16, 16, 16)
        brand_layout.setSpacing(8)

        brand_row = QLabel("◈  BlockViz")
        brand_row.setStyleSheet("font-size: 22px; font-weight: 800; color: #eef2ff;")
        brand_layout.addWidget(brand_row)

        self._rpc_status = QLabel("Offline")
        self._rpc_status.setAlignment(Qt.AlignCenter)
        self._rpc_status.setStyleSheet(status_pill_stylesheet(False))
        brand_layout.addWidget(self._rpc_status, 0, Qt.AlignLeft)
        layout.addWidget(brand_card)

        rpc_card = QFrame()
        rpc_card.setStyleSheet(sidebar_card_stylesheet())
        rpc_layout = QVBoxLayout(rpc_card)
        rpc_layout.setContentsMargins(16, 16, 16, 16)
        rpc_layout.setSpacing(10)

        self.rpc_input = QLineEdit()
        self.rpc_input.setPlaceholderText("http://127.0.0.1:8545")
        if self._config.resolve_rpc():
            self.rpc_input.setText(self._config.resolve_rpc())
        rpc_layout.addWidget(self.rpc_input)

        self.rpc_apply = QPushButton("↗ Apply RPC")
        self.rpc_apply.setCursor(Qt.PointingHandCursor)
        self.rpc_apply.setStyleSheet(accent_button_stylesheet())
        self.rpc_apply.clicked.connect(self._emit_rpc_update)
        rpc_layout.addWidget(self.rpc_apply)
        layout.addWidget(rpc_card)

        nav_card = QFrame()
        nav_card.setStyleSheet(sidebar_card_stylesheet())
        nav_layout = QVBoxLayout(nav_card)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(8)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        for key, label, icon_name in (
            ("dashboard", "Dashboard", "dashboard"),
            ("transactions", "Transactions", "transactions"),
            ("blocks", "Blocks", "blocks"),
            ("address", "Address", "address"),
        ):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(46)
            button.setStyleSheet(nav_button_stylesheet())
            if icon := build_icon(icon_name, 18):
                button.setIcon(icon)
                button.setIconSize(QSize(18, 18))
            button.clicked.connect(lambda checked=False, nav_key=key: self.nav_selected.emit(nav_key))
            self._button_group.addButton(button)
            self._nav_buttons[key] = button
            nav_layout.addWidget(button)
        layout.addWidget(nav_card)
        layout.addStretch(1)

        self.set_active_nav("dashboard")

    def _emit_rpc_update(self) -> None:
        self.network_changed.emit(self.rpc_input.text())

    def set_active_nav(self, key: str) -> None:
        button = self._nav_buttons.get(key)
        if button is not None:
            button.setChecked(True)

    def set_rpc_status(self, message: str, connected: bool) -> None:
        self._rpc_status.setText(message)
        self._rpc_status.setStyleSheet(status_pill_stylesheet(connected))
