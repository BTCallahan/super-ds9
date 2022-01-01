
from math import ceil
from typing import Dict, Final
from collections.abc import Mapping

from data_globals import string_or_int
from coords import Coords

class FrozenDict(Mapping):

    def __init__(self, ) -> None:
        super().__init__()
        
class ConfigObject:

    def __init__(self) -> None:
        
        with open("config.ini", "r") as f:
            lines = f.readlines()
            
        config_file = None
        
        for line in lines:
            if ":" in line and line[0] != "#":
                k ,v = line.split(":")
                if k == "config_file":
                    
                    config_file = "configurations/" + v.strip()
        
        if config_file is None:
            raise OSError(
                "The file 'config.ini' did not contain an entry for 'config_file'"
            )
                
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

        self.screen_width = d['screen_width']
        self.screen_height = d['screen_height']

        self.sector_width = d['sector_width']
        self.sector_height = d['sector_height']
        self.subsector_width = d['subsector_width']
        self.subsector_height = d['subsector_height']

        self.sector_display_x = d['sector_display_x']
        self.sector_display_y = d['sector_display_y']
        self.subsector_display_x = d['subsector_display_x']
        self.subsector_display_y = d['subsector_display_y']

        self.message_display_x = d['message_display_x']
        self.message_display_end_x = d['message_display_end_x']
        self.message_display_y = d['message_display_y']
        self.message_display_end_y = d['message_display_end_y']

        self.your_ship_display_x = d['your_ship_display_x']
        self.your_ship_display_end_x = d['your_ship_display_end_x']
        self.your_ship_display_y = d['your_ship_display_y']
        self.your_ship_display_end_y = d['your_ship_display_end_y']

        self.other_ship_display_x = d['other_ship_display_x']
        self.other_ship_display_end_x = d['other_ship_display_end_x']
        self.other_ship_display_y = d['other_ship_display_y']
        self.other_ship_display_end_y = d['other_ship_display_end_y']

        self.command_display_x = d['command_display_x']
        self.command_display_end_x = d['command_display_end_x']
        self.command_display_y = d['command_display_y']
        self.command_display_end_y = d['command_display_end_y']

        self.position_info_x = d['position_info_x']
        self.position_info_end_x = d['position_info_end_x']
        self.position_info_y = d['position_info_y']
        self.position_info_end_y = d['position_info_end_y']
                
        self.graphics = "fonts/" + d['graphics']

        c1:Coords = Coords(x=0, y=0)

        self.max_warp_distance = ceil(c1.distance(x=d["sector_width"], y=d["sector_height"]))
        self.max_move_distance = ceil(c1.distance(x=d["subsector_width"], y=d["subsector_height"]))
        self.max_distance = max(self.max_warp_distance, self.max_move_distance)
        
CONFIG_OBJECT:Final= ConfigObject()