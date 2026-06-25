"""
LC815
You are given an array routes representing bus routes where routes[i] is a bus route that the ith bus repeats forever.

    For example, if routes[0] = [1, 5, 7], this means that the 0th bus travels in the sequence 1 -> 5 -> 7 -> 1 -> 5 -> 7 -> 1 -> ... forever.

You will start at the bus stop source (You are not on any bus initially), and you want to go to the bus stop target. You can travel between bus stops by buses only.

Return the least number of buses you must take to travel from source to target. Return -1 if it is not possible.
"""

from collections import defaultdict, deque
from typing import List


class Solution:
    @staticmethod
    def numBusesToDestination(
        routes: List[List[int]], source: int, target: int
    ) -> int:

        stop_to_routes = defaultdict(list)
        for i, route in enumerate(routes):
            for stop in route:
                stop_to_routes[stop].append(i)

        visited_stops = set([source])
        visited_routes = set()
        queue = deque([(source, 0)])
        while queue:
            bus, taken = queue.popleft()
            if bus == target:
                return taken

            for i in stop_to_routes[bus]:
                if i not in visited_routes:
                    for stop in routes[i]:
                        if stop not in visited_stops:
                            visited_stops.add(stop)
                            queue.append((stop, taken + 1))
                    visited_routes.add(i)
        return -1


test1 = [[1, 2, 7], [3, 6, 7]]
assert Solution.numBusesToDestination(test1, 1, 6) == 2
test2 = [[7, 12], [4, 5, 15], [6], [15, 19], [9, 12, 13]]
assert Solution.numBusesToDestination(test2, 15, 12) == -1
test3 = [[1, 2, 7], [3, 6, 7]]
assert Solution.numBusesToDestination(test3, 1, 1) == 0
test4 = [[1, 2, 7], [3, 6, 7]]
assert Solution.numBusesToDestination(test4, 3, 7) == 1
test5 = [[7, 12], [4, 5, 15], [6], [15, 19], [9, 12, 19]]
assert Solution.numBusesToDestination(test5, 4, 9) == 3
