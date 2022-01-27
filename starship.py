from __future__ import annotations
from dataclasses import dataclass
from decimal import DivisionByZero
import re
from typing import TYPE_CHECKING, Dict, Final, Iterable, List, Optional, Tuple, Type, Union
from random import choice, uniform, random, randint
from math import ceil, floor, inf
from itertools import accumulate
from functools import lru_cache
from string import digits
from energy_weapon import ALL_ENERGY_WEAPONS
from get_config import CONFIG_OBJECT

from global_functions import get_first_group_in_pattern, inverse_square_law
from nation import ALL_NATIONS
from space_objects import SubSector, CanDockWith, ALL_TORPEDO_TYPES
from torpedo import Torpedo, find_most_powerful_torpedo
from coords import Coords, IntOrFloat, MutableCoords
import colors
from data_globals import DAMAGE_BEAM, DAMAGE_CANNON, DAMAGE_EXPLOSION, DAMAGE_RAMMING, DAMAGE_TORPEDO, REPAIR_DEDICATED, REPAIR_DOCKED, REPAIR_PER_TURN, SMALLEST, STATUS_AT_WARP, WARP_FACTOR, DamageType, RepairStatus, ShipStatus, STATUS_ACTIVE, STATUS_DERLICT, STATUS_CLOAKED, STATUS_CLOAK_COMPRIMISED,STATUS_HULK, STATUS_OBLITERATED, CloakStatus

def scan_assistant(v:IntOrFloat, precision:int):
    """This takes a value, v and devides it by the precision. Next, the quotent is rounded to the nearest intiger and then multiplied by the precision. The product is then returned. A lower precision value ensures more accurate results. If precision is 1, then v is returned

    E.g.:
    v = 51.25
    p = 25

    round(51.25 / 25) * 25
    round(2.41) * 25
    2 * 25
    50

    Args:
        v (IntOrFloat): The value that is modified
        precision (int): This value is used to calucalate the crecision. Lower values are more precise.

    Returns:
        int: The modified value
    """
    assert isinstance(precision, int)
    if precision == 1:
        return round(v)
    r = round(v / precision) * precision
    assert isinstance(r, float) or isinstance(r, int)
    return r

if TYPE_CHECKING:
    from game_data import GameData
    from ai import BaseAi

class StarshipSystem:
    """This handles a starship system, such as warp drives or shields.
    
    Args:
            name (str): The name of the system.
    
    """

    def __init__(self, name:str):
        self._integrety = 1.0
        self.name = '{: >17}'.format(name)

    @property
    def integrety(self):
        return self._integrety
    
    @integrety.setter
    def integrety(self, value:float):
        assert isinstance(value, float) or isinstance(value, int)
        self._integrety = value
        if self._integrety < 0.0:
            self._integrety = 0.0
        elif self._integrety > 1.0:
            self._integrety = 1.0

    @property
    def is_opperational(self):
        return self._integrety >= 0.15

    @property
    def get_effective_value(self):
        """Starship systems can take quite a bit of beating before they begin to show signs of reduced performance. 
        Generaly, when the systems integrety dips below 80% is when you will see performance degrade. Should integrety 
        fall below 15%, then the system is useless and inoperative.
        """
        return min(1.0, self._integrety * 1.25) if self.is_opperational else 0.0

    @property
    def is_comprimised(self):
        """Has this system taken sufficent damage in impaire is performance?

        Returns:
            bool: Returns True if its integrety times 1.25 is less then 1, False otherwise.
        """
        return self._integrety * 1.25 < 1.0

    @property
    def affect_cost_multiplier(self):
        try:
            return 1 / self.get_effective_value
        except DivisionByZero:
            return inf

    #def __add__(self, value):

    def get_info(self, precision:int, effective_value:bool, below_15_is_0:bool=True):
        
        i = min(1.0, self._integrety * 1.25) if effective_value else self._integrety
        
        if below_15_is_0 and not self.is_opperational:
            i = 0.0
        
        if precision <= 1.0 or i == 0.0 or i == 1.0:
            return i
        
        try :
            r = round(i * 100 / precision) * precision * 0.01
        except ZeroDivisionError:
            r = 0.0
        
        assert isinstance(r, float)
        return r

    def print_info(self, precision:float):
        return f"{self.get_info(precision, False):.2%}" if self.is_opperational else f"OFFLINE"

    def get_color(self):
        if not self.is_comprimised:
            return colors.alert_green
        return colors.alert_yellow if self.is_opperational else colors.alert_red

def randomNeumeral(n:int) -> str:
    for i in range(n):
        yield choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])

@lru_cache
def get_system_names(
    *,
    has_torpedo_launchers:bool=False,
    has_cloaking_device:bool=False,
    has_transporters:bool=True,
    mobile:bool=True,
    beam_weapon_name:str="",
    cannon_weapon_name:str=""
):
    names = [
        "Warp Core:",
        "Sensors:",
        "Shield Gen.:",
    ]
    keys = [
        "sys_warp_core",
        "sys_sensors",
        "sys_shield",
    ]
    if mobile:
        names.extend(
            [
                "Impulse Eng.:", 
                "Warp Drive:",    
            ]
        )
        keys.extend(
            [
                "sys_impulse",
                "sys_warp_drive",
            ]
        )
    if beam_weapon_name:
        names.append(f"{beam_weapon_name}:")
        keys.append("sys_beam_array")

    if cannon_weapon_name:
        names.append(f"{cannon_weapon_name}:")
        keys.append("sys_cannon_weapon")

    if has_cloaking_device:
        names.append("Cloak Dev.:")
        keys.append("sys_cloak")

    if has_torpedo_launchers:
        names.append("Torp. Launchers:")
        keys.append("sys_torpedos")
    
    if has_transporters:
        names.append("Transporters:")
        keys.append("sys_transporter")
    
    return tuple(names), tuple(keys)

VALID_SHIP_TYPES:Final = {
    "ESCORT",
    "ATTACK_FIGHTER",
    "CRUISER",
    "WARSHIP",
    "RESUPPLY",
    "PLATFORM",
    "STATION",
    "BIRD_OF_PREY",
    "WARBIRD"
}

@dataclass(frozen=True)
class ShipClass:

    ship_type:str
    name:str
    symbol:str
    max_shields:int
    max_hull:int
    max_crew:int
    max_energy:int
    damage_control:float
    energy_weapon_code:str
    nation_code:str
    system_names:Tuple[str]
    system_keys:Tuple[str]
    detection_strength:float
    targeting:float
    size:float
    evasion:float=0.0
    max_beam_energy:int=0
    max_beam_targets:int=1
    max_cannon_energy:int=0
    max_armor:int=0
    max_torpedos:int=0
    torp_types:Optional[List[str]]=None    
    torp_tubes:int=0
    warp_breach_damage:int=2
    cloak_strength:float=0.0
    cloak_cooldown:int=2

    """
    def __init__(self, *,
        ship_type:str, 
        name:str,
        symbol:str, 
        max_shields:int, 
        max_armor:int=0, 
        max_hull:int, 
        max_torps:int=0, 
        max_crew:int, 
        max_energy:int, 
        damage_control:float, 
        torp_types:Optional[List[str]]=None, 
        torp_tubes:int=0,
        max_beam_energy:int, 
        warp_breach_damage:int=2, 
        energy_weapon_code:str,
        nation_code:str,
        system_names:Tuple[str],
        system_keys:Tuple[str]
    ):
        self.ship_type = ship_type
        self.symbol = symbol
        self.name = name

        self.max_shields = max_shields
        self.max_armor = max_armor
        self.max_hull = max_hull

        self.max_crew = max_crew
        self.max_energy = max_energy

        self.damage_control = damage_control
        self.nation_code = nation_code
        self.energy_weapon_code = energy_weapon_code
        
        if (torp_types is None or len(torp_types) == 0) != (torp_tubes < 1) != (max_torps < 1):
            raise IndexError(
                f'''The length of the torp_types list is {len(torp_types)}, but the value of torp_tubes is 
{torp_tubes}, and the value of maxTorps is {max_torps}. All of these should be less then one, OR greater then or equal 
to one.'''
            )

        if torp_types:
            torp_types.sort(key=lambda t: ALL_TORPEDO_TYPES[t].damage, reverse=True)

        self.torp_types:Tuple[str] = tuple(["NONE"] if not torp_types else torp_types)

        self.max_torpedos = max_torps
        self.torp_tubes = torp_tubes
        self.max_beam_energy = max_beam_energy
        self.warp_breach_damage = warp_breach_damage
    """
    
    @classmethod
    def create_ship_class(
        cla,
        *,
        ship_type:str, 
        name:str,
        symbol:str, 
        max_shields:int, 
        max_armor:int=0, 
        max_hull:int, 
        max_torpedos:int=0, 
        max_crew:int=0, 
        max_energy:int, 
        damage_control:float, 
        torp_types:Optional[List[str]]=None, 
        torp_tubes:int=0,
        max_beam_energy:int=0,
        max_beam_targets:int=1,
        max_cannon_energy:int=0, 
        warp_breach_damage:int=2, 
        energy_weapon_code:str,
        nation_code:str,
        cloak_strength:float=0.0,
        detection_strength:float,
        size:float,
        targeting:float,
        evasion:float=0.0,
        cloak_cooldown:int=2
    ):
        
        if (torp_types is None or len(torp_types) == 0) != (torp_tubes < 1) != (max_torpedos < 1):
            raise IndexError(
                f'''The length of the torp_types list is {len(torp_types)}, but the value of torp_tubes is \
{torp_tubes}, and the value of maxTorps is {max_torpedos}. All of these should be less then one, OR greater then or equal \
to one.'''
            )
        if torp_types:
            torp_types.sort(key=lambda t: ALL_TORPEDO_TYPES[t].damage, reverse=True)

        torp_types_:Tuple[str] = tuple(["NONE"] if not torp_types else torp_types)
        
        short_beam_name_cap = ALL_ENERGY_WEAPONS[energy_weapon_code].short_beam_name_cap if max_beam_energy else ""
        
        short_can_name_cap = ALL_ENERGY_WEAPONS[energy_weapon_code].short_cannon_name_cap if max_cannon_energy else ""
        
        system_names, system_keys = get_system_names(
            has_torpedo_launchers=max_torpedos > 0 and torp_tubes > 0,
            has_cloaking_device=cloak_strength > 0.0,
            has_transporters=max_crew > 0,
            beam_weapon_name=f"{short_beam_name_cap}s",
            cannon_weapon_name=f"{short_can_name_cap}",
            mobile=evasion > 0.0
        )
        return cla(
            ship_type=ship_type,
            name=name,
            symbol=symbol,
            max_shields=max_shields,
            max_armor=max_armor,
            max_hull=max_hull,
            max_torpedos=max_torpedos,
            max_crew=max_crew,
            max_energy=max_energy,
            damage_control=damage_control,
            torp_types=torp_types_,
            torp_tubes=torp_tubes,
            max_beam_energy=max_beam_energy,
            max_beam_targets=max_beam_targets,
            max_cannon_energy=max_cannon_energy,
            warp_breach_damage=warp_breach_damage,
            energy_weapon_code=energy_weapon_code,
            nation_code=nation_code,
            system_names=system_names, 
            system_keys=system_keys,
            cloak_strength=cloak_strength,
            cloak_cooldown=cloak_cooldown,
            detection_strength=detection_strength,
            size=size,
            targeting=targeting,
            evasion=evasion
        )

    @property
    @lru_cache
    def nation(self):
        if self.nation_code not in ALL_NATIONS:
            raise KeyError(
                f"The nation code {self.nation_code} was not found in the dictionary of nations. Valid code are: {ALL_NATIONS.keys()}")
    
        return ALL_NATIONS[self.nation_code]
        
    @property
    @lru_cache
    def get_energy_weapon(self):
        if self.energy_weapon_code not in ALL_ENERGY_WEAPONS:
            raise KeyError(
                f"The energy weapon code {self.energy_weapon_code} was not found in the dictionary of energy weapons. Valid code are: {ALL_ENERGY_WEAPONS.keys()}")
        return ALL_ENERGY_WEAPONS[self.energy_weapon_code]

    def create_name(self):
        return choice(self.nation.ship_names) if self.has_proper_name else "".join([choice(digits) for a in range(8)])

    @property
    @lru_cache
    def has_proper_name(self):
        """Does this ship/station have a propper name, or just a sequence of numbers?

        Returns:
            bool: True if the ship's nation has names AND it has crew, False otherwise
        """        
        return self.nation.ship_names and self.max_crew > 0

    @property
    @lru_cache
    def ship_type_has_shields(self):
        return self.max_shields > 0

    @property
    @lru_cache
    def ship_type_can_fire_torps(self):
        return len(
            self.torp_types
        ) > 0 and self.torp_types[0] != "NONE" and self.max_torpedos > 0 and self.torp_tubes > 0

    @property
    @lru_cache
    def get_most_powerful_torpedo_type(self):
        if not self.ship_type_can_fire_torps:
            return "NONE"

        if len(self.torp_types) == 1:
            return self.torp_types[0]

        return find_most_powerful_torpedo(self.torp_types)

    @property
    @lru_cache
    def ship_type_can_fire_beam_arrays(self):
        return self.max_beam_energy > 0
    
    @property
    @lru_cache
    def ship_type_can_fire_cannons(self):
        return self.max_cannon_energy > 0

    @property
    @lru_cache
    def is_automated(self):
        return self.max_crew < 1

    @property
    @lru_cache
    def ship_type_can_cloak(self):
        return self.cloak_strength > 0.0

    @property
    @lru_cache
    def get_stragic_values(self):
        """Determins the stragic value of the ship class for scoring purpousess.

        Returns:
            Tuple[int,float]: A tuple ontaining values for the max hull, max shields, max energy, max crew members, max weapon energy, and torpedo effectiveness
        """
        
        torpedo_value = (self.max_torpedos * self.torp_tubes * 
            ALL_TORPEDO_TYPES[self.get_most_powerful_torpedo_type].damage
        ) if self.ship_type_can_fire_torps else 0
        
        try:
            cloaking = self.cloak_strength / self.cloak_cooldown
        except ZeroDivisionError:
            cloaking = 0.0
        
        evasion = self.size / (1.0 + self.evasion)
        
        return (
            self.max_hull * (1 + self.damage_control) * 4, self.max_shields, self.max_energy * 0.25, 
            self.max_crew, self.max_beam_energy, self.max_cannon_energy, torpedo_value, 
            self.detection_strength, cloaking,
            evasion, self.targeting
        )

    @property
    @lru_cache
    def get_added_stragic_values(self):
        
        hull, shields, energy, crew, weapon_energy, cannon_energy, torpedos, detection_strength, cloaking, evasion, targeting = self.get_stragic_values
        
        return hull + shields + energy + crew + weapon_energy + cannon_energy + torpedos + detection_strength

