/**
 * Purpose: a practice reference that demonstrates the concepts, standard library usage,
 * class modeling, and testing patterns that show up in coding interviews.
 * Every section is self-contained so you can copy a pattern while practicing.
 *
 * Compile & run demo:  javac Reference.java && java Reference
 * Run the tests:       java Reference --test
 *
 * Calibrated for Java 17+ (uses records, sealed interfaces, enhanced switch).
 */

import java.io.BufferedReader;
import java.io.StringReader;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalDouble;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Function;
import java.util.function.IntSupplier;
import java.util.function.Supplier;
import java.util.stream.Collectors;


public class Reference {

    // ============================================================
    // SECTION 1: METHODS, VALIDATION, CUSTOM EXCEPTIONS
    // ============================================================
    // The baseline quality signal. Clear names, Javadoc, explicit validation,
    // and a custom exception instead of a bare throw.

    static class ValidationException extends RuntimeException {
        ValidationException(String message) { super(message); }
        ValidationException(String message, Throwable cause) { super(message, cause); }
    }

    /** Convert a string like "12.50" into integer minor units (1250 cents).
     *  BigDecimal parses decimal strings exactly, unlike double. */
    static int parseAmountCents(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new ValidationException("amount is empty");
        }
        try {
            BigDecimal dollars = new BigDecimal(raw.strip());
            return dollars.multiply(BigDecimal.valueOf(100))
                    .setScale(0, RoundingMode.HALF_UP)
                    .intValueExact();
        } catch (NumberFormatException | ArithmeticException e) {
            throw new ValidationException("not a valid amount: '" + raw.strip() + "'", e);
        }
    }

    /** Return the quotient wrapped in an Optional, or empty if dividing by zero.
     *  Returning Optional is cleaner than throwing for an expected, recoverable case. */
    static OptionalDouble safeDivide(double numerator, double denominator) {
        if (denominator == 0) return OptionalDouble.empty();
        return OptionalDouble.of(numerator / denominator);
    }


    // ============================================================
    // SECTION 2: RECORDS AND CLASS MODELING (Java 16+)
    // ============================================================
    // Records replace the boilerplate of equals/hashCode/toString/getters.
    // Reaching for a record instead of a raw Map or Object[] is itself the
    // readability signal interviewers reward.

    record Money(int cents, String currency) {
        // Compact constructor: validation runs before field assignment.
        Money {
            if (cents < 0) throw new ValidationException("Money cannot be negative");
            if (currency.length() != 3)
                throw new ValidationException("currency must be a 3-letter code");
        }

        Money(int cents) { this(cents, "USD"); }

        Money add(Money other) {
            if (!this.currency.equals(other.currency))
                throw new ValidationException("cannot add different currencies");
            return new Money(this.cents + other.cents, this.currency);
        }

        /** Formatted display value. */
        String display() {
            return String.format("%.2f %s", cents / 100.0, currency);
        }
    }

    /** A mutable record-like class. Uses a factory method (fromRow) as an
     *  alternate constructor — the idiomatic way to build from a different input shape. */
    static class Transaction {
        private final String id;
        private final String merchant;
        private final Money amount;
        private final List<String> tags;

        Transaction(String id, String merchant, Money amount) {
            this(id, merchant, amount, new ArrayList<>());
        }

        Transaction(String id, String merchant, Money amount, List<String> tags) {
            this.id = id;
            this.merchant = merchant;
            this.amount = amount;
            this.tags = new ArrayList<>(tags); // defensive copy
        }

        static Transaction fromRow(Map<String, String> row) {
            return new Transaction(
                row.get("id"),
                row.get("merchant"),
                new Money(parseAmountCents(row.get("amount")),
                         row.getOrDefault("currency", "USD")));
        }

        String id()       { return id; }
        String merchant() { return merchant; }
        Money amount()    { return amount; }
        List<String> tags() { return tags; }
    }


    // ============================================================
    // SECTION 3: ENUMS AND A STATE MACHINE
    // ============================================================
    // Java enums are classes — they can hold fields, methods, and data.
    // State machines model lifecycles (a charge, a refund) and come up
    // directly in Stripe-style problems.

    enum ChargeState {
        CREATED, CAPTURED, REFUNDED, DISPUTED;

        // Allowed transitions as data, not nested if-statements.
        private static final Map<ChargeState, Set<ChargeState>> ALLOWED = Map.of(
            CREATED,  Set.of(CAPTURED),
            CAPTURED, Set.of(REFUNDED, DISPUTED),
            REFUNDED, Set.of(),
            DISPUTED, Set.of(REFUNDED));

        Set<ChargeState> allowedTransitions() { return ALLOWED.get(this); }
    }

    static class Charge {
        private final String id;
        private ChargeState state = ChargeState.CREATED;
        private final List<ChargeState> history = new ArrayList<>(List.of(ChargeState.CREATED));

        Charge(String id) { this.id = id; }

        void transition(ChargeState target) {
            if (!state.allowedTransitions().contains(target))
                throw new ValidationException(
                    "illegal transition " + state + " -> " + target);
            state = target;
            history.add(target);
        }

        ChargeState state() { return state; }
        List<ChargeState> history() { return Collections.unmodifiableList(history); }
    }


    // ============================================================
    // SECTION 4: COLLECTIONS (HashMap, merge, groupingBy, ArrayDeque)
    // ============================================================

    /** Group and sum in one pass. Map.merge avoids key-existence checks. */
    static Map<String, Integer> netVolumeByMerchant(List<Transaction> txns) {
        Map<String, Integer> totals = new HashMap<>();
        for (Transaction t : txns) {
            totals.merge(t.merchant(), t.amount().cents(), Integer::sum);
        }
        return totals;
    }

    /** Stream equivalent — groupingBy + summingInt. */
    static Map<String, Integer> netVolumeByMerchantStream(List<Transaction> txns) {
        return txns.stream().collect(
            Collectors.groupingBy(Transaction::merchant,
                Collectors.summingInt(t -> t.amount().cents())));
    }

    /** Top-K via stream sort. For large datasets, use a PriorityQueue (Section 8). */
    static List<Map.Entry<String, Integer>> topMerchants(List<Transaction> txns, int k) {
        Map<String, Integer> counts = new HashMap<>();
        for (Transaction t : txns) {
            counts.merge(t.merchant(), t.amount().cents(), Integer::sum);
        }
        return counts.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(k)
            .toList();
    }

    /** Sliding window — the right tool for fixed-width range queries. */
    static int slidingWindowMaxSum(int[] values, int window) {
        if (window <= 0 || window > values.length)
            throw new ValidationException("invalid window");
        int current = 0;
        for (int i = 0; i < window; i++) current += values[i];
        int best = current;
        for (int i = window; i < values.length; i++) {
            current += values[i] - values[i - window];
            best = Math.max(best, current);
        }
        return best;
    }


    // ============================================================
    // SECTION 5: STREAMS, LAMBDAS, MEMOIZATION
    // ============================================================

    /** Java has no @lru_cache, so memoize with a HashMap manually.
     *  Note: ConcurrentHashMap.computeIfAbsent deadlocks on recursive calls —
     *  use a plain HashMap for single-threaded recursion. */
    private static final Map<Integer, Long> FIB_CACHE = new HashMap<>();

    static long fib(int n) {
        if (n < 2) return n;
        if (FIB_CACHE.containsKey(n)) return FIB_CACHE.get(n);
        long result = fib(n - 1) + fib(n - 2);
        FIB_CACHE.put(n, result);
        return result;
    }

    /** Stream.reduce folds a sequence into one value. sum() via mapToInt is
     *  usually clearer, but reduce generalizes to any binary operation. */
    static int totalWithReduce(List<Integer> amounts) {
        return amounts.stream().reduce(0, Integer::sum);
    }


    // ============================================================
    // SECTION 6: PARSING (CSV with quoted fields)
    // ============================================================
    // Java's standard library has no CSV parser. Hand-rolled String.split(",")
    // breaks on quoted fields containing commas — the classic bug-squash defect.

    static List<Map<String, String>> parseCsv(String text) {
        List<Map<String, String>> result = new ArrayList<>();
        String[] lines = text.split("\n");
        if (lines.length < 2) return result;

        String[] headers = parseCsvLine(lines[0]);
        for (int i = 1; i < lines.length; i++) {
            if (lines[i].isBlank()) continue;
            String[] fields = parseCsvLine(lines[i]);
            Map<String, String> row = new LinkedHashMap<>();
            for (int j = 0; j < headers.length && j < fields.length; j++) {
                row.put(headers[j], fields[j]);
            }
            result.add(row);
        }
        return result;
    }

    /** Handles quoted fields: commas inside quotes are part of the value. */
    private static String[] parseCsvLine(String line) {
        List<String> fields = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inQuotes = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                inQuotes = !inQuotes;
            } else if (c == ',' && !inQuotes) {
                fields.add(sb.toString());
                sb.setLength(0);
            } else {
                sb.append(c);
            }
        }
        fields.add(sb.toString());
        return fields.toArray(String[]::new);
    }


    // ============================================================
    // SECTION 7: GRAPHS (adjacency, BFS, DFS, cycle detection)
    // ============================================================
    // Nearly every coding problem decomposes into a graph. Currency conversion,
    // dependency resolution, and routing are all graph problems.

    static Map<String, List<String>> buildAdjacency(String[][] edges) {
        Map<String, List<String>> graph = new HashMap<>();
        for (String[] edge : edges) {
            graph.computeIfAbsent(edge[0], k -> new ArrayList<>()).add(edge[1]);
        }
        return graph;
    }

    /** Breadth-first reachability using an ArrayDeque as a FIFO queue. */
    static boolean hasPathBfs(Map<String, List<String>> graph, String start, String goal) {
        if (!graph.containsKey(start)) return false;
        Set<String> seen = new HashSet<>();
        seen.add(start);
        Deque<String> queue = new ArrayDeque<>();
        queue.offer(start);
        while (!queue.isEmpty()) {
            String node = queue.poll();
            if (node.equals(goal)) return true;
            for (String next : graph.getOrDefault(node, List.of())) {
                if (seen.add(next)) queue.offer(next);
            }
        }
        return false;
    }

    /** DFS with three colors. A node on the recursion stack (inProgress)
     *  that is revisited indicates a cycle. */
    static boolean hasCycle(Map<String, List<String>> graph) {
        Set<String> visited = new HashSet<>();
        Set<String> inProgress = new HashSet<>();
        for (String node : graph.keySet()) {
            if (!visited.contains(node) && dfsCycle(graph, node, visited, inProgress))
                return true;
        }
        return false;
    }

    private static boolean dfsCycle(Map<String, List<String>> graph, String node,
                                     Set<String> visited, Set<String> inProgress) {
        visited.add(node);
        inProgress.add(node);
        for (String next : graph.getOrDefault(node, List.of())) {
            if (inProgress.contains(next)) return true;
            if (!visited.contains(next) && dfsCycle(graph, next, visited, inProgress))
                return true;
        }
        inProgress.remove(node);
        return false;
    }

    /** Immutable pair for use as a HashMap key. Arrays and mutable objects
     *  must never be used as map keys — they don't implement equals/hashCode correctly. */
    record CurrencyPair(String from, String to) {}

    /** The Evaluate Division / currency conversion pattern: a weighted graph
     *  where BFS accumulates the product of edge rates along a path.
     *  Returns the conversion factor from src to dst, or empty if unreachable. */
    static OptionalDouble convertCurrency(Map<CurrencyPair, Double> rates,
                                           String src, String dst) {
        Map<String, List<Map.Entry<String, Double>>> adj = new HashMap<>();
        for (var entry : rates.entrySet()) {
            String a = entry.getKey().from(), b = entry.getKey().to();
            double r = entry.getValue();
            adj.computeIfAbsent(a, k -> new ArrayList<>()).add(Map.entry(b, r));
            adj.computeIfAbsent(b, k -> new ArrayList<>()).add(Map.entry(a, 1.0 / r));
        }
        if (!adj.containsKey(src) || !adj.containsKey(dst))
            return OptionalDouble.empty();

        record State(String node, double acc) {}
        Set<String> seen = new HashSet<>();
        seen.add(src);
        Deque<State> queue = new ArrayDeque<>();
        queue.offer(new State(src, 1.0));
        while (!queue.isEmpty()) {
            State cur = queue.poll();
            if (cur.node().equals(dst)) return OptionalDouble.of(cur.acc());
            for (var neighbor : adj.getOrDefault(cur.node(), List.of())) {
                if (seen.add(neighbor.getKey()))
                    queue.offer(new State(neighbor.getKey(), cur.acc() * neighbor.getValue()));
            }
        }
        return OptionalDouble.empty();
    }


    // ============================================================
    // SECTION 8: HEAP / TOP-K with PriorityQueue
    // ============================================================
    // PriorityQueue is a min-heap by default. For top-K, maintain a min-heap
    // of size k: poll the smallest whenever the heap exceeds k.

    static List<String> topKFrequent(List<String> items, int k) {
        Map<String, Integer> counts = new HashMap<>();
        for (String item : items) counts.merge(item, 1, Integer::sum);

        PriorityQueue<Map.Entry<String, Integer>> minHeap =
            new PriorityQueue<>(Comparator.comparingInt(Map.Entry::getValue));
        for (var entry : counts.entrySet()) {
            minHeap.offer(entry);
            if (minHeap.size() > k) minHeap.poll();
        }
        List<String> result = new ArrayList<>();
        while (!minHeap.isEmpty()) result.add(minHeap.poll().getKey());
        Collections.reverse(result);
        return result;
    }


    // ============================================================
    // SECTION 9: POLYMORPHISM WITH SEALED INTERFACES (Java 17+)
    // ============================================================
    // Modeling fee rules as strategy objects keeps logic open for extension.
    // Sealed interfaces restrict which classes can implement them — the compiler
    // can verify exhaustive switch expressions over the permitted subtypes.

    sealed interface FeeStrategy permits FlatFee, PercentageFee {
        int feeCents(int amountCents);
    }

    record FlatFee(int cents) implements FeeStrategy {
        @Override public int feeCents(int amountCents) { return cents; }
    }

    record PercentageFee(int basisPoints) implements FeeStrategy {
        // 1 basis point = 0.01%. Integer math avoids float drift.
        @Override public int feeCents(int amountCents) {
            return amountCents * basisPoints / 10_000;
        }
    }

    static int totalFees(int amountCents, List<FeeStrategy> strategies) {
        return strategies.stream().mapToInt(s -> s.feeCents(amountCents)).sum();
    }

    /** Enhanced switch with pattern matching — exhaustive over sealed subtypes. */
    static String describeFee(FeeStrategy fee) {
        return switch (fee) {
            case FlatFee f       -> f.cents() + " cents flat";
            case PercentageFee p -> p.basisPoints() + " basis points";
        };
    }


    // ============================================================
    // SECTION 10: IDEMPOTENCY CACHE WITH TTL (injectable clock)
    // ============================================================
    // Injecting the clock makes time-dependent code testable without sleeping.

    @FunctionalInterface
    interface Clock {
        double nowSeconds();
    }

    static class IdempotencyCache<V> {
        private final double ttlSeconds;
        private final Clock clock;
        private final Map<String, CacheEntry<V>> store = new HashMap<>();

        private record CacheEntry<V>(double storedAt, V value) {}

        IdempotencyCache(double ttlSeconds, Clock clock) {
            this.ttlSeconds = ttlSeconds;
            this.clock = clock;
        }

        V getOrSet(String key, Supplier<V> compute) {
            double now = clock.nowSeconds();
            CacheEntry<V> cached = store.get(key);
            if (cached != null && now - cached.storedAt() < ttlSeconds) {
                return cached.value();
            }
            V value = compute.get();
            store.put(key, new CacheEntry<>(now, value));
            return value;
        }
    }


    // ============================================================
    // SECTION 11: TOKEN-BUCKET RATE LIMITER (injectable clock)
    // ============================================================

    /** Allows up to `capacity` requests, refilling at `refillPerSec`. */
    static class TokenBucket {
        private final double capacity;
        private final double refillPerSec;
        private final Clock clock;
        private double tokens;
        private double last;

        TokenBucket(double capacity, double refillPerSec, Clock clock) {
            this.capacity = capacity;
            this.refillPerSec = refillPerSec;
            this.clock = clock;
            this.tokens = capacity;
            this.last = clock.nowSeconds();
        }

        boolean allow() {
            double now = clock.nowSeconds();
            double elapsed = now - last;
            last = now;
            tokens = Math.min(capacity, tokens + elapsed * refillPerSec);
            if (tokens >= 1) {
                tokens -= 1;
                return true;
            }
            return false;
        }
    }


    // ============================================================
    // SECTION 12: CONCURRENCY (the bug and the fix)
    // ============================================================
    // A non-atomic read-modify-write across threads loses updates. The fix is
    // AtomicInteger (lock-free CAS) or a ReentrantLock around the critical section.

    static class UnsafeCounter {
        private int value = 0;

        void increment() {
            // BUG: read, add, write is not atomic. Concurrent threads interleave.
            int current = value;
            Thread.yield(); // widen the race window
            value = current + 1;
        }

        int value() { return value; }
    }

    /** Fix #1: AtomicInteger — lock-free, best for simple counters. */
    static class SafeCounter {
        private final AtomicInteger value = new AtomicInteger(0);

        void increment() { value.incrementAndGet(); }
        int value() { return value.get(); }
    }

    /** Fix #2: ReentrantLock — more flexible (tryLock, fairness, conditions). */
    static class LockCounter {
        private int value = 0;
        private final ReentrantLock lock = new ReentrantLock();

        void increment() {
            lock.lock();
            try { value++; } finally { lock.unlock(); }
        }

        int value() { return value; }
    }

    /** Fix #3: synchronized — simplest, built into every object. */
    static class SyncCounter {
        private int value = 0;

        synchronized void increment() { value++; }
        synchronized int value() { return value; }
    }

    static int hammer(Runnable increment, IntSupplier getValue,
                       int threads, int perThread) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        for (int t = 0; t < threads; t++) {
            pool.submit(() -> {
                for (int i = 0; i < perThread; i++) increment.run();
            });
        }
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        return getValue.getAsInt();
    }


    // ============================================================
    // SECTION 13: INTEGRATION (HttpClient, retry with backoff, pagination)
    // ============================================================
    // The retry method is fully testable offline by injecting a no-op sleeper
    // and a flaky callable.

    @FunctionalInterface
    interface Sleeper {
        void sleep(long millis) throws InterruptedException;
    }

    /** Retries on exception with exponential backoff. Sleeper is injectable
     *  so tests run instantly. */
    static <T> T retry(int times, double baseDelaySec, Sleeper sleeper,
                       Callable<T> action) throws Exception {
        Exception last = null;
        for (int attempt = 0; attempt < times; attempt++) {
            try {
                return action.call();
            } catch (Exception e) {
                last = e;
                if (attempt < times - 1) {
                    long delayMs = (long) (baseDelaySec * Math.pow(2, attempt) * 1000);
                    sleeper.sleep(delayMs);
                }
            }
        }
        throw last;
    }

    /** Reference pattern using Java 11+ HttpClient. Not exercised in the demo
     *  to avoid live network calls. */
    static String httpGetJson(String url) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Accept", "application/json")
            .timeout(Duration.ofSeconds(5))
            .build();
        HttpResponse<String> response =
            client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200)
            throw new RuntimeException("unexpected status " + response.statusCode());
        return response.body();
    }

    /** Lazy iterator that yields items across pages until a page is empty. */
    static <T> Iterator<T> paginate(Function<Integer, List<T>> fetchPage, int maxPages) {
        return new Iterator<>() {
            private int page = 0;
            private Iterator<T> current = Collections.emptyIterator();
            private boolean done = false;

            @Override public boolean hasNext() {
                while (!current.hasNext() && !done) {
                    if (page >= maxPages) { done = true; return false; }
                    List<T> items = fetchPage.apply(page++);
                    if (items == null || items.isEmpty()) { done = true; return false; }
                    current = items.iterator();
                }
                return current.hasNext();
            }

            @Override public T next() {
                if (!hasNext()) throw new NoSuchElementException();
                return current.next();
            }
        };
    }


    // ============================================================
    // SECTION 14: TRY-WITH-RESOURCES / AutoCloseable
    // ============================================================
    // Java's equivalent of Python's context manager. Any AutoCloseable can be
    // used in a try-with-resources block; close() is called even if an exception
    // is thrown.

    static class Timed implements AutoCloseable {
        private final long startNanos = System.nanoTime();
        private double elapsed;

        @Override public void close() {
            elapsed = (System.nanoTime() - startNanos) / 1e9;
        }

        double elapsed() { return elapsed; }
    }


    // ============================================================
    // SECTION 15: COMMON JAVA GOTCHAS (annotated)
    // ============================================================
    // 1. == vs .equals(): == on Integer objects compares references, not values.
    //    Integer cache covers -128 to 127; outside that, == can fail for equal values.
    //    Always use .equals() for object comparison.
    // 2. String interning: new String("abc") == "abc" is false.
    //    Always use .equals() for String comparison.
    // 3. ConcurrentModificationException: modifying a collection while iterating
    //    with for-each throws. Use Iterator.remove(), removeIf(), or collect-then-modify.
    // 4. Autoboxing NPE: Integer x = null; int y = x; throws NullPointerException.
    // 5. Arrays.asList() returns a fixed-size list backed by the array —
    //    add/remove throw UnsupportedOperationException. Wrap with new ArrayList<>().
    // 6. HashMap key mutation: if you mutate an object used as a HashMap key,
    //    the entry becomes unreachable. Use immutable keys (records, Strings).
    // 7. Checked exceptions in lambdas: Function/Consumer/Supplier don't declare
    //    checked exceptions. Wrap in try-catch or use a custom @FunctionalInterface.
    // 8. Double.NaN != Double.NaN is true. Use Double.isNaN() to check.
    // 9. List.of() / Map.of() return unmodifiable collections. Any mutation throws.
    // 10. Generics are erased at runtime: List<String> and List<Integer> are both
    //     just List at runtime (no reified generics). Cannot do `new T[]` or
    //     `instanceof List<String>`.

    static void gotchaDemos() {
        // Gotcha 1: Integer identity
        Integer a = 200, b = 200;
        System.out.println("  == on Integer(200): " + (a == b));         // likely false
        System.out.println("  .equals Integer(200): " + a.equals(b));    // true

        // Gotcha 3: ConcurrentModification — the bug and the fix
        List<String> list = new ArrayList<>(List.of("a", "b", "c"));
        // for (String s : list) list.remove(s);  // throws ConcurrentModificationException!
        list.removeIf(s -> s.equals("b"));        // safe
        System.out.println("  After removeIf: " + list);

        // Gotcha 5: Arrays.asList is fixed-size
        List<String> fixed = Arrays.asList("x", "y");
        // fixed.add("z");  // throws UnsupportedOperationException
        List<String> mutable = new ArrayList<>(Arrays.asList("x", "y"));
        mutable.add("z");
        System.out.println("  Mutable from asList: " + mutable);
    }


    // ============================================================
    // DEMO RUNNER
    // ============================================================

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--test")) {
            runTests();
            return;
        }

        System.out.println("Money: " + new Money(1250).display());

        var txns = List.of(
            Transaction.fromRow(Map.of("id", "t1", "merchant", "acme", "amount", "10.00")),
            Transaction.fromRow(Map.of("id", "t2", "merchant", "acme", "amount", "5.50")),
            Transaction.fromRow(Map.of("id", "t3", "merchant", "globex", "amount", "20.00")));
        System.out.println("Net by merchant: " + netVolumeByMerchant(txns));
        System.out.println("Top merchant: " + topMerchants(txns, 1));

        var charge = new Charge("c1");
        charge.transition(ChargeState.CAPTURED);
        charge.transition(ChargeState.REFUNDED);
        System.out.println("Charge history: " + charge.history());

        var rates = Map.of(
            new CurrencyPair("USD", "EUR"), 0.9,
            new CurrencyPair("EUR", "GBP"), 0.85);
        System.out.println("USD->GBP factor: " + convertCurrency(rates, "USD", "GBP"));

        var graph = buildAdjacency(new String[][]{{"a","b"}, {"b","c"}, {"c","a"}});
        System.out.println("Has cycle: " + hasCycle(graph));

        System.out.println("Fees on $100: " +
            totalFees(10_000, List.of(new FlatFee(30), new PercentageFee(290))) + " cents");

        var unsafeCounter = new UnsafeCounter();
        int unsafe = hammer(unsafeCounter::increment, unsafeCounter::value, 8, 2_000);
        var safeCounter = new SafeCounter();
        int safe = hammer(safeCounter::increment, safeCounter::value, 8, 2_000);
        System.out.printf("Unsafe counter (expect < 16000): %d%n", unsafe);
        System.out.printf("Safe counter   (expect 16000):  %d%n", safe);

        // try-with-resources: close() is called at end of block
        var timer = new Timed();
        try (timer) {
            fib(30);
        }
        System.out.printf("fib(30) took %.4fs (memoized)%n", timer.elapsed());

        System.out.println("\nGotcha demos:");
        gotchaDemos();
    }


    // ============================================================
    // SECTION 16: TESTS
    // ============================================================
    // Run with: java Reference --test
    // Self-contained assertion helpers — no JUnit dependency required.
    // Demonstrates the same patterns as pytest: parametrized cases, exception
    // testing, fixtures, and a controllable fake clock.

    private static int testsPassed = 0;
    private static int testsFailed = 0;

    private static void check(String name, Runnable test) {
        try {
            test.run();
            testsPassed++;
            System.out.println("  PASS  " + name);
        } catch (AssertionError | Exception e) {
            testsFailed++;
            System.out.println("  FAIL  " + name + " — " + e.getMessage());
        }
    }

    private static void assertEquals(Object expected, Object actual) {
        if (!Objects.equals(expected, actual))
            throw new AssertionError("expected " + expected + " but got " + actual);
    }

    private static void assertTrue(boolean condition) {
        if (!condition) throw new AssertionError("expected true");
    }

    private static void assertFalse(boolean condition) {
        if (condition) throw new AssertionError("expected false");
    }

    private static void assertApprox(double expected, double actual, double tol) {
        if (Math.abs(expected - actual) > tol)
            throw new AssertionError("expected ~" + expected + " but got " + actual);
    }

    private static void assertThrows(Class<? extends Throwable> type, Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected " + type.getSimpleName() + " but nothing was thrown");
        } catch (Throwable e) {
            if (!type.isInstance(e))
                throw new AssertionError(
                    "expected " + type.getSimpleName() + " but got " + e.getClass().getSimpleName());
        }
    }

    /** A controllable clock for deterministic time-based tests. */
    static class FakeClock implements Clock {
        private double now = 0.0;

        @Override public double nowSeconds() { return now; }

        void advance(double seconds) { now += seconds; }
    }

    static void runTests() {
        System.out.println("Running tests...\n");

        // --- parseAmountCents: parametrized style ---
        for (var tc : List.of(
                Map.entry("10.00", 1000), Map.entry("0.99", 99),
                Map.entry("12.5", 1250),  Map.entry(" 3 ", 300))) {
            check("parseAmountCents(\"" + tc.getKey() + "\")",
                () -> assertEquals(tc.getValue(), parseAmountCents(tc.getKey())));
        }

        check("parseAmountCents rejects garbage",
            () -> assertThrows(ValidationException.class, () -> parseAmountCents("abc")));

        check("parseAmountCents rejects empty",
            () -> assertThrows(ValidationException.class, () -> parseAmountCents("")));

        // --- Money ---
        check("Money addition and currency guard", () -> {
            assertEquals(150, new Money(100).add(new Money(50)).cents());
            assertThrows(ValidationException.class,
                () -> new Money(100, "USD").add(new Money(50, "EUR")));
        });

        check("Money rejects negative", () ->
            assertThrows(ValidationException.class, () -> new Money(-1)));

        // --- State machine ---
        check("illegal state transition", () -> {
            var charge = new Charge("c");
            assertThrows(ValidationException.class,
                () -> charge.transition(ChargeState.REFUNDED));
        });

        check("valid state transitions", () -> {
            var charge = new Charge("c");
            charge.transition(ChargeState.CAPTURED);
            charge.transition(ChargeState.REFUNDED);
            assertEquals(ChargeState.REFUNDED, charge.state());
            assertEquals(
                List.of(ChargeState.CREATED, ChargeState.CAPTURED, ChargeState.REFUNDED),
                charge.history());
        });

        // --- CSV parsing ---
        check("CSV handles quoted commas", () -> {
            var rows = parseCsv("id,note\n1,\"hello, world\"\n");
            assertEquals("hello, world", rows.get(0).get("note"));
        });

        // --- Graphs ---
        check("currency conversion path and missing", () -> {
            var rates = Map.of(
                new CurrencyPair("USD", "EUR"), 0.9,
                new CurrencyPair("EUR", "GBP"), 0.85);
            var result = convertCurrency(rates, "USD", "GBP");
            assertTrue(result.isPresent());
            assertApprox(0.9 * 0.85, result.getAsDouble(), 1e-9);
            assertTrue(convertCurrency(rates, "USD", "JPY").isEmpty());
        });

        check("cycle detection", () -> {
            assertTrue(hasCycle(buildAdjacency(new String[][]{{"a","b"}, {"b","a"}})));
            assertFalse(hasCycle(buildAdjacency(new String[][]{{"a","b"}, {"b","c"}})));
        });

        check("BFS path finding", () -> {
            var graph = buildAdjacency(new String[][]{{"a","b"}, {"b","c"}});
            assertTrue(hasPathBfs(graph, "a", "c"));
            assertFalse(hasPathBfs(graph, "c", "a"));
        });

        // --- Top-K ---
        check("topKFrequent", () -> {
            var result = new HashSet<>(topKFrequent(List.of("a","a","b","b","c"), 2));
            assertEquals(Set.of("a", "b"), result);
        });

        // --- Fee strategies ---
        check("fee strategies", () -> {
            // 2.9% + 30c on $100 = 290 + 30 = 320 cents.
            assertEquals(320, totalFees(10_000, List.of(new FlatFee(30), new PercentageFee(290))));
        });

        check("describeFee with pattern matching", () -> {
            assertEquals("30 cents flat", describeFee(new FlatFee(30)));
            assertEquals("290 basis points", describeFee(new PercentageFee(290)));
        });

        // --- Idempotency cache with fake clock ---
        check("idempotency cache hits then expires", () -> {
            var clock = new FakeClock();
            var cache = new IdempotencyCache<String>(10, clock);
            int[] calls = {0};
            Supplier<String> compute = () -> { calls[0]++; return "result"; };

            assertEquals("result", cache.getOrSet("k", compute));
            assertEquals("result", cache.getOrSet("k", compute));
            assertEquals(1, calls[0]);  // second call was a cache hit

            clock.advance(11);
            cache.getOrSet("k", compute);
            assertEquals(2, calls[0]);  // key expired, recomputed
        });

        // --- Token bucket ---
        check("token bucket limits and refills", () -> {
            var clock = new FakeClock();
            var bucket = new TokenBucket(2, 1, clock);
            assertTrue(bucket.allow());
            assertTrue(bucket.allow());
            assertFalse(bucket.allow());  // bucket empty
            clock.advance(1);
            assertTrue(bucket.allow());   // one token refilled
        });

        // --- Retry ---
        check("retry succeeds after failures", () -> {
            int[] attempts = {0};
            try {
                String result = retry(3, 0.5, ms -> {}, () -> {
                    attempts[0]++;
                    if (attempts[0] < 3) throw new RuntimeException("transient");
                    return "ok";
                });
                assertEquals("ok", result);
                assertEquals(3, attempts[0]);
            } catch (Exception e) {
                throw new AssertionError("unexpected exception", e);
            }
        });

        check("retry exhausts and raises", () ->
            assertThrows(RuntimeException.class, () -> {
                try {
                    retry(2, 0.5, ms -> {}, () -> { throw new RuntimeException("nope"); });
                } catch (RuntimeException e) {
                    throw e;
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            }));

        // --- Concurrency ---
        check("safe counter is correct under threads", () -> {
            try {
                var counter = new SafeCounter();
                int total = hammer(counter::increment, counter::value, 8, 1_000);
                assertEquals(8_000, total);
            } catch (InterruptedException e) {
                throw new AssertionError("interrupted", e);
            }
        });

        // --- Collections: fixture-style setup ---
        check("net volume with fixture data", () -> {
            var txns = sampleTransactions();
            var totals = netVolumeByMerchant(txns);
            assertEquals(1550, totals.get("acme"));
            assertEquals(2000, totals.get("globex"));
        });

        check("sliding window max sum", () -> {
            assertEquals(12, slidingWindowMaxSum(new int[]{1, 3, 5, 7, 2}, 2));
            assertThrows(ValidationException.class,
                () -> slidingWindowMaxSum(new int[]{1, 2}, 0));
        });

        // --- Summary ---
        System.out.printf("%n%d passed, %d failed%n", testsPassed, testsFailed);
        if (testsFailed > 0) System.exit(1);
    }

    /** Reusable test data — equivalent of a pytest fixture. */
    private static List<Transaction> sampleTransactions() {
        return List.of(
            new Transaction("t1", "acme", new Money(1000)),
            new Transaction("t2", "acme", new Money(550)),
            new Transaction("t3", "globex", new Money(2000)));
    }
}
