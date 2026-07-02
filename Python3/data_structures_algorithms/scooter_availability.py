
from dataclasses import dataclass
import heapq
import random

@dataclass
class Scooter:
    scooterId: int
    latitude: int
    longitude: int

class ScooterAvailability:

    def __init__(self) -> None:
        self._scooters: list[Scooter] = []

    def addScooters(self, scooters: list[Scooter]):
        self._scooters.extend(scooters)

    def getAvailableScooters(self, userLat: int, userLong: int, maxNum: int):
        scooter_distances = []
        for scooter in self._scooters:
            dist = abs(userLat-scooter.latitude)**2 + abs(userLong-scooter.longitude)**2
            heapq.heappush(scooter_distances, (dist, scooter.scooterId))

        result = []
        while scooter_distances and len(result) < maxNum:
            result.append(heapq.heappop(scooter_distances)[1])

        return result

if __name__=="__main__":
    scooterAvailability = ScooterAvailability()

    scooters = []
    scooterHashMap = {}
    for i in range(100):
        scooter = Scooter(i,random.randint(1,100),random.randint(1,100))
        scooters.append(scooter)
        scooterHashMap[scooter.scooterId] = scooter

    scooterAvailability.addScooters(scooters)

    scooterIds = scooterAvailability.getAvailableScooters(50,50,10)
    availableScooters = []
    for scooterId in scooterIds:
        availableScooters.append((scooterHashMap[scooterId]))
    print(availableScooters)