"""Configuration helpers for BlockViz."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from os import getenv
from pathlib import Path

CONFIG_PATH = Path.home() / ".blockviz.json"


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


@dataclass(slots=True)
class AppConfig:
    """Top-level runtime configuration."""

    custom_rpc_url: str = "http://127.0.0.1:8545"
    ai_api_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_proxy: str = ""
    ai_proxy_enabled: bool = False

    def __post_init__(self) -> None:
        self._load_from_disk()
        self._load_from_env()

    def _load_from_disk(self) -> None:
        if not CONFIG_PATH.exists():
            return
        try:
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.custom_rpc_url = str(payload.get("custom_rpc_url", self.custom_rpc_url)).strip() or self.custom_rpc_url
        self.ai_api_url = str(payload.get("ai_api_url", self.ai_api_url)).strip()
        self.ai_api_key = str(payload.get("ai_api_key", self.ai_api_key)).strip()
        self.ai_model = str(payload.get("ai_model", self.ai_model)).strip()
        self.ai_proxy = str(payload.get("ai_proxy", self.ai_proxy)).strip()
        self.ai_proxy_enabled = _coerce_bool(payload.get("ai_proxy_enabled", self.ai_proxy_enabled))

    def _load_from_env(self) -> None:
        env_url = getenv("BLOCKVIZ_RPC_URL", "").strip()
        if env_url:
            self.custom_rpc_url = env_url
        env_ai_url = getenv("BLOCKVIZ_AI_API_URL", "").strip()
        if env_ai_url:
            self.ai_api_url = env_ai_url
        env_ai_key = getenv("BLOCKVIZ_AI_API_KEY", "").strip()
        if env_ai_key:
            self.ai_api_key = env_ai_key
        env_ai_model = getenv("BLOCKVIZ_AI_MODEL", "").strip()
        if env_ai_model:
            self.ai_model = env_ai_model
        env_ai_proxy = getenv("BLOCKVIZ_AI_PROXY", "").strip()
        if env_ai_proxy:
            self.ai_proxy = env_ai_proxy
            self.ai_proxy_enabled = True

    def _persist(self) -> None:
        try:
            CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def resolve_rpc(self) -> str:
        """Return the currently configured RPC URL (may be empty)."""
        return self.custom_rpc_url

    def update_rpc_url(self, url: str) -> None:
        """Persist a user-supplied RPC endpoint."""
        self.custom_rpc_url = url.strip()
        self._persist()

    def update_ai_settings(self, *, api_url: str, api_key: str, model: str, proxy: str, proxy_enabled: bool) -> None:
        """Persist AI analysis settings."""
        self.ai_api_url = api_url.strip()
        self.ai_api_key = api_key.strip()
        self.ai_model = model.strip()
        self.ai_proxy_enabled = proxy_enabled
        self.ai_proxy = proxy.strip() if proxy_enabled else ""
        self._persist()


APP_CONFIG: AppConfig = AppConfig()
