"""
Evaluate Division

Given equations[i] = [Ai, Bi] with values[i] = Ai / Bi, answer queries of the form Cj / Dj.
Return -1.0 for any query that cannot be determined.

Notes:
    - Input is always valid (no division by zero, no contradictions).
    - Variables not appearing in equations are undefined; return -1.0 for their queries.

Example 1:
    equations = [["a","b"], ["b","c"]], values = [2.0, 3.0]
    queries   = [["a","c"], ["b","a"], ["a","e"], ["a","a"], ["x","x"]]
    output    = [6.0, 0.5, -1.0, 1.0, -1.0]

Example 2:
    equations = [["a","b"], ["b","c"], ["bc","cd"]], values = [1.5, 2.5, 5.0]
    queries   = [["a","c"], ["c","b"], ["bc","cd"], ["cd","bc"]]
    output    = [3.75, 0.4, 5.0, 0.2]

Example 3:
    equations = [["a","b"]], values = [0.5]
    queries   = [["a","b"], ["b","a"], ["a","c"], ["x","y"]]
    output    = [0.5, 2.0, -1.0, -1.0]
"""

from typing import List, Iterable
from collections import defaultdict
import pytest


def calculate_equation(
    equations: List[List[str]], values: List[float], queries: List[List[str]]
) -> List[float]:
    graph: Iterable[Iterable[str]] = defaultdict(dict)

    for (x, y), value in zip(equations, values, strict=True):
        graph[x][y] = value
        graph[y][x] = 1 / value

    def dfs(node: str, end: str, product: float, visited: set):
        if graph[node] != {} and graph[end] != {} and node == end:
            return product

        visited.add(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                new_product = product * graph[node][neighbor]
                result = dfs(neighbor, end, new_product, visited)
                if result != -1.0:
                    return result
        return -1.0

    result = []
    for query in queries:
        x, y = query
        result.append(dfs(x, y, 1, set()))
    return result


from collections import deque


def calculate_equation_bfs(
    equations: List[List[str]], values: List[float], queries: List[List[str]]
) -> List[float]:
    graph: Iterable[Iterable[str]] = defaultdict(dict)

    for (x, y), value in zip(equations, values, strict=True):
        graph[x][y] = value
        graph[y][x] = 1 / value

    def bfs(start: str, end: str, visited: set):
        if graph[start] == {} and graph[end] == {}:
            return -1.0

        queue = deque([(start, 1)])
        visited = set([start])
        while queue:
            node, product = queue.popleft()
            if node == end:
                return product
            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, graph[node][neighbor] * product))
        return -1.0

    result = []
    for query in queries:
        x, y = query
        result.append(bfs(x, y, set()))
    return result


@pytest.mark.parametrize("equations,values,queries,expected", [
    (
        [["a", "b"], ["b", "c"]],
        [2.0, 3.0],
        [["a", "c"], ["b", "a"], ["a", "e"], ["a", "a"], ["x", "x"]],
        [6.0, 0.5, -1.0, 1.0, -1.0],
    ),
    (
        [["a", "b"], ["b", "c"], ["bc", "cd"]],
        [1.5, 2.5, 5.0],
        [["a", "c"], ["c", "b"], ["bc", "cd"], ["cd", "bc"]],
        [3.75, 0.4, 5.0, 0.2],
    ),
    (
        [["a", "b"]],
        [0.5],
        [["a", "b"], ["b", "a"], ["a", "c"], ["x", "y"]],
        [0.5, 2.0, -1.0, -1.0],
    ),
])
def test_calculate_equation(equations, values, queries, expected):
    assert calculate_equation(equations, values, queries) == expected
    assert calculate_equation_bfs(equations, values, queries) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