shipdata_pattern = re.compile(r"SHIPCLASS:([A-Z\_]+)\n([^#]+)END_SHIPCLASS")
symbol_pattern = re.compile(r"SYM:([a-zA-Z])\n")
type_pattern = re.compile(r"TYPE:([A-Z_]+)\n")
name_pattern = re.compile(r"NAME:([\w\-\ \'\(\)]+)\n")
shields_pattern = re.compile(r"SHIELDS:([\d]+)\n")
hull_pattern = re.compile(r"HULL:([\d]+)\n")
energy_pattern = re.compile(r"ENERGY:([\d]+)\n")
energy_weapon_pattern = re.compile(r"ENERGY_WEAPON:([A-Z_]+)\n")
crew_pattern = re.compile(r"CREW:([\d]+)\n")
torpedos_pattern = re.compile(r"TORPEDOS:([\d]+)\n")
cloak_strength_pattern = re.compile(r"CLOAK_STRENGTH:([\d.]+)\n")
cloak_cooldown_pattern = re.compile(r"CLOAK_COOLDOWN:([\d]+)\n")
size_pattern = re.compile(r"SIZE:([\d.]+)\n")
targeting_pattern = re.compile(r"TARGETING:([\d.]+)\n")
evasion_pattern = re.compile(r"EVASION:([\d.]+)\n")
detection_strength_pattern = re.compile(r"DETECTION_STRENGTH:([\d.]+)")
damage_control_pattern = re.compile(r"DAMAGE_CONTROL:([\d.]+)\n")
torpedos_tubes_pattern = re.compile(r"TORPEDO_TUBES:([\d]+)\n")
torpedos_types_pattern = re.compile(r"TORPEDO_TYPES:([A-Z\,\_]+)\n")
max_beam_energy_pattern = re.compile(r"MAX_BEAM_ENERGY:([\d]+)\n")
max_beam_targets_pattern = re.compile(r"MAX_BEAM_TARGETS:([\d])\n")
max_cannon_energy_pattern = re.compile(r"MAX_CANNON_ENERGY:([\d]+)\n")
warp_core_breach_damage_pattern = re.compile(r"WARP_CORE_BREACH_DAMAGE:([\d]+)\n")
nation_types_pattern = re.compile(r"NATION:([A-Z\_]+)\n")

def create_ship_classes():
    
    with open("library/ships.txt") as shipclass_text:
        
        contents = shipclass_text.read()
        
    shipclasses = shipdata_pattern.finditer(contents)
    
    shipclass_dict:Dict[str,ShipClass] = {}
        
    for shipclass in shipclasses:
        
        shipclass_code = shipclass.group(1)
        
        shipclass_txt = shipclass.group(2)
        
        #symbol_pattern_match = symbol_pattern.search(shipclass_txt)
        
        type_ = get_first_group_in_pattern(shipclass_txt, type_pattern)

        assert type_ in VALID_SHIP_TYPES
        
        symbol = get_first_group_in_pattern(shipclass_txt, symbol_pattern)
        
        nation = get_first_group_in_pattern(shipclass_txt, nation_types_pattern)
        
        name = get_first_group_in_pattern(shipclass_txt, name_pattern)
                
        shields = get_first_group_in_pattern(
            shipclass_txt, shields_pattern, type_to_convert_to=int
        )
                
        hull = get_first_group_in_pattern(
            shipclass_txt, hull_pattern, type_to_convert_to=int
        )
        
        crew = get_first_group_in_pattern(
            shipclass_txt, crew_pattern, return_aux_if_no_match=True,
            aux_valute_to_return_if_no_match=0, type_to_convert_to=int
        )
        
        energy = get_first_group_in_pattern(
            shipclass_txt, energy_pattern, type_to_convert_to=int
        )
        
        torpedos = get_first_group_in_pattern(
            shipclass_txt, torpedos_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0,
            type_to_convert_to=int
        )
        
        torpedo_tubes = get_first_group_in_pattern(
            shipclass_txt, torpedos_tubes_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0,
            type_to_convert_to=int
        )
        
        torpedo_types_ = get_first_group_in_pattern(shipclass_txt, torpedos_types_pattern, return_aux_if_no_match=True)
        
        torpedo_types = torpedo_types_.split(",") if torpedo_types_ else None
        
        energy_weapon = get_first_group_in_pattern(shipclass_txt, energy_weapon_pattern)
        
        cloak_strength = get_first_group_in_pattern(
            shipclass_txt, cloak_strength_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0.0,
            type_to_convert_to=float
        )
        
        cloak_cooldown = get_first_group_in_pattern(
            shipclass_txt, cloak_cooldown_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=2,
            type_to_convert_to=int
        )
        
        detection_strength = get_first_group_in_pattern(
            shipclass_txt, detection_strength_pattern, type_to_convert_to=float
        )
        
        damage_control = get_first_group_in_pattern(
            shipclass_txt, damage_control_pattern, 
            type_to_convert_to=float
        )
        
        size = get_first_group_in_pattern(shipclass_txt, size_pattern, type_to_convert_to=float)
        
        evasion = get_first_group_in_pattern(
            shipclass_txt, evasion_pattern, type_to_convert_to=float, 
            return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0.0
        )
        
        targeting = get_first_group_in_pattern(shipclass_txt, targeting_pattern, type_to_convert_to=float)
        
        max_beam_energy = get_first_group_in_pattern(
            shipclass_txt, max_beam_energy_pattern, type_to_convert_to=int, 
            return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0
        )
        
        max_beam_targets = get_first_group_in_pattern(
            shipclass_txt, max_beam_targets_pattern, type_to_convert_to=int,
            return_aux_if_no_match=True, aux_valute_to_return_if_no_match=1
        )
        
        max_cannon_energy = get_first_group_in_pattern(
            shipclass_txt, max_cannon_energy_pattern, type_to_convert_to=int,
            return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0
        )
        
        warp_core_breach_damage = get_first_group_in_pattern(
            shipclass_txt, warp_core_breach_damage_pattern, type_to_convert_to=int
        )
        
        shipclass_dict[shipclass_code] = ShipClass.create_ship_class(
            ship_type=type_,
            symbol=symbol,
            name=name,
            max_shields=shields,
            max_hull=hull,
            max_torpedos=torpedos,
            torp_tubes=torpedo_tubes,
            damage_control=damage_control,
            max_beam_energy=max_beam_energy,
            max_beam_targets=max_beam_targets,
            max_cannon_energy=max_cannon_energy,
            max_energy=energy,
            max_crew=crew,
            torp_types=torpedo_types,
            cloak_strength=cloak_strength,
            cloak_cooldown=cloak_cooldown,
            detection_strength=detection_strength,
            size=size,
            targeting=targeting,
            evasion=evasion,
            warp_breach_damage=warp_core_breach_damage,
            nation_code=nation,
            energy_weapon_code=energy_weapon
        )
        
    return shipclass_dict
    
ALL_SHIP_CLASSES = create_ship_classes()
    
