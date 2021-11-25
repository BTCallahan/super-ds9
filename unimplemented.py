from enum import Enum, auto
from functools import lru_cache

from order import Order, OrderWarning



class ShipData:

    cloak_strength = 0.0

    def __init__(self, *, cloak_strength:float=0.0) -> None:
        self.cloak_strength = cloak_strength

    



