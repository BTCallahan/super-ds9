from typing import Dict, Iterable
from dataclasses import dataclass

import re
from global_functions import get_first_group_in_pattern

@dataclass(eq=True, frozen=True)
class Torpedo:
    
    #__slots__ = ("cap_name", "name", "damage", "infrastructure", "infrastructure_damage")
    
    name:str
    damage:int
    infrastructure:float
    infrastructure_damage:float
    
    """
    def __init__(self, *, name:str, damage:int, infrastructure:float, infrastructure_damage:float):
        self.cap_name = name.capitalize()
        self.name = name
        self.damage = damage
        self.infrastructure = infrastructure
        self.infrastructure_damage = infrastructure_damage

    def __hash__(self) -> int:
        
        return hash((self.cap_name, self.name, self.damage, self.infrastructure, self.infrastructure_damage))
    """
    
    @property
    def cap_name(self):
        return self.name.capitalize()

    def __lt__(self, t: "Torpedo"):

        return (self.damage < t.damage) if self.infrastructure == t.infrastructure else (self.infrastructure < t.infrastructure) 

    def __gt__(self, t: "Torpedo"):
        
        return (self.damage > t.damage) if self.infrastructure == t.infrastructure else (self.infrastructure > t.infrastructure)
    
    """
    def __eq__(self, t: "Torpedo") -> bool:
        try:
            return self.damage == t.damage and self.infrastructure == t.infrastructure and self.name == t.name and self.infrastructure_damage == t.infrastructure_damage
        except AttributeError:
            return False
    
    def __ne__(self, t: "Torpedo") -> bool:
        try:
            return self.damage != t.damage or self.infrastructure != t.infrastructure and self.name != t.name and self.infrastructure_damage != t.infrastructure_damage
        except AttributeError:
            return False
    """

torpedo_pattern = re.compile(r"TORPEDO:([A-Z\_]+)\n([^#]+)END_TORPEDO")
name_pattern = re.compile(r"NAME:([a-zA-Z\ \-\']+)\n" )
damage_pattern = re.compile(r"DAMAGE:([\d]{1,4})\n" )
req_infrastructure_pattern = re.compile(r"REQUIRED:([\d.]+)\n" )
planet_damage_pattern = re.compile(r"PLANET_DAMAGE:([\d.]+)\n" )

def create_torpedos() -> Dict[str,Torpedo]:
    
    with open("library/torpedos.txt") as torpedo_text:
        
        contents = torpedo_text.read()
        
    torpedos = torpedo_pattern.finditer(contents)
    
    torpedo_dict = {
        "NONE" : Torpedo(
            name="",
            damage=0,
            infrastructure=10000.0,
            infrastructure_damage=0.0
        )
    }
        
    for torpedo in torpedos:
        
        torpedo_code = torpedo.group(1)
        
        torpedo_txt = torpedo.group(2)
                
        name = get_first_group_in_pattern(torpedo_txt, name_pattern)
                
        damage = get_first_group_in_pattern(torpedo_txt, damage_pattern)
                
        req_infrastructure = get_first_group_in_pattern(torpedo_txt, req_infrastructure_pattern)
                
        planet_damage_ = get_first_group_in_pattern(torpedo_txt, planet_damage_pattern)
        
        try:
            planet_damage = float(planet_damage_)
        except TypeError:
            planet_damage = float(planet_damage_[0])
        
        torp = Torpedo(
            name=name,
            damage=int(damage),
            infrastructure=float(req_infrastructure),
            infrastructure_damage=planet_damage
        )
        
        torpedo_dict[torpedo_code] = torp
        
    return torpedo_dict

ALL_TORPEDO_TYPES = create_torpedos()

def find_most_powerful_torpedo(iter_torpedo_type:Iterable[str]):

    torp_type = "NONE"
    damage = 0

    for t in iter_torpedo_type:
        torp = ALL_TORPEDO_TYPES[t]
        if torp.damage > damage:
            torp_type = t
            damage = torp.damage
    return torp_type