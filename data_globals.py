from enum import Enum, auto
from collections import defaultdict
from typing import Union
import colors

string_or_int = Union[int,str]

class ShipTypes(Enum):

    TYPE_ALLIED = auto()
    TYPE_ENEMY_SMALL = auto()
    TYPE_ENEMY_LARGE = auto()

SYM_PLAYER = '@'
SYM_FIGHTER = 'F'
SYM_AD_FIGHTER = 'A'
SYM_CRUISER = 'C'
SYM_BATTLESHIP = 'B'
SYM_RESUPPLY = '$'

class PlanetHabitation(Enum):
    PLANET_BARREN = auto()
    PLANET_PREWARP = auto()
    PLANET_HOSTILE = auto()
    PLANET_FRIENDLY = auto()
    PLANET_ANGERED = auto()
    PLANET_BOMBED_OUT = auto()

planet_habitation_color_dict = {
    PlanetHabitation.PLANET_ANGERED : colors.planet_hostile,
    PlanetHabitation.PLANET_BARREN : colors.planet_barren,
    PlanetHabitation.PLANET_BOMBED_OUT : colors.planet_barren,
    PlanetHabitation.PLANET_FRIENDLY : colors.planet_allied,
    PlanetHabitation.PLANET_HOSTILE : colors.planet_hostile,
    PlanetHabitation.PLANET_PREWARP : colors.grey
}


life_supporting_planets = (PlanetHabitation.PLANET_PREWARP, PlanetHabitation.PLANET_HOSTILE, PlanetHabitation.PLANET_FRIENDLY)


PLANET_TYPES = (PlanetHabitation.PLANET_BARREN, PlanetHabitation.PLANET_HOSTILE, PlanetHabitation.PLANET_FRIENDLY)

LOCAL_ENERGY_COST = 100
SECTOR_ENERGY_COST = 500
