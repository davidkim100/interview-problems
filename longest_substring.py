"""
Longest Substring Without Repeating Characters
Given a string s, find the length of the longest substring that contains no repeating characters.
Examples:

s = "abcabcbb" returns 3 (the substring "abc")
s = "bbbbb" returns 1 (the substring "b")
s = "pwwkew" returns 3 (the substring "wke"; note that "pwke" is a subsequence, not a substring)

"abcdefgg   abcdefgd

Constraints to assume unless you want to clarify:

0 <= len(s) <= 5 * 10^4
s may contain letters, digits, symbols, and spaces.
"""

from collections import Counter

def longest_substring(string: str) -> int:
    """
    sliding window, move right pointer and save position in hashmap
    if char has been seen and is less than left pointer, move left pointer to last seen position+1
    O(n) time complexity with O(1) memory since we only store number of ASCII chars that exist in hashmap
    """
    hashmap = {}    # key: character value: last seen position

    left=0
    right=0
    result = 0

    while right < len(string):
        new_character = string[right]
        if new_character in hashmap and hashmap[new_character] >= left:
            left=hashmap[new_character]+1
        hashmap[new_character] = right
        result = max(result, right-left+1)
        right+=1
    print(result)
    return result

if __name__ == "__main__":
    TEST1="abcabcbb"
    ANSWER1=3
    TEST2="bbbbb"
    ANSWER2=1
    TEST3="pwwkew"
    ANSWER3=3
    assert longest_substring(TEST1)==ANSWER1
    assert longest_substring(TEST2)==ANSWER2
    assert longest_substring(TEST3)==ANSWER3
    print("SUCCESS")