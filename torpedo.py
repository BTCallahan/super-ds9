from typing import Dict, Final, Iterable
from dataclasses import dataclass

import re

from frozendict import frozendict
from global_functions import get_first_group_in_pattern

@dataclass(eq=True, frozen=True)
class Torpedo:
    
    code:str
    name:str
    cap_name:str
    damage:int
    infrastructure:float
    infrastructure_damage:float
    valid:bool=True
    
    def __lt__(self, t: "Torpedo"):

        return (self.damage < t.damage) if self.infrastructure == t.infrastructure else (self.infrastructure < t.infrastructure) 

    def __gt__(self, t: "Torpedo"):
        
        return (self.damage > t.damage) if self.infrastructure == t.infrastructure else (self.infrastructure > t.infrastructure)
    
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
            code="NONE",
            name="",
            cap_name="",
            damage=0,
            infrastructure=10000.0,
            infrastructure_damage=0.0,
            valid=False
        )
    }
    for torpedo in torpedos:
        
        torpedo_code = torpedo.group(1)
        
        torpedo_txt = torpedo.group(2)
        
        name = get_first_group_in_pattern(torpedo_txt, name_pattern)
        
        cap_name = name.capitalize()
        
        damage = get_first_group_in_pattern(torpedo_txt, damage_pattern, type_to_convert_to=int)
        
        req_infrastructure = get_first_group_in_pattern(
            torpedo_txt, req_infrastructure_pattern, type_to_convert_to=float
        )
        planet_damage = get_first_group_in_pattern(torpedo_txt, planet_damage_pattern, type_to_convert_to=float)
        
        torp = Torpedo(
            code=torpedo_code,
            name=name,
            cap_name=cap_name,
            damage=damage,
            infrastructure=req_infrastructure,
            infrastructure_damage=planet_damage
        )
        torpedo_dict[torpedo_code] = torp
        
    return frozendict(torpedo_dict)

ALL_TORPEDO_TYPES:Final = create_torpedos()

#def find_most_powerful_torpedo_str(iter_torpedo_type:Iterable[Tor])

def find_most_powerful_torpedo(iter_torpedo_type:Iterable[Torpedo]):

    torp_type = None
    damage = 0

    for torp in iter_torpedo_type:
        if torp.damage > damage:
            torp_type = torp
            damage = torp.damage
    return torp_type

def find_most_destructive_torpedo(iter_torpedo_type:Iterable[Torpedo]):
    
    torp_type = None
    infrastructure_damage = 0.0
    
    for torp in iter_torpedo_type:
        if torp.infrastructure_damage > infrastructure_damage:
            torp_type = torp
            infrastructure_damage = torp.infrastructure_damage
    return torp_type
