"""
Word Ladder
Given two words, beginWord and endWord, and a dictionary wordList, return the length of the shortest transformation sequence from beginWord to endWord, such that:

Only one letter can be changed at a time.
Each transformed word must exist in wordList. Note that beginWord is not required to be in wordList.

Return the number of words in the shortest transformation sequence, or 0 if no such sequence exists.
Example:
beginWord = "hit"
endWord   = "cog"
wordList  = ["hot", "dot", "dog", "lot", "log", "cog"]

Output: 5
The sequence is "hit" -> "hot" -> "dot" -> "dog" -> "cog", which is 5 words long.
Same format as before. Before writing code, give me:
"""
from typing import List
from collections import deque
import string

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

    queue = deque([(beginWord,1)])

    while queue:
        word, depth = queue.popleft()
        if word == endWord:
            return depth

        for i in range(len(word)):
            for letter in alphabet:
                newWord = word[:i]+letter+word[i+1:]
                if newWord not in visited and newWord in wordListSet:
                    visited.add(newWord)
                    queue.append((newWord,depth+1))
    
    return 0

if __name__=="__main__":
    TEST1=("hit","cog",["hot", "dot", "dog", "lot", "log", "cog"],5)
    TEST2=("hit","hit",["hit"],1)
    TEST3=("hit","pop",["pop"],0)
    assert word_ladder(TEST1[0],TEST1[1],TEST1[2]) == TEST1[3]
    assert word_ladder(TEST2[0],TEST2[1],TEST2[2]) == TEST2[3]
    assert word_ladder(TEST3[0],TEST3[1],TEST3[2]) == TEST3[3]
    print("success")