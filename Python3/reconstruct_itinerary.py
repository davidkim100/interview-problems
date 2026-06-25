"""
LC332
You are given a list of airline tickets where tickets[i] = [fromi, toi] represent the departure and the arrival airports of one flight. Reconstruct the itinerary in order and return it.

All of the tickets belong to a man who departs from "JFK", thus, the itinerary must begin with "JFK". If there are multiple valid itineraries, you should return the itinerary that has the smallest lexical order when read as a single string.

    For example, the itinerary ["JFK", "LGA"] has a smaller lexical order than ["JFK", "LGB"].

You may assume all tickets form at least one valid itinerary. You must use all the tickets once and only once.
"""

from collections import defaultdict
from typing import List


class Solution:
    @staticmethod
    def findItinerary(tickets: List[List[str]]) -> List[str]:

        graph = defaultdict(list)

        for ticket in tickets:
            graph[ticket[0]].append(ticket[1])
        for src, dsts in graph.items():
            dsts.sort(reverse=True)

        itinerary = []

        def dfs(airport):
            while graph[airport]:
                dfs(graph[airport].pop())
            itinerary.append(airport)

        dfs("JFK")
        return list(reversed(itinerary))


test1 = [["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]]
assert Solution.findItinerary(test1) == ["JFK", "MUC", "LHR", "SFO", "SJC"]
test2 = [
    ["JFK", "SFO"],
    ["JFK", "ATL"],
    ["SFO", "ATL"],
    ["ATL", "JFK"],
    ["ATL", "SFO"],
]
assert Solution.findItinerary(test2) == [
    "JFK",
    "ATL",
    "JFK",
    "SFO",
    "ATL",
    "SFO",
]
test3 = [["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "JFK"]]
assert Solution.findItinerary(test3) == ['JFK', 'SFO', 'JFK', 'ATL']
"""
DFS where at each node we always take the path with the lowest lexical order
"""
