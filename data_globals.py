from enum import Enum, auto
from collections import defaultdict, namedtuple
from random import uniform
from typing import Dict, Optional, Tuple, Union, TypeVar
import colors
from dataclasses import dataclass
from math import inf

SMALLEST:float = 1 / inf

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

@dataclass(frozen=True, eq=True)
class PlanetHabitation:
    
    color:Tuple[int,int,int]
    description:str
    supports_life:bool=True
    can_ressuply:bool = False
    min_development:float =  0.0
    max_development:float = 0.0

    def generate_development(self):
        
        return uniform(self.min_development, self.max_development) if self.max_development > 0 else 0.0
            

PLANET_PREWARP = PlanetHabitation(
    color=colors.orange, 
    supports_life=True, 
    description="Pre-Warp",
    min_development = SMALLEST,
    max_development=0.25
)
PLANET_BARREN = PlanetHabitation(
    color=colors.planet_barren, 
    supports_life=False,
    description="Uninhabited"
)
PLANET_BOMBED_OUT = PlanetHabitation(
    description="Formerly Inhabited", 
    supports_life=False,
    color=colors.planet_barren
)
PLANET_FRIENDLY = PlanetHabitation(
    supports_life=True, 
    description="Friendly", 
    can_ressuply=True, 
    color=colors.planet_allied,
    min_development=0.25,
    max_development=1.0
)
PLANET_HOSTILE = PlanetHabitation(
    supports_life=True, 
    description="Hostile", 
    color=colors.planet_hostile,
    min_development=0.25,
    max_development=1.0
)
PLANET_ANGERED = PlanetHabitation(
    supports_life=True, 
    description="Angered", 
    color=colors.planet_hostile,
    min_development=0.25,
    max_development=1.0
)

#life_supporting_planets = (PlanetHabitation.PLANET_PREWARP, PlanetHabitation.PLANET_HOSTILE, PlanetHabitation.PLANET_FRIENDLY)


PLANET_TYPES = (PLANET_BARREN, PLANET_HOSTILE, PLANET_FRIENDLY, PLANET_PREWARP)

LOCAL_ENERGY_COST = 100
SECTOR_ENERGY_COST = 500
ENERGY_REGEN_PER_TURN = 100
REPAIR_MULTIPLIER = 3

@dataclass(eq=True, frozen=True)
class Condition:
    
    text:str
    fg:Tuple[int,int,int]
    bg:Tuple[int,int,int] = colors.black

CONDITION_GREEN = Condition("CONDITION GREEN", colors.alert_green)
CONDITION_YELLOW = Condition("CONDITION YELLOW", colors.alert_yellow)
CONDITION_BLUE = Condition("CONDITION BLUE", colors.alert_blue, colors.white)
CONDITION_RED = Condition("CONDITION RED", colors.alert_red)

"""
__damType = namedtuple(
    "damType", 
    ("damage_vs_shields_multiplier", "damage_vs_hull_multiplier", "damage_vs_no_shield_multiplier", "damage_vs_systems_multiplier", "damage_chance_vs_systems_multiplier", "damage_variation", "chance_to_damage_system", "accuracy_loss_per_distance_unit", "flat_accuracy_loss"), 
    defaults=(1.0, 1.0, 1.0, 0.12, 1.5, 1.0, 1.75, 0.0, 0.0)                   
                       )
"""

