from random import randrange, randint, uniform
from math import radians, sqrt
from collections import namedtuple
from typing import Optional, Union, overload


IntOrFloat = Union[int,float]

AnyCoords = Union["Coords", "MutableCoords"]

IntFloatOrCoords = Union[int, float, "Coords", "MutableCoords"]

#c = namedtuple("Coords", ("x", "y"))

class Coords(namedtuple("Coords_", ("x", "y"))):

    __slots__ = ()#("x", "y")

    @classmethod
    def rounded_init(cls, x:IntOrFloat, y:IntOrFloat):
        return cls(round(x), round(y))

    @classmethod
    def randomPositiveCoords(cls, x:int, y:int):
        return cls(randrange(0, x), randrange(0, y))

    def __str__(self) -> str:
        return f"{self.x} {self.y}"

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def clamp_new(self, x:IntOrFloat, y:IntOrFloat):
        return Coords(x=max(min(self.x, x - 1), 0), y=max(min(self.y, y - 1), 0))

    def __sub__(self, coords:AnyCoords):
        return self.x - coords.x, self.y - coords.y

    def __add__(self, coords:AnyCoords):
        return self.x + coords.x, self.y + coords.y

    def check(self, x:IntOrFloat, y:IntOrFloat):
        return self.x == x and self.y == y

    def __eq__(self, other:AnyCoords):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other:AnyCoords):
        return self.x != other.x or self.y != other.y

    def distance(self, *, coords:Optional[AnyCoords]=None, x:Optional[IntOrFloat]=None, y:Optional[IntOrFloat]=None):
        if x is not None and y is not None:
            return pow((pow(self.x - x, 2) + pow(self.y - y, 2)), 0.5)
        if coords is not None:
            return pow((pow(self.x - coords.x, 2) + pow(self.y - coords.y, 2)), 0.5)
        return pow((pow(self.x, 2) + pow(self.y, 2)), 0.5)

    def is_adjacent(self, other:AnyCoords):
        return self.x in {other.x-1, other.x, other.x+1} and self.y in {other.y-1, other.y, other.y+1}

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
    def normalize(self, *, coords:Optional[AnyCoords]=None, x:Optional[IntOrFloat]=None, y:Optional[IntOrFloat]=None):
        if x is not None and y is not None:
            d = sqrt(pow(x, 2) + pow(y, 2))
        elif coords is not None:
            x, y = coords.x, coords.y
            d = sqrt(pow(x, 2) + pow(y, 2))
        else:
            x, y = self.x, self.y
            d = sqrt(pow(x, 2) + pow(y, 2))
        try:
            return x / d, y / d
        except ZeroDivisionError:
            return 0, 0
    
    def is_adjacent(self, *, other:Optional[AnyCoords]=None, x:Optional[int]=None, y:Optional[int]=None):
        if x is not None and y is not None:
            return self.x in {x-1, x, x+1} and self.y in {y-1, y, y+1}
        return self.x in {other.x-1, other.x, other.x+1} and self.y in {other.y-1, other.y, other.y+1}

    def __str__(self):
        return 'X: ' + str(self.x) + ', Y: ' + str(self.y)

    @classmethod
    def randomPointWithinRadius(cls, radius):
        dist = uniform(0.0, radius)
        diam = radians(uniform(0.0, 360.0))

        x = randint(-radius, radius+1)
        y =  randint(-radius, radius+1)

        d = pow((pow(x, 2) + pow(y, 2)), 0.5)
        nX, nY = cls.normalize(x=x, y=y)
        return cls(round(nX * radius), round(nY * radius))

class MutableCoords:

    __slots__ = ("x", "y")

    def __init__(self, x:IntOrFloat, y:IntOrFloat):
        self.x = x
        self.y = y
    
    def __str__(self) -> str:
        return f"{self.x} {self.y}"

    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def __eq__(self, other:AnyCoords):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other:AnyCoords):
        return self.x != other.x or self.y != other.y
        
    def is_adjacent(self, *, other:Optional[AnyCoords]=None, x:Optional[int]=None, y:Optional[int]=None):
        if x is not None and y is not None:
            return self.x in {x-1, x, x+1} and self.y in {y-1, y, y+1}
        return self.x in {other.x-1, other.x, other.x+1} and self.y in {other.y-1, other.y, other.y+1}
    
    def distance(self, *, coords:Optional[AnyCoords]=None, x:Optional[IntOrFloat]=None, y:Optional[IntOrFloat]=None) -> float:
        if x is not None and y is not None:
            return pow((pow(self.x - x, 2) + pow(self.y - y, 2)), 0.5)
        if coords is not None:
            return pow((pow(self.x - coords.x, 2) + pow(self.y - coords.y, 2)), 0.5)
        return pow((pow(x, 2) + pow(y, 2)), 0.5)

    def create_coords(self):
        return Coords(x=self.x, y=self.y)
    
    def clamp_new(self, x:IntOrFloat, y:IntOrFloat):
        self.x=max(min(self.x, x - 1), 0)
        self.y=max(min(self.y, y - 1), 0)
        

