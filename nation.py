from random import choice
from typing import Dict, Optional, Tuple
from string import digits
import re
from global_functions import get_first_group_in_pattern

class Nation:
    __slots__ = (
        "nation_color", 
        "name_long", 
        "name_short", 
        "name_possesive",
        "energy_weapon_name",
        "energy_weapon_name_plural",
        "energy_weapon_beam_name",
        "energy_weapon_beam_name_plural",
        "energy_weapon_cannon_name",
        "energy_weapon_cannon_name_plural",
        "ship_prefix",
        "congrats_text",
        "captain_rank_name",
        "comander_rank_name",
        "ship_names",
        "command_name",
        "intelligence_agency",
        "navy_name"
    )

    def __init__(self, *, 
        nation_color:Tuple[int,int,int], 
        name_long:str, 
        name_short:Optional[str]=None, 
        name_possesive:Optional[str]=None,
        energy_weapon_name:str, 
        ship_prefix:str,
        congrats_text:str,
        captain_rank_name:str,
        comander_rank_name:str,
        command_name:str,
        intelligence_agency:str,
        navy_name:str,
        ship_names:Optional[Tuple[str]]=None
    ) -> None:
        self.nation_color = nation_color
        self.name_long = name_long
        self.name_short = name_short if name_short else name_long
        self.name_possesive = name_possesive if name_possesive else (name_short if name_short else name_long)
        self.energy_weapon_name = energy_weapon_name
        self.energy_weapon_name_plural = f"{energy_weapon_name}s"
        self.energy_weapon_beam_name = f"{energy_weapon_name} beam"
        self.energy_weapon_beam_name_plural = f"{energy_weapon_name} beams"
        self.energy_weapon_cannon_name = f"{energy_weapon_name} cannon"
        self.energy_weapon_cannon_name_plural = f"{energy_weapon_name} cannons"
        self.ship_prefix = ship_prefix
        self.congrats_text = congrats_text
        self.captain_rank_name = captain_rank_name
        self.comander_rank_name = comander_rank_name
        self.ship_names = ship_names
        self.command_name = command_name
        self.intelligence_agency = intelligence_agency
        self.navy_name = navy_name
    
    def generate_ship_name(self):
        
        if not self.ship_names:
            return "".join([choice(digits) for a in range(8)])
        
        return choice(self.ship_names)
    
#\d\w\s\!\:\,\.\'\-\_
nation_pattern = re.compile(r"NATION:([\w]+)\n([^#]+)END_NATION")
color_pattern = re.compile(r"COLOR:([\d]{1,3}),([\d]{1,3}),([\d]{1,3})\n")
name_long_pattern = re.compile(r"NAME_LONG:([\w\s\ ]+)\n")
name_short_pattern = re.compile(r"NAME_SHORT:([a-zA-Z]+)\n")
name_possesive_pattern = re.compile(r"NAME_POSSESIVE:([a-zA-Z]+)\n")
command_name_pattern = re.compile(r"COMMAND_NAME:([a-zA-Z ]+)\n")
intelligence_agency_pattern = re.compile(r"INTELLIGENCE_AGENCY:([a-zA-Z ]+)\n")
navy_name_pattern = re.compile(r"NAVY_NAME:([a-zA-Z ]+)\n")
energy_weapon_pattern = re.compile(r"ENERGY_WEAPON_NAME:([a-zA-Z\ .]+)\n")
ship_prefix_pattern = re.compile(r"SHIP_PREFIX:([A-Z\.\ ]+)\n")
congratulations_pattern = re.compile(r"CONGRATULATIONS_TEXT:([a-zA-Z\.\!\,\ ]+)\n")
captain_rank_pattern = re.compile(r"CAPTAIN_RANK_NAME:([\w]+)\n")
admiral_rank_pattern = re.compile(r"ADMIRAL_RANK_NAME:([\w]+)\n")
ship_names_pattern = re.compile(r"SHIP_NAMES:([\d\w\s\!\:\,\.\'\-]+)\nSHIP_NAMES_END")

def create_nations() -> Dict[str,Nation]:
    
    with open("library/nations.txt") as nation_text:
        
        contents = nation_text.read()
        
    nations = nation_pattern.finditer(contents)
    
    nation_dict = {}
        
    for nation in nations:
        
        nation_code = nation.group(1)
        
        nation_txt = nation.group(2)
        
        color = color_pattern.search(nation_txt)
                
        color_r, color_g, color_b = color.group(1), color.group(2), color.group(3)
        
        name_long = get_first_group_in_pattern(nation_txt, name_long_pattern)
        
        name_short_pattern_match = name_short_pattern.search(nation_txt)
        
        try:
            name_short = name_short_pattern_match.group(1)
        except AttributeError:
            name_short = name_long
        
        name_possesive_pattern_match = name_possesive_pattern.search(nation_txt)
        
        try:
            name_possesive = name_possesive_pattern_match.group(1)
        except AttributeError:
            
            name_possesive = name_short
        
        command_name = get_first_group_in_pattern(nation_txt, command_name_pattern)
        
        intelligence_agency = get_first_group_in_pattern(nation_txt, intelligence_agency_pattern)
                    
        energy_weapon = get_first_group_in_pattern(nation_txt, energy_weapon_pattern)
        
        ship_prefix = get_first_group_in_pattern(nation_txt, ship_prefix_pattern, return_aux_if_no_match=True)
        
        congratulations = get_first_group_in_pattern(nation_txt, congratulations_pattern)
        
        captain_rank = get_first_group_in_pattern(nation_txt, captain_rank_pattern)
        
        admiral_rank = get_first_group_in_pattern(nation_txt, admiral_rank_pattern)
        
        navy_name = get_first_group_in_pattern(nation_txt, navy_name_pattern)
        
        ship_names_pattern_match = ship_names_pattern.search(nation_txt)
        
        try:
            ship_names_ = ship_names_pattern_match.group(1)
            
            ship_names = tuple(ship_names_.replace("\n", "").split(","))
            
            if len(ship_names) == 1 and ship_names[0] == "NONE":
                ship_names = None
        except AttributeError:
            
            ship_names = None
        
        return_this = Nation(
            nation_color=(int(color_r), int(color_g), int(color_b)),
            name_long=name_long,
            name_short=name_short,
            name_possesive=name_possesive,
            energy_weapon_name=energy_weapon,
            ship_prefix=ship_prefix,
            congrats_text=congratulations,
            captain_rank_name=captain_rank,
            comander_rank_name=admiral_rank,
            ship_names=ship_names,
            command_name=command_name,
            intelligence_agency=intelligence_agency,
            navy_name=navy_name
        )
        
        nation_dict[nation_code] = return_this
        
    return nation_dict
        
ALL_NATIONS = create_nations()