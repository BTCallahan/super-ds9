from dataclasses import dataclass
from functools import lru_cache
from posixpath import split
from random import choice
import re
from string import digits
from typing import Dict, Final, Optional, Tuple, List
from frozendict import frozendict
from energy_weapon import ALL_ENERGY_WEAPONS
from global_functions import get_first_group_in_pattern
from nation import ALL_NATIONS

from torpedo import ALL_TORPEDO_TYPES, Torpedo

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
    torp_dict:frozendict[Torpedo, int]
    evasion:float=0.0
    max_beam_energy:int=0
    max_beam_targets:int=1
    max_cannon_energy:int=0
    max_armor:int=0
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
        max_crew:int=0, 
        max_energy:int, 
        damage_control:float, 
        torp_dict:Optional[Dict[Torpedo,int]]=None,
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
        try:
            max_torpedos = sum([t for t in torp_dict.values()])
        except AttributeError:
            max_torpedos = 0

        #torp_types_:Tuple[str] = tuple(["NONE"] if not torp_types else torp_types)
        
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
        
        fd = frozendict(torp_dict)
        
        return cla(
            ship_type=ship_type,
            name=name,
            symbol=symbol,
            max_shields=max_shields,
            max_armor=max_armor,
            max_hull=max_hull,
            max_crew=max_crew,
            max_energy=max_energy,
            damage_control=damage_control,
            torp_dict=fd,
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

    @lru_cache
    def get_torp_dict(self):
        return {
            k:v for k,v in self.torp_dict
        }

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
        has_proper_name = self.has_proper_name
        return choice(self.nation.ship_names) if has_proper_name else "".join([choice(digits) for a in range(8)])

    @property
    @lru_cache
    def has_proper_name(self):
        """Does this ship/station have a propper name, or just a sequence of numbers?

        Returns:
            bool: True if the ship's nation has names AND it has crew, False otherwise
        """        
        return self.max_crew > 0 and self.nation.ship_names

    @property
    @lru_cache
    def ship_type_has_shields(self):
        return self.max_shields > 0

    @property
    @lru_cache
    def max_torpedos(self):
        return sum(v for v in self.torp_dict.values())

    @property
    @lru_cache
    def ship_type_can_fire_torps(self):
        return self.max_torpedos > 0

    @property
    @lru_cache
    def get_most_powerful_torpedo_type(self):
        if not self.ship_type_can_fire_torps:
            return ALL_TORPEDO_TYPES["NONE"]

        t = [k for k in self.torp_dict.keys()]
        
        t.sort(key=lambda a: a.damage, reverse=True)

        return t[0]

    @property
    @lru_cache
    def allowed_torpedos_set(self):
        return frozenset(self.torp_dict.keys()) if self.torp_dict else frozenset([ALL_TORPEDO_TYPES["NONE"]])

    @property
    @lru_cache
    def allowed_torpedos_tuple(self):
        return tuple(self.torp_dict.keys()) if self.torp_dict else tuple([ALL_TORPEDO_TYPES["NONE"]])

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
torpedos_pattern = re.compile(r"TORPEDOS:([\w,]+)\n")
cloak_strength_pattern = re.compile(r"CLOAK_STRENGTH:([\d.]+)\n")
cloak_cooldown_pattern = re.compile(r"CLOAK_COOLDOWN:([\d]+)\n")
size_pattern = re.compile(r"SIZE:([\d.]+)\n")
targeting_pattern = re.compile(r"TARGETING:([\d.]+)\n")
evasion_pattern = re.compile(r"EVASION:([\d.]+)\n")
detection_strength_pattern = re.compile(r"DETECTION_STRENGTH:([\d.]+)")
damage_control_pattern = re.compile(r"DAMAGE_CONTROL:([\d.]+)\n")
torpedos_tubes_pattern = re.compile(r"TORPEDO_TUBES:([\d]+)\n")
#torpedos_types_pattern = re.compile(r"TORPEDO_TYPES:([A-Z\,\_]+)\n")
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
            shipclass_txt, torpedos_pattern, return_aux_if_no_match=True
        )
        
        torp_dict = {}
        
        if torpedos:
            
            tt = torpedos.split(",")
            
            t_types = tt[::2]
            t_numbers = tt[1::2]
            
            torp_dict = {
                ALL_TORPEDO_TYPES[k] :int(v) for k,v in zip(t_types, t_numbers)
            }
        
        torpedo_tubes = get_first_group_in_pattern(
            shipclass_txt, torpedos_tubes_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0,
            type_to_convert_to=int
        )
        
        if (len(torp_dict) == 0) and (torpedo_tubes > 0):
            
            raise ValueError(
                f"In the ship class {shipclass_code} there are {len(torp_dict)} items in the torpedo dictionary, but the ship class has {torpedo_tubes} torpedo tubes."
            )
        
        #torpedo_types_ = get_first_group_in_pattern(shipclass_txt, torpedos_types_pattern, return_aux_if_no_match=True)
        
        #torpedo_types = torpedo_types_.split(",") if torpedo_types_ else None
        
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
            torp_dict=torp_dict,
            torp_tubes=torpedo_tubes,
            damage_control=damage_control,
            max_beam_energy=max_beam_energy,
            max_beam_targets=max_beam_targets,
            max_cannon_energy=max_cannon_energy,
            max_energy=energy,
            max_crew=crew,
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
    