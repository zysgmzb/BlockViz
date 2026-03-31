"""Blocks explorer view with detailed UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..services.rpc_client import BlockInfo, RpcClient, RpcError, TransactionInfo
from .async_tasks import run_in_background
from .styles import (
    accent_button_stylesheet,
    inspector_nav_stylesheet,
    panel_surface_stylesheet,
    section_title_stylesheet,
    table_widget_stylesheet,
)
from .widgets.detail_section import DetailSection
from .widgets.info_card import InfoCard


class BlocksView(QWidget):
    """Presents detailed block information based on direct searches."""

    status_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: RpcClient | None = None
        self._summary_cards: list[InfoCard] = []
        self._detail_nav_items: dict[str, QListWidgetItem] = {}
        self._lookup_request_id = 0
        self._overview_section = DetailSection("Overview")
        self._header_section = DetailSection("Header & Hashes")
        self._gas_section = DetailSection("Gas & Fees")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._search_panel = QFrame()
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        search_layout = QVBoxLayout(self._search_panel)
        search_layout.setContentsMargins(12, 12, 12, 12)
        search_layout.setSpacing(8)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter block number or hash")
        search_row.addWidget(self.search_input, 4)

        self.search_button = QPushButton("⌕ Search Block")
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setStyleSheet(accent_button_stylesheet())
        self.search_button.clicked.connect(self._handle_local_search)
        search_row.addWidget(self.search_button, 1)
        search_layout.addLayout(search_row)

        layout.addWidget(self._search_panel)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(10)
        card_defs = [
            ("Block Height", "N/A", "", "block"),
            ("Transactions", "N/A", "", "transactions"),
            ("Gas Usage", "N/A", "", "gas"),
        ]
        for idx, (title_text, value, subtitle_text, icon_name) in enumerate(card_defs):
            card = InfoCard(title_text, value, subtitle_text, icon=icon_name)
            cards_layout.addWidget(card, 0, idx)
            self._summary_cards.append(card)
        layout.addLayout(cards_layout)

        self._detail_panel = QFrame()
        self._detail_panel.setStyleSheet(panel_surface_stylesheet())
        detail_layout = QVBoxLayout(self._detail_panel)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(8)

        content_row = QHBoxLayout()
        content_row.setSpacing(10)

        self._detail_nav = QListWidget()
        self._detail_nav.setFixedWidth(188)
        self._detail_nav.setSpacing(4)
        self._detail_nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._detail_nav.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._detail_nav.setWordWrap(False)
        self._detail_nav.setStyleSheet(inspector_nav_stylesheet())
        self._detail_nav.currentRowChanged.connect(self._detail_stack_row_changed)
        content_row.addWidget(self._detail_nav)

        self._detail_stack = QStackedWidget()
        content_row.addWidget(self._detail_stack, 1)

        self._register_detail_page("overview", "Overview", self._overview_section)
        self._register_detail_page("header", "Header & Hashes", self._header_section)
        self._register_detail_page("gas", "Gas & Fees", self._gas_section)
        self._detail_nav.setCurrentRow(0)
        self._detail_nav.setFixedHeight(self._detail_nav.sizeHintForRow(0) * self._detail_nav.count() + 36)

        detail_layout.addLayout(content_row)
        layout.addWidget(self._detail_panel)

        self._tx_panel = QFrame()
        self._tx_panel.setStyleSheet(panel_surface_stylesheet())
        tx_layout = QVBoxLayout(self._tx_panel)
        tx_layout.setContentsMargins(12, 12, 12, 12)
        tx_layout.setSpacing(8)

        self._tx_label = QLabel("Transactions in Block")
        self._tx_label.setStyleSheet(section_title_stylesheet())
        tx_layout.addWidget(self._tx_label)

        self.tx_table = QTableWidget(0, 5, self)
        self.tx_table.setHorizontalHeaderLabels(["Tx Hash", "From", "To", "Value (ETH)", "Type"])
        header = self.tx_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.tx_table.verticalHeader().hide()
        self.tx_table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tx_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tx_table.setFocusPolicy(Qt.StrongFocus)
        self.tx_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tx_table.setAlternatingRowColors(True)
        self.tx_table.setStyleSheet(table_widget_stylesheet())
        tx_layout.addWidget(self.tx_table, 1)
        layout.addWidget(self._tx_panel, 1)

    def refresh_theme(self) -> None:
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        self.search_button.setStyleSheet(accent_button_stylesheet())
        for card in self._summary_cards:
            card.refresh_theme()
        self._detail_panel.setStyleSheet(panel_surface_stylesheet())
        self._detail_nav.setStyleSheet(inspector_nav_stylesheet())
        self._overview_section.refresh_theme()
        self._header_section.refresh_theme()
        self._gas_section.refresh_theme()
        self._tx_panel.setStyleSheet(panel_surface_stylesheet())
        self._tx_label.setStyleSheet(section_title_stylesheet())
        self.tx_table.setStyleSheet(table_widget_stylesheet())

    def _register_detail_page(self, key: str, label: str, widget: QWidget) -> None:
        item = QListWidgetItem(label)
        self._detail_nav.addItem(item)
        self._detail_nav_items[key] = item
        self._detail_stack.addWidget(widget)

    def _detail_stack_row_changed(self, row: int) -> None:
        if row >= 0:
            self._detail_stack.setCurrentIndex(row)

    def _select_detail_page(self, key: str) -> None:
        item = self._detail_nav_items.get(key)
        if item is not None:
            self._detail_nav.setCurrentItem(item)

    def set_rpc_client(self, client: RpcClient | None) -> None:
        self._rpc_client = client
        self._lookup_request_id += 1
        if client is None:
            self.status_message.emit("RPC not configured. Provide an endpoint to search blocks.")
            self._set_placeholder()
            return
        self.status_message.emit("Ready. Enter a block height or hash.")

    def _set_placeholder(self) -> None:
        placeholders = [
            ("N/A", "Waiting for selection"),
            ("N/A", "Count in block"),
            ("N/A", "Gas used vs limit"),
        ]
        for card, (value, subtitle) in zip(self._summary_cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        self._overview_section.update_rows([("Block", "No block selected")])
        self._header_section.update_rows([])
        self._gas_section.update_rows([])
        self.tx_table.setRowCount(0)
        self._select_detail_page("overview")

    def _handle_local_search(self) -> None:
        query = self.search_input.text().strip()
        if query:
            self.show_block(query)

    def show_block(self, identifier: str) -> None:
        if not self._rpc_client:
            self.status_message.emit("RPC not configured. Provide an endpoint to search blocks.")
            return
        self.status_message.emit(f"Loading block {identifier}...")
        self._lookup_request_id += 1
        request_id = self._lookup_request_id
        endpoint = self._rpc_client.endpoint

        run_in_background(
            lambda: RpcClient(endpoint).get_block(identifier, full_transactions=True),
            on_success=lambda block: self._handle_block_loaded(request_id, block),
            on_error=lambda exc: self._handle_block_failed(request_id, exc),
        )

    def _handle_block_loaded(self, request_id: int, block: BlockInfo) -> None:
        if request_id != self._lookup_request_id:
            return
        self.status_message.emit(f"Displaying block {block.number}")
        self._render_block(block)

    def _handle_block_failed(self, request_id: int, exc: Exception) -> None:
        if request_id != self._lookup_request_id:
            return
        self.status_message.emit(f"Block lookup failed: {exc}")
        self._set_placeholder()

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

        self._overview_section.update_rows(
            [
                ("Block Number", str(block.number)),
                ("Timestamp", block.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")),
                ("Miner", block.miner or "N/A"),
                ("Transactions", str(block.tx_count)),
            ]
        )
        self._header_section.update_rows(
            [
                ("Hash", block.hash),
                ("Parent Hash", block.parent_hash),
                ("State Root", block.state_root or "N/A"),
                ("Transactions Root", block.transactions_root or "N/A"),
            ]
        )
        base_fee = f"{block.base_fee_gwei:.2f} gwei" if block.base_fee_gwei is not None else "N/A"
        gas_rows = [
            ("Gas Used", f"{block.gas_used:,}"),
            ("Gas Limit", f"{block.gas_limit:,}"),
            ("Usage Ratio", f"{gas_ratio:.2%}"),
            ("Base Fee", base_fee),
        ]
        self._gas_section.update_rows(gas_rows)
        self._populate_transactions(block.transactions or [])
        self._select_detail_page("overview")

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
            self.tx_table.setItem(row, 4, QTableWidgetItem(self._tx_type(tx)))

    def _tx_type(self, tx: TransactionInfo) -> str:
        if tx.to_address is None:
            return "Contract Creation"
        if tx.input_data and tx.input_data != "0x":
            return "Call"
        return "Transfer"
