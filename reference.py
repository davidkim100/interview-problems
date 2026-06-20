"""
Purpose: a practice reference that demonstrates the concepts, libraries,
class modeling, and testing patterns that show up in coding interviews.
Every section is self-contained so you can copy a pattern while practicing.

Run the demos:     python interview_reference.py
Run the tests:     pytest interview_reference.py -q

Calibrated for Python 3.10+ (uses modern type hints like list[int]).
"""

from __future__ import annotations

import csv
import io
import json
import threading
import time
import urllib.request
from abc import ABC, abstractmethod
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from functools import lru_cache, reduce, wraps
from heapq import nlargest
from typing import Callable, Iterable, Iterator, Optional


# ============================================================
# SECTION 1: FUNCTIONS, TYPE HINTS, ERRORS, DOCSTRINGS
# ============================================================
# The baseline quality signal. Clear names, type hints, a short docstring,
# explicit validation, and a custom exception instead of a bare raise.


class ValidationError(ValueError):
    """Raised when input fails a domain rule. Custom exceptions read better
    in reviews and let callers catch precisely."""


def parse_amount_cents(raw: str) -> int:
    """Convert a string like '12.50' into integer minor units (1250 cents).

    Money is represented as integer cents to avoid float rounding errors.
    Raises ValidationError on malformed input.
    """
    raw = raw.strip()
    if not raw:
        raise ValidationError("amount is empty")
    try:
        # Decimal parses decimal strings exactly, unlike float.
        dollars = Decimal(raw)
    except Exception as exc:  # noqa: BLE001 - re-raise as a domain error
        raise ValidationError(f"not a valid amount: {raw!r}") from exc
    cents = (dollars * 100).to_integral_value(rounding=ROUND_HALF_UP)
    return int(cents)


def safe_divide(numerator: float, denominator: float) -> Optional[float]:
    """Return the quotient, or None if dividing by zero. Returning Optional
    is often cleaner than raising for an expected, recoverable case."""
    if denominator == 0:
        return None
    return numerator / denominator


# ============================================================
# SECTION 2: DATACLASSES AND CLASS MODELING
# ============================================================
# Reaching for a dataclass instead of a raw tuple or dict is itself the
# readability signal interviewers reward.


@dataclass(frozen=True)
class Money:
    """An immutable money value. frozen=True makes it hashable and prevents
    accidental mutation. Stored as integer cents plus an ISO currency code."""

    cents: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.cents < 0:
            raise ValidationError("Money cannot be negative")
        if len(self.currency) != 3:
            raise ValidationError("currency must be a 3-letter code")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValidationError("cannot add different currencies")
        return Money(self.cents + other.cents, self.currency)

    @property
    def dollars(self) -> str:
        """Formatted display value. A @property exposes derived data without
        a method call at the call site."""
        return f"{self.cents / 100:.2f} {self.currency}"


@dataclass
class Transaction:
    """A mutable record. default_factory avoids the mutable-default-argument
    trap (a shared list across instances)."""

    id: str
    merchant: str
    amount: Money
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "Transaction":
        """An alternate constructor. classmethods are the idiomatic way to
        build an object from a different shape of input."""
        return cls(
            id=row["id"],
            merchant=row["merchant"],
            amount=Money(parse_amount_cents(row["amount"]), row.get("currency", "USD")),
        )


# ============================================================
# SECTION 3: ENUMS AND A STATE MACHINE
# ============================================================
# State machines model lifecycles (a charge, a refund) and come up directly
# in Stripe-style problems.


class ChargeState(Enum):
    CREATED = "created"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


# Allowed transitions as data, not nested if-statements.
_ALLOWED: dict[ChargeState, set[ChargeState]] = {
    ChargeState.CREATED: {ChargeState.CAPTURED},
    ChargeState.CAPTURED: {ChargeState.REFUNDED, ChargeState.DISPUTED},
    ChargeState.REFUNDED: set(),
    ChargeState.DISPUTED: {ChargeState.REFUNDED},
}


class Charge:
    """A charge whose state can only change along allowed edges. Invalid
    transitions raise rather than silently corrupting state."""

    def __init__(self, charge_id: str) -> None:
        self.id = charge_id
        self.state = ChargeState.CREATED
        self.history: list[ChargeState] = [self.state]

    def transition(self, target: ChargeState) -> None:
        if target not in _ALLOWED[self.state]:
            raise ValidationError(f"illegal transition {self.state.value} -> {target.value}")
        self.state = target
        self.history.append(target)


