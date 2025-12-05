"""Address lookup view with explorer-style panels."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    QApplication,
)
from PySide6.QtCore import QTimer

from ..services.rpc_client import AccountInfo, RpcClient, RpcError
from .styles import SUBTLE_TEXT_COLOR
from .widgets.info_card import InfoCard


class AddressView(QWidget):
    """Showcases account lookups backed by RPC data."""

    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: RpcClient | None = None
        self._summary_cards: list[InfoCard] = []
        self._code_view = QPlainTextEdit()
        self._code_view.setReadOnly(True)
        #self._address_label = QLabel("No address selected.")
        #self._address_label.setWordWrap(True)
        #self._address_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        #self._address_label.setStyleSheet("font-family: 'Cascadia Code', 'Consolas'; font-size: 13px; color: white;")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Address")
        header.setStyleSheet("font-size: 24px; font-weight: 700; color: white;")
        layout.addWidget(header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter account address (0x...)")
        search_row.addWidget(self.search_input, 4)

        self.search_button = QPushButton("Search Address")
        self.search_button.clicked.connect(self._handle_local_search)
        search_row.addWidget(self.search_button, 1)
        layout.addLayout(search_row)

        self.feedback_label = QLabel("Connect RPC and input an address to display balances.")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setFixedHeight(36)
        self.feedback_label.setStyleSheet(f"color: {SUBTLE_TEXT_COLOR.name()}; font-size: 12px;")
        layout.addWidget(self.feedback_label)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(18)
        card_defs = [
            ("Balance (ETH)", "N/A", "", "address"),
            ("Tx Count", "N/A", "", "transaction"),
            ("Account Type", "N/A", "EOA vs Contract", "block"),
        ]
        for idx, (title, value, subtitle, icon_name) in enumerate(card_defs):
            card = InfoCard(title, value, subtitle, icon=icon_name)
            cards_layout.addWidget(card, 0, idx)
            self._summary_cards.append(card)
        layout.addLayout(cards_layout)

        #layout.addWidget(self._address_label)

        # Contract Code 标题行，包含标签和复制按钮
        code_header = QHBoxLayout()
        code_header.setContentsMargins(0, 0, 0, 8)
        
        code_label = QLabel("Contract Code")
        code_label.setStyleSheet("font-size: 14px; font-weight: 600; color: white;")
        code_header.addWidget(code_label)
        
        code_header.addStretch(1)
        
        # 复制按钮
        self.code_copy_button = QPushButton()
        self.code_copy_button.setFixedSize(28, 28)
        self.code_copy_button.setCursor(Qt.PointingHandCursor)
        self.code_copy_button.setToolTip("Copy to clipboard")
        
        # 使用Unicode复制图标
        self.code_copy_button.setText("📋")  # 复制图标
        self.code_copy_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.code_copy_button.clicked.connect(self._copy_contract_code)
        code_header.addWidget(self.code_copy_button)
        
        layout.addLayout(code_header)
        
        # Contract Code 文本框
        self._code_view.setPlaceholderText("No contract code (EOA) or RPC not set.")
        self._code_view.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                color: rgba(255, 255, 255, 0.9);
                padding: 12px;
                selection-background-color: rgba(100, 149, 237, 0.5);
            }
            QPlainTextEdit:focus {
                border: 1px solid rgba(100, 149, 237, 0.5);
            }
        """)
        layout.addWidget(self._code_view, 1)

    def _copy_contract_code(self) -> None:
        """复制Contract Code到剪贴板"""
        text = self._code_view.toPlainText()
        # 只有当有实际代码时才复制，排除占位符文本
        if text and text != "No contract code (EOA) or RPC not set." and text != "No contract bytecode (Externally Owned Account).":
            # 使用 QApplication.clipboard() 获取剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
            # 临时改变按钮文本显示复制成功
            original_text = self.code_copy_button.text()
            self.code_copy_button.setText("✓")
            self.code_copy_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(76, 175, 80, 0.2);
                    border: 1px solid rgba(76, 175, 80, 0.4);
                    border-radius: 6px;
                    color: #4CAF50;
                    font-size: 14px;
                    padding: 0;
                }
            """)
            
            # 1秒后恢复原始状态
            QTimer.singleShot(1000, lambda: self._restore_copy_button(original_text))
    
    def _restore_copy_button(self, original_text: str) -> None:
        """恢复复制按钮的原始状态"""
        self.code_copy_button.setText(original_text)
        self.code_copy_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)

    def set_rpc_client(self, client: RpcClient | None) -> None:
        self._rpc_client = client
        if client is None:
            self.feedback_label.setText("RPC not configured. Provide an endpoint to inspect addresses.")
            self._set_placeholder()
            return
        self.feedback_label.setText("Ready. Enter an address to inspect balance and nonce.")

    def _set_placeholder(self) -> None:
        placeholders = [
            ("N/A", ""),
            ("N/A", ""),
            ("N/A", "EOA vs Contract"),
        ]
        for card, (value, subtitle) in zip(self._summary_cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        #self._address_label.setText("No address selected.")
        self._code_view.clear()

    def _handle_local_search(self) -> None:
        address = self.search_input.text().strip()
        if address:
            self.show_address(address)

    def show_address(self, address: str) -> None:
        if not self._rpc_client:
            self.feedback_label.setText("RPC not configured. Provide an endpoint to inspect addresses.")
            return
        try:
            account = self._rpc_client.get_account(address)
        except RpcError as exc:
            self.feedback_label.setText(f"Address lookup failed: {exc}")
            self._set_placeholder()
            return
        try:
            code_hex = self._rpc_client.get_code(account.address)
        except RpcError as exc:
            self.feedback_label.setText(f"Address lookup failed: {exc}")
            self._set_placeholder()
            return
        account_type = "Contract" if code_hex and code_hex != "0x" else "Externally Owned Account"
        self.feedback_label.setText(f"Displaying {account.address}")
        self._render_account(account, code_hex, account_type)

    def _render_account(self, account: AccountInfo, code_hex: str, account_type: str) -> None:
        self._summary_cards[0].update_card(value=f"{account.balance_eth:.8f}", subtitle="Current balance")
        self._summary_cards[1].update_card(value=str(account.tx_count), subtitle="Transaction count / nonce")
        self._summary_cards[2].update_card(value=account_type, subtitle="")
        #self._address_label.setText(f"Address: {account.address}\nNonce: {account.tx_count}")
        if code_hex and code_hex != "0x":
            self._code_view.setPlainText(code_hex)
        else:
            self._code_view.setPlainText("No contract bytecode (Externally Owned Account).")