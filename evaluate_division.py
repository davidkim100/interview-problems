"""
You are given an array of variable pairs equations and an array of real numbers values, where equations[i] = [Ai, Bi] and values[i] represent the equation Ai / Bi = values[i]. 
Each Ai or Bi is a string that represents a single variable.
You are also given some queries, where queries[j] = [Cj, Dj] represents the jth query where you must find the answer for Cj / Dj = ?.
Return the answers to all queries. If a single answer cannot be determined, return -1.0.
Note: The input is always valid. You may assume that evaluating the queries will not result in division by zero and that there is no contradiction.
Note: The variables that do not occur in the list of equations are undefined, so the answer cannot be determined for them.

Example 1:

Input: equations = [["a","b"],["b","c"]], values = [2.0,3.0], queries = [["a","c"],["b","a"],["a","e"],["a","a"],["x","x"]]
Output: [6.00000,0.50000,-1.00000,1.00000,-1.00000]
Explanation: 
Given: a / b = 2.0, b / c = 3.0
queries are: a / c = ?, b / a = ?, a / e = ?, a / a = ?, x / x = ? 
return: [6.0, 0.5, -1.0, 1.0, -1.0 ]
note: x is undefined => -1.0

Example 2:

Input: equations = [["a","b"],["b","c"],["bc","cd"]], values = [1.5,2.5,5.0], queries = [["a","c"],["c","b"],["bc","cd"],["cd","bc"]]
Output: [3.75000,0.40000,5.00000,0.20000]

Example 3:

Input: equations = [["a","b"]], values = [0.5], queries = [["a","b"],["b","a"],["a","c"],["x","y"]]
Output: [0.50000,2.00000,-1.00000,-1.00000]
"""
from typing import List, Iterable
from collections import defaultdict

def calculate_equation(equations: List[List[str]], values: List[float], queries: List[List[str]]) -> List[float]:
    graph: Iterable[Iterable[str]] = defaultdict(dict)

    for (x,y),value in zip(equations, values, strict=True):
        graph[x][y] = value
        graph[y][x] = 1/value

    def dfs(node: str, end: str, product: float, visited: set):
        if graph[node]!={} and graph[end]!={} and node == end:
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
        x,y = query
        result.append(dfs(x,y, 1, set()))
    return result

if __name__=="__main__":
    EQUATIONS1 = [["a","b"],["b","c"]]
    VALUES1 = [2.0,3.0]
    QUERIES1 = [["a","c"],["b","a"],["a","e"],["a","a"],["x","x"]]
    assert calculate_equation(EQUATIONS1,VALUES1,QUERIES1)==[6.0,0.5,-1.0,1.0,-1.0]
    EQUATIONS2 = [["a","b"],["b","c"],["bc","cd"]]
    VALUES2 = [1.5,2.5,5.0]
    QUERIES2 = [["a","c"],["c","b"],["bc","cd"],["cd","bc"]]
    assert calculate_equation(EQUATIONS2,VALUES2,QUERIES2)==[3.75,0.4,5.0,0.2]
    EQUATIONS3 = [["a","b"]]
    VALUES3 = [0.5]
    QUERIES3 = [["a","b"],["b","a"],["a","c"],["x","y"]]
    assert calculate_equation(EQUATIONS3,VALUES3,QUERIES3)==[0.50000,2.00000,-1.00000,-1.00000]
    print("success")