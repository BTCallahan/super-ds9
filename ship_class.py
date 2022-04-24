from dataclasses import dataclass
from functools import lru_cache
from posixpath import split
from random import choice
import re
from string import digits
from typing import Dict, Final, Optional, Tuple, List
from frozendict import frozendict
from energy_weapon import ALL_ENERGY_WEAPONS, EnergyWeapon
from global_functions import get_first_group_in_pattern
from nation import ALL_NATIONS, Nation

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
    has_warp:bool=True,
    has_shields:bool,
    has_polerized_hull:bool,
    has_impulse:bool=True,
    beam_weapon_name:str="",
    cannon_weapon_name:str=""
):
    names = [
        "Warp Core:",
        "Sensors:",
        "Scanners:"
    ]
    keys = [
        "sys_warp_core",
        "sys_sensors",
        "sys_scanners"
    ]
    """
    if has_shields:
        names.append("Shields:")
        keys.append("shield")
        
    if has_polerized_hull:
        names.append("Polarization:")
        keys.append("polarization")
    """
        
    if has_shields:
        names.append("Shield Gen.:")
        keys.append("sys_shield")
    
    if has_polerized_hull:
        names.append("P. Hull:")
        keys.append("sys_polarize")
    
    if has_warp:
        names.append("Warp Drive:")
        keys.append("sys_warp_drive")
    
    if has_impulse:
        names.append("I. Engines:")
        keys.append("sys_impulse")
        
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
    max_hull:int
    max_crew:int
    max_energy:int
    power_generated_per_turn:int
    damage_control:float
    energy_weapon:EnergyWeapon
    scanner_range:int
    nation:Nation
    system_names:Tuple[str]
    system_keys:Tuple[str]
    detection_strength:float
    targeting:float
    size:float
    torp_dict:frozendict[Torpedo, int]
    transporters:int=0
    max_shields:int=0
    evasion:float=0.0
    max_beam_energy:int=0
    max_beam_targets:int=1
    max_cannon_energy:int=0
    max_armor:int=0
    polarized_hull:int=0
    max_warp:int=0
    torp_tubes:int=0
    warp_breach_damage:int=0
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
        max_shields:int=0,
        polarized_hull:int=0, 
        max_armor:int=0, 
        max_hull:int, 
        max_crew:int=0, 
        transporters:int=0,
        max_energy:int, 
        max_warp:int,
        power_generated_per_turn:int,
        damage_control:float, 
        scanner_range:int,
        torp_dict:Optional[Dict[Torpedo,int]]=None,
        torp_tubes:int=0,
        max_beam_energy:int=0,
        max_beam_targets:int=1,
        max_cannon_energy:int=0, 
        warp_breach_damage:int=2, 
        energy_weapon:EnergyWeapon,
        nation:Nation,
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
        
        short_beam_name_cap = energy_weapon.short_beam_name_cap if max_beam_energy else ""
        
        short_can_name_cap = energy_weapon.short_cannon_name_cap if max_cannon_energy else ""
        
        system_names, system_keys = get_system_names(
            has_torpedo_launchers=max_torpedos > 0 and torp_tubes > 0,
            has_cloaking_device=cloak_strength > 0.0,
            has_transporters=max_crew > 0,
            beam_weapon_name=f"{short_beam_name_cap}s",
            cannon_weapon_name=f"{short_can_name_cap}",
            has_impulse=evasion > 0.0,
            has_warp=max_warp > 0,
            has_shields=max_shields > 0, 
            has_polerized_hull=polarized_hull > 0
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
            transporters=transporters,
            scanner_range=scanner_range,
            max_energy=max_energy,
            polarized_hull=polarized_hull,
            power_generated_per_turn=power_generated_per_turn,
            damage_control=damage_control,
            torp_dict=fd,
            torp_tubes=torp_tubes,
            max_warp=max_warp,
            max_beam_energy=max_beam_energy,
            max_beam_targets=max_beam_targets,
            max_cannon_energy=max_cannon_energy,
            warp_breach_damage=warp_breach_damage,
            energy_weapon=energy_weapon,
            nation=nation,
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
    def is_mobile(self):
        return self.evasion > 0.0

    @property
    @lru_cache
    def can_be_docked_with(self):
        return not self.is_mobile and self.is_automated

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

def create_ship_classes():
    
    shipdata_pattern = re.compile(r"SHIPCLASS:([A-Z\_]+)\n([^#]+)END_SHIPCLASS")
    symbol_pattern = re.compile(r"SYM:([a-zA-Z])\n")
    type_pattern = re.compile(r"TYPE:([A-Z_]+)\n")
    name_pattern = re.compile(r"NAME:([\w\-\ \'\(\)]+)\n")
    shields_pattern = re.compile(r"SHIELDS:([\d]+)\n")
    polarized_hull_pattern = re.compile(r"POLARIZED_HULL:([\d]+)\n")
    hull_pattern = re.compile(r"HULL:([\d]+)\n")
    scanner_pattern = re.compile(r"SCANNER_RANGE:([\d]+)\n")
    energy_pattern = re.compile(r"ENERGY:([\d]+)\n")
    power_generation_pattern = re.compile(r"POWER:([\d]+)\n")
    energy_weapon_pattern = re.compile(r"ENERGY_WEAPON:([A-Z_]+)\n")
    crew_pattern = re.compile(r"CREW:([\d]+)\n")
    transporters_pattern = re.compile(r"TRANSPORTERS:([\d]+)\n")
    torpedos_pattern = re.compile(r"TORPEDOS:([\w,]+)\n")
    cloak_strength_pattern = re.compile(r"CLOAK_STRENGTH:([\d.]+)\n")
    cloak_cooldown_pattern = re.compile(r"CLOAK_COOLDOWN:([\d]+)\n")
    size_pattern = re.compile(r"SIZE:([\d.]+)\n")
    targeting_pattern = re.compile(r"TARGETING:([\d.]+)\n")
    evasion_pattern = re.compile(r"EVASION:([\d.]+)\n")
    detection_strength_pattern = re.compile(r"DETECTION_STRENGTH:([\d.]+)\n")
    max_warp_pattern = re.compile(r"MAX_WARP:([\d]+)\n")
    damage_control_pattern = re.compile(r"DAMAGE_CONTROL:([\d.]+)\n")
    torpedos_tubes_pattern = re.compile(r"TORPEDO_TUBES:([\d]+)\n")
    max_beam_energy_pattern = re.compile(r"MAX_BEAM_ENERGY:([\d]+)\n")
    max_beam_targets_pattern = re.compile(r"MAX_BEAM_TARGETS:([\d])\n")
    max_cannon_energy_pattern = re.compile(r"MAX_CANNON_ENERGY:([\d]+)\n")
    warp_core_breach_damage_pattern = re.compile(r"WARP_CORE_BREACH_DAMAGE:([\d]+)\n")
    nation_types_pattern = re.compile(r"NATION:([A-Z\_]+)\n")
    
    with open("library/ships.txt") as shipclass_text:
        
        contents = shipclass_text.read()
        
    shipclasses = shipdata_pattern.finditer(contents)
    
    shipclass_dict:Dict[str,ShipClass] = {}
        
    for shipclass in shipclasses:
        
        shipclass_code = shipclass.group(1)
        
        shipclass_txt = shipclass.group(2)
                
        type_ = get_first_group_in_pattern(
            shipclass_txt, type_pattern,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'TYPE:'"
        )
        assert type_ in VALID_SHIP_TYPES
        
        symbol = get_first_group_in_pattern(
            shipclass_txt, symbol_pattern,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'SYM:'"
        )
        nation_ = get_first_group_in_pattern(
            shipclass_txt, nation_types_pattern,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'NATION:'"
        )
        if nation_ not in ALL_NATIONS:
            raise KeyError(
                f"The nation code {nation_} was not found in the dictionary of nations. Valid code are: {ALL_NATIONS.keys()}")
        else:
            nation = ALL_NATIONS[nation_]
        
        name = get_first_group_in_pattern(
            shipclass_txt, name_pattern,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'NAME:'"
        )
        shields = get_first_group_in_pattern(
            shipclass_txt, shields_pattern, return_aux_if_no_match=True,
            aux_valute_to_return_if_no_match=0, type_to_convert_to=int
        )
        polarized_hull = get_first_group_in_pattern(
            shipclass_txt, polarized_hull_pattern, return_aux_if_no_match=True,
            aux_valute_to_return_if_no_match=0, type_to_convert_to=int
        )
        hull = get_first_group_in_pattern(
            shipclass_txt, hull_pattern, type_to_convert_to=int,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'HULL:'"
        )
        crew = get_first_group_in_pattern(
            shipclass_txt, crew_pattern, return_aux_if_no_match=True,
            aux_valute_to_return_if_no_match=0, type_to_convert_to=int
        )
        scanner_range = get_first_group_in_pattern(
            shipclass_txt, scanner_pattern, type_to_convert_to=int,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'SCANNER_RANGE:'"
        )
        transporters = get_first_group_in_pattern(
            shipclass_txt, transporters_pattern, return_aux_if_no_match=True,
            aux_valute_to_return_if_no_match=0, type_to_convert_to=int
        )
        energy = get_first_group_in_pattern(
            shipclass_txt, energy_pattern, type_to_convert_to=int,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'ENERGY:'"
        )
        torpedos = get_first_group_in_pattern(
            shipclass_txt, torpedos_pattern, return_aux_if_no_match=True
        )
        if torpedos:
            
            tt = torpedos.split(",")
            
            t_types = tt[::2]
            t_numbers = tt[1::2]
            
            torp_dict_ = {
                ALL_TORPEDO_TYPES[k] :int(v) for k,v in zip(t_types, t_numbers)
            }
        else:
            torp_dict_ = {}
        
        torp_dict = frozendict(torp_dict_)
        
        torpedo_tubes = get_first_group_in_pattern(
            shipclass_txt, torpedos_tubes_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0,
            type_to_convert_to=int
        )
        if (len(torp_dict) == 0) and (torpedo_tubes > 0):
            
            raise ValueError(
                f"In the ship class {shipclass_code} there are {len(torp_dict)} items in the torpedo dictionary, but the ship class has {torpedo_tubes} torpedo tubes."
            )
        
        power_generation = get_first_group_in_pattern(
            shipclass_txt, power_generation_pattern, type_to_convert_to=int,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'POWER:'"
        )
        energy_weapon_ = get_first_group_in_pattern(
            shipclass_txt, energy_weapon_pattern,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'ENERGY_WEAPON:'"
        )
        if energy_weapon_ not in ALL_ENERGY_WEAPONS:
            raise KeyError(
                f"The energy weapon code {energy_weapon_} was not found in the dictionary of energy weapons. Valid code are: {ALL_ENERGY_WEAPONS.keys()}")
        else:
            energy_weapon = ALL_ENERGY_WEAPONS[energy_weapon_]
        
        cloak_strength = get_first_group_in_pattern(
            shipclass_txt, cloak_strength_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0.0,
            type_to_convert_to=float
        )
        cloak_cooldown = get_first_group_in_pattern(
            shipclass_txt, cloak_cooldown_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=2,
            type_to_convert_to=int
        )
        detection_strength = get_first_group_in_pattern(
            shipclass_txt, detection_strength_pattern, type_to_convert_to=float,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'TYPE:'"
        )
        damage_control = get_first_group_in_pattern(
            shipclass_txt, damage_control_pattern, 
            type_to_convert_to=float,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'DAMAGE_CONTROL:'"
        )
        size = get_first_group_in_pattern(
            shipclass_txt, size_pattern, type_to_convert_to=float,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'SIZE:'"
        )
        evasion = get_first_group_in_pattern(
            shipclass_txt, evasion_pattern, type_to_convert_to=float, 
            return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0.0
        )
        max_warp = get_first_group_in_pattern(
            shipclass_txt, max_warp_pattern, type_to_convert_to=int, return_aux_if_no_match=True,
            aux_valute_to_return_if_no_match=0
        )
        targeting = get_first_group_in_pattern(
            shipclass_txt, targeting_pattern, type_to_convert_to=float,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'TARGETING:'"
        )
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
            shipclass_txt, warp_core_breach_damage_pattern, type_to_convert_to=int,
            error_message=f"The entry {shipclass_code} file 'library/ships.txt' did not contain an entry for 'WARP_CORE_BREACH_DAMAGE:'"
        )
        shipclass_dict[shipclass_code] = ShipClass.create_ship_class(
            ship_type=type_,
            symbol=symbol,
            name=name,
            max_shields=shields,
            polarized_hull=polarized_hull,
            max_hull=hull,
            scanner_range=scanner_range,
            torp_dict=torp_dict,
            torp_tubes=torpedo_tubes,
            damage_control=damage_control,
            max_beam_energy=max_beam_energy,
            max_beam_targets=max_beam_targets,
            max_cannon_energy=max_cannon_energy,
            max_energy=energy,
            power_generated_per_turn=power_generation,
            max_crew=crew,
            transporters=transporters,
            cloak_strength=cloak_strength,
            cloak_cooldown=cloak_cooldown,
            detection_strength=detection_strength,
            size=size,
            targeting=targeting,
            evasion=evasion,
            max_warp=max_warp,
            warp_breach_damage=warp_core_breach_damage,
            nation=nation,
            energy_weapon=energy_weapon
        )
        
    return frozendict(shipclass_dict)
    
ALL_SHIP_CLASSES:Final = create_ship_classes()
