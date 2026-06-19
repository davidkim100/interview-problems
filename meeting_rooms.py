"""
Problem: Meeting Rooms

Given an array of meeting time intervals where intervals[i] = [start_i, end_i], return the
minimum number of conference rooms required to hold all meetings without overlap.

Note: a meeting ending at time t and one starting at t do not conflict.

Example:
    Input:  [[0, 30], [5, 10], [15, 20]]
    Output: 2
"""

from typing import List
import heapq
import pytest


def calculate_meeting_rooms(meetings: List[List[int]]) -> int:
    """
    Uses a heap to store earliest meeting end time and compare to start time
    Size of heap is max number of rooms required
    Time complexity: O(nlogn), Space complexity: O(n)
    """
    sorted_meetings = sorted(meetings)

    end_time_heap = []

    maxrooms = 0

    for meeting in sorted_meetings:
        while end_time_heap and meeting[0] >= end_time_heap[0]:
            heapq.heappop(end_time_heap)

        heapq.heappush(end_time_heap, (meeting[1]))
        maxrooms = max(len(end_time_heap), maxrooms)
    return maxrooms


def calculate_meeting_rooms_optimized(meetings: List[List[int]]) -> int:
    """
    Uses two sorted list of start times and end times and two pointers.
    Number of start times less than the current end time is number of rooms needed.
    Time complexity: O(nlogn), Space complexity: O(n)
    """
    starts = []
    ends = []
    for meeting in meetings:
        starts.append(meeting[0])
        ends.append(meeting[1])

    starts.sort()
    ends.sort()

    s = 0
    e = 0
    count = 0
    maxcount = 0
    while s < len(starts) and e < len(ends):
        if starts[s] < ends[e]:
            count += 1
            s += 1
        else:
            count -= 1
            e += 1
        maxcount = max(count, maxcount)
    return maxcount


@pytest.mark.parametrize("meetings,expected", [
    ([[0, 30], [5, 10], [15, 20]], 2),
    ([[10, 15], [5, 10], [0, 5]], 1),
])
def test_calculate_meeting_rooms(meetings, expected):
    assert calculate_meeting_rooms(meetings) == expected
    assert calculate_meeting_rooms_optimized(meetings) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
