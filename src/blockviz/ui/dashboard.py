"""Dashboard view that mirrors a blockchain explorer home page."""

from __future__ import annotations

from statistics import mean
from typing import Callable, Iterable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QAbstractItemView, QFrame, QGridLayout, QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ..services.rpc_client import BlockInfo, RpcClient, RpcError
from .async_tasks import run_in_background
from .styles import panel_surface_stylesheet, section_title_stylesheet, table_widget_stylesheet
from .widgets.info_card import InfoCard
from .widgets.search_bar import SearchBar


class DashboardView(QWidget):
    """Top-level dashboard with metrics and block feed."""

    status_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: RpcClient | None = None
        self._blocks: list[BlockInfo] = []
        self._navigate_callback: Callable[[str, str], None] | None = None
        self._load_request_id = 0
        self._load_in_flight = False
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(12)

        self._search_panel = QFrame()
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        search_layout = QVBoxLayout(self._search_panel)
        search_layout.setContentsMargins(14, 14, 14, 14)
        search_layout.setSpacing(10)

        self.search_bar = SearchBar("Search block height / tx hash / address")
        self.search_bar.search_requested.connect(self._handle_search)
        search_layout.addWidget(self.search_bar)

        root_layout.addWidget(self._search_panel)

        self._cards: list[InfoCard] = []
        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)
        cards = [
            InfoCard("Latest Block", "N/A", "", icon="block"),
            InfoCard("Avg Block Time", "N/A", "", icon="transactions"),
            InfoCard("Gas Price", "N/A", "", icon="gas"),
            InfoCard("Recent Tx Count", "N/A", "", icon="dashboard"),
        ]
        for idx, card in enumerate(cards):
            cards_layout.addWidget(card, idx // 2, idx % 2)
            self._cards.append(card)
        root_layout.addLayout(cards_layout)

        self._table_panel = QFrame()
        self._table_panel.setStyleSheet(panel_surface_stylesheet())
        table_layout = QVBoxLayout(self._table_panel)
        table_layout.setContentsMargins(14, 14, 14, 14)
        table_layout.setSpacing(10)

        self._block_header = QLabel("Recent Blocks")
        self._block_header.setStyleSheet(section_title_stylesheet())
        table_layout.addWidget(self._block_header)

        self.blocks_table = QTableWidget(0, 5, self)
        self.blocks_table.setHorizontalHeaderLabels(["Block", "Miner", "Timestamp", "Transactions", "Gas Used"])
        header_view = self.blocks_table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.Stretch)
        self.blocks_table.verticalHeader().hide()
        self.blocks_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.blocks_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.blocks_table.setFocusPolicy(Qt.StrongFocus)
        self.blocks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.blocks_table.setAlternatingRowColors(True)
        self.blocks_table.setStyleSheet(table_widget_stylesheet())
        table_layout.addWidget(self.blocks_table)

        root_layout.addWidget(self._table_panel, 1)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(20_000)
        self._refresh_timer.timeout.connect(self._refresh_if_ready)

    def refresh_theme(self) -> None:
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        self.search_bar.refresh_theme()
        for card in self._cards:
            card.refresh_theme()
        self._table_panel.setStyleSheet(panel_surface_stylesheet())
        self._block_header.setStyleSheet(section_title_stylesheet())
        self.blocks_table.setStyleSheet(table_widget_stylesheet())

    def set_navigation_handler(self, handler: Callable[[str, str], None]) -> None:
        self._navigate_callback = handler

    def set_rpc_client(self, client: RpcClient | None) -> None:
        self._rpc_client = client
        self._load_request_id += 1
        self._load_in_flight = False
        if client is None:
            self._refresh_timer.stop()
            self.status_message.emit("RPC not configured. Enter an endpoint to sync data.")
            self._clear_data()
            return
        self.status_message.emit("Loading latest on-chain data...")
        self._refresh_timer.start()
        self._load_data()

    def _clear_data(self) -> None:
        placeholders = [("N/A", ""), ("N/A", ""), ("N/A", ""), ("N/A", "")]
        for card, (value, subtitle) in zip(self._cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        self.blocks_table.setRowCount(0)
        self._blocks = []

    def _refresh_if_ready(self) -> None:
        if self._rpc_client is not None:
            self._load_data()

    def _load_data(self) -> None:
        if self._rpc_client is None or self._load_in_flight:
            return
        self._load_in_flight = True
        self._load_request_id += 1
        request_id = self._load_request_id
        endpoint = self._rpc_client.endpoint

        def fetch_dashboard_payload() -> tuple[list[BlockInfo], float]:
            client = RpcClient(endpoint)
            blocks = client.fetch_recent_blocks(count=10)
            gas_price = client.gas_price_gwei()
            return blocks, gas_price

        run_in_background(
            fetch_dashboard_payload,
            on_success=lambda payload: self._handle_dashboard_loaded(request_id, payload),
            on_error=lambda exc: self._handle_dashboard_failed(request_id, exc),
        )

    def _handle_dashboard_loaded(self, request_id: int, payload: tuple[list[BlockInfo], float]) -> None:
        if request_id != self._load_request_id:
            return
        self._load_in_flight = False
        blocks, gas_price = payload
        if not blocks:
            self._clear_data()
            self.status_message.emit("No blocks retrieved.")
            return
        self._blocks = blocks
        self._apply_metrics(blocks, gas_price)
        self._populate_blocks(blocks)
        self.status_message.emit(f"Updated from block {blocks[0].number}")

    def _handle_dashboard_failed(self, request_id: int, exc: Exception) -> None:
        if request_id != self._load_request_id:
            return
        self._load_in_flight = False
        message = str(exc)
        if isinstance(exc, RpcError):
            message = str(exc)
        self.status_message.emit(f"RPC error: {message}")
        self._clear_data()

    def _apply_metrics(self, blocks: Iterable[BlockInfo], gas_price: float) -> None:
        blocks = list(blocks)
        latest = blocks[0]
        tx_counts = sum(block.tx_count for block in blocks)
        block_time = self._average_block_time(blocks)
        metrics = [
            (f"{latest.number}", ""),
            (f"{block_time:.2f}s" if block_time else "N/A", ""),
            (f"{gas_price:.2f} gwei", ""),
            (f"{tx_counts}", ""),
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

    def _handle_search(self, query: str) -> None:
        if query.startswith("0x"):
            if len(query) == 66:
                self.status_message.emit("Opening transaction view...")
                self._navigate_to_detail("transactions", query)
                return
            if len(query) == 42:
                self.status_message.emit("Opening address view...")
                self._navigate_to_detail("address", query)
                return
            self.status_message.emit("Invalid hash/address length.")
            return
        if query.isdigit():
            self.status_message.emit("Opening block view...")
            self._navigate_to_detail("blocks", query)
            return
        self.status_message.emit("Invalid search.")

    def _navigate_to_detail(self, target: str, query: str) -> None:
        if self._navigate_callback:
            self._navigate_callback(target, query)
