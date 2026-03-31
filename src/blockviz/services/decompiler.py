"""Helpers for bytecode decompilation via heimdall-rs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


class DecompileError(RuntimeError):
    """Raised when bytecode decompilation fails."""


@dataclass(slots=True)
class DecompileArtifacts:
    bytecode: str
    source_code: str
    abi: str


def heimdall_available() -> bool:
    """Return whether the heimdall CLI is available in PATH."""
    return shutil.which("heimdall") is not None


def _safe_name(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-._")
    return sanitized or "contract"


def _read_optional(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback
    text = path.read_text(encoding="utf-8").strip()
    return text or fallback


def _format_abi(text: str) -> str:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    return json.dumps(payload, indent=2, ensure_ascii=False)


def decompile_bytecode(bytecode: str, *, name: str = "contract") -> DecompileArtifacts:
    """Run heimdall decompile and return bytecode, source, and ABI outputs."""
    normalized = bytecode.strip()
    if not normalized.startswith("0x") or normalized == "0x":
        raise DecompileError("No deployable contract bytecode available for decompilation.")
    if not heimdall_available():
        raise DecompileError("Heimdall CLI was not found in PATH.")

    safe_name = _safe_name(name)
    with tempfile.TemporaryDirectory(prefix="blockviz-heimdall-") as temp_dir:
        command = [
            "heimdall",
            "decompile",
            normalized,
            "--default",
            "--include-sol",
            "--output",
            temp_dir,
            "--name",
            safe_name,
            "--color",
            "never",
            "-q",
        ]
        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode != 0:
            message = (process.stderr or process.stdout or "Heimdall decompile failed.").strip()
            raise DecompileError(message)

        output_dir = Path(temp_dir)
        abi_path = output_dir / f"{safe_name}-abi.json"
        source_path = output_dir / f"{safe_name}-decompiled.sol"

        if not abi_path.exists():
            matches = sorted(output_dir.glob("*-abi.json"))
            if matches:
                abi_path = matches[0]
        if not source_path.exists():
            matches = sorted(output_dir.glob("*-decompiled.sol"))
            if matches:
                source_path = matches[0]

        abi_text = _read_optional(abi_path, "Heimdall did not produce an ABI output.")
        source_text = _read_optional(source_path, "Heimdall did not produce a Solidity source output.")

        return DecompileArtifacts(
            bytecode=normalized,
            source_code=source_text,
            abi=_format_abi(abi_text),
        )
