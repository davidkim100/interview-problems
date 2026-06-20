"""
Problem: Transaction Log Processor
You are processing a log of payment transactions to compute what each merchant is owed. Each transaction is a record with an id, a merchant, an amount in minor units (cents), a type, and a timestamp.
pythontransactions = [
    {"id": "tx1", "merchant": "acme",   "amount_cents": 10_000, "type": "charge",  "ts": "2026-01-10T09:00:00Z"},
    {"id": "tx2", "merchant": "acme",   "amount_cents":  2_500, "type": "refund",  "ts": "2026-01-10T11:30:00Z"},
    {"id": "tx3", "merchant": "globex", "amount_cents":  5_000, "type": "charge",  "ts": "2026-01-11T14:00:00Z"},
]
Before writing code, confirm with me: Are amounts always positive integers, with type carrying the sign? Can the same merchant appear in multiple currencies? Should a refund that exceeds prior charges be allowed, or flagged? How should I represent money in the output?
Part 1: Aggregate net volume per merchant
Write process(transactions) that returns the net amount per merchant, where a charge adds and a refund subtracts.
process(transactions)  ->  {"acme": 7_500, "globex": 5_000}
Keep money as integer cents throughout. Decide how you handle an unrecognized type.
Part 2: Calculate fees
Stripe takes a processing fee on charges. Compute the fee as 2.9% plus 30 cents per charge, and return, per merchant, the gross volume, total fees, and the net payable (gross minus fees), with refunds reducing the payable but not generating a fee.
process(transactions)
    ->  {
          "acme":   {"gross": 10_000, "fees": 320, "net": 7_180},
          "globex": {"gross":  5_000, "fees": 175, "net": 4_825},
        }
# acme fee:   round(10000 * 0.029) + 30 = 290 + 30 = 320
# acme net:   10000 - 320 - 2500 (refund) = 7180
Be deliberate about rounding: the percentage fee must resolve to whole cents, and you should state your rounding rule. Use integer math where you can.
Part 3: Deduplicate replayed records
The log is produced by an at-least-once delivery system, so the same transaction can appear more than once with the same id. A duplicate id is the same economic event and must be counted only once.
pythontransactions_with_dupes = [
    {"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:00Z"},
    {"id": "tx1", "merchant": "acme", "amount_cents": 10_000, "type": "charge", "ts": "2026-01-10T09:00:05Z"},  # replay
    {"id": "tx2", "merchant": "acme", "amount_cents":  2_500, "type": "refund", "ts": "2026-01-10T11:30:00Z"},
]
# tx1 must be counted once, not twice
Extend process to dedupe by id before aggregating. Then decide: what if two records share an id but disagree on amount or merchant (a genuine conflict, not a clean replay)? Choose a policy (for example, keep the earliest by timestamp and flag the conflict) and justify it.
Part 4: Idempotent streaming
The real system does not hand you the full list at once; records arrive one at a time and you may be asked for the current totals at any point. Refactor into a class that ingests one record at a time, ignores ids it has already seen, and answers a balance query on demand.
pythonprocessor = TransactionProcessor(fee_bps=290, fee_fixed_cents=30)
processor.ingest(record)        # idempotent: a repeated id is a no-op
processor.payable("acme")       # -> current net payable for acme
Stretch, if time remains: bound memory. You cannot keep every id forever in a long-running stream. Discuss (or implement) an approach that still rejects recent replays without unbounded growth, for example a time-windowed set of seen ids, and name the tradeoff you are accepting.
"""

from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import threading

MERCHANT = "merchant"
AMOUNT = "amount_cents"
TYPE = "type"
CHARGE = "charge"
REFUND = "refund"
GROSS = "gross"
FEES = "fees"
NET = "net"
account_lock = threading.Lock()

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
    gross: float = 0
    fees: float = 0
    net: float = 0


class TransactionProcessor:
    def __init__(self):
        self.alltransactions: defaultdict[str, list[Transaction]] = defaultdict(
            list[Transaction]
        )
        self.accounts: defaultdict[str, Account] = defaultdict(Account)

    def payable(self, merchant: str) -> float:
        with account_lock:
            return self.accounts[merchant].net

    def _calculate_account(self, transaction: Transaction):
        merchant = transaction.merchant
        amount = transaction.amount

        fees = 0
        net = 0
        with account_lock:
            if transaction.type == CHARGE:
                self.accounts[merchant].gross += amount
                fees = amount * 0.029 + 30
                net = amount - fees
            elif transaction.type == REFUND:
                self.accounts[merchant].gross -= amount
                net -= amount

            self.accounts[merchant].fees += fees
            self.accounts[merchant].net += net

    def ingest(self, transaction_external: dict):
        transaction = Transaction(
            transaction_external["id"],
            transaction_external["merchant"],
            transaction_external["amount_cents"],
            transaction_external["type"],
            transaction_external["ts"],
        )
        if transaction.id in self.alltransactions:
            print("transaction ID already processed")
            return None
        self.alltransactions[transaction.id].append(transaction)
        self._calculate_account(transaction)

    def process(self, transactions_external: list[dict]) -> dict:
        for transaction in transactions_external:
            self.alltransactions[transaction["id"]].append(
                Transaction(
                    transaction["id"],
                    transaction["merchant"],
                    transaction["amount_cents"],
                    transaction["type"],
                    transaction["ts"],
                )
            )

        for transactions in self.alltransactions.items():
            transactions[1].sort(key=lambda transaction: transaction.timestamp)
            single_transaction = transactions[1][0]
            self._calculate_account(single_transaction)

        result = {}
        for merchant, account in self.accounts.items():
            result[merchant] = account.net
        return result


def test():
    transactions = [
        {
            "id": "tx1",
            "merchant": "acme",
            "amount_cents": 10_000,
            "type": "charge",
            "ts": "2026-01-10T09:00:00Z",
        },
        {
            "id": "tx2",
            "merchant": "acme",
            "amount_cents": 2_500,
            "type": "refund",
            "ts": "2026-01-10T11:30:00Z",
        },
        {
            "id": "tx3",
            "merchant": "globex",
            "amount_cents": 5_000,
            "type": "charge",
            "ts": "2026-01-11T14:00:00Z",
        },
        {
            "id": "tx1",
            "merchant": "acme",
            "amount_cents": 80_000,
            "type": "charge",
            "ts": "2026-01-10T09:01:00Z",
        },
    ]
    tp1 = TransactionProcessor()
    result = tp1.process(transactions)
    print(result)
    tp2 = TransactionProcessor()
    for trans in transactions:
        tp2.ingest(trans)
        print(f'acme account payable: {tp2.payable("acme")}')
        print(f'globex account payable: {tp2.payable("globex")}')

if __name__ == "__main__":
    test()
