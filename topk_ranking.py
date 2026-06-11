"""
We have entities users, drivers, restaurants, products
Design a top-k ranking system that can return the top-k entities with the highest scores. 
The system should support updating the score of an entity and retrieving the top-k entities efficiently.
"""
from sortedcontainers import SortedList

class Ranking:
    """
    Store rankings in SortedList using tuple of -score and entityId
    This keeps rankings sorted based on highest score
    Keep dictionary of entityId with score - this will be used to remove the tuple in rankings
    Update: Time Complexity: O(logN)
    TopK: Time Complexity: O(logNK)
    Remove: Time Complexity: O(logN)
    """

    def __init__(self):
        self.scores = {} # key: entityId, value: score
        self.rankings = SortedList() # (-score, entityId)

    def update(self, entityId: str, score: int):
        if entityId in self.scores and self.scores[entityId] != None:
            old_score = self.scores[entityId]

            self.rankings.discard((-old_score, entityId))
        
        self.scores[entityId]=score
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

if __name__=="__main__":
    ranking = Ranking()
    ranking.update("user1", 10)
    ranking.update("user2", 20)
    ranking.update("user3", 15)
    assert ranking.topK(2) == ["user2","user3"]
    ranking.update("user1", 25)
    assert ranking.topK(2) == ["user1","user2"]
    ranking.remove("user2")
    assert ranking.topK(2) == ["user1","user3"]
    print("success")