# ============================================================
# SECTION 4: COLLECTIONS (defaultdict, Counter, deque)
# ============================================================


def net_volume_by_merchant(txns: Iterable[Transaction]) -> dict[str, int]:
    """Group and sum in one pass. defaultdict avoids key-existence checks."""
    totals: dict[str, int] = defaultdict(int)
    for t in txns:
        totals[t.merchant] += t.amount.cents
    return dict(totals)


def top_merchants(txns: Iterable[Transaction], k: int) -> list[tuple[str, int]]:
    """Counter plus most_common is the cleanest top-K when counting."""
    counter: Counter[str] = Counter()
    for t in txns:
        counter[t.merchant] += t.amount.cents
    return counter.most_common(k)


def sliding_window_max_sum(values: list[int], window: int) -> int:
    """deque is the right tool for sliding windows and BFS queues."""
    if window <= 0 or window > len(values):
        raise ValidationError("invalid window")
    q: deque[int] = deque(values[:window])
    best = current = sum(q)
    for v in values[window:]:
        current += v - q.popleft()
        q.append(v)
        best = max(best, current)
    return best


# ============================================================
# SECTION 5: itertools, functools, COMPREHENSIONS
# ============================================================


@lru_cache(maxsize=None)
def fib(n: int) -> int:
    """lru_cache memoizes pure functions. Useful for recursion with overlap."""
    return n if n < 2 else fib(n - 1) + fib(n - 2)


def total_with_reduce(amounts: list[int]) -> int:
    """reduce folds a sequence into one value. sum() is usually clearer, but
    reduce generalizes to any binary operation."""
    return reduce(lambda acc, x: acc + x, amounts, 0)


# ============================================================
# SECTION 6: PARSING (CSV with quoted fields, JSON)
# ============================================================
# The csv module handles quoted fields containing commas correctly. Hand-rolled
# str.split(',') does not, and that gap is a classic bug-squash defect.


