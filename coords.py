from random import randrange, randint, uniform
from math import radians
class Coords:

    def __init__(self, x, y):
        self.x = round(x)
        self.y = round(y)

    @classmethod
    def randomPositiveCoords(cls, x, y):
        return cls(random.randrange(0, x), random.randrange(0, y))

    def clamp(self, x, y):
        self.x = max(min(self.x, x - 1), 0)
        self.y = max(min(self.y, y - 1), 0)

    def __sub__(self, coords):
        return self.x - coords.x, self.y - coords.y

    def __add__(self, coords):
        return self.x + coords.x, self.y + coords.y

    def check(self, x, y):
        return self.x == x and self.y == y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y

    def distance(self, cooards):
        return pow((pow(self.x - cooards.x, 2) + pow(self.y - cooards.y, 2)), 0.5)


    def normalize(self, x=0, y=0):
        if x == 0 and y == 0:
            x = self.x
            y = self.y
        d = math.sqrt(pow(x, 2) + pow(y, 2))
        return x / d, y / d

    def isInBounds(self, rangeX, rangeY):
        return self.x in rangeX and self.y in rangeY
        """
    @property
    def isInSectorBounds(self):
        return self.x in SUB_SECTORS_RANGE_X and self.y in SUB_SECTORS_RANGE_Y

    @property
    def isInLocalBounds(self):
        return self.x in SUB_SECTOR_SIZE_RANGE_X and self.y in SUB_SECTOR_SIZE_RANGE_Y
"""
    def isAdjacent(self, coords):
        return self.x in range(coords.x - 1, coords.x + 1) and self.y in range(coords.y - 1, coords.y + 1)

    def __str__(self):
        return 'X: ' + str(self.x) + ', Y: ' + str(self.y)

    @classmethod
    def randomPointWithinRadius(cls, radius):
        dist = uniform(0.0, radius)
        diam = math.radians(uniform(0.0, 360.0))

        x = random.randint(-radius, radius+1)
        y =  random.randint(-radius, radius+1)

        d = pow((pow(x, 2) + pow(y, 2)), 0.5)
        nX, nY = self.normalize(x, y)
        return cls(round(nX * radius), round(nY * radius))
