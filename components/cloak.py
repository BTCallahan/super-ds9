from __future__ import annotations
from typing import TYPE_CHECKING
from components.starship_system import StarshipSystem

from data_globals import CloakStatus

if TYPE_CHECKING:
    from starship import Starship

class Cloak(StarshipSystem):
        
    def __init__(self) -> None:
        super().__init__("Cloak:")
            
        self.cloak_status = CloakStatus.INACTIVE
        self.cloak_cooldown = 0
    
    @property
    def get_cloak_power(self):
        return self.starship.ship_class.cloak_strength * self.get_effective_value
    
    @property
    def ship_can_cloak(self):
        return self.is_opperational and self.cloak_cooldown < 1
    
    @property
    def cloak_is_turned_on(self):
        return self.cloak_status != CloakStatus.INACTIVE
    
    @property
    def get_energy_cost_per_turn(self):
        return self.starship.power_generator.get_max_energy * 0.005 if self.cloak_is_turned_on and self.is_opperational else 0
    
    def force_fire_decloak(self):
        if self.cloak_is_turned_on:
            
            self.cloak_cooldown = self.starship.ship_class.cloak_cooldown
            self.cloak_status = CloakStatus.INACTIVE
            return True
        return False
    
    def handle_cooldown_and_status_recovery(self):
        
        if self.cloak_is_turned_on:
            if self.is_opperational:
                if self.cloak_status == CloakStatus.COMPRIMISED:
                    self.cloak_status = CloakStatus.ACTIVE
            else:
                self.cloak_status = CloakStatus.COMPRIMISED
        
        if self.cloak_cooldown > 0:
        
            self.cloak_cooldown -= 1
        
            if self.cloak_cooldown == 0 and self.starship.is_controllable:
        
                self.starship.game_data.engine.message_log.add_message(
                    f"The cloaking device is ready, {self.starship.game_data.player.nation.captain_rank_name}."
                )
    