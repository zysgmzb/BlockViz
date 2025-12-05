"""Main application window layout."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QStatusBar, QWidget

from ..core.config import APP_CONFIG
from ..services.rpc_client import RpcClient, RpcError
from .dashboard import DashboardView
from .transactions import TransactionsView
from .blocks import BlocksView
from .address import AddressView
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
        self._build_layout()
        self._create_views()
        preset_url = self._config.resolve_rpc()
        if preset_url:
            self._handle_network_change(preset_url)

    def _build_layout(self) -> None:
        container = QWidget()
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = Sidebar(self._config)
        self.sidebar.network_changed.connect(self._handle_network_change)
        self.sidebar.nav_selected.connect(self._handle_nav_change)

        layout.addWidget(self.sidebar)
        layout.addWidget(self._stack, 1)
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
        self._register_view("address", AddressView())
        self._stack.setCurrentWidget(self._view_registry["dashboard"])

    def _register_view(self, key: str, widget: QWidget) -> None:
        self._view_registry[key] = widget
        self._stack.addWidget(widget)
        setter = getattr(widget, "set_rpc_client", None)
        if callable(setter):
            setter(self._rpc_client)

    def _handle_network_change(self, rpc_url: str) -> None:
        rpc_url = (rpc_url or "").strip()
        self._config.update_rpc_url(rpc_url)
        if not rpc_url:
            self._rpc_client = None
            self.statusBar().showMessage("RPC not configured. Enter a full node endpoint.")
            self._broadcast_rpc(None)
            return
        client = RpcClient(rpc_url)
        try:
            client.verify()
        except RpcError as exc:
            self._rpc_client = None
            self.statusBar().showMessage(f"RPC connection failed: {exc}")
            self._broadcast_rpc(None)
            return
        self._rpc_client = client
        self.statusBar().showMessage(f"Connected to RPC: {rpc_url}")
        self._broadcast_rpc(client)

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