class Starship(CanDockWith):
    """
    """

    game_data: GameData

    def __init__(self, 
    ship_class:ShipClass, 
    ai_cls: Type[BaseAi],
    xCo, yCo, 
    secXCo, secYCo,
    *,
    name:Optional[str]=None,
    override_nation_code:Optional[str]=None
    ):
        def set_torps(torpedo_types_:Iterable[str], max_torps:int):
            tDict: Dict[str, int] = {}
            if not torpedo_types_:
                return tDict

            for t in torpedo_types_:
                
                tDict[t] = max_torps if t == torpedo_types_[0] else 0
                
            return tDict

        self.local_coords:MutableCoords = MutableCoords(xCo, yCo)
        self.sector_coords:MutableCoords = MutableCoords(secXCo, secYCo)
        
        self.ship_class:ShipClass = ship_class
        
        self.name = name if name else self.ship_class.create_name()
        
        self.proper_name = (
            f"{self.ship_class.nation.ship_prefix} {self.name}" if self.ship_class.nation.ship_prefix else self.name
        )
        self._shields = ship_class.max_shields
        self.armor = ship_class.max_armor
        self._hull = ship_class.max_hull
        
        self._hull_damage = 0

        self.torps = set_torps(ship_class.torp_types, ship_class.max_torpedos)

        self.able_crew = ship_class.max_crew
        self.injured_crew = 0
        self._energy = ship_class.max_energy

        self.sys_warp_drive = StarshipSystem('Warp Drive:')
        self.sys_torpedos = StarshipSystem('Torp. Tubes:')
        self.sys_impulse = StarshipSystem('Impulse:')
        self.sys_beam_array = StarshipSystem(f'{self.ship_class.get_energy_weapon.short_beam_name_cap}s:')
        self.sys_cannon_weapon = StarshipSystem(f"{self.ship_class.get_energy_weapon.short_cannon_name_cap}s:")
        self.sys_shield_generator = StarshipSystem('Shield:')
        self.sys_sensors = StarshipSystem('Sensors:')
        self.sys_cloak = StarshipSystem("Cloak:")
        self.sys_transporter = StarshipSystem("Transporter:")
        self.sys_warp_core = StarshipSystem('Warp Core:')
        self.override_nation_code = override_nation_code
        
        self.docked = False

        self.turn_taken = False

        self.turn_repairing = 0
        self.cloak_status = CloakStatus.INACTIVE
        self.cloak_cooldown = 0
        
        self.warp_destinations:Optional[Tuple[Coords]] = None
        self.warp_progress:float=0.0
        self.current_warp_factor:int=0

        try:
            self.torpedo_loaded = "NONE" if not self.ship_type_can_fire_torps else self.ship_class.torp_types[0]
        except IndexError:
            self.torpedo_loaded = "NONE"

        self.shields_up = True

        self.ai: Optional[BaseAi] = ai_cls(entity=self)
    
    def get_warp_current_warp_sector(self):
        
        try:
            return self.warp_destinations[floor(self.warp_progress)]
        except IndexError:
            return self.warp_destinations[-1]
    
    @property
    def is_at_warp(self):
        return self.current_warp_factor > 0
    
    def increment_warp_progress(self):
        self.warp_progress += WARP_FACTOR[self.current_warp_factor][0]
    
    @property
    def nation(self):
        return ALL_NATIONS[self.override_nation_code] if self.override_nation_code else self.ship_class.nation
    
    @property
    def shields(self):
        return self._shields

    @shields.setter
    def shields(self, value):
        self._shields = round(value)
        if self._shields < 0:
            self._shields = 0
        elif self._shields > self.get_max_effective_shields:
            self._shields = self.get_max_effective_shields
    
    @property
    def hull_damage(self):
        return self._hull_damage
    
    @hull_damage.setter
    def hull_damage(self, value):
        self._hull_damage = round(value)
        if self._hull_damage < 0:
            self._hull_damage = 0
    
    @property
    def get_max_hull(self):
        return self.ship_class.max_hull - self._hull_damage
    
    @property
    def hull(self):
        return self._hull

    @hull.setter
    def hull(self, value):
        self._hull = round(value)
        if self._hull > self.get_max_hull:
            self._hull = self.get_max_hull

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy = round(value)
        if self._energy < 0:
            self._energy = 0
        elif self._energy > self.ship_class.max_energy:
            self._energy = self.ship_class.max_energy

    @property
    def shields_percentage(self):
        try:
            return self._shields / self.ship_class.max_shields
        except ZeroDivisionError:
            return 0.0

    @property
    def hull_percentage(self):
        try:
            return self.hull / self.ship_class.max_hull
        except ZeroDivisionError:
            return 0.0

    @property
    def get_sub_sector(self) -> SubSector:
        return self.game_data.grid[self.sector_coords.y][self.sector_coords.x]

    @property
    def ship_type_can_fire_torps(self):
        return self.ship_class.ship_type_can_fire_torps

    @property
    def ship_can_fire_torps(self):
        return (
            self.ship_class.ship_type_can_fire_torps and self.sys_torpedos.is_opperational and 
            sum(self.torps.values()) > 0
        )

    @property
    def ship_type_can_fire_beam_arrays(self):
        return self.ship_class.ship_type_can_fire_beam_arrays

    @property
    def ship_can_fire_beam_arrays(self):
        return self.ship_class.ship_type_can_fire_beam_arrays and self.sys_beam_array.is_opperational

    @property
    def ship_type_can_fire_cannons(self):
        return self.ship_class.ship_type_can_fire_cannons

    @property
    def ship_can_fire_cannons(self):
        return self.ship_class.ship_type_can_fire_cannons and self.sys_cannon_weapon.is_opperational

    @property
    def ship_can_transport(self):
        return not self.is_automated and self.sys_transporter.is_opperational

    @property
    def is_automated(self):
        return self.ship_class.is_automated

    @property
    def is_mobile(self):
        return self.ship_class.evasion > 0.0

    @property
    def can_be_docked_with(self):
        return not self.is_mobile and not self.ship_class.is_automated

    def can_dock_with(self, starship: Starship, require_adjacent:bool=True):
        
        return (
            not self.is_mobile and not self.ship_class.is_automated and starship.nation is self.nation and 
            starship.local_coords.is_adjacent(other=self.local_coords)
        ) if require_adjacent else (
            not self.is_mobile and not self.ship_class.is_automated and starship.nation is self.nation
        )
    
    @property
    def get_dock_repair_factor(self):
        
        return self.ship_class.damage_control

    @property
    def can_move_stl(self):
        return self.is_mobile and self.sys_impulse.is_opperational

    @property
    def crew_readyness(self):
        
        return self.caluclate_crew_readyness(
            self.able_crew, self.injured_crew
        )
    
    def scan_crew_readyness(self, precision:int):
        
        return self.caluclate_crew_readyness(
            scan_assistant(self.able_crew, precision), scan_assistant(self.injured_crew, precision)
        )
    
    def caluclate_crew_readyness(self, able_crew:int, injured_crew:int):
        if self.is_automated:
            return 1.0
        total = able_crew + injured_crew * 0.25
        return 0.0 if total == 0.0 else (total / self.ship_class.max_crew) * 0.5 + 0.5
    
    @property
    def ship_type_can_cloak(self):
        return self.ship_class.ship_type_can_cloak

    @property
    def ship_can_cloak(self):
        return self.ship_class.ship_type_can_cloak and self.sys_cloak.is_opperational and self.cloak_cooldown < 1

    @property
    def get_cloak_power(self):
        return self.ship_class.cloak_strength * self.sys_cloak.get_effective_value

    @property
    def get_total_torpedos(self):
        return 0 if not self.ship_type_can_fire_torps else tuple(accumulate(self.torps.values()))[-1]

    @property
    def get_max_shields(self):
        return self.ship_class.max_shields

    @property
    def get_max_effective_shields(self):
        return ceil(self.ship_class.max_shields * self.sys_shield_generator.get_effective_value)

    @property
    def get_max_beam_firepower(self):
        return self.ship_class.max_beam_energy
    
    @property
    def ship_color(self):
        return self.ship_class.nation.nation_color

    @property
    def get_max_effective_beam_firepower(self):
        return ceil(self.ship_class.max_beam_energy * self.sys_beam_array.get_effective_value)

    @property
    def get_max_effective_cannon_firepower(self):
        return ceil(self.ship_class.max_cannon_energy * self.sys_cannon_weapon.get_effective_value)

    @property
    def is_enemy(self):
        return self.game_data.player.nation is not self.nation

    def get_number_of_torpedos(self, precision:int = 1):
        """This generates the number of torpedos that the ship has @ precision - must be an intiger not less then 0 and 
        not more then 100 
        Yields tuples containing the torpedo type and the number of torpedos

        Args:
            precision (int, optional): The precision value. 1 is best, higher values are worse. Defaults to 1.

        Raises:
            TypeError: Raised if precision is a float.
            ValueError: Rasied if precision is lower then 1 or higher then 100

        Yields:
            [type]: [description]
        """
        #scanAssistant = lambda v, p: round(v / p) * p
        if  isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be a intiger inbetween 1 and 100")
        if precision not in {1, 2, 5, 10, 15, 20, 25, 50, 100, 200, 500}:
            raise ValueError(
f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. \
It's actually value is {precision}."
            )

        if self.ship_type_can_fire_torps:
            if precision == 1:
                for t in self.ship_class.torp_types:
                    yield (t, self.torps[t])
            else:
                for t in self.ship_class.torp_types:
                    yield (t, scan_assistant(self.torps[t], precision))
        else:
            yield ("NONE", 0)

    @property
    def get_combat_effectivness(self):
        divisor = 7
        total = (
            self.sys_warp_core.get_effective_value + self.sys_beam_array.get_effective_value + 
            self.sys_shield_generator.get_effective_value + self.sys_sensors.get_effective_value + 
            self.crew_readyness + (self.hull / self.ship_class.max_hull) * 2
        )
        
        if self.ship_type_can_fire_torps:
            total += self.sys_torpedos.get_effective_value
            divisor += 1
        
        return total / divisor

    @property
    def get_stragic_value(self):
        
        hull, shields, energy, crew, beam_energy, cannon_energy, torpedo_value, detection_strength, cloaking, evasion, targeting = self.ship_class.get_stragic_values

        hull_value = hull * self.hull_percentage
        shields_value = shields * self.sys_shield_generator.get_effective_value
        energy_value = energy * self.sys_warp_core.get_effective_value
        crew_value = crew * self.crew_readyness
        beam_energy_value = beam_energy * self.sys_beam_array.get_effective_value if beam_energy else 0
        cannon_energy_value = cannon_energy * self.sys_cannon_weapon.get_effective_value if cannon_energy else 0
        torpedo_value_value = torpedo_value * self.sys_torpedos.get_effective_value if torpedo_value else 0

        return (
            hull_value + shields_value + energy_value + crew_value + 
                beam_energy_value + cannon_energy_value + torpedo_value_value
        )

    @property
    def get_ship_value(self):
        return (self.hull + self.ship_class.max_hull) * 0.5 if self.ship_status.is_active else 0.0

    def calculate_ship_stragic_value(
        self, 
        *, 
        value_multiplier_for_destroyed:float=0.0, 
        value_multiplier_for_derlict:float=0.0, 
        value_multiplier_for_active:float=1.0
    ):
        
        def calculate_value(
            hull:float, shields:float, energy:float, crew:int, 
            weapon_energy:int, cannon_energy:int, torpedo_value:int, multiplier_value:float
        ):
            
            if multiplier_value == 0.0:
                return 0.0
            
            hull_value = hull * self.hull_percentage
            shields_value = shields * self.sys_shield_generator.get_effective_value
            energy_value = energy * self.sys_warp_core.get_effective_value
            crew_value = crew * self.crew_readyness
            weapon_energy_value = weapon_energy * self.sys_beam_array.get_effective_value if weapon_energy else 0
            cannon_energy_value = cannon_energy * self.sys_cannon_weapon.get_effective_value if cannon_energy else 0
            torpedo_value_value = torpedo_value * self.sys_torpedos.get_effective_value if torpedo_value else 0
            transporter_value = self.sys_transporter.get_effective_value
            return (
                hull_value + shields_value + energy_value + crew_value + weapon_energy_value + 
                cannon_energy_value + torpedo_value_value + transporter_value
            ) * multiplier_value
        
        hull, shields, energy, crew, beam_energy, cannon_energy, torpedo_value, detection_strength, cloaking, evasion, targeting = self.ship_class.get_stragic_values
        
        max_possible_value = sum(
            (hull, shields, energy, crew, beam_energy, cannon_energy, torpedo_value, 1), 
            start= 0.0
        )
        
        ship_status = self.ship_status
        
        value_used_in_calculation = (
            value_multiplier_for_destroyed if ship_status.is_destroyed else (
                value_multiplier_for_derlict if ship_status.is_recrewable else value_multiplier_for_active
            )
        )
        
        value_to_be_returned = calculate_value(
            hull, shields, energy, crew, beam_energy, cannon_energy, torpedo_value, value_used_in_calculation
        )
        
        return max_possible_value, value_to_be_returned
        
    @property
    def determin_precision(self):
        """Takes the effective value of the ships sensor system and returns an intiger value based on it. This
        intiger is passed into the scanAssistant function that is used for calculating the precision when 
        scanning another ship. If the sensors are heavly damaged, their effective 'resoultion' drops. Say their 
        effective value is 0.65. This means that this function will return 25. 
        
        Returns:
            int: The effective value that is used for 
        """
        getEffectiveValue = self.sys_sensors.get_effective_value

        if getEffectiveValue >= 1.0:
            return 1
        if getEffectiveValue >= 0.99:
            return 2
        if getEffectiveValue >= 0.95:
            return 5
        if getEffectiveValue >= 0.9:
            return 10
        if getEffectiveValue >= 0.8:
            return 15
        if getEffectiveValue >= 0.7:
            return 20
        if getEffectiveValue >= 0.6:
            return 25
        if getEffectiveValue >= 0.5:
            return 50
        if getEffectiveValue >= 0.4:
            return 100
        
        return 200 if getEffectiveValue >= 0.3 else 500

    #shields, hull, energy, torps, sys_warp_drive, sysImpuls, sysPhaser, sys_shield_generator, sys_sensors, sys_torpedos
    
    def scan_for_print(self, precision: int=1):
        
        if isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be an intiger between 1 amd 100")
        if precision not in {1, 2, 5, 10, 15, 20, 25, 50, 100, 200, 500}:
            raise ValueError(
                f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. It's actually value is {precision}."
            )

        def print_color(amount:float, base:float, inverse:bool=False):
            a = amount / base
            
            if inverse:
                if a <= 0.0:
                    return colors.alert_green
                if a <= 0.25:
                    return colors.lime
                if a <= 0.5:
                    return colors.alert_yellow
                if a <= 0.75:
                    return colors.orange
                return colors.alert_red
            
            if a >= 1.0:
                return colors.alert_green
            if a >= 0.75:
                return colors.lime
            if a >= 0.5:
                return colors.alert_yellow
            if a >= 0.25:
                return colors.orange
            return colors.alert_red

        shields = scan_assistant(self.shields, precision)
        hull = scan_assistant(self.hull, precision)
        energy = scan_assistant(self.energy, precision)
        
        ship_class = self.ship_class
        
        ship_type_can_fire_torps = self.ship_type_can_fire_torps
        
        hull_damage = scan_assistant(self.hull_damage, precision)
        
        d= {
            "shields" : (shields, print_color(shields, ship_class.max_shields)),
            "hull" : (hull, print_color(hull, ship_class.max_hull)),
            "energy" : (energy, print_color(energy, ship_class.max_energy))
        }
        
        if hull_damage:
            d["hull_damage"] = hull_damage, print_color(hull_damage, ship_class.max_hull)
        
        if ship_type_can_fire_torps:
            d["number_of_torps"] = tuple(self.get_number_of_torpedos(precision))
        
        if not self.ship_class.is_automated:
            able_crew = scan_assistant(self.able_crew, precision)
            injured_crew = scan_assistant(self.injured_crew, precision)
            d["able_crew"] = (able_crew, print_color(able_crew, ship_class.max_crew))
            d["injured_crew"] = (injured_crew, print_color(injured_crew, ship_class.max_crew, True))
        
        ship_type_can_cloak = self.ship_type_can_cloak

        if ship_type_can_cloak:
            d["cloak_cooldown"] = (
                self.cloak_cooldown, print_color(self.cloak_cooldown, ship_class.cloak_cooldown, True)
            )

        if self.is_mobile:
            d["sys_warp_drive"] = self.sys_warp_drive.print_info(precision), self.sys_warp_drive.get_color(), self.sys_warp_drive.name
            d["sys_impulse"] = self.sys_impulse.print_info(precision), self.sys_impulse.get_color(), self.sys_impulse.name
        if self.ship_type_can_fire_beam_arrays:
            d["sys_beam_array"] = self.sys_beam_array.print_info(precision), self.sys_beam_array.get_color(), self.sys_beam_array.name
        if self.ship_type_can_fire_cannons:
            d["sys_cannon_weapon"] = self.sys_cannon_weapon.print_info(precision), self.sys_cannon_weapon.get_color(), self.sys_cannon_weapon.name
        d["sys_shield"] = self.sys_shield_generator.print_info(precision), self.sys_shield_generator.get_color(), self.sys_shield_generator.name
        d["sys_sensors"] = self.sys_sensors.print_info(precision), self.sys_sensors.get_color(), self.sys_sensors.name
        if ship_type_can_fire_torps:
            d["sys_torpedos"] = self.sys_torpedos.print_info(precision), self.sys_torpedos.get_color(), self.sys_torpedos.name
        if ship_type_can_cloak:
            d["sys_cloak"] = self.sys_cloak.print_info(precision), self.sys_cloak.get_color(), self.sys_cloak.name
        if not self.is_automated:
            d["sys_transporter"] = self.sys_transporter.print_info(precision), self.sys_transporter.get_color(), self.sys_transporter.name
        d["sys_warp_core"] = self.sys_warp_core.print_info(precision), self.sys_warp_core.get_color(), self.sys_warp_core.name
            
        if ship_type_can_fire_torps:

            torps = tuple(self.get_number_of_torpedos(precision))
            for k, v in torps:
                d[k] = v

        return d
    
    def scan_this_ship(
        self, precision: int=1, *, scan_for_crew:bool=True, scan_for_systems:bool=True, use_effective_values=False
    )->Dict[str,Union[int,Tuple,ShipStatus]]:
        """Scans the ship based on the precision value.

        Args:
            precision (int, optional): Used to see how precise the scan wiil be. lower values are better. Defaults to 1.
            scan_for_crew (bool, optional): If true, dictionary enteries will be return for the able and infured crew. Defaults to True.
            scan_for_systems (bool, optional): If trun, dictionary enteries will be returbed for the systems. Defaults to True.

        Raises:
            TypeError: If precision is a float.
            ValueError: if precision is not in the following

        Returns:
            Dict[str,Union[int,Tuple,ShipStatus]]: A dictionary containing enteries for the ships hull, shield, energy, torpedos, 
        """

        if isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be an intiger between 1 amd 100")
        if precision not in {1, 2, 5, 10, 15, 20, 25, 50, 100, 200, 500}:
            raise ValueError(
                f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. It's actually value is {precision}."
            )

        hull = scan_assistant(self.hull, precision)
        
        status = STATUS_ACTIVE if hull > 0 else (
            STATUS_OBLITERATED if hull < self.ship_class.max_hull * -0.5 else STATUS_HULK
        )

        d= {
            "shields" : scan_assistant(self.shields, precision),
            "hull" : hull,
            "energy" : scan_assistant(self.energy, precision),
            
            "number_of_torps" : tuple(self.get_number_of_torpedos(precision)),
            #"torp_tubes" : s
        }
        
        if scan_for_crew and not self.ship_class.is_automated:
            able_crew = scan_assistant(self.able_crew, precision)
            injured_crew = scan_assistant(self.injured_crew, precision)
            d["able_crew"] = able_crew
            d["injured_crew"] = injured_crew
            
            if status is STATUS_ACTIVE and not self.ship_class.is_automated and able_crew + injured_crew <= 0:
                status = STATUS_DERLICT

        ship_type_can_cloak = self.ship_type_can_cloak

        if ship_type_can_cloak:
            d["cloak_cooldown"] = self.cloak_cooldown

        ship_type_can_fire_torps = self.ship_type_can_fire_torps

        if scan_for_systems:
            
            if self.is_mobile:
                d["sys_warp_drive"] = self.sys_warp_drive.get_info(precision, use_effective_values)# * 0.01,
                d["sys_impulse"] = self.sys_impulse.get_info(precision, use_effective_values)# * 0.01,
            if self.ship_type_can_fire_beam_arrays:
                d["sys_beam_array"] = self.sys_beam_array.get_info(precision, use_effective_values)# * 0.01,
            if self.ship_type_can_fire_cannons:
                d["sys_cannon_weapon"] = self.sys_cannon_weapon.get_info(precision, use_effective_values)
            d["sys_shield"] = self.sys_shield_generator.get_info(precision, use_effective_values)# * 0.01,
            d["sys_sensors"] = self.sys_sensors.get_info(precision, use_effective_values)# * 0.01,
            if ship_type_can_fire_torps:
                d["sys_torpedos"] = self.sys_torpedos.get_info(precision, use_effective_values)# * 0.01
            if ship_type_can_cloak:
                d["sys_cloak"] = self.sys_cloak.get_info(precision, use_effective_values)
            if not self.is_automated:
                d["sys_transporter"] = self.sys_transporter.get_info(precision, use_effective_values)
            d["sys_warp_core"] = self.sys_warp_core.get_info(precision, use_effective_values)
            
        d["status"] = status

        if ship_type_can_fire_torps:

            torps = tuple(self.get_number_of_torpedos(precision))
            for k, v in torps:
                d[k] = v

        return d

    def get_random_ajacent_empty_coord(self):
        
        star_system = self.get_sub_sector
        
        ships = set(ship.local_coords.create_coords() for ship in self.game_data.grab_ships_in_same_sub_sector(self, include_self_in_ships_to_grab=True, accptable_ship_statuses={STATUS_ACTIVE,STATUS_DERLICT,STATUS_HULK}))
        
        a2 = [a_ for a_ in star_system.safe_spots if a_.is_ajacent(self.local_coords) and a_ not in ships]
        
        return choice(a2)

    def destroy(self, cause:str, *, warp_core_breach:bool=False, self_destruct:bool=False):
        """Destroys the ship. I hope this wasn't you!

        Args:
            cause (str): A description of the cause of destruction.
            warp_core_breach (bool, optional): If True, the ship will be totaly destroyed and will damage neabye craft. If False, it will leave behind wreckage. Defaults to False.
            self_destruct (bool, optional): Similar to the above, but more damaging. Defaults to False.
        """
        gd = self.game_data
        #gd.grid[self.sector_coords.y][self.sector_coords.x].removeShipFromSec(self)
        is_controllable = self.is_controllable
        #wc_value = self.sys_warp_core.get_effective_value

        for t in self.ship_class.torp_types:
            self.torps[t] = 0

        if self.is_controllable:
            self.game_data.cause_of_damage = cause

        self.shields = 0
        self.energy = 0
        self.sys_beam_array.integrety = 0.0
        self.sys_cannon_weapon.integrety = 0.0
        self.sys_impulse.integrety = 0.0
        self.sys_sensors.integrety = 0.0
        self.sys_shield_generator.integrety = 0.0
        self.sys_torpedos.integrety = 0.0
        self.sys_warp_core.integrety = 0.0
        self.sys_warp_drive.integrety = 0.0
        self.sys_transporter.integrety = 0.0

        if is_controllable:
            gd.engine.message_log.print_messages = False

        if warp_core_breach or self_destruct:
        
            self.warp_core_breach(self_destruct)
            self.hull = -self.ship_class.max_hull
                
        if self is self.game_data.selected_ship_planet_or_star:
            self.game_data.selected_ship_planet_or_star = None
        
    def warp_core_breach(self, self_destruct=False):

        shipList = self.game_data.grab_ships_in_same_sub_sector(self)

        #damage = self.ship_class.max_hull * ((2 if self_destruct else 1) / 3)

        for s in shipList:
            
            damage = self.warp_core_breach_damage_based_on_distance(s, self_destruct)

            distance = self.local_coords.distance(coords=s.local_coords)
            
            damPercent = 1 - (distance / self.ship_class.warp_breach_damage)

            if damPercent > 0.0 and s.hull < 0:

                s.take_damage(
                    round(damPercent * damage), 
                    f'Caught in the {"auto destruct radius" if self_destruct else "warp core breach"} of the {self.name}', 
                    damage_type=DAMAGE_EXPLOSION
                )

    def warp_core_breach_damage_based_on_distance(self, target:Starship, self_destruct:bool=False):
        
        distance = self.local_coords.distance(coords=target.local_coords)
        
        damage = inverse_square_law(
            base=self.ship_class.warp_breach_damage * ((4/3) if self_destruct else 1), 
            distance=distance
        )
        
        return round(damage)

    def calc_self_destruct_damage(
        self, target:Starship, *, scan:Optional[Dict]=None, number_of_simulations:int=1, 
        simulate_systems:bool=False, simulate_crew:bool=False
        ):
        """Calculates the damage that this ship would inflict on the target if it were auto-destructed.

        Args:
            target (Starship): The ship that is going to be 'attacked'.
            scan (Optional[Dict], optional): A scan of the ship, if not present, one will be generated. Defaults to None.
            number_of_simulations (int, optional): How many times the simulation will be preformed. Defaults to 1.
            simulate_systems (bool, optional): If true, damage to the systems will be taken into account. Defaults to False.
            simulate_crew (bool, optional): If True, crew fatalities and injuries will be taken into account. Defaults to False.

        Returns:
            Tuple[float, float, float, float, float, float]: A tuple containing floats
        """
        
        precision = self.determin_precision
        
        scan = scan if scan else target.scan_this_ship(
            precision, scan_for_crew=simulate_crew, scan_for_systems=simulate_systems
        )
        
        amount = self.warp_core_breach_damage_based_on_distance(target)
        
        averaged_shield = 0
        averaged_hull = 0
        averaged_shield_damage = 0
        averaged_hull_damage = 0
        averaged_crew_readyness = 0
        
        #crew_readyness = self.crew_readyness
        
        scan_target_crew = not target.ship_class.is_automated and simulate_crew
                
        #target_crew_readyness = target.scan_crew_readyness(precision) if scan_target_crew else 1.0
        
        for i in range(number_of_simulations):
        
            new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage = self.calculate_damage(
                amount, scan_dict=scan, precision=precision, calculate_crew=simulate_crew, 
                calculate_systems=simulate_systems, damage_type=DAMAGE_EXPLOSION
            )
            
            averaged_shield += new_shields
            averaged_hull += new_hull
            averaged_shield_damage += shields_dam
            averaged_hull_damage += hull_dam
            
            if scan_target_crew:
                
                averaged_crew_readyness += target.caluclate_crew_readyness(
                    scan["able_crew"], scan["injured_crew"]
                )
                
        averaged_shield /= number_of_simulations
        averaged_hull /= number_of_simulations
        averaged_shield_damage /= number_of_simulations
        averaged_hull_damage /= number_of_simulations
        
        if scan_target_crew:
            averaged_crew_readyness /= number_of_simulations
        else:
            averaged_crew_readyness = 1.0
                
        return averaged_shield, averaged_hull, averaged_shield_damage, averaged_hull_damage, averaged_hull <= 0, averaged_crew_readyness

    @property
    def ship_status(self):
        """Checks if the ship is relitivly intact. 
        
        If a ship is destroyed but intact ship, then it is a ruined hulk, like the ones we saw in aftermath of the battle of Wolf 389. 

        Checks is the ship has no living crew, and returns True if it does not, False if it does.

        Returns:
            bool: Returns True if the hull is greater then or equal to half the negitive max hit points, and less then or equal to zero.
        """
        if self.is_at_warp:
            return STATUS_AT_WARP
        if self.hull < self.ship_class.max_hull * -0.5:
            return STATUS_OBLITERATED
        if self.hull <= 0:
            return STATUS_HULK
        if not self.ship_class.is_automated and self.able_crew + self.injured_crew < 1:
            return STATUS_DERLICT
        if self.ship_can_cloak and self.cloak_status != CloakStatus.INACTIVE:
            return STATUS_CLOAKED if self.cloak_status == CloakStatus.ACTIVE else STATUS_CLOAK_COMPRIMISED
        return STATUS_ACTIVE
            
    def ram(self, other_ship:Starship, intentional_ram_attempt:bool):
        """Prepare for RAMMING speed!

        The ship will attempt to ram another ship.

        Args:
            other_ship (Starship): The ship that the attacker will atempt to ram.
            intentional_ram_attempt (bool): If True,
        """
        self_status = self.ship_status
        other_status = other_ship.ship_status
        
        self_hp = (self.shields if self_status.do_shields_work else 0) + self.hull
        other_hp = (other_ship.shields if other_status.do_shields_work else 0) + other_ship.hull
        
        self_damage = self_hp + self.ship_class.max_hull * 0.5
        #other_damage = other_hp + other_ship.ship_class.max_hull * 0.5

        hit_roll = self.roll_to_hit(
            other_ship, 
            systems_used_for_accuray=[self.sys_impulse.get_effective_value, self.ship_class.evasion],
            damage_type=DAMAGE_RAMMING,
            crew_readyness=self.crew_readyness,
            target_crew_readyness=other_ship.crew_readyness
        )
        if hit_roll:

            self.take_damage(
                other_hp, f'Rammed the {self.name}', damage_type=DAMAGE_EXPLOSION
            )
            other_ship.take_damage(
                self_damage, f'Rammed by the {self.name}', damage_type=DAMAGE_EXPLOSION
            )
        if intentional_ram_attempt and (
            not hit_roll or (
                self.ship_status is not STATUS_OBLITERATED and other_ship.ship_status is not STATUS_OBLITERATED
            )
        ):
            ships_in_same_sector = self.game_data.grab_ships_in_same_sub_sector(
                other_ship, accptable_ship_statuses={
                    STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
                }
            )
            bad_spots = [
                ship.local_coords.create_coords() for ship in ships_in_same_sector if 
                other_ship.local_coords.is_adjacent(other=ship.local_coords)
            ]
            safe_spots = [
                spot for spot in self.get_sub_sector.safe_spots if other_ship.local_coords.is_adjacent(other=spot) and
                spot not in bad_spots
            ]
            spot = choice(safe_spots)
            
            self.local_coords.x = spot.x
            self.local_coords.y = spot.y

        return hit_roll

    def calculate_damage(
        self, amount:int, *, 
        scan_dict:Optional[Dict]=None, 
        precision:int=1, 
        calculate_crew:bool=True, 
        calculate_systems:bool=True,  
        damage_type:DamageType,
        use_effective_values:bool=True
    ):
        #assume damage is 64, current shields are 80, max shields are 200
        #armor is 75, max armor is 100
        #80 * 2 / 200 = 160 / 200 = 0.8
        #0.8 * 64 = 51.2 = the amount of damage that hits the shields
        #64 - 51.2 = 12.8 = the amount of damage that hits the armor and hull
        #1 - (75 / 100) = 1 - 0.25 = 0.75
        #12.8 * 0.75 = 9.6 = the amount of damage that hits the armor
        #12.8 - 9.6 = 3.2 = the amount of damage that hits the hull
        
        random_varation = damage_type.damage_variation
        
        if random_varation > 0.0:
            amount = round(amount * uniform(1.0 - random_varation, 1.0))
        
        old_scan = scan_dict if scan_dict else self.scan_this_ship(
            precision, scan_for_crew=calculate_crew, 
            scan_for_systems=calculate_systems, 
            use_effective_values=use_effective_values
        )
        
        current_shields:int = old_scan["shields"]
        
        current_hull:int = old_scan["hull"]
        
        #old_hull_as_a_percent = current_hull / self.ship_class.max_hull
        
        old_status = self.ship_status
        
        is_hulk = current_hull < 0
        
        try:
            is_derlict = old_scan["able_crew"] + old_scan["injured_crew"] <= 0
        except KeyError:
            is_derlict = False
        
        try:
            shield_effectiveness = 0 if old_scan["sys_shield"] < 0.15 else min(old_scan["sys_shield"] * 1.25, 1.0)
        except KeyError:
            shield_effectiveness = 1
        
        shields_are_already_down = shield_effectiveness <= 0 or current_shields <= 0 or not old_status.do_shields_work or not self.shields_up
        
        shields_dam = 0
        armorDam = amount
        hull_dam = amount
        
        shield_dam_multi = damage_type.damage_vs_shields_multiplier

        armorHullDamMulti = (
            damage_type.damage_vs_no_shield_multiplier 
            if shields_are_already_down else damage_type.damage_vs_hull_multiplier
        ) 
        
        shields_percentage = current_shields / self.ship_class.max_shields
        
        #shieldPercent = self.shields_percentage * 0.5 + 0.5
        
        bleedthru_factor = min(shields_percentage + 0.5, 1.0)
        
        if shields_are_already_down:
            
            hull_dam = amount * armorHullDamMulti
        else:
            to_add = 0
            shields_dam = amount * bleedthru_factor * shield_dam_multi
            if shields_dam > current_shields:
                to_add = shields_dam - current_shields
                
                shields_dam = current_shields
            amount *= (1 - bleedthru_factor)
            amount += to_add
            hull_dam = amount * armorHullDamMulti
        
        new_shields = scan_assistant(current_shields - shields_dam, precision) if shields_dam > 0 else current_shields
        new_hull = scan_assistant(current_hull - hull_dam, precision) if hull_dam > 0 else current_hull
        
        hull_damage_as_a_percent = hull_dam / self.ship_class.max_hull
        new_shields_as_a_percent = new_shields / self.ship_class.max_shields
        new_hull_as_a_percent = new_hull / self.ship_class.max_hull
        
        killed_outright = 0
        killed_in_sickbay = 0
        wounded = 0
        
        if calculate_crew and not is_derlict and not is_hulk:
            
            crew_killed = hull_dam > 0 and new_hull_as_a_percent < random() and not self.ship_class.is_automated
            
            if crew_killed:
                able_crew = old_scan["able_crew"]
                injured_crew = old_scan["injured_crew"]
                
                percentage_of_crew_killed = hull_damage_as_a_percent * random()
                
                total_crew = able_crew + injured_crew
                
                wounded_fac = uniform(0.25, 0.75)
                
                _able_crew_percentage = able_crew / total_crew
                
                percentage_of_able_crew_killed = _able_crew_percentage * (percentage_of_crew_killed * (1 - wounded_fac))
                percentage_of_able_crew_wounded = _able_crew_percentage * (percentage_of_crew_killed * (wounded_fac))
                percentage_of_injured_crew_killed = (injured_crew / total_crew) * percentage_of_crew_killed
                
                killed_outright = round(self.able_crew * percentage_of_able_crew_killed)
                killed_in_sickbay = round(0.5 * self.able_crew * percentage_of_injured_crew_killed)
                wounded = round(self.able_crew * percentage_of_able_crew_wounded)
        
        shield_sys_damage = 0
        energy_weapons_sys_damage = 0
        cannon_sys_damage = 0
        impulse_sys_damage = 0
        warp_drive_sys_damage = 0
        sensors_sys_damage = 0
        torpedo_sys_damage = 0
        warp_core_sys_damage = 0
        cloak_sys_damage = 0
        transporter_sys_damage = 0
        
        if calculate_systems and not is_hulk:
            chance_to_damage_system = damage_type.chance_to_damage_system
            
            systems_damaged = hull_dam > 0 and new_hull_as_a_percent < uniform(
                hull_damage_as_a_percent, 1.25 + hull_damage_as_a_percent)
            
            if systems_damaged:
                system_damage_chance = damage_type.damage_chance_vs_systems_multiplier
                
                def chance_of_system_damage():
                    # this is cumbersome. A better way may be random() * chance_to_damage_system > (old_hull_as_a_percent + new_hull_as_a_percent) * 0.5
                    return uniform(
                        hull_damage_as_a_percent, chance_to_damage_system + hull_damage_as_a_percent
                        ) > new_hull_as_a_percent
                
                def random_system_damage():
                    return uniform(0.0, system_damage_chance * hull_damage_as_a_percent)
                
                if chance_of_system_damage():
                    shield_sys_damage = random_system_damage()
                    
                if self.ship_type_can_fire_beam_arrays and chance_of_system_damage():
                    energy_weapons_sys_damage = random_system_damage()
                    
                if self.ship_type_can_fire_cannons and chance_of_system_damage():
                    cannon_sys_damage = random_system_damage()
                    
                if chance_of_system_damage():
                    impulse_sys_damage = random_system_damage()
                    
                if chance_of_system_damage():
                    warp_drive_sys_damage = random_system_damage()
                    
                if chance_of_system_damage():
                    sensors_sys_damage = random_system_damage()
                    
                if self.ship_type_can_fire_torps and chance_of_system_damage():
                    torpedo_sys_damage = random_system_damage()
                    
                if chance_of_system_damage():
                    warp_core_sys_damage = random_system_damage()
                    
                if self.ship_type_can_cloak and chance_of_system_damage():
                    cloak_sys_damage = random_system_damage()
                
                if chance_of_system_damage():
                    transporter_sys_damage = random_system_damage()
                        
        return (
            new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, 
            new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, 
            impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, 
            warp_core_sys_damage, 
            energy_weapons_sys_damage, cannon_sys_damage, 
            torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage
        )

    def take_damage(self, amount, text, *, damage_type:DamageType):
        #is_controllable = self.isControllable
        gd = self.game_data
        message_log = gd.engine.message_log
        
        old_ship_status = self.ship_status
        
        ship_originaly_destroyed = old_ship_status in {STATUS_HULK, STATUS_OBLITERATED}
        
        new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage = self.calculate_damage(amount, damage_type=damage_type)
        
        ship_destroyed = new_hull < 0
        
        ship_is_player = self is self.game_data.player

        pre = 1 if ship_is_player else self.game_data.player.determin_precision
        
        old_scan = self.scan_this_ship(
            pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player, use_effective_values=True
        )
        
        perm_hull_damage = round(hull_dam * 0.15)
        
        self.shields = new_shields
        self.hull = new_hull
        
        self.hull_damage += perm_hull_damage
        
        if not self.ship_class.is_automated:
            self.able_crew -= wounded
            self.injured_crew += wounded
            self.able_crew -= killed_outright
            self.injured_crew -= killed_in_sickbay
        
        self.sys_shield_generator.integrety -= shield_sys_damage
        self.sys_beam_array.integrety -= energy_weapons_sys_damage
        self.sys_cannon_weapon.integrety -= cannon_sys_damage
        self.sys_impulse.integrety -= impulse_sys_damage
        self.sys_sensors.integrety -= sensors_sys_damage
        self.sys_warp_drive.integrety -= warp_drive_sys_damage
        self.sys_torpedos.integrety -= torpedo_sys_damage
        self.sys_transporter.integrety -= transporter_sys_damage
        
        new_ship_status = self.ship_status
        
        new_scan = self.scan_this_ship(pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player)
        
        #name = "our" if ship_is_player else f"the {self.name}'s"
        
        #name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
        #name_second_occ = "our" if ship_is_player else f"the {self.name}'s"
                
        if self.turn_repairing > 0:
            self.turn_repairing -= 1
        
        if not ship_destroyed:
            
            old_shields = old_scan["shields"] if old_ship_status.do_shields_work else 0
            
            newer_shields = new_scan['shields'] if new_ship_status.do_shields_work else 0
            
            old_hull = old_scan["hull"]
            
            newer_hull = new_scan["hull"]
            
            scaned_shields_percentage = newer_shields / self.ship_class.max_shields
            
            shield_status = "holding" if scaned_shields_percentage > 0.9 else (
                f"at {scaned_shields_percentage:.0%}" if self.shields > 0 else "down")
            
            shields_are_down = newer_shields == 0
            
            #shields_just_got_knocked_down = old_shields > 0 and shields_are_down
            
            shields_are_already_down = old_shields == 0 and shields_are_down
            
            old_hull_percent = old_hull / self.ship_class.max_hull
            newer_hull_hull_percent = newer_hull / self.ship_class.max_hull
            
            if old_hull_percent < newer_hull_hull_percent:
                
                #this is where things get a bit complecated. Rather then use a serise of nested if-elif-else statements to decide what the message to preing regarding the hull status is, I'm going to compress this into a grid. The variable 'old_hull_status' acts as the 'y' value, and the variable 'newer_hull_status' acts as the 'x' value
                
                if old_hull_percent <= 0.1:
                    old_hull_status = 3
                elif old_hull_percent <= 0.25:
                    old_hull_status = 2
                elif old_hull_percent <= 0.5:
                    old_hull_status = 1
                else:
                    old_hull_status = 0
                
                if newer_hull_hull_percent <= 0.1:
                    newer_hull_status = 3
                elif newer_hull_hull_percent <= 0.25:
                    newer_hull_status = 2
                elif newer_hull_hull_percent <= 0.5:
                    newer_hull_status = 1
                else:
                    newer_hull_status = 0 
                
                grid = (
                    (0,1,2,3),
                    (0,0,2,3),
                    (0,0,0,3),
                    (0,0,0,0)
                )
                
                hull_breach_message_code = grid[old_hull_status][newer_hull_status]
                
                hull_breach_messages = (
                    f"structural integrity is at {newer_hull_hull_percent:.0%}.",
                    f"a hull breach.",
                    f"hull breaches on multiple decks!"
                    f"hull is buckling!"
                )
                
                hull_breach_message = hull_breach_messages[hull_breach_message_code]
                
                message_to_print = []
                
                if not shields_are_already_down:
                    
                    name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
                    
                    message_to_print.append(
                        
                        f"{name_first_occ} shields are {shield_status}, and"
                    )
                    
                    if hull_breach_message_code in {1,2}:
                        
                        message_to_print.append(
                            'we have' if ship_is_player else 'they have'
                        )
                    else:
                        message_to_print.append(
                            'our' if ship_is_player else 'their'
                        )
                    
                    message_to_print.append(
                        hull_breach_message
                    )
                else:
                    
                    if hull_breach_message_code in {1,2}:
                        
                        message_to_print.append(
                            'We have' if ship_is_player else f'The {self.name} has'
                        )
                    else:
                        message_to_print.append(
                            'Our' if ship_is_player else f"The {self.name}'s"
                        )
                    
                    message_to_print.append(
                        hull_breach_message
                    )
                
                fg = colors.white if not ship_is_player else (
                    colors.red if new_hull_as_a_percent < 0.1 else (
                        colors.orange if new_hull_as_a_percent < 0.25 else (
                            colors.yellow if new_hull_as_a_percent < 0.5 else colors.white
                        )
                    )
                )
                
                message_log.add_message(" ".join(message_to_print),fg)
                
            else:
                name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
                message_log.add_message(f"{name_first_occ} shields are {shield_status}." )
            
            if old_ship_status.is_active and new_ship_status.is_recrewable and not ship_is_player:
                
                message_log.add_message("Captain, I am not reading any life signs.")
            
            if ship_is_player:
                
                if not self.ship_class.is_automated:
                    if killed_outright > 0:
                        message_log.add_message(f'{killed_outright} active duty crewmembers were killed.')
                        
                    if killed_in_sickbay > 0:
                        message_log.add_message(f'{killed_in_sickbay} crewmembers in sickbay were killed.')
                    
                if wounded > 0:
                    message_log.add_message(f'{wounded} crewmembers were injured.')
                
                if impulse_sys_damage > 0:
                    message_log.add_message('Impulse engines damaged.')
                    
                if warp_drive_sys_damage > 0:
                    message_log.add_message('Warp drive damaged.')
                    
                if energy_weapons_sys_damage > 0:
                    message_log.add_message(f'{self.ship_class.get_energy_weapon.beam_name} emitters damaged.')
                    
                if cannon_sys_damage > 0:
                    message_log.add_message(f'{self.ship_class.get_energy_weapon.cannon_name} damaged.')
                    
                if sensors_sys_damage > 0:
                    message_log.add_message('Sensors damaged.')
                            
                if shield_sys_damage > 0:
                    message_log.add_message('Shield generator damaged.')
                
                if warp_core_sys_damage > 0:
                    message_log.add_message('Warp core damaged.')
                            
                if self.ship_type_can_fire_torps and torpedo_sys_damage > 0:
                    message_log.add_message('Torpedo launcher damaged.')
                
                if self.ship_class.ship_type_can_cloak and cloak_sys_damage > 0:
                    message_log.add_message("Cloaking device damaged.")
                
        elif not ship_originaly_destroyed:
            wc_breach = ((not old_ship_status.is_destroyed and new_ship_status is STATUS_OBLITERATED) or (
                    random() > 0.85 and random() > self.sys_warp_core.get_effective_value and 
                    random() > self.sys_warp_core.integrety) or self.sys_warp_core.integrety == 0.0)
            
            if ship_is_player:
                
                if wc_breach:
                    message_log.add_message("Warp core breach iminate!", colors.orange)
                
                message_log.add_message("Abandon ship, abandon ship, all hands abandon ship...", colors.red)
                
                
            else:
                message_log.add_message(
                    f"The {self.name} {'suffers a warp core breach' if wc_breach else 'is destroyed'}!"
                )
                
            self.destroy(text, warp_core_breach=wc_breach)
        elif old_ship_status == STATUS_HULK and not ship_is_player:
            
            message_log.add_message(
                f"The remains of the {self.proper_name} disintrate under the onslaght!" if 
                new_ship_status == STATUS_OBLITERATED else 
                f"Peices of the {self.proper_name} break off."
            )
        
    def repair(self):
        """This method handles repairing the ship after each turn. Here's how it works:
        
        If the ship is not being fired on, manuivering, or firing topredos, then some rudimentory repairs are going to be done. Also, the ships batteries will be slowly be refilled by the warp core.
        
        However, if the ship focuses its crews attention soley on fixing the ship (by using the RepairOrder order), then the repairs are going to be much more effective. For each consuctive turn the ship's crew spends on fixing things up, a small but clumitive bonus is applied. The ships batteries will also recharge much more quickly.
        
        If the ship is docked/landed at a friendly planet, then the ship will benifit even more from the expertise of the local eneriners.
        """        
        #self.crew_readyness
        repair_factor:RepairStatus = REPAIR_DOCKED if self.docked else (
            REPAIR_DEDICATED if self.turn_repairing else REPAIR_PER_TURN
        )
        time_bonus = 1.0 + (self.turn_repairing / 25.0)
        energy_regeneration_bonus = 1.0 + (self.turn_repairing / 5.0)

        repair_amount = self.ship_class.damage_control * self.crew_readyness * time_bonus

        hull_repair_factor = repair_amount * repair_factor.hull_repair
        
        system_repair_factor = repair_amount * repair_factor.system_repair
        
        status = self.ship_status

        self.energy+= (
            repair_factor.energy_regeration * self.sys_warp_core.get_effective_value * energy_regeneration_bonus
        ) - ((REPAIR_PER_TURN.energy_regeration * 0.5) if status.energy_drain else 0)

        if not self.ship_class.is_automated:
            heal_crew = min(self.injured_crew, ceil(self.injured_crew * 0.2) + randint(2, 5))
            self.able_crew+= heal_crew
            self.injured_crew-= heal_crew
        
        repair_amount = hull_repair_factor * uniform(0.5, 1.25) * self.ship_class.max_hull
        
        perm_hull_repair = ceil(repair_amount * repair_factor.repair_permanent_hull_damage)

        self.hull_damage -= perm_hull_repair
        self.hull += repair_amount
        self.sys_sensors.integrety += system_repair_factor * (0.5 + random() * 0.5)
        if self.is_mobile:
            self.sys_warp_drive.integrety += system_repair_factor * (0.5 + random() * 0.5)
            self.sys_impulse.integrety += system_repair_factor * (0.5 + random() * 0.5)
        if self.ship_type_can_fire_beam_arrays:
            self.sys_beam_array.integrety += (0.5 + random() * 0.5)
        if self.ship_type_can_fire_cannons:
            self.sys_cannon_weapon.integrety += (0.5 + random() * 0.5)
        self.sys_shield_generator.integrety += system_repair_factor * (0.5 + random() * 0.5)
        self.sys_warp_core.integrety += system_repair_factor * (0.5 + random() * 0.5)
        if not self.is_automated:
            self.sys_transporter.integrety += system_repair_factor * (0.5 + random() * 0.5)
        if self.ship_type_can_fire_torps:
            self.sys_torpedos.integrety += system_repair_factor * (0.5 + random() * 0.5)
    
    def roll_to_hit(
        self, enemy:Starship, *, 
        systems_used_for_accuray:Iterable[float], precision:int=1, 
        estimated_enemy_impulse:Optional[float]=None, damage_type:DamageType, crew_readyness:float, target_crew_readyness:float
    ):
        """A method that preforms a number of calcuations to see if an attack roll succeded or not.

        Args:
            enemy (Starship): The target that the attacker will be rolling against.
            systems_used_for_accuray (Iterable[float]): An iterable of floats. Often, these will be the effective value of the sensors system, and another system such as cannons, torpedos, or beam arrays.
            damage_type (DamageType): The type of damage. This must be onw of the DamageType constants.
            crew_readyness (float): The readyness of the crew of the attacking ship.
            target_crew_readyness (float): The readyness of the crew of the defending ship.
            precision (int, optional): The precision that is used to determin the enemy impulse (see below). Defaults to 1.
            estimated_enemy_impulse (Optional[float], optional): This value is used to determin the defenders chance of evading the attack. If not present, then it will be estimated using the precision argument. Defaults to None.

        Returns:
            bool: Returns True if the attack hit the target ship, False if it missed.
        """
        assert damage_type is not DAMAGE_EXPLOSION
        
        enemy_ship_status = enemy.ship_status
        
        if not enemy_ship_status.is_active:
            
            estimated_enemy_impulse = 0.0
        
        elif estimated_enemy_impulse is None:
            
            estimated_enemy_impulse = enemy.sys_impulse.get_info(
                precision, True
            ) * enemy.ship_class.evasion * target_crew_readyness
        else:
            estimated_enemy_impulse *= enemy.ship_class.evasion * target_crew_readyness
        
        # ramming an imobile object always works!
        if damage_type.autohit_if_target_cant_move and estimated_enemy_impulse == 0.0:
            return True
        
        enemy_size = enemy.ship_class.size
        
        distance_penalty = (
            damage_type.accuracy_loss_per_distance_unit * self.local_coords.distance(coords=enemy.local_coords)
        ) if damage_type.accuracy_loss_per_distance_unit > 0 else 0.0
                
        distance_penalty += damage_type.flat_accuracy_loss
        
        distance_penalty /= enemy_size
        
        deffence_value = (estimated_enemy_impulse + distance_penalty) * (1 if enemy_ship_status.is_visible else 8)
        
        targeting = (sum(systems_used_for_accuray) / len(systems_used_for_accuray)) * self.ship_class.targeting
        
        attack_value = crew_readyness * targeting * (1 if enemy_ship_status.is_visible else 0.125)
        
        return attack_value + random() > deffence_value
    
    def attack_energy_weapon(self, enemy:Starship, amount:float, energy_cost:float,  damage_type:DamageType):
        
        assert damage_type in {DAMAGE_BEAM, DAMAGE_CANNON}
        
        assert self.sys_beam_array.is_opperational
        
        gd = self.game_data
                
        attacker_is_player = self is self.game_data.player
        target_is_player = not attacker_is_player and enemy is self.game_data.player

        self.energy-=energy_cost
                        
        gd.engine.message_log.add_message(
            f"Firing on the {enemy.name}!" 
            if attacker_is_player else 
            f"The {self.name} has fired on {'us' if target_is_player else f'the {enemy.name}'}!"
        )
        if self.roll_to_hit(
            enemy, 
            estimated_enemy_impulse=-1.0, 
            systems_used_for_accuray=(
                self.sys_beam_array.get_effective_value,
                self.sys_sensors.get_effective_value
            ),
            damage_type=damage_type,
            crew_readyness=self.crew_readyness,# * 0.5 + 0.5
            target_crew_readyness=enemy.crew_readyness
        ):
            
            target_name = "We're" if target_is_player else f'The {enemy.name} is'

            gd.engine.message_log.add_message(
                f"Direct hit on {enemy.name}!" if attacker_is_player else
                f"{target_name} hit!", fg=colors.orange
            )

            enemy.take_damage(
                amount * self.sys_beam_array.get_effective_value, 
                f'Destroyed by a {self.ship_class.get_energy_weapon.beam_name} hit from the {self.name}.', 
                damage_type=damage_type
            )
            return True
        else:
            gd.engine.message_log.add_message("We missed!" if attacker_is_player else "A miss!")

        return False

    def attack_torpedo(self, gd:GameData, enemy:Starship, torp:Torpedo):
        
        assert self.sys_torpedos.is_opperational
        
        gd = self.game_data
        
        if self.roll_to_hit(
            enemy, 
            systems_used_for_accuray=(
                self.sys_sensors.get_effective_value,
                self.sys_torpedos.get_effective_value
            ),
            damage_type=DAMAGE_TORPEDO,
            crew_readyness = self.crew_readyness,# * 0.5 + 0.5
            target_crew_readyness=enemy.crew_readyness
        ):
            #chance to hit:
            #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
            gd.engine.message_log.add_message(f'{enemy.name} was hit by a {torp.name} torpedo from {self.name}.')

            enemy.take_damage(
                torp.damage, f'Destroyed by a {torp.name} torpedo hit from the {self.name}', 
                damage_type=DAMAGE_TORPEDO
            )

            return True
        gd.engine.message_log.add_message(f'A {torp.name} torpedo from {self.name} missed {enemy.name}.')
        return False
    
    def get_no_of_avalible_torp_tubes(self, number=0):
        if not self.sys_torpedos.is_opperational:
            return 0

        if number == 0:
            number = self.ship_class.torp_tubes
        else:
            number = min(number, self.ship_class.torp_tubes)

        return max(1, round(number * self.sys_torpedos.get_effective_value))
    
    @property
    def is_controllable(self):
        return self is self.game_data.player
    
    @property
    def get_most_powerful_torp_avaliable(self):
        rt = self.ship_class.get_most_powerful_torpedo_type

        if rt == "NONE":
            return rt
        
        if self.get_total_torpedos > 0:
            if self.torps[rt] > 0:
                return rt

            avaliable_torps = [t for t, tyt in self.torps.items() if tyt]
            
            most_powerful = find_most_powerful_torpedo(avaliable_torps)

            return most_powerful

        return "NONE"
    
    def restock_torps(self, infrastructure:float):
        if self.ship_class.max_torpedos != self.get_total_torpedos:
            torpSpace = self.ship_class.max_torpedos - self.get_total_torpedos
            for t in self.ship_class.torp_types:
                if ALL_TORPEDO_TYPES[t].infrastructure <= infrastructure:
                    self.torps[t]+= torpSpace
                    return True
        return False
    
    def simulate_torpedo_hit(
        self, target:Starship, number_of_simulations:int, *, simulate_systems:bool=False, simulate_crew:bool=False
    ):
        precision = self.determin_precision
        
        target_scan = target.scan_this_ship(precision, scan_for_crew=simulate_crew)
        
        #shields, hull, energy, torps, sys_warp_drive, sysImpuls, sysPhaser, sys_shield_generator, sys_sensors, sys_torpedos
        
        targ_shield = target_scan["shields"]
        targ_hull = target_scan["hull"]
        
        torp = self.get_most_powerful_torp_avaliable
        
        if torp == None:
            return targ_shield, targ_hull
        
        torpedos = self.torps[torp]
        
        damage = ALL_TORPEDO_TYPES[torp].damage

        times_to_fire = min(self.get_no_of_avalible_torp_tubes(), torpedos)

        total_shield_dam = 0
        total_hull_dam = 0
        
        averaged_hull = 0
        averaged_shields = 0
        averaged_crew_readyness = 0
        
        number_of_ship_kills = 0
        
        number_of_crew_kills = 0
        
        crew_readyness = self.crew_readyness
        
        scan_target_crew = not target.ship_class.is_automated and simulate_crew
                
        target_crew_readyness = target.scan_crew_readyness(precision) if scan_target_crew else 1.0

        for s in range(number_of_simulations):
            
            new_hull = target_scan["hull"]
            
            for attack in range(times_to_fire):
                hull_dam  = 0
                shield_dam = 0
                if self.roll_to_hit(
                    target, 
                    estimated_enemy_impulse=min(
                        1.0, min(target_scan["sys_impulse"] * 1.25, 1.0)
                    ), 
                    systems_used_for_accuray=(
                        self.sys_sensors.get_effective_value,
                        self.sys_torpedos.get_effective_value
                    ),
                    damage_type=DAMAGE_TORPEDO,
                    crew_readyness=crew_readyness,
                    target_crew_readyness=target_crew_readyness
                ):
                    new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage =self.calculate_damage(
                        damage, precision=precision, calculate_crew=simulate_crew, 
                        calculate_systems=simulate_systems, scan_dict=target_scan, damage_type=DAMAGE_TORPEDO
                    )
                    target_scan["shields"] = new_shields
                    target_scan["hull"] = new_hull
                    
                    shield_dam += shields_dam
                    hull_dam += hull_dam
                    
                    if simulate_systems:
                        
                        target_scan["sys_impulse"] -= impulse_sys_damage
                        target_scan["sys_shield"] -= shield_sys_damage
                        target_scan["sys_warp_drive"] -= warp_drive_sys_damage
                        target_scan["sys_warp_core"] -= warp_core_sys_damage
                        
                    if scan_target_crew:
                        
                        target_scan["able_crew"] -= wounded + killed_outright
                        target_scan["injured_crew"] += wounded - killed_in_sickbay
                        
                        target_crew_readyness = target.caluclate_crew_readyness(
                            target_scan["able_crew"], target_scan["injured_crew"]
                        )
            
            total_shield_dam += shield_dam
            total_hull_dam += hull_dam
            
            if new_hull <= 0:
                number_of_ship_kills +=1
            
            averaged_hull += target_scan["hull"]
            averaged_shields += target_scan["shields"]
            
            if scan_target_crew:
                _crew_readyness = target.caluclate_crew_readyness(
                    target_scan["able_crew"], target_scan["injured_crew"]
                )
                
                if _crew_readyness == 0.0:
                    number_of_crew_kills += 1
                
            target_crew_readyness = target.scan_crew_readyness(precision) if scan_target_crew else 1.0
            
            target_scan = target.scan_this_ship(precision, scan_for_crew=simulate_crew)
        
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        total_shield_dam /= number_of_simulations
        total_hull_dam /= number_of_simulations
        
        if scan_target_crew:
            averaged_crew_readyness /= number_of_simulations
        else:
            averaged_crew_readyness = 1.0
        
        return averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, number_of_ship_kills / number_of_simulations, number_of_crew_kills / number_of_simulations, averaged_crew_readyness

    def simulate_energy_hit(
        self, target:Starship, number_of_simulations:int, energy:float, cannon:bool=False, 
        *, simulate_systems:bool=False, simulate_crew:bool=False
    ):
        """Run a number of simulations of energy weapon hits against the target ship and returns the avaraged result.

        Args:
            target (Starship): The target ship.
            number_of_simulations (int): How many simulations will be run. High is mroe accurate.
            energy (float): The amound of energy used in the attack.
            cannon (bool, optional): If true, it will simulat a cannon attack. Defaults to False.
            simulate_systems (bool, optional): If true, systems damage will be taken into account. Defaults to False.
            simulate_crew (bool, optional): If true, crew deaths and injuries will be taken into account. Defaults to False.

        Returns:
            tuple[float, float, float, float, float, float, float]: A tuple containing float values for the following: averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_number_of_ship_kills, averaged_number_of_crew_kills, averaged_crew_readyness
        """
        precision = self.determin_precision

        targScan = target.scan_this_ship(
            precision, scan_for_systems=simulate_systems, scan_for_crew=simulate_crew, use_effective_values=True
        )
        
        targ_shield = targScan["shields"]
        targ_hull = targScan["hull"]

        total_shield_dam = 0
        total_hull_dam = 0
        
        averaged_shields = 0
        averaged_hull = 0
        
        averaged_crew_readyness = 0
        
        number_of_ship_kills = 0
        
        number_of_crew_kills = 0
        
        damage_type = DAMAGE_CANNON if cannon else DAMAGE_BEAM

        amount = min(self.energy, self.get_max_effective_beam_firepower, energy)
        
        crew_readyness = self.crew_readyness# * 0.5 + 0.5
        
        scan_target_crew = not target.ship_class.is_automated and simulate_crew
                
        target_crew_readyness = target.scan_crew_readyness(precision) if scan_target_crew else 1.0
        
        #target_crew_readyness = self.scan_crew_readyness(precision) if simulate_crew else 1.0
        
        for i in range(number_of_simulations):
            
            if self.roll_to_hit(
                target, 
                precision=precision, 
                systems_used_for_accuray=(
                    self.sys_sensors.get_effective_value,
                    self.sys_beam_array.get_effective_value
                ),
                damage_type=damage_type,
                crew_readyness=crew_readyness,
                target_crew_readyness=target_crew_readyness
            ):
                new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage =self.calculate_damage(
                    amount, precision=precision, calculate_crew=scan_target_crew, 
                    calculate_systems=simulate_systems, scan_dict=targScan, damage_type=damage_type
                )
                averaged_shields += new_shields
                averaged_hull += new_hull
                total_shield_dam += shields_dam
                total_hull_dam += hull_dam
                
                if new_hull <= 0:
                    number_of_ship_kills+=1
                
                if scan_target_crew:
                    able_crew = targScan["able_crew"] - (wounded + killed_outright)
                    injured_crew = targScan["injured_crew"] - killed_in_sickbay
                    
                    averaged_crew_readyness += target.caluclate_crew_readyness(able_crew, injured_crew)
                    
                    if able_crew + injured_crew == 0:
                        
                        number_of_crew_kills += 1
            else:
                averaged_shields += targ_shield
                averaged_hull += targ_hull
                
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        total_shield_dam /= number_of_simulations
        total_hull_dam /= number_of_simulations
        averaged_number_of_ship_kills = number_of_ship_kills / number_of_simulations
        averaged_number_of_crew_kills = number_of_crew_kills / number_of_simulations
        
        if scan_target_crew:
            averaged_crew_readyness /= number_of_simulations
        else:
            averaged_crew_readyness = 1.0
        
        return averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_number_of_ship_kills, averaged_number_of_crew_kills, averaged_crew_readyness

    def check_torpedo_los(self, target:Starship):
        """Returns a float that examins the chance of a torpedo hitting an intended target.

        Args:
            target (Starship): The starship that the attacker is aiming at

        Returns:
            [float]: A float between 1 and 0 (inclusive)
        """
        gd = self.game_data

        # Normalize the x and y direction
        dirX, dirY = Coords(
            target.local_coords.x - self.local_coords.x, target.local_coords.y - self.local_coords.y
        ).normalize()
        
        g:SubSector = self.get_sub_sector

        torp_positions = gd.engine.get_lookup_table(direction_x=dirX, direction_y=dirY, normalise_direction=False)

        # Create dictionary of positions and ships for ships in the same system that are are not obliterated
        ship_positions = {
            ship.local_coords.create_coords() : ship for ship in 
            gd.grab_ships_in_same_sub_sector(self, accptable_ship_statuses={STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK})
        }
        
        score = []

        for pos in torp_positions:
            x = pos.x + self.local_coords.x
            y = pos.y + self.local_coords.y
            
            if x not in gd.subsec_size_range_x or y not in gd.subsec_size_range_y:
                break

            ajusted_pos = Coords(x=pos.x+self.local_coords.x, y=pos.y+self.local_coords.y)

            if ajusted_pos in g.stars_dict or pos in g.planets_dict:
                break

            try:
                hit_ship = ship_positions[ajusted_pos]
                score.append(
                    0 if hit_ship.is_controllable == self.is_controllable else 1
                )
                
            except KeyError:
                pass
        
        number_of_ship_hits = len(score)
                
        if number_of_ship_hits == 0:
            return 0.0

        if number_of_ship_hits == 1:
            return float(score[0])
        
        total = sum(score)
        
        return total / number_of_ship_hits

    def detect_cloaked_ship(self, ship:Starship):
        if ship.cloak_status != CloakStatus.ACTIVE:
            raise AssertionError(f"The ship {self.name} is atempting to detect the ship {ship.name}, even though {ship.name} is not cloaked.")

        if not self.sys_sensors.is_opperational:
            return False
        
        detected = True
        
        detection_strength = self.ship_class.detection_strength * self.sys_sensors.get_effective_value
        
        cloak_strength = ship.get_cloak_power

        for i in range(CONFIG_OBJECT.chances_to_detect_cloak):

            if uniform(
                0.0, detection_strength
            ) < uniform(
                0.0, cloak_strength
            ):
                detected = False
                break
            
        player = self.game_data.player
        
        if detected and player.sector_coords == self.sector_coords:
            
            cr = player.nation.captain_rank_name
            
            self.game_data.engine.message_log.add_message(
f'{f"{cr}, we have" if self is player else f"The {self.name} has"} detected {"us" if ship is player else ship.name}!'
            )
        return detected
