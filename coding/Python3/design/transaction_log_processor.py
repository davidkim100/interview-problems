"""
Problem: Transaction Log Processor

Process a log of payment transactions to compute what each merchant is owed.
Each transaction has an id, merchant, amount in minor units (cents), type, and timestamp.

transactions = [
    {"id": "tx1", "merchant": "acme",   "amount_cents": 10_000, "type": "charge",  "ts": "2026-01-10T09:00:00Z"},
    {"id": "tx2", "merchant": "acme",   "amount_cents":  2_500, "type": "refund",  "ts": "2026-01-10T11:30:00Z"},
    {"id": "tx3", "merchant": "globex", "amount_cents":  5_000, "type": "charge",  "ts": "2026-01-11T14:00:00Z"},
]

Part 1 — Net volume per merchant:
    process(transactions) -> {"acme": {"gross": 10_000, "fees": 320, "net": 7_180},
                              "globex": {"gross": 5_000, "fees": 175, "net": 4_825}}
    Charges add, refunds subtract. Unrecognized types raise ValueError.

Part 2 — Fees:
    Fee per charge = round_half_up(amount * 2.9%) + 30 cents.
    Refunds reduce net payable but do not generate a fee.
    All arithmetic stays in integer cents.

Part 3 — Dedup:
    At-least-once delivery means duplicate IDs can appear.
    Policy: keep the earliest record by timestamp; if a later duplicate disagrees
    on amount/merchant/type, flag it as a conflict.

Part 4 — Idempotent streaming:
    processor = TransactionProcessor(fee_bps=290, fee_fixed_cents=30)
    processor.ingest(record)     # idempotent: repeated id is a no-op
    processor.payable("acme")    # current net payable for acme

Stretch — Bounded memory:
    Optional dedup_window (timedelta) evicts seen-IDs older than the window,
    trading acceptance of very-late replays for bounded memory growth.
"""

from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
import threading


class TransactionType(Enum):
    CHARGE = "charge"
    REFUND = "refund"


@dataclass
class Transaction:
    id: str
    merchant: str
    amount: int
    type: TransactionType
    timestamp: str


@dataclass
class Account:
    gross: int = 0
    fees: int = 0
    net: int = 0


class TransactionProcessor:
    def __init__(self, fee_bps: int = 290, fee_fixed_cents: int = 30,
                 dedup_window: timedelta | None = None):
        self.fee_bps = fee_bps
        self.fee_fixed_cents = fee_fixed_cents
        self._seen: OrderedDict[str, Transaction] = OrderedDict()
        self._accounts: defaultdict[str, Account] = defaultdict(Account)
        self._lock = threading.Lock()
        self._dedup_window = dedup_window
        self.conflicts: list[tuple[Transaction, Transaction]] = []

    @staticmethod
    def _parse(raw: dict) -> Transaction:
        try:
            tx_type = TransactionType(raw["type"])
        except ValueError:
            raise ValueError(f"unrecognized transaction type: {raw['type']!r}")
        return Transaction(
            id=raw["id"],
            merchant=raw["merchant"],
            amount=raw["amount_cents"],
            type=tx_type,
            timestamp=raw["ts"],
        )

    def _calculate_fee(self, amount: int) -> int:
        # Round-half-up on the percentage part, then add fixed per-charge fee.
        # All integer math: amount * fee_bps is exact, +5000 biases for rounding.
        return (amount * self.fee_bps + 5_000) // 10_000 + self.fee_fixed_cents

    def _apply(self, tx: Transaction):
        acct = self._accounts[tx.merchant]
        if tx.type == TransactionType.CHARGE:
            fee = self._calculate_fee(tx.amount)
            acct.gross += tx.amount
            acct.fees += fee
            acct.net += tx.amount - fee
        elif tx.type == TransactionType.REFUND:
            acct.net -= tx.amount

    def _evict_old_ids(self, current_ts: str):
        """Bounded-memory stretch: drop seen-IDs older than the dedup window."""
        if self._dedup_window is None:
            return
        cutoff = datetime.fromisoformat(current_ts) - self._dedup_window
        while self._seen:
            oldest_id, oldest_tx = next(iter(self._seen.items()))
            if datetime.fromisoformat(oldest_tx.timestamp) < cutoff:
                del self._seen[oldest_id]
            else:
                break

    def _dedup(self, tx: Transaction) -> bool:
        """Returns True if this transaction should be processed (first time seen)."""
        self._evict_old_ids(tx.timestamp)
        if tx.id not in self._seen:
            self._seen[tx.id] = tx
            return True
        existing = self._seen[tx.id]
        if (existing.amount != tx.amount
                or existing.merchant != tx.merchant
                or existing.type != tx.type):
            self.conflicts.append((existing, tx))
            print(f"CONFLICT: tx {tx.id} differs from earlier record; keeping earliest")
        return False

    def ingest(self, raw: dict):
        tx = self._parse(raw)
        with self._lock:
            if self._dedup(tx):
                self._apply(tx)

    def payable(self, merchant: str) -> int:
        with self._lock:
            return self._accounts[merchant].net

    def process(self, transactions: list[dict]) -> dict:
        parsed = [self._parse(t) for t in transactions]
        for tx in parsed:
            if self._dedup(tx):
                self._apply(tx)
        return {
            merchant: {"gross": acct.gross, "fees": acct.fees, "net": acct.net}
            for merchant, acct in self._accounts.items()
        }


