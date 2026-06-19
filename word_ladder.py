"""
Word Ladder

Given two words, beginWord and endWord, and a dictionary wordList, return the number of words
in the shortest transformation sequence from beginWord to endWord, or 0 if none exists.

Rules:
    - Only one letter can be changed at a time.
    - Each transformed word must exist in wordList.
    - beginWord is not required to be in wordList.

Example:
    beginWord = "hit"
    endWord   = "cog"
    wordList  = ["hot", "dot", "dog", "lot", "log", "cog"]

    Output: 5  ("hit" -> "hot" -> "dot" -> "dog" -> "cog")
"""

from typing import List
from collections import deque
import string
import pytest


def word_ladder(beginWord: str, endWord: str, wordList: List[str]) -> int:
    """
    BFS starting from beginWord, keeping track of visited words
    changing each character with alphabet and seeing if it exists in wordList
    O(N*L^2) time complexity and O(N*L) N is number of words L is length of word
    """
    alphabet = list(string.ascii_lowercase)
    visited = {beginWord}
    wordListSet = set(wordList)

    if endWord not in wordListSet:
        return 0

    queue = deque([(beginWord, 1)])

    while queue:
        word, depth = queue.popleft()
        if word == endWord:
            return depth

        for i in range(len(word)):
            for letter in alphabet:
                newWord = word[:i] + letter + word[i + 1 :]
                if newWord not in visited and newWord in wordListSet:
                    visited.add(newWord)
                    queue.append((newWord, depth + 1))

    return 0


@pytest.mark.parametrize("begin_word,end_word,word_list,expected", [
    ("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"], 5),
    ("hit", "hit", ["hit"], 1),
    ("hit", "pop", ["pop"], 0),
])
def test_word_ladder(begin_word, end_word, word_list, expected):
    assert word_ladder(begin_word, end_word, word_list) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
