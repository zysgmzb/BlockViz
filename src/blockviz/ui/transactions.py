"""Transactions explorer view with detail search."""

from __future__ import annotations

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
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont, QPalette, QColor

from ..services.rpc_client import RpcClient, RpcError, TransactionInfo
from .styles import SUBTLE_TEXT_COLOR
from .widgets.info_card import InfoCard
from .widgets.detail_section import DetailSection


class TransactionsView(QWidget):
    """Displays transaction details for a given hash."""

    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: RpcClient | None = None
        self._summary_cards: list[InfoCard] = []
        self._overview_section = DetailSection("Overview")
        self._fees_section = DetailSection("Fees & Gas")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Transactions")
        header.setStyleSheet("font-size: 24px; font-weight: 700; color: white;")
        layout.addWidget(header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter transaction hash")
        search_row.addWidget(self.search_input, 4)

        self.search_button = QPushButton("Search Tx")
        self.search_button.clicked.connect(self._handle_local_search)
        search_row.addWidget(self.search_button, 1)
        layout.addLayout(search_row)

        self.feedback_label = QLabel("Connect RPC and input a tx hash to display details.")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setFixedHeight(36)
        self.feedback_label.setStyleSheet(f"color: {SUBTLE_TEXT_COLOR.name()}; font-size: 12px;")
        layout.addWidget(self.feedback_label)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(18)
        card_defs = [
            #("Status", "N/A", "Waiting for selection", "transaction"),
            ("Value (ETH)", "N/A", "", "address"),
            ("Gas Used", "N/A", "", "gas"),
            ("Type", "N/A", "", "block"),
        ]
        for idx, (title, value, subtitle, icon_name) in enumerate(card_defs):
            card = InfoCard(title, value, subtitle, icon=icon_name)
            cards_layout.addWidget(card, 0, idx)
            self._summary_cards.append(card)
        layout.addLayout(cards_layout)

        sections_row = QHBoxLayout()
        sections_row.setSpacing(18)
        sections_row.addWidget(self._overview_section, 1)
        sections_row.addWidget(self._fees_section, 1)
        layout.addLayout(sections_row)

        # Input Data 标题行，包含标签和复制按钮
        input_header = QHBoxLayout()
        input_header.setContentsMargins(0, 0, 0, 8)
        
        input_label = QLabel("Input Data")
        input_label.setStyleSheet("font-size: 14px; font-weight: 600; color: white;")
        input_header.addWidget(input_label)
        
        input_header.addStretch(1)
        
        # 复制按钮
        self.copy_button = QPushButton()
        self.copy_button.setFixedSize(28, 28)
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.setToolTip("Copy to clipboard")
        
        # 使用Unicode复制图标
        self.copy_button.setText("📋")  # 复制图标
        self.copy_button.setStyleSheet("""
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
        self.copy_button.clicked.connect(self._copy_input_data)
        input_header.addWidget(self.copy_button)
        
        layout.addLayout(input_header)
        
        # Input Data 文本框
        self.input_view = QPlainTextEdit()
        self.input_view.setReadOnly(True)
        #self.input_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.input_view.setMaximumHeight(160)
        self.input_view.setStyleSheet("""
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
        layout.addWidget(self.input_view)

    def _copy_input_data(self) -> None:
        """复制Input Data到剪贴板"""
        text = self.input_view.toPlainText()
        if text and text != "No input data.":
            # 使用 QApplication.clipboard() 获取剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            
            # 临时改变按钮文本显示复制成功
            original_text = self.copy_button.text()
            self.copy_button.setText("✓")
            self.copy_button.setStyleSheet("""
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
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, lambda: self._restore_copy_button(original_text))
    
    def _restore_copy_button(self, original_text: str) -> None:
        """恢复复制按钮的原始状态"""
        self.copy_button.setText(original_text)
        self.copy_button.setStyleSheet("""
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
            self.feedback_label.setText("RPC not configured. Provide an endpoint to search transactions.")
            self._set_placeholder()
            return
        self.feedback_label.setText("Ready. Enter a transaction hash.")

    def _set_placeholder(self) -> None:
        placeholders = [
            ("N/A", "Waiting for selection"),
            ("N/A", ""),
            ("N/A", ""),
        ]
        for card, (value, subtitle) in zip(self._summary_cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        self._overview_section.update_rows([("Transaction", "No transaction selected")])
        self._fees_section.update_rows([])
        self.input_view.clear()

    def _handle_local_search(self) -> None:
        tx_hash = self.search_input.text().strip()
        if tx_hash:
            self.show_transaction(tx_hash)

    def show_transaction(self, tx_hash: str) -> None:
        if not self._rpc_client:
            self.feedback_label.setText("RPC not configured. Provide an endpoint to search transactions.")
            return
        try:
            tx = self._rpc_client.get_transaction(tx_hash)
        except RpcError as exc:
            self.feedback_label.setText(f"Transaction lookup failed: {exc}")
            self._set_placeholder()
            return
        self.feedback_label.setText(f"Displaying transaction {tx.tx_hash[:14]}...")
        self._render_transaction(tx)

    def _render_transaction(self, tx: TransactionInfo) -> None:
        destination = tx.to_address or "Contract Creation"
        #tx_type = "Contract Creation" if tx.to_address is None else "Transfer"
        if tx.to_address is None:
            tx_type = "Contract Creation"
        else:
            if tx.input_data and tx.input_data != "0x":
                tx_type = "Call"
            else:
                tx_type = "Transfer"
        status = tx.status or "Pending"
        gas_used_str = f"{tx.gas_used:,}" if tx.gas_used is not None else "N/A"
        #self._summary_cards[0].update_card(value=status, subtitle=f"Block {tx.block_number}")
        self._summary_cards[0].update_card(value=f"{tx.value_eth:.8f}", subtitle="Value transferred in ETH")
        self._summary_cards[1].update_card(
            value=gas_used_str,
            subtitle=f"Gas price {tx.gas_price_gwei:.2f} gwei" if tx.gas_price_gwei else "Gas price unavailable",
        )
        self._summary_cards[2].update_card(value=tx_type, subtitle=f"Transcation Type")

        self._overview_section.update_rows(
            [
                ("Transaction Hash", tx.tx_hash),
                ("Block Number", f"{tx.block_number}"),
                ("Timestamp", tx.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")),
                #("Type", tx_type),
                ("From", tx.from_address),
                ("To", destination),
                ("Nonce", str(tx.nonce)),
            ]
        )
        fee_rows = []
        if tx.gas_price_gwei is not None:
            fee_rows.append(("Gas Price", f"{tx.gas_price_gwei:.2f} gwei"))
        if tx.max_fee_gwei is not None:
            fee_rows.append(("Max Fee Per Gas", f"{tx.max_fee_gwei:.2f} gwei"))
        if tx.max_priority_gwei is not None:
            fee_rows.append(("Max Priority Fee", f"{tx.max_priority_gwei:.2f} gwei"))
        if tx.gas_used is not None:
            fee_rows.append(("Gas Used", f"{tx.gas_used:,}"))
        self._fees_section.update_rows(fee_rows)
        self.input_view.setPlainText(tx.input_data or "No input data.")