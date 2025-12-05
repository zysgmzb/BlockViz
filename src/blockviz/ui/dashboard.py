"""Dashboard view that mirrors a blockchain explorer home page."""

from __future__ import annotations

from statistics import mean
from typing import Callable, Iterable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QGridLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..services.rpc_client import BlockInfo, RpcClient, RpcError
from .styles import SUBTLE_TEXT_COLOR
from .widgets.info_card import InfoCard
from .widgets.search_bar import SearchBar


class DashboardView(QWidget):
    """Top-level dashboard with metrics and block feed."""

    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: RpcClient | None = None
        self._blocks: list[BlockInfo] = []
        self._navigate_callback: Callable[[str, str], None] | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(20)

        header = QLabel("Network Overview")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: white;")
        root_layout.addWidget(header)

        self.search_bar = SearchBar("Search block height / tx hash / address")
        self.search_bar.search_requested.connect(self._handle_search)
        root_layout.addWidget(self.search_bar)

        self.search_feedback = QLabel("Select a search type and enter a keyword.")
        self.search_feedback.setStyleSheet("color: rgba(255,255,255,0.55); font-size: 12px;")
        root_layout.addWidget(self.search_feedback)

        self._cards: list[InfoCard] = []
        cards_layout = QGridLayout()
        cards_layout.setSpacing(18)
        cards = [
            InfoCard("Latest Block", "N/A", "Waiting for RPC input", icon="block"),
            InfoCard("Avg Block Time", "N/A", "Based on last 10 blocks", icon="transaction"),
            InfoCard("Gas Price", "N/A", "eth_gasPrice", icon="gas"),
            InfoCard("Recent Tx Count", "N/A", "Across the latest blocks", icon="transaction"),
        ]
        for idx, card in enumerate(cards):
            cards_layout.addWidget(card, idx // 2, idx % 2)
            self._cards.append(card)
        root_layout.addLayout(cards_layout)

        block_header = QLabel("Recent Blocks")
        block_header.setStyleSheet("font-size: 18px; font-weight: 600; color: white;")
        root_layout.addWidget(block_header)

        self.blocks_table = QTableWidget(0, 5, self)
        self.blocks_table.setHorizontalHeaderLabels(["Block", "Miner", "Timestamp", "Transactions", "Gas Used"])
        header_view = self.blocks_table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Stretch)
        self.blocks_table.verticalHeader().hide()
        self.blocks_table.setSelectionMode(QTableWidget.NoSelection)
        self.blocks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.blocks_table.setAlternatingRowColors(True)
        root_layout.addWidget(self.blocks_table)

        self.connection_hint = QLabel("Connect an RPC endpoint to load live data.")
        self.connection_hint.setStyleSheet(f"color: {SUBTLE_TEXT_COLOR.name()}; font-size: 12px;")
        root_layout.addWidget(self.connection_hint)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(20_000)
        self._refresh_timer.timeout.connect(self._refresh_if_ready)

    def set_navigation_handler(self, handler: Callable[[str, str], None]) -> None:
        self._navigate_callback = handler

    def set_rpc_client(self, client: RpcClient | None) -> None:
        self._rpc_client = client
        if client is None:
            self._refresh_timer.stop()
            self.connection_hint.setText("RPC not configured. Enter an endpoint to sync data.")
            self._clear_data()
            return
        self.connection_hint.setText("Loading latest on-chain data...")
        self._refresh_timer.start()
        QTimer.singleShot(0, self._load_data)

    def _clear_data(self) -> None:
        placeholders = [
            ("N/A", "Waiting for RPC input"),
            ("N/A", "Based on last 10 blocks"),
            ("N/A", "eth_gasPrice"),
            ("N/A", "Across the latest blocks"),
        ]
        for card, (value, subtitle) in zip(self._cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        self.blocks_table.setRowCount(0)
        self._blocks = []

    def _refresh_if_ready(self) -> None:
        if self._rpc_client is not None:
            self._load_data()

    def _load_data(self) -> None:
        if self._rpc_client is None:
            return
        try:
            blocks = self._rpc_client.fetch_recent_blocks(count=6)
            gas_price = self._rpc_client.gas_price_gwei()
        except RpcError as exc:
            self.connection_hint.setText(f"RPC error: {exc}")
            self._clear_data()
            return
        if not blocks:
            self._clear_data()
            self.connection_hint.setText("No blocks retrieved.")
            return
        self._blocks = blocks
        self._apply_metrics(blocks, gas_price)
        self._populate_blocks(blocks)
        self.connection_hint.setText(f"Updated from block {blocks[0].number}")

    def _apply_metrics(self, blocks: Iterable[BlockInfo], gas_price: float) -> None:
        blocks = list(blocks)
        latest = blocks[0]
        tx_counts = sum(block.tx_count for block in blocks)
        block_time = self._average_block_time(blocks)
        metrics = [
            (f"{latest.number}", f"Mined at {latest.timestamp.strftime('%H:%M:%S UTC')}"),
            (f"{block_time:.2f}s" if block_time else "N/A", "Average spacing (last 6 blocks)"),
            (f"{gas_price:.2f} gwei", "eth_gasPrice"),
            (f"{tx_counts}", "Transactions in latest blocks"),
        ]
        for card, (value, subtitle) in zip(self._cards, metrics, strict=False):
            card.update_card(value=value, subtitle=subtitle)

    def _average_block_time(self, blocks: list[BlockInfo]) -> float:
        if len(blocks) < 2:
            return 0.0
        deltas = []
        for first, second in zip(blocks, blocks[1:], strict=False):
            deltas.append(abs((first.timestamp - second.timestamp).total_seconds()))
        return mean(deltas) if deltas else 0.0

    def _populate_blocks(self, blocks: Iterable[BlockInfo]) -> None:
        self.blocks_table.setRowCount(0)
        for block in blocks:
            row = self.blocks_table.rowCount()
            self.blocks_table.insertRow(row)
            self.blocks_table.setItem(row, 0, QTableWidgetItem(str(block.number)))
            self.blocks_table.setItem(row, 1, QTableWidgetItem(block.miner or "N/A"))
            self.blocks_table.setItem(row, 2, QTableWidgetItem(block.timestamp.strftime("%H:%M:%S - %Y-%m-%d")))
            self.blocks_table.setItem(row, 3, QTableWidgetItem(str(block.tx_count)))
            self.blocks_table.setItem(row, 4, QTableWidgetItem(f"{block.gas_used / 1_000_000:.2f} MGas"))
        self._adjust_block_table_height()

    def _adjust_block_table_height(self) -> None:
        row_count = self.blocks_table.rowCount()
        header = self.blocks_table.horizontalHeader().height()
        row_height = self.blocks_table.verticalHeader().defaultSectionSize()
        frame = self.blocks_table.frameWidth() * 2
        height = header + row_height * row_count + frame
        self.blocks_table.setFixedHeight(height)

    def _handle_search(self, query: str) -> None:
        if not self._rpc_client:
            self.search_feedback.setText("Configure an RPC endpoint before searching.")
            return
        if query.startswith("0x"):
            if len(query) == 66:
                scope = "transaction"
            elif len(query) == 42:
                scope = "address"
            else:
                self.search_feedback.setText("Invalid hash/address length.")
                return
        else:
            if query.isdigit():
                scope = "block"
            else:
                self.search_feedback.setText("Invalid search.")
                return
        try:
            if scope == "transaction":
                tx = self._rpc_client.get_transaction(query)
                self.search_feedback.setText(
                    f"Tx {tx.tx_hash[:10]}... in block {tx.block_number} for {tx.value_eth:.6f} ETH"
                )
                self._navigate_to_detail("transactions", tx.tx_hash)
            elif scope == "block":
                block = self._rpc_client.get_block(query, full_transactions=False)
                self.search_feedback.setText(
                    f"Block {block.number} • {block.tx_count} tx • miner {block.miner[:12]}..."
                )
                self._navigate_to_detail("blocks", str(block.number))
            else:
                account = self._rpc_client.get_account(query)
                self.search_feedback.setText(
                    f"{account.address[:10]}... balance {account.balance_eth:.4f} ETH • tx count {account.tx_count}"
                )
                self._navigate_to_detail("address", account.address)
        except RpcError as exc:
            self.search_feedback.setText(f"Search failed: {exc}")

    def _navigate_to_detail(self, target: str, query: str) -> None:
        if self._navigate_callback:
            self._navigate_callback(target, query)
