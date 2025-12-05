"""Navigation sidebar with network selector."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from ...core.config import AppConfig
from ..styles import ACCENT_COLOR, CARD_COLOR, PRIMARY_COLOR, TEXT_COLOR


class Sidebar(QWidget):
    """Left-hand vertical navigation."""

    network_changed = Signal(str)
    nav_selected = Signal(str)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._nav_items: dict[str, QListWidgetItem] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(20)
        self.setFixedWidth(240)
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {CARD_COLOR.name()};
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }}
            QListWidget {{
                background: transparent;
                color: {TEXT_COLOR.name()};
                border: none;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 8px;
            }}
            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
            QListWidget::item:selected {{
                background-color: {PRIMARY_COLOR.name()};
            }}
            """
        )

        logo = QLabel("BlockViz")
        logo.setStyleSheet("font-size: 24px; font-weight: 800; color: white; letter-spacing: 1px; margin-bottom: 4px;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        
        tagline = QLabel("Chain Console")
        tagline.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 11px; text-transform: uppercase; letter-spacing: 1.3px; margin-bottom: 4px;")
        tagline.setAlignment(Qt.AlignCenter)
        layout.addWidget(tagline)

        # 添加一个水平分隔线
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(255,255,255,0.06); margin: 8px 0;")
        layout.addWidget(line)

        network_label = QLabel("Custom RPC URL")
        network_label.setAlignment(Qt.AlignCenter)
        network_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 600; margin-top: 8px;")
        layout.addWidget(network_label)

        # 优化文本框样式
        self.rpc_input = QLineEdit()
        self.rpc_input.setPlaceholderText("http://127.0.0.1:8545")
        self.rpc_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px 12px;
                color: {TEXT_COLOR.name()};
                font-size: 13px;
                margin: 4px 0;
            }}
            QLineEdit:focus {{
                border: 1px solid {PRIMARY_COLOR.name()};
                background-color: rgba(255, 255, 255, 0.09);
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.35);
            }}
            """
        )
        if self._config.resolve_rpc():
            self.rpc_input.setText(self._config.resolve_rpc())
        layout.addWidget(self.rpc_input)

        self.rpc_apply = QPushButton("Apply RPC")
        self.rpc_apply.setCursor(Qt.PointingHandCursor)
        self.rpc_apply.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {PRIMARY_COLOR.name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                margin: 4px 0;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_COLOR.lighter(115).name()};
            }}
            """
        )
        self.rpc_apply.clicked.connect(self._emit_rpc_update)
        layout.addWidget(self.rpc_apply)

        layout.addSpacing(12)

        self.nav_list = QListWidget()
        self.nav_list.setSelectionMode(QListWidget.SingleSelection)
        for key, label in (
            ("dashboard", "Dashboard"),
            ("transactions", "Transactions"),
            ("blocks", "Blocks"),
            ("address", "Address"),
        ):
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            item.setTextAlignment(Qt.AlignCenter)  # 居中文本
            self.nav_list.addItem(item)
            self._nav_items[key] = item
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentItemChanged.connect(self._emit_nav_change)
        layout.addWidget(self.nav_list)

        layout.addStretch(1)

        # 添加另一个分隔线
        line2 = QWidget()
        line2.setFixedHeight(1)
        line2.setStyleSheet("background-color: rgba(255,255,255,0.06); margin: 8px 0;")
        layout.addWidget(line2)

        cta_button = QPushButton("Connect Wallet")
        cta_button.setCursor(Qt.PointingHandCursor)
        cta_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_COLOR.name()};
                color: {CARD_COLOR.name()};
                font-weight: 700;
                border-radius: 8px;
                padding: 10px;
                margin-top: 8px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_COLOR.lighter(125).name()};
            }}
            """
        )
        cta_button.setEnabled(False)
        layout.addWidget(cta_button)

    def _emit_rpc_update(self) -> None:
        url = self.rpc_input.text().strip()
        self.network_changed.emit(url)

    def _emit_nav_change(self, current: QListWidgetItem | None) -> None:
        if current is not None:
            self.nav_selected.emit(current.data(Qt.UserRole))

    def set_active_nav(self, key: str) -> None:
        item = self._nav_items.get(key)
        if not item:
            return
        row = self.nav_list.row(item)
        if row != self.nav_list.currentRow():
            self.nav_list.blockSignals(True)
            self.nav_list.setCurrentRow(row)
            self.nav_list.blockSignals(False)