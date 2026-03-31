"""Main application window layout."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QStackedWidget, QStatusBar, QVBoxLayout, QWidget

from ..core.config import APP_CONFIG
from ..services.rpc_client import RpcClient, RpcError
from .address import AddressView
from .async_tasks import run_in_background
from .blocks import BlocksView
from .dashboard import DashboardView
from .styles import content_shell_stylesheet
from .transactions import TransactionsView
from .widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    """Primary window containing navigation and stacked pages."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BlockViz")
        self.resize(1280, 820)
        self._config = APP_CONFIG
        self._view_registry: dict[str, QWidget] = {}
        self._stack = QStackedWidget()
        self._rpc_client: RpcClient | None = None
        self._rpc_request_id = 0
        self._build_layout()
        self._create_views()
        self._activate_view("dashboard")
        preset_url = self._config.resolve_rpc()
        if preset_url:
            self._handle_network_change(preset_url)

    def _build_layout(self) -> None:
        container = QWidget()
        self.setCentralWidget(container)
        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(10)

        self.sidebar = Sidebar(self._config)
        self.sidebar.network_changed.connect(self._handle_network_change)
        self.sidebar.nav_selected.connect(self._handle_nav_change)
        root_layout.addWidget(self.sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        body = QFrame()
        body.setStyleSheet(content_shell_stylesheet())
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(18, 18, 18, 18)
        body_layout.addWidget(self._stack)
        right_layout.addWidget(body, 1)
        root_layout.addWidget(right, 1)
        self._build_status_bar()

    def _build_status_bar(self) -> None:
        status = QStatusBar()
        status.showMessage("Enter an RPC URL to connect to the network.")
        self.setStatusBar(status)

    def _create_views(self) -> None:
        dashboard = DashboardView()
        dashboard.set_navigation_handler(self._handle_dashboard_navigation)
        self._register_view("dashboard", dashboard)
        self._register_view("transactions", TransactionsView())
        self._register_view("blocks", BlocksView())
        self._register_view("address", AddressView(self._config))
        self._stack.setCurrentWidget(self._view_registry["dashboard"])

    def _register_view(self, key: str, widget: QWidget) -> None:
        self._view_registry[key] = widget
        self._stack.addWidget(widget)
        status_signal = getattr(widget, "status_message", None)
        if status_signal is not None and hasattr(status_signal, "connect"):
            status_signal.connect(self.statusBar().showMessage)
        setter = getattr(widget, "set_rpc_client", None)
        if callable(setter):
            setter(self._rpc_client)

    def _handle_network_change(self, rpc_url: str) -> None:
        rpc_url = (rpc_url or "").strip()
        self._config.update_rpc_url(rpc_url)
        self._rpc_request_id += 1
        request_id = self._rpc_request_id
        if not rpc_url:
            self._rpc_client = None
            self.statusBar().showMessage("RPC not configured. Enter a full node endpoint.")
            self._set_network_state(False, "RPC Offline")
            self._broadcast_rpc(None)
            return

        self.statusBar().showMessage(f"Connecting to RPC: {rpc_url}")
        self._set_network_state(False, "Connecting...")

        def verify_client() -> RpcClient:
            client = RpcClient(rpc_url)
            client.verify()
            return client

        run_in_background(
            verify_client,
            on_success=lambda client: self._handle_rpc_verified(request_id, rpc_url, client),
            on_error=lambda exc: self._handle_rpc_failed(request_id, exc),
        )

    def _handle_rpc_verified(self, request_id: int, rpc_url: str, client: RpcClient) -> None:
        if request_id != self._rpc_request_id:
            return
        self._rpc_client = client
        self.statusBar().showMessage(f"Connected to RPC: {rpc_url}")
        self._set_network_state(True, "RPC Live")
        self._broadcast_rpc(client)

    def _handle_rpc_failed(self, request_id: int, exc: Exception) -> None:
        if request_id != self._rpc_request_id:
            return
        message = str(exc)
        if isinstance(exc, RpcError):
            message = str(exc)
        self._rpc_client = None
        self.statusBar().showMessage(f"RPC connection failed: {message}")
        self._set_network_state(False, "RPC Error")
        self._broadcast_rpc(None)

    def _set_network_state(self, connected: bool, badge_text: str) -> None:
        self.sidebar.set_rpc_status(badge_text, connected)

    def _broadcast_rpc(self, client: RpcClient | None) -> None:
        for widget in self._view_registry.values():
            setter = getattr(widget, "set_rpc_client", None)
            if callable(setter):
                setter(client)

    def _handle_nav_change(self, key: str) -> None:
        self._activate_view(key)

    def _handle_dashboard_navigation(self, target: str, query: str) -> None:
        widget = self._view_registry.get(target)
        if not widget:
            return
        handler_name = {
            "transactions": "show_transaction",
            "blocks": "show_block",
            "address": "show_address",
        }.get(target)
        if handler_name and hasattr(widget, handler_name):
            getattr(widget, handler_name)(query)
        self._activate_view(target)

    def _activate_view(self, key: str) -> None:
        widget = self._view_registry.get(key)
        if widget is None:
            return
        self.sidebar.set_active_nav(key)
        self._stack.setCurrentWidget(widget)
