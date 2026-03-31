"""Dialog for configuring AI analysis settings."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ..core.config import AppConfig
from ..services.ai_client import AIClient, AIClientError
from .async_tasks import run_in_background
from .styles import (
    accent_button_stylesheet,
    hint_banner_stylesheet,
    page_eyebrow_stylesheet,
    page_subtitle_stylesheet,
    page_title_stylesheet,
    panel_surface_stylesheet,
    secondary_button_stylesheet,
)


class AISettingsDialog(QDialog):
    """Collects API URL, API key, and model selection for AI analysis."""

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._request_id = 0
        self._busy_mode: str | None = None
        self.setWindowTitle("AI Settings")
        self.resize(620, 420)
        self._build_ui()
        self._load_config_values()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setStyleSheet(panel_surface_stylesheet())
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 22, 22, 22)
        hero_layout.setSpacing(8)

        eyebrow = QLabel("AI ANALYSIS")
        eyebrow.setStyleSheet(page_eyebrow_stylesheet())
        hero_layout.addWidget(eyebrow)

        title = QLabel("Model provider setup")
        title.setStyleSheet(page_title_stylesheet())
        hero_layout.addWidget(title)

        subtitle = QLabel("Configure an OpenAI-compatible endpoint for Solidity polishing, model discovery, and connection testing.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(page_subtitle_stylesheet())
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        form_card = QFrame()
        form_card.setStyleSheet(panel_surface_stylesheet())
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(22, 22, 22, 22)
        form_layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft)

        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://api.openai.com/v1")
        form.addRow("API URL", self.api_url_input)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        form.addRow("API Key", self.api_key_input)

        self.proxy_enabled_checkbox = QCheckBox("Enable proxy")
        self.proxy_enabled_checkbox.toggled.connect(self._sync_proxy_enabled_state)
        form.addRow("Proxy", self.proxy_enabled_checkbox)

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:7890")
        form.addRow("Proxy URL", self.proxy_input)

        model_row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_row.addWidget(self.model_combo, 1)

        self.fetch_models_button = QPushButton("Fetch Models")
        self.fetch_models_button.setStyleSheet(secondary_button_stylesheet())
        self.fetch_models_button.clicked.connect(self._handle_fetch_models)
        model_row.addWidget(self.fetch_models_button)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.setStyleSheet(secondary_button_stylesheet())
        self.test_connection_button.clicked.connect(self._handle_test_connection)
        model_row.addWidget(self.test_connection_button)
        form.addRow("Model", model_row)

        form_layout.addLayout(form)

        self.status_label = QLabel("Use an OpenAI-compatible API endpoint, then fetch models.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(hint_banner_stylesheet())
        form_layout.addWidget(self.status_label)
        layout.addWidget(form_card)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = self.button_box.button(QDialogButtonBox.Save)
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        if save_button is not None:
            save_button.setStyleSheet(accent_button_stylesheet())
        if cancel_button is not None:
            cancel_button.setStyleSheet(secondary_button_stylesheet())
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _load_config_values(self) -> None:
        self.api_url_input.setText(self._config.ai_api_url)
        self.api_key_input.setText(self._config.ai_api_key)
        self.proxy_enabled_checkbox.setChecked(self._config.ai_proxy_enabled)
        self.proxy_input.setText(self._config.ai_proxy)
        self._sync_proxy_enabled_state(self._config.ai_proxy_enabled)
        if self._config.ai_model:
            self.model_combo.addItem(self._config.ai_model)
            self.model_combo.setCurrentText(self._config.ai_model)

    def _set_fetch_busy(self, busy: bool, mode: str | None = None) -> None:
        if busy:
            self._busy_mode = mode
        else:
            self._busy_mode = None
        self.fetch_models_button.setEnabled(not busy)
        self.test_connection_button.setEnabled(not busy)
        self.button_box.setEnabled(not busy)
        self.fetch_models_button.setText("Fetching..." if self._busy_mode == "fetch" else "Fetch Models")
        self.test_connection_button.setText("Testing..." if self._busy_mode == "test" else "Test Connection")

    def _sync_proxy_enabled_state(self, enabled: bool) -> None:
        self.proxy_input.setEnabled(enabled)
        self.proxy_input.setVisible(enabled)

    def _build_client(self) -> AIClient:
        return AIClient(
            self.api_url_input.text().strip(),
            self.api_key_input.text().strip(),
            proxy=self.proxy_input.text().strip() if self.proxy_enabled_checkbox.isChecked() else "",
        )

    def _handle_fetch_models(self) -> None:
        try:
            client = self._build_client()
        except AIClientError as exc:
            self.status_label.setText(str(exc))
            return

        self._request_id += 1
        request_id = self._request_id
        self._set_fetch_busy(True, "fetch")
        self.status_label.setText("Fetching models from provider...")

        run_in_background(
            client.list_models,
            on_success=lambda models: self._handle_fetch_models_success(request_id, models),
            on_error=lambda exc: self._handle_fetch_models_error(request_id, exc),
        )

    def _handle_fetch_models_success(self, request_id: int, models: list[str]) -> None:
        if request_id != self._request_id:
            return
        current = self.model_combo.currentText().strip()
        self.model_combo.clear()
        self.model_combo.addItems(models)
        if current and current in models:
            self.model_combo.setCurrentText(current)
        elif self._config.ai_model and self._config.ai_model in models:
            self.model_combo.setCurrentText(self._config.ai_model)
        self.status_label.setText(f"Loaded {len(models)} models from provider.")
        self._set_fetch_busy(False)

    def _handle_fetch_models_error(self, request_id: int, exc: Exception) -> None:
        if request_id != self._request_id:
            return
        self.status_label.setText(f"Model fetch failed: {exc}")
        self._set_fetch_busy(False)

    def _handle_test_connection(self) -> None:
        try:
            client = self._build_client()
        except AIClientError as exc:
            self.status_label.setText(str(exc))
            return

        self._request_id += 1
        request_id = self._request_id
        self._set_fetch_busy(True, "test")
        self.status_label.setText("Testing connection to provider...")

        run_in_background(
            client.list_models,
            on_success=lambda models: self._handle_test_connection_success(request_id, models),
            on_error=lambda exc: self._handle_test_connection_error(request_id, exc),
        )

    def _handle_test_connection_success(self, request_id: int, models: list[str]) -> None:
        if request_id != self._request_id:
            return
        preview = ", ".join(models[:3])
        suffix = " ..." if len(models) > 3 else ""
        self.status_label.setText(
            f"Connection successful. Found {len(models)} models"
            f"{': ' + preview + suffix if preview else '.'}"
        )
        self._set_fetch_busy(False)

    def _handle_test_connection_error(self, request_id: int, exc: Exception) -> None:
        if request_id != self._request_id:
            return
        self.status_label.setText(f"Connection test failed: {exc}")
        self._set_fetch_busy(False)

    def accept(self) -> None:
        self._config.update_ai_settings(
            api_url=self.api_url_input.text(),
            api_key=self.api_key_input.text(),
            model=self.model_combo.currentText(),
            proxy=self.proxy_input.text(),
            proxy_enabled=self.proxy_enabled_checkbox.isChecked(),
        )
        super().accept()
