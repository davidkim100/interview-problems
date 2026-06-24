"""
Longest Substring Without Repeating Characters

Given a string s, find the length of the longest substring that contains no repeating characters.

Examples:
    "abcabcbb" -> 3  (substring "abc")
    "bbbbb"    -> 1  (substring "b")
    "pwwkew"   -> 3  (substring "wke"; note "pwke" is a subsequence, not a substring)

Constraints:
    0 <= len(s) <= 5 * 10^4
    s may contain letters, digits, symbols, and spaces.
"""

import pytest

def longest_substring(string: str) -> int:
    """
    sliding window, move right pointer and save position in hashmap
    if char has been seen and is less than left pointer, move left pointer to last seen position+1
    O(n) time complexity with O(1) memory since we only store number of ASCII chars that exist in hashmap
    """
    hashmap = {}  # key: character value: last seen position

    left = 0
    right = 0
    result = 0

    while right < len(string):
        new_character = string[right]
        if new_character in hashmap and hashmap[new_character] >= left:
            left = hashmap[new_character] + 1
        hashmap[new_character] = right
        result = max(result, right - left + 1)
        right += 1
    print(result)
    return result


@pytest.mark.parametrize("string,expected", [
    ("abcabcbb", 3),
    ("bbbbb", 1),
    ("pwwkew", 3),
])
def test_longest_substring(string, expected):
    assert longest_substring(string) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
