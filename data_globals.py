from enum import Enum, auto
from collections import defaultdict, namedtuple
from typing import Dict, Tuple, Union, TypeVar
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
ENERGY_REGEN_PER_TURN = 100
REPAIR_MULTIPLIER = 3

class Condition(Enum):

    GREEN = auto()
    YELLOW = auto()
    BLUE = auto()
    RED = auto()

CONDITIONS: Dict[Condition,Tuple[str, Tuple[int,int,int]]] = {
    Condition.GREEN : ("CONDITION GREEN", colors.alert_green),
    Condition.YELLOW : ("CONDITION YELLOW", colors.alert_yellow),
    Condition.BLUE : ("CONDITION BLUE", colors.alert_blue),
    Condition.RED : ("CONDITION RED", colors.alert_red)
}

"""
__damType = namedtuple(
    "damType", 
    ("damage_vs_shields_multiplier", "damage_vs_hull_multiplier", "damage_vs_no_shield_multiplier", "damage_vs_systems_multiplier", "damage_chance_vs_systems_multiplier", "damage_variation", "chance_to_damage_system", "accuracy_loss_per_distance_unit", "flat_accuracy_loss"), 
    defaults=(1.0, 1.0, 1.0, 0.12, 1.5, 1.0, 1.75, 0.0, 0.0)                   
                       )
"""

class DamageType:
    
    __slots__ = ("damage_vs_shields_multiplier", "damage_vs_hull_multiplier", "damage_vs_no_shield_multiplier", "damage_vs_systems_multiplier", "damage_chance_vs_systems_multiplier", "damage_variation", "chance_to_damage_system", "accuracy_loss_per_distance_unit", "flat_accuracy_loss")
    
    def __init__(self, *, damage_vs_shields_multiplier:float=1.0, damage_vs_hull_multiplier:float=1.0, damage_vs_no_shield_multiplier:float=1.0, damage_vs_systems_multiplier:float=0.12, damage_chance_vs_systems_multiplier:float=1.5, damage_variation:float=1.0, chance_to_damage_system:float=1.75, accuracy_loss_per_distance_unit:float=0.0, flat_accuracy_loss:float=0.0):
        
        self.damage_vs_shields_multiplier = damage_vs_shields_multiplier
        self.damage_vs_hull_multiplier = damage_vs_hull_multiplier
        self.damage_vs_no_shield_multiplier = damage_vs_no_shield_multiplier
        self.damage_vs_systems_multiplier = damage_vs_systems_multiplier
        self.damage_chance_vs_systems_multiplier = damage_chance_vs_systems_multiplier
        self.damage_variation = damage_variation
        self.chance_to_damage_system = chance_to_damage_system
        self.accuracy_loss_per_distance_unit = accuracy_loss_per_distance_unit
        self.flat_accuracy_loss = flat_accuracy_loss
        
    def __hash__(self) -> int:
        return hash((self.damage_vs_shields_multiplier, self.damage_vs_hull_multiplier, self.damage_vs_no_shield_multiplier, self.damage_vs_systems_multiplier, self.damage_chance_vs_systems_multiplier, self.damage_variation, self.chance_to_damage_system, self.accuracy_loss_per_distance_unit, self.flat_accuracy_loss))
    
    def __eq__(self, o: "DamageType") -> bool:
        try:
            return self.damage_vs_shields_multiplier == o.damage_vs_shields_multiplier and self.damage_vs_hull_multiplier == o.damage_vs_hull_multiplier and self.damage_vs_no_shield_multiplier == o.damage_vs_no_shield_multiplier and self.damage_vs_systems_multiplier == o.damage_vs_systems_multiplier and self.damage_chance_vs_systems_multiplier == o.damage_chance_vs_systems_multiplier and self.damage_variation == o.damage_variation and self.chance_to_damage_system == o.chance_to_damage_system and self.accuracy_loss_per_distance_unit == o.accuracy_loss_per_distance_unit and self.flat_accuracy_loss == o.flat_accuracy_loss
        except AttributeError:
            return False

#A = TypeVar("A", int)
#DamageType = TypeVar("DamageType", DamageType)

DAMAGE_BEAM = DamageType(
    damage_variation=0.025, 
    damage_chance_vs_systems_multiplier=2.75, 
    damage_vs_systems_multiplier=0.25, 
    chance_to_damage_system=2.75,
    accuracy_loss_per_distance_unit = 0.01
)
DAMAGE_CANNON = DamageType(
    damage_vs_shields_multiplier= 1.25, 
    damage_vs_hull_multiplier=1.25, 
    damage_vs_no_shield_multiplier=1.25, 
    damage_variation=0.075,
    accuracy_loss_per_distance_unit=0.03
)
DAMAGE_TORPEDO = DamageType(
    damage_vs_shields_multiplier=0.75, 
    damage_vs_hull_multiplier=1.05, 
    damage_vs_no_shield_multiplier=1.75, 
    damage_variation=0.1
)
DAMAGE_EXPLOSION = DamageType(
    damage_vs_no_shield_multiplier=1.1, 
    damage_variation=0.25
)

class RepairStatus:
    
    __slots__ = ("hull_repair", "system_repair", "energy_regeration", "repair_permanent_hull_damage")
    
    def __init__(self, *, hull_repair:float, system_repair:float, energy_regeration:int, repair_permanent_hull_damage:bool=False) -> None:
        self.hull_repair = hull_repair
        self.system_repair = system_repair
        self.energy_regeration = energy_regeration
        self.repair_permanent_hull_damage = repair_permanent_hull_damage
    
    def __hash__(self) -> int:
        return hash((self.hull_repair, self.system_repair, self.energy_regeration, self.repair_permanent_hull_damage))
    
    def __eq__(self, o: "RepairStatus") -> bool:
        try:
            return self.hull_repair == o.hull_repair and self.system_repair == o.system_repair and self.energy_regeration == o.energy_regeration and self.repair_permanent_hull_damage == o.repair_permanent_hull_damage
        except AttributeError:
            return False

#RepairStatus = TypeVar("RepairStatus", RepairStatus)

REPAIR_PER_TURN = RepairStatus(
    hull_repair=0.01,
    system_repair=0.005,
    energy_regeration=100
)
REPAIR_DEDICATED = RepairStatus(
    hull_repair=0.1,
    system_repair=0.05,
    energy_regeration=250
)
REPAIR_DOCKED = RepairStatus(
    hull_repair=0.25,
    system_repair=0.15,
    energy_regeration=750,
    repair_permanent_hull_damage=True
)