"""OpenAI-compatible client helpers for AI source polishing."""

from __future__ import annotations

from typing import Any

import requests


class AIClientError(RuntimeError):
    """Raised when the AI provider returns an error."""


class AIClient:
    """Minimal OpenAI-compatible API client."""

    def __init__(self, api_url: str, api_key: str, *, timeout: float = 60.0, proxy: str = "") -> None:
        self.api_url = api_url.strip().rstrip("/")
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.proxy = proxy.strip()
        self._session = requests.Session()
        self._session.trust_env = False
        if not self.api_url:
            raise AIClientError("API URL is required.")
        if not self.api_key:
            raise AIClientError("API key is required.")

    def _endpoint(self, path: str) -> str:
        if self.api_url.endswith("/v1"):
            return f"{self.api_url}{path}"
        return f"{self.api_url}/v1{path}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _proxies(self) -> dict[str, str] | None:
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}

    def _request(self, method: str, path: str, *, json_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self._session.request(
                method,
                self._endpoint(path),
                headers=self._headers(),
                json=json_payload,
                timeout=self.timeout,
                proxies=self._proxies(),
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise AIClientError(f"Network error: {exc}") from exc
        except ValueError as exc:
            raise AIClientError("Malformed JSON response from AI provider.") from exc
        if "error" in data:
            error = data["error"]
            if isinstance(error, dict):
                message = error.get("message") or str(error)
            else:
                message = str(error)
            raise AIClientError(message)
        return data

    def list_models(self) -> list[str]:
        data = self._request("GET", "/models")
        models = data.get("data", [])
        model_ids = sorted(str(entry.get("id", "")).strip() for entry in models if entry.get("id"))
        if not model_ids:
            raise AIClientError("No models returned by the provider.")
        return model_ids

    def polish_solidity(self, source_code: str, *, model: str) -> str:
        if not source_code.strip():
            raise AIClientError("No source code available for AI analysis.")
        if not model.strip():
            raise AIClientError("A model must be selected before analysis.")
        payload = {
            "model": model.strip(),
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert Solidity auditor and reverse engineer. "
                        "Improve readability of decompiled Solidity while preserving behavior. "
                        "Return only a single Solidity code block without markdown fences. "
                        "Prefer clearer names, formatting, comments, and conservative inferences. "
                        "If uncertain, keep original structure and add short explanatory comments."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Please rewrite the following decompiled Solidity into a more readable Solidity version. "
                        "Preserve semantics as much as possible.\n\n"
                        f"{source_code}"
                    ),
                },
            ],
        }
        data = self._request("POST", "/chat/completions", json_payload=payload)
        choices = data.get("choices", [])
        if not choices:
            raise AIClientError("AI provider returned no completion choices.")
        message = choices[0].get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise AIClientError("AI provider returned an empty analysis result.")
        if content.startswith("```"):
            lines = content.splitlines()
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
                content = "\n".join(lines[1:-1]).strip()
        return content
