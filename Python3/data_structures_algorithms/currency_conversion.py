"""
Currency Conversion

Given a list of exchange rates as (from_currency, to_currency, rate) triples where one unit of
from_currency equals rate units of to_currency (and 1/rate in reverse), convert an amount from
a source currency to a destination currency.

Example rates:
    ("USD", "EUR", 0.90)
    ("EUR", "GBP", 0.85)
    ("USD", "GBP", 0.80)
    ("GBP", "JPY", 190.0)
    ("USD", "CAD", 1.35)
    ("AUD", "NZD", 1.10)
"""

import pytest
from collections import defaultdict, deque

_RATES = [
    ("USD", "EUR", 0.90),
    ("EUR", "GBP", 0.85),
    ("USD", "GBP", 0.80),
    ("GBP", "JPY", 190.0),
    ("USD", "CAD", 1.35),
    ("AUD", "NZD", 1.10),
]


class Conversion:
    """Given a set of currency rates, able to convert one currency to another currency amount"""

    def __init__(self, rates):
        self.rates = rates

    def convert(self, amount: float, src: str, dest: str) -> tuple[float, list[str]]:
        """
        converts amount given src and dest currency
        """
        graph = defaultdict(dict)

        for rate in self.rates:
            rate_list = list(rate)
            graph[rate_list[0]][rate_list[1]] = rate_list[2]
            graph[rate_list[1]][rate_list[0]] = 1 / rate_list[2]

        queue = deque([(src, 1.0, [src])])
        visited = set([src])
        while queue:
            node, rate, moves = queue.popleft()

            if node == dest:
                return (rate * amount, moves)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(
                        (neighbor, rate * graph[node][neighbor], moves + [neighbor])
                    )

        raise ValueError(f"cannot convert {src} to {dest}")


@pytest.mark.parametrize("amount,src,dest,expected", [
    (100, "USD", "EUR", 100 * 0.9),
    (100, "USD", "JPY", 100 * 0.80 * 190.0),
])
def test_conversion(amount, src, dest, expected):
    conversion = Conversion(_RATES)
    converted_amount, _ = conversion.convert(amount, src, dest)
    assert converted_amount == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
