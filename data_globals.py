from enum import Enum, auto
from random import uniform
from typing import Dict, Final, Optional, Tuple, Union
import colors
from dataclasses import dataclass
from math import inf

SMALLEST:Final = 1 / inf

string_or_int = Union[int,str]

PRECISION_SCANNING_VALUES:Final = {1, 2, 5, 10, 15, 20, 25, 50, 100, 200, 500}
@dataclass(frozen=True, eq=True)
class PlanetHabitation:
    
    color:Tuple[int,int,int]
    description:str
    supports_life:bool = True
    can_ressuply:bool = False
    min_development:float =  0.0
    max_development:float = 0.0
    has_disposition_towards_warp_capiable_civs:bool = False

    def generate_development(self):
        
        return float(uniform(self.min_development, self.max_development) if self.max_development > 0 else 0.0)
            
PLANET_PREWARP:Final = PlanetHabitation(
    color=colors.orange, 
    supports_life=True, 
    description="Pre-Warp",
    min_development = SMALLEST,
    max_development=0.05
)
PLANET_BARREN:Final = PlanetHabitation(
    color=colors.planet_barren, 
    supports_life=False,
    description="Uninhabited"
)
PLANET_BOMBED_OUT:Final = PlanetHabitation(
    description="Formerly Inhabited", 
    supports_life=False,
    color=colors.planet_barren
)
PLANET_WARP_CAPABLE:Final = PlanetHabitation(
    description="Warp Capable",
    supports_life=True,
    color=colors.white,
    has_disposition_towards_warp_capiable_civs=True
)
PLANET_FRIENDLY:Final = PlanetHabitation(
    supports_life=True, 
    description="Friendly", 
    can_ressuply=True, 
    color=colors.planet_allied,
    min_development=0.05,
    max_development=1.0
)
PLANET_HOSTILE:Final = PlanetHabitation(
    supports_life=True, 
    description="Hostile", 
    color=colors.planet_hostile,
    min_development=0.05,
    max_development=1.0
)
PLANET_NEUTRAL:Final = PlanetHabitation(
    supports_life=True, 
    description="Neutral", 
    color=colors.planet_neutral,
    min_development=0.05,
    max_development=1.0
)
PLANET_TYPES:Final = (PLANET_BARREN, PLANET_PREWARP, PLANET_WARP_CAPABLE)

LOCAL_ENERGY_COST:Final = 50
SECTOR_ENERGY_COST:Final = 250

@dataclass(eq=True, frozen=True)
class Condition:
    
    text:str
    fg:Tuple[int,int,int]
    bg:Tuple[int,int,int] = colors.black

CONDITION_GREEN:Final = Condition("CONDITION GREEN", colors.alert_green)
CONDITION_YELLOW:Final = Condition("CONDITION YELLOW", colors.alert_yellow)
CONDITION_BLUE:Final = Condition("CONDITION BLUE", colors.alert_blue)
CONDITION_RED:Final = Condition("CONDITION RED", colors.alert_red)

@dataclass(eq=True, frozen=True)
class DamageType:
    
    damage_vs_shields_multiplier:float = 1.0
    damage_vs_hull_multiplier:float = 1.0
    damage_vs_no_shield_multiplier:float = 1.0
    damage_vs_systems_multiplier:float = 0.12
    damage_chance_vs_systems_multiplier:float = 1.0
    damage_variation:float = 0.0
    chance_to_damage_system:float = 0.75
    accuracy_loss_per_distance_unit:float = 0.0
    flat_accuracy_loss:float = 0.0
    autohit_if_target_cant_move:bool = False
    
