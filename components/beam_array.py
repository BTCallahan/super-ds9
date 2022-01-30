from __future__ import annotations
from math import ceil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship_class import ShipClass
    from starship import Starship

from components.starship_system import StarshipSystem

class BeamArray(StarshipSystem):
    
    starship:Starship
    
    def __init__(self, shipclass:ShipClass) -> None:
        super().__init__(f"{shipclass.get_energy_weapon.short_beam_name_cap}s")
        
    
    @property
    def ship_can_fire_beam_arrays(self):
        return self.starship.ship_class.ship_type_can_fire_beam_arrays and self.is_opperational
    
    @property
    def get_max_effective_beam_firepower(self):
        return ceil(self.starship.ship_class.max_beam_energy * self.get_effective_value)
    
    @property
    def get_max_beam_firepower(self):
        return self.starship.ship_class.max_beam_energy