def parse_csv(text: str) -> list[dict[str, str]]:
    """Parse CSV text into a list of row dicts using the header row."""
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def parse_json_records(text: str) -> list[dict]:
    """Parse a JSON array of objects, failing clearly on malformed input."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValidationError("expected a JSON array")
    return data


# ============================================================
# SECTION 7: GRAPHS (adjacency, BFS, DFS, cycle detection)
# ============================================================
# Nearly every Stripe coding problem decomposes into a graph. Currency
# conversion, dependency resolution, and routing are all graph problems.


def build_adjacency(edges: Iterable[tuple[str, str]]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for src, dst in edges:
        graph[src].append(dst)
    return dict(graph)


def has_path_bfs(graph: dict[str, list[str]], start: str, goal: str) -> bool:
    """Breadth-first reachability using a deque as a FIFO queue."""
    if start not in graph:
        return False
    seen = {start}
    q: deque[str] = deque([start])
    while q:
        node = q.popleft()
        if node == goal:
            return True
        for nxt in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return False


def has_cycle(graph: dict[str, list[str]]) -> bool:
    """DFS with three colors. A node currently on the recursion stack
    (in_progress) that is revisited indicates a cycle."""
    visited: set[str] = set()
    in_progress: set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        in_progress.add(node)
        for nxt in graph.get(node, []):
            if nxt in in_progress:
                return True
            if nxt not in visited and dfs(nxt):
                return True
        in_progress.discard(node)
        return False

    return any(dfs(n) for n in list(graph) if n not in visited)


def convert_currency(rates: dict[tuple[str, str], float], src: str, dst: str) -> Optional[float]:
    """The Evaluate Division / currency conversion pattern: a weighted graph
    where BFS accumulates the product of edge rates along a path. Returns the
    conversion factor from src to dst, or None if unreachable.

    rates maps (from, to) -> rate, and the reverse edge (to, from) -> 1/rate
    is added automatically.
    """
    graph: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (a, b), r in rates.items():
        graph[a].append((b, r))
        graph[b].append((a, 1 / r))

    if src not in graph or dst not in graph:
        return None
    seen = {src}
    q: deque[tuple[str, float]] = deque([(src, 1.0)])
    while q:
        node, acc = q.popleft()
        if node == dst:
            return acc
        for nxt, rate in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, acc * rate))
    return None


# ============================================================
# SECTION 8: HEAP / TOP-K
# ============================================================


def top_k_frequent(items: Iterable[str], k: int) -> list[str]:
    """Counting plus a heap. nlargest is O(n log k), better than a full sort
    when k is small relative to n."""
    counts = Counter(items)
    return [item for item, _ in nlargest(k, counts.items(), key=lambda kv: kv[1])]


# ============================================================
# SECTION 9: POLYMORPHISM WITH AN ABSTRACT BASE CLASS
# ============================================================
# Modeling fee rules as strategy objects keeps logic open for extension, which
# is exactly what the multi-part format rewards.


class FeeStrategy(ABC):
    @abstractmethod
    def fee_cents(self, amount_cents: int) -> int:
        ...


class FlatFee(FeeStrategy):
    def __init__(self, cents: int) -> None:
        self.cents = cents

    def fee_cents(self, amount_cents: int) -> int:
        return self.cents


class PercentageFee(FeeStrategy):
    def __init__(self, basis_points: int) -> None:
        # 1 basis point = 0.01%. Integer math avoids float drift.
        self.basis_points = basis_points

    def fee_cents(self, amount_cents: int) -> int:
        return amount_cents * self.basis_points // 10_000


def total_fees(amount_cents: int, strategies: list[FeeStrategy]) -> int:
    return sum(s.fee_cents(amount_cents) for s in strategies)


# ============================================================
# SECTION 10: IDEMPOTENCY CACHE WITH TTL (injectable clock)
# ============================================================
# Injecting the clock makes time-dependent code testable without sleeping.


Clock = Callable[[], float]


class IdempotencyCache:
    """Stores results keyed by an idempotency key, expiring after ttl seconds.
    The clock is injected so tests can advance time deterministically."""

    def __init__(self, ttl_seconds: float, clock: Clock = time.monotonic) -> None:
        self.ttl = ttl_seconds
        self.clock = clock
        self._store: dict[str, tuple[float, object]] = {}

    def get_or_set(self, key: str, compute: Callable[[], object]) -> object:
        now = self.clock()
        if key in self._store:
            stored_at, value = self._store[key]
            if now - stored_at < self.ttl:
                return value  # cache hit, do not recompute
        value = compute()
        self._store[key] = (now, value)
        return value


# ============================================================
# SECTION 11: TOKEN-BUCKET RATE LIMITER (injectable clock)
# ============================================================


class TokenBucket:
    """Allows up to `capacity` requests, refilling at `refill_per_sec`."""

    def __init__(self, capacity: float, refill_per_sec: float, clock: Clock = time.monotonic) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.clock = clock
        self.tokens = capacity
        self.last = clock()

    def allow(self) -> bool:
        now = self.clock()
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


# ============================================================
# SECTION 12: CONCURRENCY (the bug and the fix)
# ============================================================
# A non-atomic read-modify-write across threads loses updates. This is the
# classic bug-squash defect. The fix is a lock around the critical section.


class UnsafeCounter:
    def __init__(self) -> None:
        self.value = 0

    def increment(self) -> None:
        # BUG: read, add, write is not atomic. Concurrent threads interleave
        # and overwrite each other, so the final value is too low.
        current = self.value
        time.sleep(0)  # widen the race window to make the bug reproducible
        self.value = current + 1


class SafeCounter:
    def __init__(self) -> None:
        self.value = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:  # only one thread mutates at a time
            self.value += 1


def hammer(counter, threads: int, per_thread: int) -> int:
    """Run `threads` workers, each calling increment() `per_thread` times."""
    def worker() -> None:
        for _ in range(per_thread):
            counter.increment()

    with ThreadPoolExecutor(max_workers=threads) as pool:
        for _ in range(threads):
            pool.submit(worker)
    return counter.value


# ============================================================
# SECTION 13: INTEGRATION (HTTP, retry with backoff, pagination)
# ============================================================
# The retry decorator is fully testable offline by injecting a fake sleep and
# a flaky function. The HTTP helpers below are reference patterns; in a real
# integration round prefer `requests` if it is available.


def retry(times: int, base_delay: float = 0.5, sleep: Callable[[float], None] = time.sleep):
    """Decorator that retries on exception with exponential backoff.
    `sleep` is injectable so tests run instantly."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)  # preserves the wrapped function's name and docstring
        def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt < times - 1:
                        sleep(base_delay * (2 ** attempt))
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


