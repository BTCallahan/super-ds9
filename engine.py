from __future__ import annotations

from coords import Coords, AnyCoords
from typing import Dict, Tuple, TYPE_CHECKING
from data_globals import ENERGY_REGEN_PER_TURN, REPAIR_MULTIPLIER
from message_log import MessageLog
from game_data import GameData
from starship import Starship
from get_config import config_object
import lzma, pickle

if TYPE_CHECKING:
    from scenario import Scenerio

class Engine:

    game_data: GameData

    def __init__(self, 
        player: Starship, 
        filename: str,
        easy_aim: bool,
        easy_navigation: bool,
        easy_warp:bool,
        torpedo_warning: bool,
        crash_warning: bool
    ):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        self.screen_width = config_object.screen_width
        self.screen_height = config_object.screen_height

        self.easy_aim = easy_aim
        self.easy_navigation = easy_navigation
        self.easy_warp = easy_warp
        self.torpedo_warning = torpedo_warning
        self.crash_warning = crash_warning
        
        self.filename = filename

        self.lookup_table:Dict[Coords,Tuple[Coords]] = {}
        
    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)

    def handle_enemy_turns(self):

        for entity in self.game_data.all_enemy_ships:

            if entity.sector_coords == self.player.sector_coords and entity.ai and entity.ship_status.is_active:
                entity.ai.perform()
                entity.repair()
                
        self.game_data.set_condition()
        self.game_data.update_mega_sector_display()

    def get_lookup_table(self, *, direction_x:float, direction_y:float, normalise_direction:bool=True):

        origin_tuple = Coords(direction_x, direction_y)
        
        try:
            return self.lookup_table[(origin_tuple, normalise_direction)]
        except KeyError:
            
            new_coords_x, new_coords_y = Coords(x=direction_x, y=direction_y).normalize() if normalise_direction else (direction_x, direction_y)

            def create_tuple():

                old_x, old_y = new_coords_x, new_coords_y
                old_c = None
                for r in range(config_object.max_move_distance):

                    c:Coords = Coords(round(old_x), round(old_y))

                    if not old_c or c != old_c:
                        yield c
                    
                    old_c = c
                    old_x += new_coords_x
                    old_y += new_coords_y
            
            t = tuple(create_tuple())

            self.lookup_table[(origin_tuple, normalise_direction)] = t

            return t