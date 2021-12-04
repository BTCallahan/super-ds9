from enum import Enum, auto
from typing import Dict, Iterable

class TorpedoType(Enum):

    TORP_TYPE_NONE = auto()
    TORP_TYPE_POLARON = auto()
    TORP_TYPE_PHOTON = auto()
    TORP_TYPE_QUANTUM = auto()

class Torpedo:
    def __init__(self, name:str, damage:int, infrastructure:float):
        self.capName = name.capitalize()
        self.name = name
        self.capPlural = name.capitalize() + 's'
        self.plural = name + 's'
        self.capPluralColon = self.capPlural + ':'
        self.damage = damage
        self.infrastructure = infrastructure

    def __hash__(self) -> int:
        return hash((self.name, self.damage, self.infrastructure))

    def __lt__(self, t: "Torpedo"):

        return (self.damage < t.damage) if self.infrastructure == t.infrastructure else (self.infrastructure < t.infrastructure) 

    def __gt__(self, t: "Torpedo"):
        return (self.damage > t.damage) if self.infrastructure == t.infrastructure else (self.infrastructure > t.infrastructure)
    
    def __eq__(self, t: "Torpedo") -> bool:
        try:
            return self.damage == t.damage and self.infrastructure == t.infrastructure and self.name == t.name
        except AttributeError:
            return False
    
    def __ne__(self, t: "Torpedo") -> bool:
        try:
            return self.damage != t.damage or self.infrastructure != t.infrastructure and self.name != t.name
        except AttributeError:
            return False

"""
TORP_TYPE_NONE = Torpedo('', 0, 0.0)
TORP_TYPE_POLARON = Torpedo('polaron', 60, 0.35)
TORP_TYPE_PHOTON = Torpedo('photon', 75, 0.5)
TORP_TYPE_QUANTUM = Torpedo('quantum', 100, 0.75)
"""

ALL_TORPEDO_TYPES: Dict[TorpedoType,Torpedo] = {
    TorpedoType.TORP_TYPE_NONE : Torpedo('', 0, 0.0),
    TorpedoType.TORP_TYPE_POLARON : Torpedo('polaron', 240, 0.35),
    TorpedoType.TORP_TYPE_PHOTON : Torpedo('photon', 300, 0.5), 
    TorpedoType.TORP_TYPE_QUANTUM : Torpedo('quantum', 400, 0.75)
}

def find_most_powerful_torpedo(iter_torpedo_type:Iterable[TorpedoType]):

    torp_type = TorpedoType.TORP_TYPE_NONE
    damage = 0

    for t in iter_torpedo_type:
        torp = ALL_TORPEDO_TYPES[t]
        if torp.damage > damage:
            torp_type = t
            damage = torp.damage
    return torp_type