@dataclass(eq=True, frozen=True)
class DamageType:
    
    damage_vs_shields_multiplier:float = 1.0
    damage_vs_hull_multiplier:float = 1.0
    damage_vs_no_shield_multiplier:float = 1.0
    damage_vs_systems_multiplier:float = 0.12
    damage_chance_vs_systems_multiplier:float = 1.5
    damage_variation:float = 0.0
    chance_to_damage_system:float = 1.75
    accuracy_loss_per_distance_unit:float = 0.0
    flat_accuracy_loss:float = 0.0
    
    ''''
    __slots__ = ("damage_vs_shields_multiplier", "damage_vs_hull_multiplier", "damage_vs_no_shield_multiplier", "damage_vs_systems_multiplier", "damage_chance_vs_systems_multiplier", "damage_variation", "chance_to_damage_system", "accuracy_loss_per_distance_unit", "flat_accuracy_loss")
    '''
    
    """
    def __init__(self, *, damage_vs_shields_multiplier:float=1.0, damage_vs_hull_multiplier:float=1.0, damage_vs_no_shield_multiplier:float=1.0, damage_vs_systems_multiplier:float=0.12, damage_chance_vs_systems_multiplier:float=1.5, damage_variation:float=0.0, chance_to_damage_system:float=1.75, accuracy_loss_per_distance_unit:float=0.0, flat_accuracy_loss:float=0.0):
        
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
    """


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
    damage_vs_hull_multiplier=1.15, 
    damage_vs_no_shield_multiplier=1.75,
    flat_accuracy_loss=0.12,
    damage_variation=0.1
)
DAMAGE_EXPLOSION = DamageType(
    damage_vs_no_shield_multiplier=1.05, 
    damage_variation=0.25
)
DAMAGE_RAMMING = DamageType(
    damage_vs_shields_multiplier=1.05,
    damage_vs_hull_multiplier=1.2,
    damage_vs_no_shield_multiplier=1.35,
    damage_variation=0.05,
    accuracy_loss_per_distance_unit=0.005,
    flat_accuracy_loss=0.08,
)

@dataclass(eq=True, frozen=True)
class RepairStatus:
    
    #__slots__ = ("hull_repair", "system_repair", "energy_regeration", "repair_permanent_hull_damage")
    
    hull_repair:float
    system_repair:float
    energy_regeration:int
    repair_permanent_hull_damage:bool = False
    
    """
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
    """

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

@dataclass(eq=True, frozen=True)
class ShipStatus:
    """Psudo-Enum of the four ship statuses.

    ACTIVE: The ship is intact and crewed.
    DERLICT: The ship is intact but has no living crew.
    HULK: The ship is wrecked but mostly intact. Think battle of Wolf 359
    OBLITERATED: The ship has been reduced to space dust.
    
    Args:
            is_active (bool, optional): If this is True, the ship will be able to take action. Defaults to False.
            is_visible (bool, optional): If this is True, this ship will be visible on the main screen. Defaults to True.
            is_recrewable (bool, optional): If this is True, other ships will be able recrew/capture it. Defaults to False.
            is_collidable (bool, optional): If this is True, other ships/torpedos may collide with this ship. Defaults to True.
            override_color (Optional[Tuple[int,int,int]], optional): This color will be displayed instead of the ships default color. Defaults to None.
    """
    
    #__slots__ = ("is_active", "is_visible", "is_recrewable", "is_collidable", "do_shields_work", "override_color")
    
    is_active:bool=False
    is_visible:bool=True
    is_recrewable:bool=False
    is_collidable:bool=True
    is_destroyed:bool=False
    do_shields_work:bool=False
    can_be_targeted:bool=True
    override_color:Optional[Tuple[int,int,int]]=None
    
    """
    def __init__(self, *, is_active:bool=False, is_visible:bool=True, is_recrewable:bool=False, is_collidable:bool=True, do_shields_work:bool=False, override_color:Optional[Tuple[int,int,int]]=None) -> None:
        self.is_active = is_active
        self.is_visible = is_visible
        self.is_recrewable = is_recrewable
        self.is_collidable = is_collidable
        self.do_shields_work = do_shields_work
        self.override_color = override_color
    
    
    def __hash__(self) -> int:
        return hash((self.is_active, self.is_visible, self.is_recrewable, self.is_collidable, self.override_color))

    def __eq__(self, o: "ShipStatus") -> bool:
        try:
            return self.is_active == o.is_active and self.is_visible == o.is_visible and self.is_recrewable == o.is_recrewable and self.is_collidable == o.is_collidable and self.override_color == o.override_color
        except AttributeError:
            return False
    """
    
STATUS_ACTIVE = ShipStatus(
    is_active=True, 
    do_shields_work=True
)
STATUS_DERLICT = ShipStatus(
    is_recrewable=True, 
    override_color=colors.white
)
STATUS_HULK = ShipStatus(
    override_color=colors.grey, 
    is_destroyed=True
)
STATUS_OBLITERATED = ShipStatus(
    is_visible=False, 
    is_collidable=False, 
    is_destroyed=True, 
    can_be_targeted=False
)