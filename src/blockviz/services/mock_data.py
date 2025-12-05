"""Temporary mocked blockchain data sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import choices, randint, random

HEX_CHARS = "0123456789abcdef"


@dataclass(slots=True)
class NetworkStats:
    blocks_last_24h: int
    avg_block_time: float
    gas_price_gwei: float
    tx_volume: float


@dataclass(slots=True)
class BlockSummary:
    block_number: int
    producer: str
    timestamp: datetime
    tx_count: int
    gas_used: float


@dataclass(slots=True)
class TransactionSummary:
    tx_hash: str
    from_address: str
    to_address: str
    value_eth: float
    timestamp: datetime


@dataclass(slots=True)
class AccountSummary:
    address: str
    balance_eth: float
    tx_count: int
    last_active: datetime


def _random_hex(prefix: str, length: int) -> str:
    return prefix + "".join(choices(HEX_CHARS, k=length))


def generate_network_stats() -> NetworkStats:
    """Return pseudo-randomized stats for UI placeholders."""
    return NetworkStats(
        blocks_last_24h=6500 + randint(-120, 120),
        avg_block_time=12.1 + random(),
        gas_price_gwei=24.5 + random() * 10,
        tx_volume=1.2 + random() * 0.4,
    )


def recent_blocks(limit: int = 6) -> list[BlockSummary]:
    """Return fake recent blocks with descending block numbers."""
    base = 19_500_000
    now = datetime.now(tz=timezone.utc)
    blocks: list[BlockSummary] = []
    for idx in range(limit):
        block_number = base - idx
        blocks.append(
            BlockSummary(
                block_number=block_number,
                producer=f"Validator {randint(1, 1000)}",
                timestamp=now - timedelta(minutes=idx * 2),
                tx_count=randint(150, 380),
                gas_used=29 + random() * 5,
            )
        )
    return blocks


def recent_transactions(limit: int = 8) -> list[TransactionSummary]:
    """Generate pseudo transaction rows."""
    now = datetime.now(tz=timezone.utc)
    rows: list[TransactionSummary] = []
    for idx in range(limit):
        rows.append(
            TransactionSummary(
                tx_hash=_random_hex("0x", 64),
                from_address=_random_hex("0x", 40),
                to_address=_random_hex("0x", 40),
                value_eth=round(random() * 3, 4),
                timestamp=now - timedelta(minutes=idx * 3 + randint(0, 5)),
            )
        )
    return rows


def top_accounts(limit: int = 5) -> list[AccountSummary]:
    """Generate placeholder accounts summary."""
    now = datetime.now(tz=timezone.utc)
    accounts: list[AccountSummary] = []
    for idx in range(limit):
        accounts.append(
            AccountSummary(
                address=_random_hex("0x", 40),
                balance_eth=round(120 + random() * 500, 2),
                tx_count=randint(200, 1200),
                last_active=now - timedelta(hours=idx * 4 + randint(0, 2)),
            )
        )
    return accounts
