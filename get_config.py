
from math import ceil
from typing import Dict, Final
from collections.abc import Mapping
from datetime import timedelta
from dataclasses import dataclass
import re
from global_functions import get_first_group_in_pattern
from data_globals import string_or_int
from coords import Coords

class FrozenDict(Mapping):

    def __init__(self, ) -> None:
        super().__init__()
        
@dataclass(frozen=True)
class ConfigObject:

    chances_to_detect_cloak:int
    time_per_turn:int
    energy_cost_per_torpedo:int
    
    screen_width:int
    screen_height:int
    
    sector_width:int
    sector_height:int
    
    subsector_width:int
    subsector_height:int
    
    sector_display_x:int
    sector_display_y:int
    
    subsector_display_x:int
    subsector_display_y:int
    
    message_display_x:int
    message_display_end_x:int
    message_display_y:int
    message_display_end_y:int
    
    your_ship_display_x:int
    your_ship_display_end_x:int
    your_ship_display_y:int
    your_ship_display_end_y:int

    other_ship_display_x:int
    other_ship_display_end_x:int
    other_ship_display_y:int
    other_ship_display_end_y:int

    command_display_x:int
    command_display_end_x:int
    command_display_y:int
    command_display_end_y:int

    position_info_x:int
    position_info_end_x:int
    position_info_y:int
    position_info_end_y:int
    
    graphics:str
    max_warp_distance:int
    max_move_distance:int
    max_distance:int
    
    @classmethod
    def create_config(self) -> "ConfigObject":
        
        config_file_pattern = re.compile(r"config_file:([\w.,-]+)\n")
        
        with open("config.ini", "r") as f:
            #lines = f.readlines()
            text = f.read()
                    
        config_file = get_first_group_in_pattern(text, config_file_pattern, return_aux_if_no_match=True)
        
        if config_file is None:
            raise OSError(
                "The file 'config.ini' did not contain an entry for 'config_file'"
            )
        else:
            config_file = "configurations/" + config_file.strip()

        seconds_per_turn_pattern = re.compile(r"seconds_per_turn:([\d]+)\n")

        seconds_per_turn = get_first_group_in_pattern(
            text, seconds_per_turn_pattern, return_aux_if_no_match=True, type_to_convert_to=int
        )
        if seconds_per_turn is None:
            
            raise OSError("The file 'config.ini' did not contain an entry for 'seconds_per_turn'")
        
        elif seconds_per_turn == 0:
            
            raise ValueError(
                "The value of 'seconds_per_turn' is zero, which means that no time will pass between turns"
            )
        
        time_per_turn = timedelta(seconds=seconds_per_turn)
        
        chances_to_detect_cloak_pattern = re.compile(r"chances_to_detect_cloak:([\d]+)\n")
        
        chances_to_detect_cloak = get_first_group_in_pattern(
            text, chances_to_detect_cloak_pattern, return_aux_if_no_match=True, type_to_convert_to=int
        )
        if chances_to_detect_cloak is None:
            
            raise OSError("The file 'config.ini' did not contain an entry for 'chances_to_detect_cloak'")
        
        elif chances_to_detect_cloak == 0:
            
            raise ValueError("The value of 'chances_to_detect_cloak' is zero, which means that ship will not get any chances to detect a cloaked ship")
        
        chances_to_detect_cloak = chances_to_detect_cloak
        
        energy_cost_per_torpedo_patten = re.compile(r"energy_cost_per_torpedo:([\d]+)\n")
        
        energy_cost_per_torpedo = get_first_group_in_pattern(
            text, energy_cost_per_torpedo_patten, return_aux_if_no_match=True, type_to_convert_to=int
        )
        if energy_cost_per_torpedo is None:
            
            raise OSError("The file 'config.ini' did not contain an entry for 'energy_cost_per_torpedo'")
        
        d:Dict[str,string_or_int] = {}
        
        with open(config_file, "r") as f:
            lines = f.readlines()
        for line in lines:
            if ":" in line and line[0] != "#":
                k ,v = line.split(":")
                try:
                    d[k] = int(v)
                except ValueError:
                    d[k] = v
        f.close()

        your_ship_display_x = d['your_ship_display_x']
        your_ship_display_end_x = d['your_ship_display_end_x']
        your_ship_display_y = d['your_ship_display_y']
        your_ship_display_end_y = d['your_ship_display_end_y']

        other_ship_display_x = d['other_ship_display_x']
        other_ship_display_end_x = d['other_ship_display_end_x']
        other_ship_display_y = d['other_ship_display_y']
        other_ship_display_end_y = d['other_ship_display_end_y']

        command_display_x = d['command_display_x']
        command_display_end_x = d['command_display_end_x']
        command_display_y = d['command_display_y']
        command_display_end_y = d['command_display_end_y']

        position_info_x = d['position_info_x']
        position_info_end_x = d['position_info_end_x']
        position_info_y = d['position_info_y']
        position_info_end_y = d['position_info_end_y']
                
        graphics = "fonts/" + d['graphics']

        c1:Coords = Coords(x=0, y=0)

        max_warp_distance = ceil(c1.distance(x=d["sector_width"], y=d["sector_height"]))
        max_move_distance = ceil(c1.distance(x=d["subsector_width"], y=d["subsector_height"]))
        max_distance = max(max_warp_distance, max_move_distance)
        
        screen_width = d['screen_width']
        screen_height = d['screen_height']

        sector_width = d['sector_width']
        sector_height = d['sector_height']
        subsector_width = d['subsector_width']
        subsector_height = d['subsector_height']

        sector_display_x = d['sector_display_x']
        sector_display_y = d['sector_display_y']
        subsector_display_x = d['subsector_display_x']
        subsector_display_y = d['subsector_display_y']

        message_display_x = d['message_display_x']
        message_display_end_x = d['message_display_end_x']
        message_display_y = d['message_display_y']
        message_display_end_y = d['message_display_end_y']
        
        return ConfigObject(
            chances_to_detect_cloak=chances_to_detect_cloak,
            time_per_turn=time_per_turn,
            energy_cost_per_torpedo=energy_cost_per_torpedo,
            screen_width=screen_width,
            screen_height=screen_height,
            sector_width=sector_width,
            sector_height=sector_height,
            subsector_width=subsector_width,
            subsector_height=subsector_height,
            sector_display_x=sector_display_x,
            sector_display_y=sector_display_y,
            subsector_display_x=subsector_display_x,
            subsector_display_y=subsector_display_y,
            message_display_x=message_display_x,
            message_display_end_x=message_display_end_x,
            message_display_y=message_display_y,
            message_display_end_y=message_display_end_y,
            your_ship_display_x=your_ship_display_x,
            your_ship_display_end_x=your_ship_display_end_x,
            your_ship_display_y=your_ship_display_y,
            your_ship_display_end_y=your_ship_display_end_y,
            other_ship_display_x=other_ship_display_x,
            other_ship_display_end_x=other_ship_display_end_x,
            other_ship_display_y=other_ship_display_y,
            other_ship_display_end_y=other_ship_display_end_y,
            command_display_x=command_display_x,
            command_display_end_x=command_display_end_x,
            command_display_y=command_display_y,
            command_display_end_y=command_display_end_y,
            position_info_x=position_info_x,
            position_info_end_x=position_info_end_x,
            position_info_y=position_info_y,
            position_info_end_y=position_info_end_y,
            graphics=graphics,
            max_warp_distance=max_warp_distance,
            max_move_distance=max_move_distance,
            max_distance=max_distance
        )
        
CONFIG_OBJECT:Final= ConfigObject.create_config()