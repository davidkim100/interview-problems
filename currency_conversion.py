"""
You are building a small currency conversion service. 
You are given a list of exchange rates, each a triple of (from_currency, to_currency, rate), 
meaning one unit of from_currency equals rate units of to_currency. 
Assume each rate is also valid in reverse at 1 / rate.

rates = [
    ("USD", "EUR", 0.90),
    ("EUR", "GBP", 0.85),
    ("USD", "GBP", 0.80),
    ("GBP", "JPY", 190.0),
    ("USD", "CAD", 1.35),
    ("AUD", "NZD", 1.10),
]
"""
import unittest
from collections import defaultdict, deque

class Conversion():
    """Given a set of currency rates, able to convert one currency to another currency amount"""
    def __init__(self,rates):
        self.rates = rates

    def convert(self, amount: float, src: str, dest: str) -> tuple[float, list[str]]:
        """
        converts amount given src and dest currency
        """
        graph = defaultdict(dict)

        for rate in self.rates:
            rate_list = list(rate)
            graph[rate_list[0]][rate_list[1]] = rate_list[2]
            graph[rate_list[1]][rate_list[0]] = 1/rate_list[2]

        queue = deque([(src,1.0,[src])])
        visited = set([src])
        while queue:
            node,rate,moves = queue.popleft()

            if node == dest:
                return (rate*amount,moves)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor,rate*graph[node][neighbor],moves+[neighbor]))

        raise ValueError(f'cannot convert {src} to {dest}')

class Testing(unittest.TestCase):
    """Test class for currency conversion"""
    def test(self):
        """teseting basic stuff"""
        rates = [
            ("USD", "EUR", 0.90),
            ("EUR", "GBP", 0.85),
            ("USD", "GBP", 0.80),
            ("GBP", "JPY", 190.0),
            ("USD", "CAD", 1.35),
            ("AUD", "NZD", 1.10),
        ]
        conversion = Conversion(rates)

        converted_amount,moves = conversion.convert(100, "USD","EUR")
        print(moves)
        assert converted_amount == 100*0.9

        converted_amount,moves = conversion.convert(100,"USD","JPY")
        print(moves)
        assert converted_amount == 100*(0.80*190.0)

if __name__=="__main__":
    unittest.main()
