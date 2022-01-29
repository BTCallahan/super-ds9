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