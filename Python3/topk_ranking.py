"""
Top-K Ranking

Design a ranking system for entities that supports:
    - Updating an entity's score
    - Retrieving the top-k entities by score
    - Removing an entity
"""

from sortedcontainers import SortedList


class Ranking:
    """
    Store rankings in SortedList using tuple of -score and entityId
    This keeps rankings sorted based on highest score
    Keep dictionary of entityId with score - this will be used to remove the tuple in rankings
    SortedList documentation: https://grantjenks.com/docs/sortedcontainers/sortedlist.html#sortedcontainers.SortedList
    Update: Time Complexity: O(logN)
    TopK: Time Complexity: O(logNK)
    Remove: Time Complexity: O(logN)
    """

    def __init__(self):
        self.scores = {}  # key: entityId, value: score
        self.rankings = SortedList()  # (-score, entityId)

    def update(self, entityId: str, score: int):
        if entityId in self.scores and self.scores[entityId] is not None:
            old_score = self.scores[entityId]

            self.rankings.discard((-old_score, entityId))

        self.scores[entityId] = score
        self.rankings.add((-score, entityId))

    def topK(self, k: int) -> list[str]:
        result = []
        for i in range(k):
            result.append(self.rankings[i][1])
        return result

    def remove(self, entityId: str):
        if entityId in self.scores:
            self.rankings.discard((-self.scores[entityId], entityId))
            self.scores[entityId] = None
        return

def test():
    ranking = Ranking()
    ranking.update("entity1", 10)
    ranking.update("entity2", 20)
    ranking.update("entity3", 15)
    assert ranking.topK(2) == ["entity2", "entity3"]
    ranking.update("entity1", 25)
    assert ranking.topK(2) == ["entity1", "entity2"]
    ranking.remove("entity2")
    assert ranking.topK(2) == ["entity1", "entity3"]
    print("success")


if __name__ == "__main__":
    test()
