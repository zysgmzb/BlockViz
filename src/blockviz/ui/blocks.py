"""Blocks explorer view with detailed UI."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from ..services.rpc_client import BlockInfo, RpcClient, RpcError, TransactionInfo
from .styles import SUBTLE_TEXT_COLOR
from .widgets.info_card import InfoCard
from .widgets.detail_section import DetailSection


class BlocksView(QWidget):
    """Presents detailed block information based on direct searches."""

    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: RpcClient | None = None
        self._summary_cards: list[InfoCard] = []
        self._meta_section = DetailSection("Block Metadata")
        self._gas_section = DetailSection("Gas & Fees")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Blocks")
        header.setStyleSheet("font-size: 24px; font-weight: 700; color: white;")
        layout.addWidget(header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter block number or hash")
        search_row.addWidget(self.search_input, 4)

        self.search_button = QPushButton("Search Block")
        self.search_button.clicked.connect(self._handle_local_search)
        search_row.addWidget(self.search_button, 1)
        layout.addLayout(search_row)

        self.feedback_label = QLabel("Connect RPC and search a block to display details.")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setFixedHeight(36)
        self.feedback_label.setStyleSheet(f"color: {SUBTLE_TEXT_COLOR.name()}; font-size: 12px;")
        layout.addWidget(self.feedback_label)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(18)
        card_defs = [
            ("Block Height", "N/A", "Waiting for selection", "block"),
            ("Transactions", "N/A", "Count in block", "transaction"),
            ("Gas Usage", "N/A", "Gas used vs limit", "gas"),
        ]
        for idx, (title, value, subtitle, icon_name) in enumerate(card_defs):
            card = InfoCard(title, value, subtitle, icon=icon_name)
            cards_layout.addWidget(card, 0, idx)
            self._summary_cards.append(card)
        layout.addLayout(cards_layout)

        sections = QHBoxLayout()
        sections.setSpacing(18)
        sections.addWidget(self._meta_section, 1)
        sections.addWidget(self._gas_section, 1)
        layout.addLayout(sections)

        tx_label = QLabel("Transactions in Block")
        tx_label.setStyleSheet("font-size: 16px; font-weight: 600; color: white;")
        layout.addWidget(tx_label)

        self.tx_table = QTableWidget(0, 5, self)
        self.tx_table.setHorizontalHeaderLabels(["Tx Hash", "From", "To", "Value (ETH)", "Type"])
        header = self.tx_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.tx_table.verticalHeader().hide()
        self.tx_table.setSelectionMode(QTableWidget.NoSelection)
        self.tx_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.tx_table)

    def set_rpc_client(self, client: RpcClient | None) -> None:
        self._rpc_client = client
        if client is None:
            self.feedback_label.setText("RPC not configured. Provide an endpoint to search blocks.")
            self._set_placeholder()
            return
        self.feedback_label.setText("Ready. Enter a block height or hash.")

    def _set_placeholder(self) -> None:
        placeholders = [
            ("N/A", "Waiting for selection"),
            ("N/A", "Count in block"),
            ("N/A", "Gas used vs limit"),
        ]
        for card, (value, subtitle) in zip(self._summary_cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        self._meta_section.update_rows([("Block", "No block selected")])
        self._gas_section.update_rows([("Status", "No data")])
        self.tx_table.setRowCount(0)

    def _handle_local_search(self) -> None:
        query = self.search_input.text().strip()
        if query:
            self.show_block(query)

    def show_block(self, identifier: str) -> None:
        if not self._rpc_client:
            self.feedback_label.setText("RPC not configured. Provide an endpoint to search blocks.")
            return
        try:
            block = self._rpc_client.get_block(identifier, full_transactions=True)
        except RpcError as exc:
            self.feedback_label.setText(f"Block lookup failed: {exc}")
            self._set_placeholder()
            return
        self.feedback_label.setText(f"Displaying block {block.number}")
        self._render_block(block)

    def _render_block(self, block: BlockInfo) -> None:
        gas_ratio = block.gas_used / block.gas_limit if block.gas_limit else 0
        self._summary_cards[0].update_card(
            value=str(block.number), subtitle=block.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        self._summary_cards[1].update_card(value=str(block.tx_count), subtitle="Transactions in block")
        self._summary_cards[2].update_card(
            value=f"{block.gas_used / 1_000_000:.2f} MGas",
            subtitle=f"Limit {block.gas_limit / 1_000_000:.2f} MGas • {gas_ratio:.0%} used",
        )

        self._meta_section.update_rows(
            [
                ("Hash", block.hash),
                ("Parent Hash", block.parent_hash),
                ("Miner", block.miner or "N/A"),
                ("Timestamp", block.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")),
                ("Size", f"{block.size_bytes:,} bytes"),
            ]
        )
        base_fee = f"{block.base_fee_gwei:.2f} gwei" if block.base_fee_gwei is not None else "N/A"
        self._gas_section.update_rows(
            [
                ("Gas Used", f"{block.gas_used:,}"),
                ("Gas Limit", f"{block.gas_limit:,}"),
                ("Base Fee", base_fee),
                ("Transactions", str(block.tx_count)),
            ]
        )
        self._populate_transactions(block.transactions or [])

    def _populate_transactions(self, transactions: list[TransactionInfo]) -> None:
        self.tx_table.setRowCount(0)
        for tx in transactions:
            row = self.tx_table.rowCount()
            self.tx_table.insertRow(row)
            self.tx_table.setItem(row, 0, QTableWidgetItem(tx.tx_hash))
            self.tx_table.setItem(row, 1, QTableWidgetItem(tx.from_address or ""))
            to_display = tx.to_address or "Contract Creation"
            self.tx_table.setItem(row, 2, QTableWidgetItem(to_display))
            self.tx_table.setItem(row, 3, QTableWidgetItem(f"{tx.value_eth:.6f}"))
            #tx_type = "Contract Creation" if tx.to_address is None else "Transfer"
            if tx.to_address is None:
                tx_type = "Contract Creation"
            else:
                if tx.input_data and tx.input_data != "0x":
                    tx_type = "Call"
                else:
                    tx_type = "Transfer"
            self.tx_table.setItem(row, 4, QTableWidgetItem(tx_type))
