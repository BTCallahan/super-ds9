from typing import Dict, Optional, Tuple
import re

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
        "ship_names")

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
        ship_names:Optional[Tuple[str]]=None
    ) -> None:
        self.nation_color = nation_color
        self.name_long = name_long
        self.name_short = name_short if name_short else name_long
        self.name_possesive = name_possesive if name_possesive else (name_short if name_short else name_long)
        self.energy_weapon_name = energy_weapon_name
        self.energy_weapon_name_plural = f"{energy_weapon_name}s"
        self.energy_weapon_beam = f"{energy_weapon_name} beam"
        self.energy_weapon_beam_plural = f"{energy_weapon_name} beams"
        self.energy_cannon_name = f"{energy_weapon_name} cannon"
        self.energy_cannon_name_plural = f"{energy_weapon_name} cannons"
        self.ship_prefix = ship_prefix
        self.congrats_text = congrats_text
        self.captain_rank_name = captain_rank_name
        self.comander_rank_name = comander_rank_name
        self.ship_names = ship_names
    
    def ship_name(self, name:str):
        return f"{self.ship_prefix} {name}" if self.ship_prefix else name

"""
federation = Nation(
    nation_color= (50, 45, 235),
    name_long="United Federation of Planets",
    name_short="Federation",
    energy_weapon_name="Phaser array",
    energy_weapon_name_plural="Phaser arrays",
    energy_cannon_name="Phaser cannon",
    energy_cannon_name_plural="Phaser cannons",
    ship_prefix="U.S.S.",
    congrats_text="Well Done!",
    captain_rank_name="Captain",
    comander_rank_name="Admiral"
)

dominion = Nation(
    nation_color=(210, 20, 227),
    name_long="Dominion",
    name_short="Dominion",
    energy_weapon_name="Phased Poleron array",
    energy_weapon_name_plural="Phased Poleron arrays",
    energy_cannon_name="Phased Poleron cannon",
    energy_cannon_name_plural="Phased Poleron cannons",
    ship_prefix="D.D.S.",
    congrats_text="Victory is Life!",
    captain_rank_name="First",
    comander_rank_name="Founder"
)

klingon = Nation(
    nation_color=(231, 50, 12),
    name_long="Kingon Empire",
    name_short="Kingon",
    energy_weapon_name="Disruptor array",
    energy_weapon_name_plural="Disruptor arrays",
    energy_cannon_name="Disruptor cannon",
    energy_cannon_name_plural="Disruptor cannons",
    ship_prefix="I.K.S.",
    congrats_text="Qapah!",
    captain_rank_name="Captain",
    comander_rank_name="General"
)

romulan = Nation(
    nation_color=(10, 10, 240),
    name_long="Romulan Star Empire",
    name_short="Romulan",
    energy_weapon_name="Disruptor array",
    energy_weapon_name_plural="Disruptor arrays",
    energy_cannon_name="Disruptor cannon",
    energy_cannon_name_plural="Disruptor cannons",
    ship_prefix="",
    congrats_text="Victory!",
    captain_rank_name="Commander",
    comander_rank_name="Admiral"
)

cardassian = Nation(
    nation_color=(237, 227, 16),
    name_long="Cardassian Union",
    name_short="Cardassian",
    energy_weapon_name="Compresser array",
    energy_weapon_name_plural="Compresser arrays",
    energy_cannon_name="Compresser pluse cannon",
    energy_cannon_name_plural="Compresser pluse cannons",
    ship_prefix="",# C.U.W. ?
    congrats_text="Excellent.",
    captain_rank_name="Gul",
    comander_rank_name="Legate"
)
"""

nation_pattern = re.compile(r"\nNATION:([\w]+)\n([\w\s!:,.']+)\nNATIONEND\n")
color_pattern = re.compile(r"COLOR:(\d+),(\d+),(\d+)\n")
name_long_pattern = re.compile(r"NAME_LONG:([a-zA-Z ]+)\n")
name_short_pattern = re.compile(r"NAME_SHORT:([a-zA-Z]+)\n")
name_possesive_pattern = re.compile(r"NAME_POSSESIVE:([a-zA-Z]+)\n")
energy_weapon_pattern = re.compile(r"ENERGY_WEAPON_NAME:([a-zA-Z ]+)\n")
ship_prefix_pattern = re.compile(r"SHIP_PREFIX:([A-Z. ]+)\n")
congratulations_pattern = re.compile(r"CONGRATULATIONS_TEXT:([a-zA-Z.!, ]+)\n")
captain_rank_pattern = re.compile(r"CAPTAIN_RANK_NAME:([a-zA-Z]+)\n")
admiral_rank_pattern = re.compile(r"ADMIRAL_RANK_NAME:([a-zA-Z]+)\n")
ship_names_pattern = re.compile(r"SHIP_NAMES:([a-z', \n]+)\nSHIP_NAMES\n")

def create_nations() -> Dict[str,Nation]:
    
    with open("library/nations.txt") as nation_text:
        
        contents = nation_text.read()
        
    nations = nation_pattern.finditer(contents)
    
    nation_dict = {}
        
    for nation in nations:
        
        nation_code = nation.group(1)
        
        nation_txt = nation.group(2)
        
        color = color_pattern.match(nation_txt)
                
        color_r, color_g, color_b = color.group(1), color.group(2), color.group(3)
                
        name_long_pattern_match = name_long_pattern.match(nation_txt)
        
        name_long = name_long_pattern_match.group(1)
        
        name_short_pattern_match = name_short_pattern.match(nation_txt)
        
        try:
            name_short = name_short_pattern_match.group(1)
        except AttributeError:
            name_short = name_long
        
        name_possesive_pattern_match = name_possesive_pattern.match(nation_txt)
        
        try:
            name_possesive = name_possesive_pattern_match.group(1)
        except AttributeError:
            
            name_possesive = name_short
            
        energy_weapon = energy_weapon_pattern.match(nation_txt).group(1)
        
        ship_prefix_pattern_match = ship_prefix_pattern.match(nation_txt)
        
        try:
            ship_prefix = ship_prefix_pattern_match.group(1)
        except AttributeError:
            ship_prefix = None
        
        congratulations = congratulations_pattern.match(nation_txt).group(1)
        
        captain_rank = captain_rank_pattern.match(nation_txt).group(1)
        
        admiral_rank = admiral_rank_pattern.match(nation_txt).group(1)
        
        ship_names_ = ship_names_pattern.match(nation_txt).group(1)
        
        ship_names = tuple(ship_names_.replace("\n", "").split(","))
        
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
            ship_names=ship_names
        )
        
        nation_dict[nation_code] = return_this
        
    return nation_dict
        
all_nations = create_nations()