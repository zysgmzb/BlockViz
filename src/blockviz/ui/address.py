"""Address lookup view with explorer-style panels."""

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

from ..core.config import AppConfig
from ..services.ai_client import AIClient, AIClientError
from ..services.decompiler import DecompileArtifacts, DecompileError, decompile_bytecode, heimdall_available
from .async_tasks import run_in_background
from ..services.rpc_client import AccountInfo, RpcClient, RpcError
from .ai_settings_dialog import AISettingsDialog
from .styles import (
    accent_button_stylesheet,
    hint_banner_stylesheet,
    icon_button_stylesheet,
    inspector_nav_stylesheet,
    panel_surface_stylesheet,
    section_title_stylesheet,
    text_view_stylesheet,
)
from .widgets.info_card import InfoCard


class AddressView(QWidget):
    """Showcases account lookups backed by RPC data."""

    status_message = Signal(str)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._rpc_client: RpcClient | None = None
        self._summary_cards: list[InfoCard] = []
        self._content_views: dict[str, QPlainTextEdit] = {}
        self._nav_items: dict[str, QListWidgetItem] = {}
        self._current_address: str | None = None
        self._current_bytecode: str = ""
        self._is_contract = False
        self._has_decompiled_output = False
        self._lookup_request_id = 0
        self._action_request_id = 0
        self._busy_action: str | None = None
        self._action_elapsed_seconds = 0
        self._action_timer = QTimer(self)
        self._action_timer.setInterval(1000)
        self._action_timer.timeout.connect(self._tick_action_timer)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._search_panel = QFrame()
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        search_layout = QVBoxLayout(self._search_panel)
        search_layout.setContentsMargins(18, 18, 18, 18)
        search_layout.setSpacing(12)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter account address (0x...)")
        search_row.addWidget(self.search_input, 4)

        self.search_button = QPushButton("⌕ Search Address")
        self.search_button.setCursor(Qt.PointingHandCursor)
        self.search_button.setStyleSheet(accent_button_stylesheet())
        self.search_button.clicked.connect(self._handle_local_search)
        search_row.addWidget(self.search_button, 1)
        search_layout.addLayout(search_row)

        layout.addWidget(self._search_panel)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)
        card_defs = [
            ("Balance (ETH)", "N/A", "", "address"),
            ("Tx Count", "N/A", "", "transactions"),
            ("Account Type", "N/A", "", "block"),
        ]
        for idx, (title_text, value, subtitle_text, icon_name) in enumerate(card_defs):
            card = InfoCard(title_text, value, subtitle_text, icon=icon_name)
            cards_layout.addWidget(card, 0, idx)
            self._summary_cards.append(card)
        layout.addLayout(cards_layout)

        self._analysis_panel = QFrame()
        self._analysis_panel.setStyleSheet(panel_surface_stylesheet())
        analysis_layout = QVBoxLayout(self._analysis_panel)
        analysis_layout.setContentsMargins(18, 18, 18, 18)
        analysis_layout.setSpacing(12)

        panel_header = QHBoxLayout()
        panel_header.addStretch(1)

        self.action_button = QPushButton("Decompile")
        self.action_button.setCursor(Qt.PointingHandCursor)
        self.action_button.setToolTip("Decompile contract bytecode with Heimdall")
        self.action_button.setStyleSheet(accent_button_stylesheet())
        self.action_button.clicked.connect(self._handle_primary_action)
        panel_header.addWidget(self.action_button)

        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setToolTip("AI analysis settings")
        self.settings_button.setStyleSheet(self._default_copy_button_style())
        self.settings_button.clicked.connect(self._open_ai_settings)
        panel_header.addWidget(self.settings_button)

        self.code_copy_button = QPushButton("⎘")
        self.code_copy_button.setFixedSize(32, 32)
        self.code_copy_button.setCursor(Qt.PointingHandCursor)
        self.code_copy_button.setToolTip("Copy to clipboard")
        self.code_copy_button.setStyleSheet(self._default_copy_button_style())
        self.code_copy_button.clicked.connect(self._copy_current_view)
        panel_header.addWidget(self.code_copy_button)
        analysis_layout.addLayout(panel_header)

        self._action_banner = QLabel("")
        self._action_banner.setWordWrap(True)
        self._action_banner.setVisible(False)
        self._action_banner.setStyleSheet(hint_banner_stylesheet())
        analysis_layout.addWidget(self._action_banner)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        self._content_nav = QListWidget()
        self._content_nav.setFixedWidth(188)
        self._content_nav.setSpacing(4)
        self._content_nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._content_nav.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._content_nav.setWordWrap(False)
        self._content_nav.setStyleSheet(inspector_nav_stylesheet())
        self._content_nav.currentRowChanged.connect(self._stack_row_changed)
        content_row.addWidget(self._content_nav)

        self._content_stack = QStackedWidget()
        content_row.addWidget(self._content_stack, 1)

        self._register_content_page("bytecode", "Bytecode")
        self._register_content_page("source_heimdall", "Source (Heimdall)")
        self._register_content_page("source_ai", "Source (AI)")
        self._register_content_page("abi", "ABI")
        self._content_nav.setCurrentRow(0)
        self._content_nav.setFixedHeight(self._content_nav.sizeHintForRow(0) * self._content_nav.count() + 36)

        analysis_layout.addLayout(content_row, 1)
        layout.addWidget(self._analysis_panel, 1)
        self._set_placeholder()

    def refresh_theme(self) -> None:
        self._search_panel.setStyleSheet(panel_surface_stylesheet())
        self.search_button.setStyleSheet(accent_button_stylesheet())
        for card in self._summary_cards:
            card.refresh_theme()
        self._analysis_panel.setStyleSheet(panel_surface_stylesheet())
        self.action_button.setStyleSheet(accent_button_stylesheet())
        self.settings_button.setStyleSheet(self._default_copy_button_style())
        if self.code_copy_button.text() != "✓":
            self.code_copy_button.setStyleSheet(self._default_copy_button_style())
        self._action_banner.setStyleSheet(hint_banner_stylesheet())
        self._content_nav.setStyleSheet(inspector_nav_stylesheet())
        for view in self._content_views.values():
            view.setStyleSheet(text_view_stylesheet())

    def _register_content_page(self, key: str, label: str) -> None:
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setStyleSheet(text_view_stylesheet())
        self._content_views[key] = editor
        self._nav_items[key] = QListWidgetItem(label)
        self._content_nav.addItem(self._nav_items[key])
        self._content_stack.addWidget(editor)

    def _stack_row_changed(self, row: int) -> None:
        if row >= 0:
            self._content_stack.setCurrentIndex(row)

    def _select_content_page(self, key: str) -> None:
        item = self._nav_items.get(key)
        if item is not None:
            self._content_nav.setCurrentItem(item)

    def _default_copy_button_style(self) -> str:
        return icon_button_stylesheet()

    def _copy_current_view(self) -> None:
        text = self._current_view().toPlainText()
        if not text or self._is_placeholder(text):
            return
        QApplication.clipboard().setText(text)
        original_text = self.code_copy_button.text()
        self.code_copy_button.setText("✓")
        self.code_copy_button.setStyleSheet(
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
        self.code_copy_button.setText(original_text)
        self.code_copy_button.setStyleSheet(self._default_copy_button_style())

    def _set_action_busy(self, action: str | None) -> None:
        self._busy_action = action
        busy = action is not None
        self.search_input.setEnabled(not busy)
        self.search_button.setEnabled(not busy)
        self.settings_button.setEnabled(not busy)
        self.action_button.setEnabled(self._is_contract if not busy else True)
        if busy:
            self._action_elapsed_seconds = 0
            banner_text = "Heimdall is decompiling contract bytecode in the background..." if action == "decompile" else "AI is rewriting the Heimdall source in the background. This may take a while for larger contracts."
            self._action_banner.setText(banner_text)
            self._action_banner.setVisible(True)
            self._update_action_button_text()
            self._action_timer.start()
        else:
            self._action_timer.stop()
            self._action_elapsed_seconds = 0
            self._action_banner.clear()
            self._action_banner.setVisible(False)
            self.action_button.setText("AI Analysis" if self._has_decompiled_output else "Decompile")

    def _update_action_button_text(self) -> None:
        if self._busy_action == "decompile":
            self.action_button.setText(f"Cancel Decompile ({self._action_elapsed_seconds}s)")
            self._action_banner.setText(
                f"Heimdall is decompiling contract bytecode in the background... {self._action_elapsed_seconds}s elapsed."
            )
        elif self._busy_action == "ai":
            self.action_button.setText(f"Cancel AI ({self._action_elapsed_seconds}s)")
            self._action_banner.setText(
                f"AI is rewriting the Heimdall source in the background... {self._action_elapsed_seconds}s elapsed."
            )
        else:
            self.action_button.setText("AI Analysis" if self._has_decompiled_output else "Decompile")

    def _tick_action_timer(self) -> None:
        self._action_elapsed_seconds += 1
        self._update_action_button_text()
        if self._busy_action == "ai" and self._action_elapsed_seconds in {15, 30, 60, 120}:
            self.status_message.emit(
                f"AI analysis is still running ({self._action_elapsed_seconds}s). You can press Cancel and ignore the late result."
            )

    def _cancel_current_action(self) -> None:
        if self._busy_action is None:
            return
        canceled_action = self._busy_action
        self._action_request_id += 1
        self._set_action_busy(None)
        self._action_banner.setText("Canceled current background task. Any late result will be ignored.")
        self._action_banner.setVisible(True)
        self.status_message.emit(
            f"Canceled {canceled_action}. Any late background result will be ignored."
        )

    def _current_view(self) -> QPlainTextEdit:
        widget = self._content_stack.currentWidget()
        assert isinstance(widget, QPlainTextEdit)
        return widget

    def _is_placeholder(self, text: str) -> bool:
        placeholders = {
            "No contract bytecode (Externally Owned Account).",
            "No contract code (EOA) or RPC not set.",
            "Click Decompile to generate Solidity-like source with Heimdall.",
            "Click AI Analysis to generate an AI-polished Solidity version.",
            "Click Decompile to generate ABI output with Heimdall.",
        }
        return text in placeholders

    def _reset_analysis_views(self) -> None:
        self._content_views["source_heimdall"].setPlainText("Click Decompile to generate Solidity-like source with Heimdall.")
        self._content_views["source_ai"].setPlainText("Click AI Analysis to generate an AI-polished Solidity version.")
        self._content_views["abi"].setPlainText("Click Decompile to generate ABI output with Heimdall.")
        self._has_decompiled_output = False

    def _set_placeholder(self) -> None:
        placeholders = [("N/A", "Current balance"), ("N/A", "Transaction count / nonce"), ("N/A", "EOA vs Contract")]
        for card, (value, subtitle) in zip(self._summary_cards, placeholders, strict=False):
            card.update_card(value=value, subtitle=subtitle)
        self._current_address = None
        self._current_bytecode = ""
        self._is_contract = False
        self._has_decompiled_output = False
        self._content_views["bytecode"].setPlainText("No contract code (EOA) or RPC not set.")
        self._content_views["source_heimdall"].setPlainText("Click Decompile to generate Solidity-like source with Heimdall.")
        self._content_views["source_ai"].setPlainText("Click AI Analysis to generate an AI-polished Solidity version.")
        self._content_views["abi"].setPlainText("Click Decompile to generate ABI output with Heimdall.")
        self._select_content_page("bytecode")
        self._set_action_busy(None)
        self.action_button.setEnabled(False)

    def _open_ai_settings(self) -> None:
        dialog = AISettingsDialog(self._config, self)
        if dialog.exec():
            model = self._config.ai_model or "No model selected"
            self.status_message.emit(f"Saved AI settings. Current model: {model}")

    def set_rpc_client(self, client: RpcClient | None) -> None:
        self._rpc_client = client
        self._lookup_request_id += 1
        if client is None:
            self.status_message.emit("RPC not configured. Provide an endpoint to inspect addresses.")
            self._set_placeholder()
            return
        self.status_message.emit("Ready. Enter an address to inspect balance and nonce.")

    def _handle_local_search(self) -> None:
        address = self.search_input.text().strip()
        if address:
            self.show_address(address)

    def _handle_primary_action(self) -> None:
        if self._busy_action is not None:
            self._cancel_current_action()
        elif self._has_decompiled_output:
            self._handle_ai_analysis()
        else:
            self._handle_decompile()

    def _handle_decompile(self) -> None:
        if not self._is_contract or not self._current_bytecode or self._current_bytecode == "0x":
            self.status_message.emit("Current address does not contain deployable contract bytecode.")
            return
        if not heimdall_available():
            self.status_message.emit("Heimdall CLI not found in PATH. Install it before using Decompile.")
            return

        self._action_request_id += 1
        request_id = self._action_request_id
        self.status_message.emit("Running Heimdall decompile in background...")
        self._set_action_busy("decompile")

        run_in_background(
            lambda: decompile_bytecode(
                self._current_bytecode,
                name=(self._current_address or "contract").replace("0x", "contract-"),
            ),
            on_success=lambda artifacts: self._handle_decompile_success(request_id, artifacts),
            on_error=lambda exc: self._handle_decompile_error(request_id, exc),
        )

    def _handle_decompile_success(self, request_id: int, artifacts: DecompileArtifacts) -> None:
        if request_id != self._action_request_id:
            return
        self._apply_decompile_artifacts(artifacts)
        self.status_message.emit(f"Decompiled {self._current_address or 'contract'} with Heimdall.")
        self._select_content_page("source_heimdall")
        self._set_action_busy(None)

    def _handle_decompile_error(self, request_id: int, exc: Exception) -> None:
        if request_id != self._action_request_id:
            return
        self.status_message.emit(f"Heimdall decompile failed: {exc}")
        self._set_action_busy(None)

    def _handle_ai_analysis(self) -> None:
        source_code = self._content_views["source_heimdall"].toPlainText().strip()
        if not self._has_decompiled_output or not source_code or self._is_placeholder(source_code):
            self.status_message.emit("Please decompile the contract first.")
            return
        if not self._config.ai_model:
            self.status_message.emit("No AI model configured. Open Settings and choose a base model first.")
            return
        if not self._config.ai_api_url or not self._config.ai_api_key:
            self.status_message.emit("AI API URL or API key is missing. Open Settings first.")
            return

        try:
            client = AIClient(
                self._config.ai_api_url,
                self._config.ai_api_key,
                timeout=180.0,
                proxy=self._config.ai_proxy if self._config.ai_proxy_enabled else "",
            )
        except AIClientError as exc:
            self.status_message.emit(f"AI settings invalid: {exc}")
            return

        self._action_request_id += 1
        request_id = self._action_request_id
        self.status_message.emit("Running AI analysis in background. You can press Cancel if it takes too long...")
        self._set_action_busy("ai")

        run_in_background(
            lambda: client.polish_solidity(source_code, model=self._config.ai_model),
            on_success=lambda polished: self._handle_ai_analysis_success(request_id, polished),
            on_error=lambda exc: self._handle_ai_analysis_error(request_id, exc),
        )

    def _handle_ai_analysis_success(self, request_id: int, polished: str) -> None:
        if request_id != self._action_request_id:
            return
        self._content_views["source_ai"].setPlainText(polished)
        self.status_message.emit(f"AI analysis complete using model {self._config.ai_model}.")
        self._select_content_page("source_ai")
        self._set_action_busy(None)

    def _handle_ai_analysis_error(self, request_id: int, exc: Exception) -> None:
        if request_id != self._action_request_id:
            return
        self.status_message.emit(f"AI analysis failed: {exc}")
        self._set_action_busy(None)

    def _apply_decompile_artifacts(self, artifacts: DecompileArtifacts) -> None:
        self._content_views["bytecode"].setPlainText(artifacts.bytecode)
        self._content_views["source_heimdall"].setPlainText(artifacts.source_code)
        self._content_views["source_ai"].setPlainText("Click AI Analysis to generate an AI-polished Solidity version.")
        self._content_views["abi"].setPlainText(artifacts.abi)
        self._has_decompiled_output = True

    def show_address(self, address: str) -> None:
        if not self._rpc_client:
            self.status_message.emit("RPC not configured. Provide an endpoint to inspect addresses.")
            return
        self.status_message.emit(f"Loading address {address[:14]}...")
        self._lookup_request_id += 1
        request_id = self._lookup_request_id
        endpoint = self._rpc_client.endpoint

        def fetch_address_payload() -> tuple[AccountInfo, str, str]:
            client = RpcClient(endpoint)
            account = client.get_account(address)
            code_hex = client.get_code(account.address)
            account_type = "Contract" if code_hex and code_hex != "0x" else "Externally Owned Account"
            return account, code_hex, account_type

        run_in_background(
            fetch_address_payload,
            on_success=lambda payload: self._handle_address_loaded(request_id, payload),
            on_error=lambda exc: self._handle_address_failed(request_id, exc),
        )

    def _handle_address_loaded(self, request_id: int, payload: tuple[AccountInfo, str, str]) -> None:
        if request_id != self._lookup_request_id:
            return
        account, code_hex, account_type = payload
        self.status_message.emit(f"Displaying {account.address}")
        self._render_account(account, code_hex, account_type)

    def _handle_address_failed(self, request_id: int, exc: Exception) -> None:
        if request_id != self._lookup_request_id:
            return
        self.status_message.emit(f"Address lookup failed: {exc}")
        self._set_placeholder()

    def _render_account(self, account: AccountInfo, code_hex: str, account_type: str) -> None:
        self._summary_cards[0].update_card(value=f"{account.balance_eth:.8f}", subtitle="Current balance")
        self._summary_cards[1].update_card(value=str(account.tx_count), subtitle="Transaction count / nonce")
        self._summary_cards[2].update_card(value=account_type, subtitle="EOA vs Contract")

        self._current_address = account.address
        self._current_bytecode = code_hex
        self._is_contract = bool(code_hex and code_hex != "0x")
        self._has_decompiled_output = False

        if self._is_contract:
            self._content_views["bytecode"].setPlainText(code_hex)
            self._reset_analysis_views()
            self.action_button.setEnabled(True)
        else:
            self._content_views["bytecode"].setPlainText("No contract bytecode (Externally Owned Account).")
            self._reset_analysis_views()
            self.action_button.setEnabled(False)

        self._set_action_busy(None)
        self._select_content_page("bytecode")
