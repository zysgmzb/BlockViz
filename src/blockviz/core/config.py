"""Configuration helpers for BlockViz."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(slots=True)
class AppConfig:
    """Top-level runtime configuration."""

    custom_rpc_url: str = "http://127.0.0.1:8545"

    def __post_init__(self) -> None:
        env_url = getenv("BLOCKVIZ_RPC_URL", "").strip()
        if env_url:
            self.custom_rpc_url = env_url

    def resolve_rpc(self) -> str:
        """Return the currently configured RPC URL (may be empty)."""
        return self.custom_rpc_url

    def update_rpc_url(self, url: str) -> None:
        """Persist a user-supplied RPC endpoint."""
        self.custom_rpc_url = url.strip()


APP_CONFIG: AppConfig = AppConfig()
