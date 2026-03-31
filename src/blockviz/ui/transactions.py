"""Transactions explorer view with detail search."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..services.rpc_client import RpcClient, RpcError, TransactionInfo
from .async_tasks import run_in_background
from .styles import (
    accent_button_stylesheet,
    icon_button_stylesheet,
    inspector_nav_stylesheet,
    panel_surface_stylesheet,
    section_title_stylesheet,
    text_view_stylesheet,
)
from .widgets.detail_section import DetailSection
from .widgets.info_card import InfoCard


class TransactionsView(QWidget):
    """Displays transaction details for a given hash."""

    status_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._rpc_client: RpcClient | None = None
        self._summary_cards: list[InfoCard] = []
        self._detail_nav_items: dict[str, QListWidgetItem] = {}
        self._lookup_request_id = 0
        self._overview_section = DetailSection("Overview")
        self._fees_section = DetailSection("Fees & Gas")
        self._execution_section = DetailSection("Execution")
        self._signature_section = DetailSection("Signature")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._search_panel = QFrame()
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        search_layout = QVBoxLayout(self._search_panel)
        search_layout.setContentsMargins(14, 14, 14, 14)
        search_layout.setSpacing(10)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter transaction hash")
        search_row.addWidget(self.search_input, 4)

        self.search_button = QPushButton("⌕ Search Tx")
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setStyleSheet(accent_button_stylesheet())
        self.search_button.clicked.connect(self._handle_local_search)
        search_row.addWidget(self.search_button, 1)
        search_layout.addLayout(search_row)

        layout.addWidget(self._search_panel)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)
        card_defs = [
            ("Status", "N/A", "", "transactions"),
            ("Value (ETH)", "N/A", "", "address"),
            ("Gas Used", "N/A", "", "gas"),
            ("Type", "N/A", "", "block"),
        ]
        for idx, (title_text, value, subtitle_text, icon_name) in enumerate(card_defs):
            card = InfoCard(title_text, value, subtitle_text, icon=icon_name)
            cards_layout.addWidget(card, 0, idx)
            self._summary_cards.append(card)
        layout.addLayout(cards_layout)

        self._detail_panel = QFrame()
        self._detail_panel.setStyleSheet(panel_surface_stylesheet())
        detail_layout = QVBoxLayout(self._detail_panel)
        detail_layout.setContentsMargins(14, 14, 14, 14)
        detail_layout.setSpacing(8)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)

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
        self._register_detail_page("fees", "Fees & Gas", self._fees_section)
        self._register_detail_page("execution", "Execution", self._execution_section)
        self._register_detail_page("signature", "Signature", self._signature_section)
        self._detail_nav.setCurrentRow(0)
        self._detail_nav.setFixedHeight(self._detail_nav.sizeHintForRow(0) * self._detail_nav.count() + 36)

        detail_layout.addLayout(content_row)
        layout.addWidget(self._detail_panel)

        self._input_panel = QFrame()
        self._input_panel.setStyleSheet(panel_surface_stylesheet())
        input_layout = QVBoxLayout(self._input_panel)
        input_layout.setContentsMargins(14, 14, 14, 14)
        input_layout.setSpacing(8)

        input_header = QHBoxLayout()
        self._input_label = QLabel("Input Data")
        self._input_label.setStyleSheet(section_title_stylesheet())
        input_header.addWidget(self._input_label)
        input_header.addStretch(1)

        self.copy_button = QPushButton("⎘")
        self.copy_button.setFixedSize(32, 32)
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.setToolTip("Copy to clipboard")
        self.copy_button.setStyleSheet(self._default_copy_button_style())
        self.copy_button.clicked.connect(self._copy_input_data)
        input_header.addWidget(self.copy_button)
        input_layout.addLayout(input_header)

        self.input_view = QPlainTextEdit()
        self.input_view.setReadOnly(True)
        self.input_view.setMaximumHeight(150)
        self.input_view.setStyleSheet(text_view_stylesheet())
        input_layout.addWidget(self.input_view)
        layout.addWidget(self._input_panel)

    def refresh_theme(self) -> None:
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        self.search_button.setStyleSheet(accent_button_stylesheet())
        for card in self._summary_cards:
            card.refresh_theme()
        self._detail_panel.setStyleSheet(panel_surface_stylesheet())
        self._detail_nav.setStyleSheet(inspector_nav_stylesheet())
        self._overview_section.refresh_theme()
        self._fees_section.refresh_theme()
        self._execution_section.refresh_theme()
        self._signature_section.refresh_theme()
        self._input_panel.setStyleSheet(panel_surface_stylesheet())
        self._input_label.setStyleSheet(section_title_stylesheet())
        if self.copy_button.text() != "✓":
            self.copy_button.setStyleSheet(self._default_copy_button_style())
        self.input_view.setStyleSheet(text_view_stylesheet())

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

    def _default_copy_button_style(self) -> str:
        return icon_button_stylesheet()

    def _copy_input_data(self) -> None:
        text = self.input_view.toPlainText()
        if text and text != "No input data.":
            QApplication.clipboard().setText(text)
            original_text = self.copy_button.text()
            self.copy_button.setText("✓")
            self.copy_button.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(52, 211, 153, 0.16);
                    border: 1px solid rgba(52, 211, 153, 0.34);
                    border-radius: 12px;
                    color: #34d399;
                    font-size: 14px;
                    padding: 0;
                }
                """
            )
            QTimer.singleShot(1000, lambda: self._restore_copy_button(original_text))

    def _restore_copy_button(self, original_text: str) -> None:
        self.copy_button.setText(original_text)
        self.copy_button.setStyleSheet(self._default_copy_button_style())

    def set_rpc_client(self, client: RpcClient | None) -> None:
        self._rpc_client = client
        self._lookup_request_id += 1
        if client is None:
            self.status_message.emit("RPC not configured. Provide an endpoint to search transactions.")
            self._set_placeholder()
            return
        self.status_message.emit("Ready. Enter a transaction hash.")

    def _set_placeholder(self) -> None:
        placeholders = [
            ("N/A", "Waiting for selection"),
            ("N/A", "No value loaded"),
            ("N/A", "Gas receipt pending"),
            ("N/A", "Envelope unknown"),
        ]
        for card, (value, subtitle) in zip(self._summary_cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        self._overview_section.update_rows([("Transaction", "No transaction selected")])
        self._fees_section.update_rows([])
        self._execution_section.update_rows([])
        self._signature_section.update_rows([])
        self.input_view.setPlainText("No input data.")
        self._select_detail_page("overview")

    def _handle_local_search(self) -> None:
        tx_hash = self.search_input.text().strip()
        if tx_hash:
            self.show_transaction(tx_hash)

    def show_transaction(self, tx_hash: str) -> None:
        if not self._rpc_client:
            self.status_message.emit("RPC not configured. Provide an endpoint to search transactions.")
            return
        self.status_message.emit(f"Loading transaction {tx_hash[:14]}...")
        self._lookup_request_id += 1
        request_id = self._lookup_request_id
        endpoint = self._rpc_client.endpoint

        run_in_background(
            lambda: RpcClient(endpoint).get_transaction(tx_hash),
            on_success=lambda tx: self._handle_transaction_loaded(request_id, tx),
            on_error=lambda exc: self._handle_transaction_failed(request_id, exc),
        )

    def _handle_transaction_loaded(self, request_id: int, tx: TransactionInfo) -> None:
        if request_id != self._lookup_request_id:
            return
        self.status_message.emit(f"Displaying transaction {tx.tx_hash[:14]}...")
        self._render_transaction(tx)

    def _handle_transaction_failed(self, request_id: int, exc: Exception) -> None:
        if request_id != self._lookup_request_id:
            return
        self.status_message.emit(f"Transaction lookup failed: {exc}")
        self._set_placeholder()

    def _render_transaction(self, tx: TransactionInfo) -> None:
        action_type = self._action_type(tx)
        envelope_type = self._envelope_type(tx.tx_type)
        status = tx.status or "Pending"
        gas_used_str = f"{tx.gas_used:,}" if tx.gas_used is not None else "Pending"
        block_display = str(tx.block_number) if tx.block_number else "Pending"
        destination = tx.to_address or tx.contract_address or "Contract Creation"

        self._summary_cards[0].update_card(value=status, subtitle=f"Block {block_display}")
        self._summary_cards[1].update_card(value=f"{tx.value_eth:.8f}", subtitle="Value transferred in ETH")
        self._summary_cards[2].update_card(
            value=gas_used_str,
            subtitle=(
                f"Effective {tx.effective_gas_price_gwei:.2f} gwei"
                if tx.effective_gas_price_gwei is not None
                else "Awaiting receipt / fee data"
            ),
        )
        self._summary_cards[3].update_card(value=action_type, subtitle=envelope_type)

        self._overview_section.update_rows(
            [
                ("Transaction Hash", tx.tx_hash),
                ("Block Number", block_display),
                ("Timestamp", tx.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")),
                ("From", tx.from_address),
                ("To", destination),
                ("Nonce", str(tx.nonce)),
            ]
        )

        fee_rows = [
            ("Gas Limit", self._display_int(tx.gas_limit)),
            ("Gas Used", self._display_int(tx.gas_used)),
            ("Effective Gas Price", self._display_gwei(tx.effective_gas_price_gwei)),
            ("Total Fee Paid", self._display_eth(tx.total_fee_eth)),
        ]
        self._fees_section.update_rows(self._non_empty_rows(fee_rows))

        execution_rows = [
            ("Execution Type", action_type),
            ("Envelope Type", envelope_type),
            ("Status", status),
            ("Method ID", tx.method_id or "N/A"),
            ("Input Size", f"{tx.input_size_bytes:,} bytes"),
            ("Contract Address", tx.contract_address or "N/A"),
        ]
        self._execution_section.update_rows(self._non_empty_rows(execution_rows))

        self._signature_section.update_rows(
            [
                ("v", tx.v or "N/A"),
                ("r", tx.r or "N/A"),
                ("s", tx.s or "N/A"),
            ]
        )

        self.input_view.setPlainText(tx.input_data or "No input data.")
        self._select_detail_page("overview")

    def _action_type(self, tx: TransactionInfo) -> str:
        if tx.to_address is None:
            return "Contract Creation"
        if tx.input_data and tx.input_data != "0x":
            return "Call"
        return "Transfer"

    def _envelope_type(self, tx_type: int | None) -> str:
        mapping = {
            0: "Legacy (Type 0)",
            1: "Access List (Type 1)",
            2: "EIP-1559 (Type 2)",
            3: "Blob (Type 3)",
        }
        if tx_type is None:
            return "Unknown"
        return mapping.get(tx_type, f"Type {tx_type}")

    def _display_int(self, value: int | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:,}"

    def _display_gwei(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.4f} gwei"

    def _display_eth(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.8f} ETH"

    def _non_empty_rows(self, rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return [(key, value) for key, value in rows if value != "N/A"]
