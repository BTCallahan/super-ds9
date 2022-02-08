from __future__ import annotations

from coords import Coords, AnyCoords
from typing import Dict, Tuple, TYPE_CHECKING
import lzma, pickle
from data_globals import STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
from message_log import MessageLog
from get_config import CONFIG_OBJECT

if TYPE_CHECKING:
    from game_data import GameData

from starship import Starship

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
        self.screen_width = CONFIG_OBJECT.screen_width
        self.screen_height = CONFIG_OBJECT.screen_height

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

        for entity in self.game_data.all_other_ships:
            
            if not entity.ship_status.is_active:
                continue
            
            try:
                entity.cloak.handle_cooldown_and_status_recovery()
            except AttributeError:
                pass
            
            try:
                entity.sensors.detect_all_enemy_cloaked_ships_in_system()
            except AttributeError:
                pass

            #if entity.sector_coords == self.player.sector_coords and entity.ai and entity.ship_status.is_active:
                        
            entity.ai.perform()
            entity.handle_repair_and_energy_consumption()
        
        game_data = self.game_data
        
        game_data.ships_in_same_sub_sector_as_player = game_data.grab_ships_in_same_sub_sector(
            game_data.player, accptable_ship_statuses={
                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
            }
        )
        game_data.visible_ships_in_same_sub_sector_as_player = [
            ship for ship in game_data.ships_in_same_sub_sector_as_player if ship.ship_status.is_visible
        ]
        
        selected_ship_planet_or_star = self.game_data.selected_ship_planet_or_star
        
        if isinstance(
            selected_ship_planet_or_star, Starship
        ) and not selected_ship_planet_or_star.ship_status.is_visible:
        
            self.game_data.selected_ship_planet_or_star = None
        
        self.game_data.set_condition()
        self.game_data.update_mega_sector_display()

    def get_lookup_table(
        self, *, direction_x:float, direction_y:float, normalise_direction:bool=True, no_dups:bool=True
    ):
        origin_tuple = Coords(direction_x, direction_y)
        
        try:
            return self.lookup_table[(origin_tuple, normalise_direction, no_dups)]
        except KeyError:
            
            new_coords_x, new_coords_y = Coords(x=direction_x, y=direction_y).normalize() if normalise_direction else (direction_x, direction_y)

            def create_tuple():

                old_x, old_y = new_coords_x, new_coords_y
                old_c = None
                for r in range(CONFIG_OBJECT.max_distance):

                    c:Coords = Coords(round(old_x), round(old_y))

                    if not no_dups or (not old_c or c != old_c):
                        yield c
                    
                    old_c = c
                    old_x += new_coords_x
                    old_y += new_coords_y
            
            t = tuple(create_tuple())

            self.lookup_table[(origin_tuple, normalise_direction, no_dups)] = t

            return t