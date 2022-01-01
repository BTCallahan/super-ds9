from dataclasses import dataclass
import re
from typing import Dict, Final, Tuple
from global_functions import get_first_group_in_pattern, get_multiple_groups_in_pattern

@dataclass(eq=True, frozen=True)
class EnergyWeapon:
    
    name:str
    beam_name:str
    cannon_name:str
    
    short_name:str
    short_beam_name:str
    short_cannon_name:str
    
    name_cap:str
    beam_name_cap:str
    cannon_name_cap:str
    
    short_name_cap:str
    short_beam_name_cap:str
    short_cannon_name_cap:str
    
    color:Tuple[int,int,int]
    
    @staticmethod
    def _cap_each_word(word:str):
        
        spl = word.split(" ")
        
        if len(spl) == 1:
            return word.capitalize()
        
        w2 = [w.capitalize() for w in spl]
        
        return " ".join(w2)
    
    @classmethod
    def create_weapon(cls, name:str, short_name:str, color:Tuple[int,int,int]):
        
        beam_name = f"{name} array"
        cannon_name = f"{name} cannon"
        
        short_beam_name:str = f"{short_name} array"
        short_cannon_name:str = f"{short_name} cannon"
        
        return cls(
            name=name,
            beam_name=beam_name,
            cannon_name=cannon_name,
            
            short_name=short_name,
            short_beam_name=short_beam_name,
            short_cannon_name=short_cannon_name,
            
            name_cap=cls._cap_each_word(name),
            beam_name_cap=cls._cap_each_word(beam_name),
            cannon_name_cap=cls._cap_each_word(cannon_name),
            
            short_name_cap=cls._cap_each_word(short_name),
            short_beam_name_cap=cls._cap_each_word(short_beam_name),
            short_cannon_name_cap=cls._cap_each_word(short_cannon_name),
            color=color
        )


energy_weapon_pattern = re.compile(r"ENERGY_WEAPON:([\w\d_]+)\n([^#]+)END_ENERGY_WEAPON")
color_pattern = re.compile(r"COLOR:([\d]+),([\d]+),([\d]+)\n")
name_pattern = re.compile(r"NAME:([\w\d\ ]+)\n" )
name_short_pattern = re.compile(r"NAME_SHORT:([a-zA-Z \.]+)\n")

def create_energy_weapons() -> Dict[str,EnergyWeapon]:
    
    with open("library/energy_weapons.txt") as energy_weapon_text:
        
        contents = energy_weapon_text.read()
        
    energy_weapons = energy_weapon_pattern.finditer(contents)
    
    energy_weapon_dict:Dict[str,EnergyWeapon] = {}
        
    for energy_weapon in energy_weapons:
        
        energy_weapon_code = energy_weapon.group(1)
        
        energy_weapon_txt = energy_weapon.group(2)
        
        color = color_pattern.search(energy_weapon_txt)
        #get_multiple_groups_in_pattern
        color_r, color_g, color_b = color.group(1), color.group(2), color.group(3)
        
        color_tuple = (int(color_r), int(color_g), int(color_b))
        
        name = get_first_group_in_pattern(energy_weapon_txt, name_pattern)
        
        short_name = get_first_group_in_pattern(
            energy_weapon_txt, name_short_pattern,return_aux_if_no_match=True, aux_valute_to_return_if_no_match=name
        )
        
        energy_weapon_dict[energy_weapon_code] = EnergyWeapon.create_weapon(name, short_name, color_tuple)
    
    return energy_weapon_dict

ALL_ENERGY_WEAPONS:Final = create_energy_weapons()