def http_get_json(url: str, timeout: float = 5.0) -> dict:
    """Reference pattern using only the standard library. Handles status and
    decoding explicitly. Not exercised in the demo to avoid live network calls.
    """
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        if resp.status != 200:
            raise RuntimeError(f"unexpected status {resp.status}")
        return json.loads(resp.read().decode("utf-8"))


def paginate(fetch_page: Callable[[int], list], max_pages: int = 100) -> Iterator[object]:
    """Generator that yields items across pages until a page is empty.
    A generator streams results lazily instead of buffering everything."""
    for page in range(max_pages):
        items = fetch_page(page)
        if not items:
            return
        yield from items


# ============================================================
# SECTION 14: CONTEXT MANAGER (a small custom one)
# ============================================================


class timed:
    """Context manager that records elapsed time. Demonstrates __enter__ and
    __exit__. Use `with timed() as t: ...` then read t.elapsed."""

    def __enter__(self) -> "timed":
        self.start = time.monotonic()
        return self

    def __exit__(self, *exc) -> bool:
        self.elapsed = time.monotonic() - self.start
        return False  # do not suppress exceptions


# ============================================================
# SECTION 15: COMMON PYTHON GOTCHAS (annotated)
# ============================================================
# 1. Mutable default arguments: def f(x, acc=[]) shares one list across calls.
#    Fix: default to None, or use dataclass field(default_factory=list).
# 2. Float money: 0.1 + 0.2 != 0.3. Use integer cents or Decimal.
# 3. Dict ordering is insertion order in 3.7+, but do not rely on it for sets.
# 4. Late binding closures: [lambda: i for i in range(3)] all return 2.
#    Fix: capture with a default arg, lambda i=i: i.
# 5. Shallow copy: copy.copy on a nested structure shares inner objects.
#    Use copy.deepcopy when you need full isolation.


def mutable_default_trap_demo() -> tuple[list, list]:
    """Shows the trap and the fix side by side."""

    def buggy(item, acc=[]):  # noqa: B006 - intentional, for demonstration
        acc.append(item)
        return acc

    def fixed(item, acc=None):
        acc = [] if acc is None else acc
        acc.append(item)
        return acc

    buggy("a")
    second = buggy("b")  # second is ["a", "b"], the leaked shared list
    clean = fixed("a")  # always a fresh list
    return second, clean


# ============================================================
# DEMO RUNNER
# ============================================================


def _demo() -> None:
    print("Money:", Money(1250).dollars)

    txns = [
        Transaction.from_row({"id": "t1", "merchant": "acme", "amount": "10.00"}),
        Transaction.from_row({"id": "t2", "merchant": "acme", "amount": "5.50"}),
        Transaction.from_row({"id": "t3", "merchant": "globex", "amount": "20.00"}),
    ]
    print("Net by merchant:", net_volume_by_merchant(txns))
    print("Top merchant:", top_merchants(txns, 1))

    charge = Charge("c1")
    charge.transition(ChargeState.CAPTURED)
    charge.transition(ChargeState.REFUNDED)
    print("Charge history:", [s.value for s in charge.history])

    rates = {("USD", "EUR"): 0.9, ("EUR", "GBP"): 0.85}
    print("USD->GBP factor:", convert_currency(rates, "USD", "GBP"))

    graph = build_adjacency([("a", "b"), ("b", "c"), ("c", "a")])
    print("Has cycle:", has_cycle(graph))

    print("Fees on $100:", total_fees(10_000, [FlatFee(30), PercentageFee(290)]), "cents")

    unsafe = hammer(UnsafeCounter(), threads=8, per_thread=2_000)
    safe = hammer(SafeCounter(), threads=8, per_thread=2_000)
    print(f"Unsafe counter (expect < 16000): {unsafe}")
    print(f"Safe counter   (expect 16000):  {safe}")

    with timed() as t:
        fib(30)
    print(f"fib(30) took {t.elapsed:.4f}s (memoized)")


