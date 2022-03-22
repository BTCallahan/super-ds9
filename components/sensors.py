from __future__ import annotations
from random import uniform
from typing import TYPE_CHECKING
from data_globals import STATUS_CLOAKED, CloakStatus
from get_config import CONFIG_OBJECT

if TYPE_CHECKING:
    from starship import Starship

from components.starship_system import StarshipSystem

class Sensors(StarshipSystem):
    
    def __init__(self):
        super().__init__("Sensors:")
    
    @property
    def determin_precision(self):
        """Takes the effective value of the ships sensor system and returns an intiger value based on it. This
        intiger is passed into the scanAssistant function that is used for calculating the precision when 
        scanning another ship. If the sensors are heavly damaged, their effective 'resoultion' drops. Say their 
        effective value is 0.65. This means that this function will return 25. 
        
        Returns:
            int: The effective value that is used for 
        """
        getEffectiveValue = self.get_effective_value

        if getEffectiveValue >= 1.0:
            return 1
        if getEffectiveValue >= 0.99:
            return 2
        if getEffectiveValue >= 0.95:
            return 5
        if getEffectiveValue >= 0.9:
            return 10
        if getEffectiveValue >= 0.8:
            return 15
        if getEffectiveValue >= 0.7:
            return 20
        if getEffectiveValue >= 0.6:
            return 25
        if getEffectiveValue >= 0.5:
            return 50
        if getEffectiveValue >= 0.4:
            return 100
        
        return 200 if getEffectiveValue >= 0.3 else 500
    
    @property
    def get_targeting_power(self):
        return self.starship.ship_class.targeting * self.get_effective_value
    
    def detect_all_enemy_cloaked_ships_in_system(self):
        
        if not self.is_opperational:
            return
        
        # can't detect while at warp!
        try:
            if self.starship.warp_drive.is_at_warp:
                return
        except AttributeError:
            pass
        
        allied_nations = self.starship.game_data.scenerio.get_set_of_allied_nations
        
        is_on_players_side = self.starship.nation in allied_nations
        
        nations = allied_nations if is_on_players_side else self.starship.game_data.scenerio.get_set_of_enemy_nations
        
        ships_in_same_system = self.starship.game_data.grab_ships_in_same_sub_sector(
            self.starship, accptable_ship_statuses={STATUS_CLOAKED}
        )
        cloaked_enemy_ships = [
            ship for ship in ships_in_same_system if ship.nation in nations
        ]
        player = self.starship.game_data.player
        
        for ship in cloaked_enemy_ships:
            
            detected = True
            
            detection_strength = self.starship.ship_class.detection_strength * self.get_effective_value
            
            cloak_strength = ship.get_cloak_power

            for i in range(CONFIG_OBJECT.chances_to_detect_cloak):

                if uniform(
                    0.0, detection_strength
                ) < uniform(
                    0.0, cloak_strength
                ):
                    detected = False
                    break
                
            if detected:
                
                ship.cloak.cloak_status = CloakStatus.COMPRIMISED
                
                if player.sector_coords == self.starship.sector_coords:
                    
                    cr = player.nation.captain_rank_name
                    
                    self.starship.game_data.engine.message_log.add_message(
f'{f"{cr}, we have" if self is player else f"The {self.name} has"} detected {"us" if ship is player else ship.name}!'
                    )
    
    def detect_cloaked_ship(self, ship:Starship):
        if ship.cloak.cloak_status != CloakStatus.ACTIVE:
            raise AssertionError(f"The ship {self.starship.name} is atempting to detect the ship {ship.name}, even though {ship.name} is not cloaked.")

        if not self.is_opperational:
            return False
        
        detected = True
        
        detection_strength = self.starship.ship_class.detection_strength * self.get_effective_value
        
        cloak_strength = ship.get_cloak_power

        for i in range(CONFIG_OBJECT.chances_to_detect_cloak):

            if uniform(
                0.0, detection_strength
            ) < uniform(
                0.0, cloak_strength
            ):
                detected = False
                break
            
        player = self.starship.game_data.player
        
        if detected and player.sector_coords == self.starship.sector_coords:
            
            cr = player.nation.captain_rank_name
            
            self.starship.game_data.engine.message_log.add_message(
f'{f"{cr}, we have" if self is player else f"The {self.name} has"} detected {"us" if ship is player else ship.name}!'
            )
        return detected
