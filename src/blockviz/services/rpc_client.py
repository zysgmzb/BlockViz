"""JSON-RPC helper utilities for Ethereum-compatible nodes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

import requests

SECONDS_TO_MS = 1000
WEI_IN_ETH = 10**18
GWEI_IN_WEI = 10**9


class RpcError(RuntimeError):
    """Raised when the remote node returns an error."""


def _hex_to_int(value: str | None) -> int:
    if not value:
        return 0
    return int(value, 16)


def _wei_to_eth(value: str | None) -> float:
    return _hex_to_int(value) / WEI_IN_ETH


def _wei_to_gwei(value: str | None) -> float:
    return _hex_to_int(value) / GWEI_IN_WEI


def _to_datetime(value: str | None) -> datetime:
    return datetime.fromtimestamp(_hex_to_int(value), tz=timezone.utc)


def _hex_data_size(value: str | None) -> int:
    if not value or value == "0x":
        return 0
    payload = value[2:] if value.startswith("0x") else value
    return len(payload) // 2


def _method_id(value: str | None) -> str | None:
    if not value or value == "0x":
        return None
    payload = value[2:] if value.startswith("0x") else value
    if len(payload) < 8:
        return None
    return f"0x{payload[:8]}"


@dataclass(slots=True)
class BlockInfo:
    number: int
    hash: str
    parent_hash: str
    miner: str
    timestamp: datetime
    tx_count: int
    gas_used: int
    gas_limit: int
    base_fee_gwei: float | None
    size_bytes: int
    nonce: str | None = None
    state_root: str | None = None
    transactions_root: str | None = None
    receipts_root: str | None = None
    sha3_uncles: str | None = None
    extra_data: str | None = None
    difficulty: int | None = None
    total_difficulty: int | None = None
    transactions: list["TransactionInfo"] | None = None


@dataclass(slots=True)
class TransactionInfo:
    tx_hash: str
    from_address: str
    to_address: str | None
    value_eth: float
    block_number: int
    timestamp: datetime
    gas_price_gwei: float | None
    max_fee_gwei: float | None
    max_priority_gwei: float | None
    gas_used: int | None
    status: str | None
    nonce: int
    input_data: str
    tx_type: int | None = None
    gas_limit: int | None = None
    transaction_index: int | None = None
    chain_id: int | None = None
    block_hash: str | None = None
    v: str | None = None
    r: str | None = None
    s: str | None = None
    y_parity: int | None = None
    effective_gas_price_gwei: float | None = None
    total_fee_eth: float | None = None
    cumulative_gas_used: int | None = None
    contract_address: str | None = None
    logs_count: int | None = None
    input_size_bytes: int = 0
    method_id: str | None = None
    access_list_entries: int | None = None
    blob_versioned_hashes: int | None = None
    max_fee_per_blob_gwei: float | None = None
    blob_gas_used: int | None = None
    blob_gas_price_gwei: float | None = None


@dataclass(slots=True)
class AccountInfo:
    address: str
    balance_eth: float
    tx_count: int


class RpcClient:
    """Thin wrapper around Ethereum JSON-RPC endpoints."""

    def __init__(self, endpoint: str, *, timeout: float = 12.0) -> None:
        self.endpoint = endpoint.strip()
        self.timeout = timeout
        self._session = requests.Session()
        self._request_id = 0

    def _call(self, method: str, params: Iterable[Any] | None = None) -> Any:
        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": list(params or []),
        }
        try:
            response = self._session.post(self.endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise RpcError(f"Network error: {exc}") from exc
        except ValueError as exc:
            raise RpcError("Malformed JSON response") from exc
        if "error" in data:
            error = data["error"]
            raise RpcError(f"{error.get('code')}: {error.get('message')}")
        return data.get("result")

    def _build_transaction_info(
        self,
        tx: dict[str, Any],
        *,
        timestamp: datetime,
        receipt: dict[str, Any] | None = None,
    ) -> TransactionInfo:
        status = None
        gas_used = None
        effective_gas_price_gwei = None
        total_fee_eth = None
        cumulative_gas_used = None
        contract_address = None
        logs_count = None
        blob_gas_used = None
        blob_gas_price_gwei = None

        if receipt:
            status_hex = receipt.get("status")
            gas_used = _hex_to_int(receipt.get("gasUsed"))
            cumulative_gas_used = _hex_to_int(receipt.get("cumulativeGasUsed"))
            contract_address = receipt.get("contractAddress")
            logs_count = len(receipt.get("logs", []))
            blob_gas_used = _hex_to_int(receipt.get("blobGasUsed")) if receipt.get("blobGasUsed") else None
            blob_gas_price_gwei = (
                _wei_to_gwei(receipt.get("blobGasPrice")) if receipt.get("blobGasPrice") else None
            )
            if status_hex is not None:
                status = "Success" if int(status_hex, 16) == 1 else "Failed"
            effective_gas_price_wei = _hex_to_int(receipt.get("effectiveGasPrice"))
            if effective_gas_price_wei:
                effective_gas_price_gwei = effective_gas_price_wei / GWEI_IN_WEI
            if gas_used is not None and effective_gas_price_wei:
                total_fee_eth = (gas_used * effective_gas_price_wei) / WEI_IN_ETH
        elif not tx.get("blockNumber"):
            status = "Pending"

        access_list = tx.get("accessList")
        blob_hashes = tx.get("blobVersionedHashes")

        return TransactionInfo(
            tx_hash=tx.get("hash", ""),
            from_address=tx.get("from", ""),
            to_address=tx.get("to"),
            value_eth=_wei_to_eth(tx.get("value")),
            block_number=_hex_to_int(tx.get("blockNumber")),
            timestamp=timestamp,
            gas_price_gwei=_wei_to_gwei(tx.get("gasPrice")) if tx.get("gasPrice") else None,
            max_fee_gwei=_wei_to_gwei(tx.get("maxFeePerGas")) if tx.get("maxFeePerGas") else None,
            max_priority_gwei=_wei_to_gwei(tx.get("maxPriorityFeePerGas")) if tx.get("maxPriorityFeePerGas") else None,
            gas_used=gas_used,
            status=status,
            nonce=_hex_to_int(tx.get("nonce")),
            input_data=tx.get("input", ""),
            tx_type=_hex_to_int(tx.get("type")) if tx.get("type") is not None else None,
            gas_limit=_hex_to_int(tx.get("gas")) if tx.get("gas") is not None else None,
            transaction_index=_hex_to_int(tx.get("transactionIndex")) if tx.get("transactionIndex") is not None else None,
            chain_id=_hex_to_int(tx.get("chainId")) if tx.get("chainId") is not None else None,
            block_hash=tx.get("blockHash"),
            v=tx.get("v"),
            r=tx.get("r"),
            s=tx.get("s"),
            y_parity=_hex_to_int(tx.get("yParity")) if tx.get("yParity") is not None else None,
            effective_gas_price_gwei=effective_gas_price_gwei,
            total_fee_eth=total_fee_eth,
            cumulative_gas_used=cumulative_gas_used,
            contract_address=contract_address,
            logs_count=logs_count,
            input_size_bytes=_hex_data_size(tx.get("input")),
            method_id=_method_id(tx.get("input")),
            access_list_entries=len(access_list) if access_list is not None else None,
            blob_versioned_hashes=len(blob_hashes) if blob_hashes is not None else None,
            max_fee_per_blob_gwei=_wei_to_gwei(tx.get("maxFeePerBlobGas")) if tx.get("maxFeePerBlobGas") else None,
            blob_gas_used=blob_gas_used,
            blob_gas_price_gwei=blob_gas_price_gwei,
        )

    def verify(self) -> None:
        """Perform a lightweight call to ensure the endpoint is reachable."""
        self.latest_block_number()

    def latest_block_number(self) -> int:
        return _hex_to_int(self._call("eth_blockNumber"))

    def gas_price_gwei(self) -> float:
        return _wei_to_gwei(self._call("eth_gasPrice"))

    def get_block(self, identifier: int | str, *, full_transactions: bool = False) -> BlockInfo:
        if isinstance(identifier, int):
            tag = hex(identifier)
        else:
            identifier = identifier.strip()
            if identifier.isdigit():
                tag = hex(int(identifier))
            else:
                tag = identifier
        block = self._call("eth_getBlockByNumber", [tag, full_transactions])
        if block is None:
            raise RpcError("Block not found")
        tx_field = block.get("transactions", [])
        tx_count = len(tx_field)
        base_fee = block.get("baseFeePerGas")
        transactions: list[TransactionInfo] | None = None
        if full_transactions:
            block_timestamp = _to_datetime(block.get("timestamp"))
            transactions = [self._build_transaction_info(entry, timestamp=block_timestamp) for entry in tx_field]
        return BlockInfo(
            number=_hex_to_int(block.get("number")),
            hash=block.get("hash", ""),
            parent_hash=block.get("parentHash", ""),
            miner=block.get("miner", ""),
            timestamp=_to_datetime(block.get("timestamp")),
            tx_count=tx_count,
            gas_used=_hex_to_int(block.get("gasUsed")),
            gas_limit=_hex_to_int(block.get("gasLimit")),
            base_fee_gwei=_wei_to_gwei(base_fee) if base_fee else None,
            size_bytes=_hex_to_int(block.get("size")),
            nonce=block.get("nonce"),
            state_root=block.get("stateRoot"),
            transactions_root=block.get("transactionsRoot"),
            receipts_root=block.get("receiptsRoot"),
            sha3_uncles=block.get("sha3Uncles"),
            extra_data=block.get("extraData"),
            difficulty=_hex_to_int(block.get("difficulty")) if block.get("difficulty") is not None else None,
            total_difficulty=_hex_to_int(block.get("totalDifficulty")) if block.get("totalDifficulty") is not None else None,
            transactions=transactions,
        )

    def fetch_recent_blocks(self, count: int = 6) -> list[BlockInfo]:
        latest = self.latest_block_number()
        blocks: list[BlockInfo] = []
        for offset in range(count):
            number = latest - offset
            if number < 0:
                break
            blocks.append(self.get_block(number, full_transactions=False))
        return blocks

    def fetch_recent_transactions(self, limit: int = 10) -> list[TransactionInfo]:
        latest = self.latest_block_number()
        transactions: list[TransactionInfo] = []
        number = latest
        while len(transactions) < limit and number >= 0:
            block_tag = hex(number)
            block = self._call("eth_getBlockByNumber", [block_tag, True])
            if block is None:
                number -= 1
                continue
            timestamp = _to_datetime(block.get("timestamp"))
            for tx in reversed(block.get("transactions", [])):
                transactions.append(self._build_transaction_info(tx, timestamp=timestamp))
                if len(transactions) >= limit:
                    break
            number -= 1
        return transactions

    def get_transaction(self, tx_hash: str) -> TransactionInfo:
        tx_hash = tx_hash.strip()
        tx = self._call("eth_getTransactionByHash", [tx_hash])
        if tx is None:
            raise RpcError("Transaction not found")
        block = self._call("eth_getBlockByNumber", [tx.get("blockNumber"), False]) if tx.get("blockNumber") else None
        receipt = self._call("eth_getTransactionReceipt", [tx_hash])
        timestamp = _to_datetime(block["timestamp"]) if block else datetime.now(tz=timezone.utc)
        return self._build_transaction_info(tx, timestamp=timestamp, receipt=receipt)

    def get_account(self, address: str) -> AccountInfo:
        address = address.strip()
        if not address.startswith("0x"):
            raise RpcError("Address must start with 0x")
        balance = _wei_to_eth(self._call("eth_getBalance", [address, "latest"]))
        tx_count = _hex_to_int(self._call("eth_getTransactionCount", [address, "latest"]))
        return AccountInfo(address=address, balance_eth=balance, tx_count=tx_count)

    def get_code(self, address: str) -> str:
        address = address.strip()
        if not address.startswith("0x"):
            raise RpcError("Address must start with 0x")
        return self._call("eth_getCode", [address, "latest"]) or "0x"

    def fetch_transactions_for_address(self, address: str, limit: int = 10, max_blocks: int = 2000) -> list[TransactionInfo]:
        """Scan backwards through recent blocks for transactions involving the address."""
        address = address.lower()
        latest = self.latest_block_number()
        results: list[TransactionInfo] = []
        number = latest
        scanned = 0
        while len(results) < limit and number >= 0 and scanned < max_blocks:
            block_tag = hex(number)
            block = self._call("eth_getBlockByNumber", [block_tag, True])
            scanned += 1
            if block is None:
                number -= 1
                continue
            timestamp = _to_datetime(block.get("timestamp"))
            txs = block.get("transactions", [])
            for tx in txs:
                from_addr = (tx.get("from") or "").lower()
                to_addr = (tx.get("to") or "").lower()
                if from_addr == address or (tx.get("to") and to_addr == address):
                    results.append(self._build_transaction_info(tx, timestamp=timestamp))
                    if len(results) >= limit:
                        break
            number -= 1
        return results