# ============================================================
# SECTION 16: PYTEST TESTS
# ============================================================
# Run with: pytest stripe_interview_reference.py -q
# Demonstrates plain asserts, parametrize, exception testing, fixtures, and a
# controllable fake clock for time-dependent code.

import pytest  # noqa: E402  (kept at the bottom so the file runs without pytest)


@pytest.mark.parametrize(
    "raw,expected",
    [("10.00", 1000), ("0.99", 99), ("12.5", 1250), (" 3 ", 300)],
)
def test_parse_amount_cents(raw, expected):
    assert parse_amount_cents(raw) == expected


def test_parse_amount_rejects_garbage():
    with pytest.raises(ValidationError):
        parse_amount_cents("abc")


def test_money_addition_and_currency_guard():
    assert (Money(100) + Money(50)).cents == 150
    with pytest.raises(ValidationError):
        Money(100, "USD") + Money(50, "EUR")


def test_illegal_state_transition():
    charge = Charge("c")
    with pytest.raises(ValidationError):
        charge.transition(ChargeState.REFUNDED)  # cannot refund before capture


def test_csv_handles_quoted_commas():
    text = 'id,note\n1,"hello, world"\n'
    rows = parse_csv(text)
    assert rows[0]["note"] == "hello, world"


def test_currency_conversion_path_and_missing():
    rates = {("USD", "EUR"): 0.9, ("EUR", "GBP"): 0.85}
    assert convert_currency(rates, "USD", "GBP") == pytest.approx(0.9 * 0.85)
    assert convert_currency(rates, "USD", "JPY") is None


def test_cycle_detection():
    assert has_cycle(build_adjacency([("a", "b"), ("b", "a")])) is True
    assert has_cycle(build_adjacency([("a", "b"), ("b", "c")])) is False


def test_top_k_frequent():
    assert set(top_k_frequent(["a", "a", "b", "b", "c"], 2)) == {"a", "b"}


def test_fee_strategies():
    # 2.9% + 30c on $100 = 290 + 30 = 320 cents.
    assert total_fees(10_000, [FlatFee(30), PercentageFee(290)]) == 320


class FakeClock:
    """A controllable clock for deterministic time-based tests."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_idempotency_cache_hits_then_expires():
    clock = FakeClock()
    cache = IdempotencyCache(ttl_seconds=10, clock=clock)
    calls = []

    def compute():
        calls.append(1)
        return "result"

    assert cache.get_or_set("k", compute) == "result"
    assert cache.get_or_set("k", compute) == "result"
    assert len(calls) == 1  # second call was a cache hit

    clock.advance(11)
    cache.get_or_set("k", compute)
    assert len(calls) == 2  # key expired, recomputed


def test_token_bucket_limits_and_refills():
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_per_sec=1, clock=clock)
    assert bucket.allow() is True
    assert bucket.allow() is True
    assert bucket.allow() is False  # bucket empty
    clock.advance(1)
    assert bucket.allow() is True  # one token refilled


def test_retry_succeeds_after_failures():
    attempts = {"n": 0}

    @retry(times=3, sleep=lambda _: None)  # inject no-op sleep
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    assert flaky() == "ok"
    assert attempts["n"] == 3


def test_retry_exhausts_and_raises():
    @retry(times=2, sleep=lambda _: None)
    def always_fails():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        always_fails()


def test_safe_counter_is_correct_under_threads():
    total = hammer(SafeCounter(), threads=8, per_thread=1_000)
    assert total == 8_000


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    """A fixture provides reusable setup to multiple tests."""
    return [
        Transaction("t1", "acme", Money(1000)),
        Transaction("t2", "acme", Money(550)),
        Transaction("t3", "globex", Money(2000)),
    ]


def test_net_volume_with_fixture(sample_transactions):
    totals = net_volume_by_merchant(sample_transactions)
    assert totals == {"acme": 1550, "globex": 2000}


def test_mutable_default_trap():
    leaked, clean = mutable_default_trap_demo()
    assert leaked == ["a", "b"]  # the bug: state leaked across calls
    assert clean == ["a"]  # the fix: fresh list each call


if __name__ == "__main__":
    _demo()