def test():
    transactions = [
        {"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:00Z"},
        {"id": "tx2", "merchant": "acme", "amount_cents": 2_500, "type": "refund", "ts": "2026-01-10T11:30:00Z"},
        {"id": "tx3", "merchant": "globex", "amount_cents": 5_000, "type": "charge", "ts": "2026-01-11T14:00:00Z"},
    ]
    tp = TransactionProcessor()
    result = tp.process(transactions)
    assert result == {
        "acme": {"gross": 10_000, "fees": 320, "net": 7_180},
        "globex": {"gross": 5_000, "fees": 175, "net": 4_825},
    }, f"Part 2 failed: {result}"
    print(f"Part 2 OK: {result}")

    transactions_with_dupes = [
        {"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:00Z"},
        {"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:05Z"},
        {"id": "tx2", "merchant": "acme", "amount_cents": 2_500, "type": "refund", "ts": "2026-01-10T11:30:00Z"},
        {"id": "tx3", "merchant": "globex", "amount_cents": 5_000, "type": "charge", "ts": "2026-01-11T14:00:00Z"},
    ]
    tp2 = TransactionProcessor()
    result2 = tp2.process(transactions_with_dupes)
    assert result2 == result, f"Part 3 dedup failed: {result2}"
    print(f"Part 3 dedup OK: {result2}")

    transactions_with_conflict = [
        {"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:00Z"},
        {"id": "tx1", "merchant": "acme", "amount_cents": 80_000, "type": "charge", "ts": "2026-01-10T09:01:00Z"},
    ]
    tp3 = TransactionProcessor()
    tp3.process(transactions_with_conflict)
    assert len(tp3.conflicts) == 1, f"Conflict detection failed: {tp3.conflicts}"
    print(f"Part 3 conflict OK: {tp3.conflicts[0][0].amount} vs {tp3.conflicts[0][1].amount}")

    tp4 = TransactionProcessor(fee_bps=290, fee_fixed_cents=30)
    for raw in transactions:
        tp4.ingest(raw)
    assert tp4.payable("acme") == 7_180, f"Part 4 acme failed: {tp4.payable('acme')}"
    assert tp4.payable("globex") == 4_825, f"Part 4 globex failed: {tp4.payable('globex')}"
    print(f"Part 4 streaming OK: acme={tp4.payable('acme')}, globex={tp4.payable('globex')}")

    tp5 = TransactionProcessor()
    tp5.ingest({"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:00Z"})
    tp5.ingest({"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:05Z"})
    assert tp5.payable("acme") == 9_680, f"Part 4 idempotent failed: {tp5.payable('acme')}"
    print(f"Part 4 idempotent OK: acme={tp5.payable('acme')}")

    print("\nAll tests passed.")


if __name__ == "__main__":
    test()