DAMAGE_BEAM:Final = DamageType(
    damage_variation=0.025, 
    damage_chance_vs_systems_multiplier=1.75, 
    damage_vs_systems_multiplier=0.25, 
    chance_to_damage_system=2.25,
    accuracy_loss_per_distance_unit = 0.01
)
DAMAGE_CANNON:Final = DamageType(
    damage_vs_shields_multiplier= 1.25, 
    damage_vs_hull_multiplier=1.25, 
    damage_vs_no_shield_multiplier=1.25, 
    damage_variation=0.075,
    accuracy_loss_per_distance_unit=0.03
)
DAMAGE_TORPEDO:Final = DamageType(
    damage_vs_shields_multiplier=0.75, 
    damage_vs_hull_multiplier=1.15, 
    damage_vs_no_shield_multiplier=1.75,
    flat_accuracy_loss=0.12,
    damage_variation=0.1
)
DAMAGE_EXPLOSION:Final = DamageType(
    damage_vs_no_shield_multiplier=1.05, 
    damage_variation=0.25
)
DAMAGE_RAMMING:Final = DamageType(
    damage_vs_shields_multiplier=1.05,
    damage_vs_hull_multiplier=1.2,
    damage_vs_no_shield_multiplier=1.35,
    damage_variation=0.05,
    autohit_if_target_cant_move=True
)

@dataclass(eq=True, frozen=True)
class RepairStatus:
        
    hull_repair:float
    system_repair:float
    energy_regeration:float
    repair_permanent_hull_damage:float = 0.0
    
REPAIR_PER_TURN:Final = RepairStatus(
    hull_repair=0.01,
    system_repair=0.005,
    energy_regeration=1.0
)
REPAIR_DEDICATED:Final = RepairStatus(
    hull_repair=0.1,
    system_repair=0.05,
    energy_regeration=2.5
)
REPAIR_DOCKED:Final = RepairStatus(
    hull_repair=0.25,
    system_repair=0.15,
    energy_regeration=7.5,
    repair_permanent_hull_damage=0.175
)

@dataclass(eq=True, frozen=True)
class ShipStatus:
    """Psudo-Enum of the four ship statuses.

    ACTIVE: The ship is intact and crewed.
    DERLICT: The ship is intact but has no living crew.
    HULK: The ship is wrecked but mostly intact. Think battle of Wolf 359
    OBLITERATED: The ship has been reduced to space dust.
    STATUS_CLOAKED: The ship is cloaked and cannot be targeted or seen. However, it's shields are off line.
    STATUS_CLOAK_COMPRIMISED: The ship has been detected can be targeted and seen. It.s shields are off line.
    
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
    energy_drain:bool=False
    
STATUS_ACTIVE:Final = ShipStatus(
    is_active=True, 
    do_shields_work=True
)
STATUS_DERLICT:Final = ShipStatus(
    is_recrewable=True, 
    override_color=colors.white
)
STATUS_HULK:Final = ShipStatus(
    override_color=colors.grey, 
    is_destroyed=True
)
STATUS_OBLITERATED:Final = ShipStatus(
    is_visible=False, 
    is_collidable=False, 
    is_destroyed=True, 
    can_be_targeted=False
)
STATUS_CLOAKED:Final = ShipStatus(
    is_visible=False,
    is_active=True,
    can_be_targeted=False,
    energy_drain=True
)
STATUS_CLOAK_COMPRIMISED = ShipStatus(
    is_active=True,
    energy_drain=True
)
STATUS_AT_WARP = ShipStatus(
    is_active=True,
    is_visible=False,
    is_collidable=False,
    do_shields_work=True
)

class CloakStatus(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
    COMPRIMISED = auto()

def create_warp_factor():
    """This is used to generate the warp factor tuple. Each item contains an intiger and a float. W

    Yields:
        Tuple[int, float]: The intiger represent the speed, and the float represnt
    """
    
    ad = 0.125
    
    #yield (0,0)
    
    for i in range(10):
        yield i, i * (1+ad)
        
        ad *= 2

WARP_FACTOR = tuple(create_warp_factor())

class PlanetRelation(Enum):
    FRIENDLY = auto()
    NEUTRAL = auto()
    HOSTILE = auto()

PLANET_RELATIONS = (
    PlanetRelation.FRIENDLY,
    PlanetRelation.NEUTRAL,
    PlanetRelation.HOSTILE
)
PLANET_RELATION_DICT:Final = {
    PlanetRelation.FRIENDLY : PLANET_FRIENDLY,
    PlanetRelation.NEUTRAL : PLANET_NEUTRAL,
    PlanetRelation.HOSTILE : PLANET_HOSTILE
}