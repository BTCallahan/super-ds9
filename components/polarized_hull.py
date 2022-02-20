from __future__ import annotations
from typing import TYPE_CHECKING
from math import ceil

from components.starship_system import StarshipSystem

if TYPE_CHECKING:
    from ship_class import ShipClass

class PolarizedHull(StarshipSystem):
    """The polarized hull is a pre-shields system used to reduce damage.

    new damage = max(square root(get_max_effective_polarized_hull) - damage, 0)
    """
    
    def __init__(self, shipclass:ShipClass) -> None:
        super().__init__("Polarized Hull:")
        
        self.is_polarized = True
        self.polarization_amount = shipclass.polarized_hull
    
    @property
    def get_polarized_hull(self):
        return self.starship.ship_class.polarized_hull

    @property
    def get_max_effective_polarized_hull(self):
        return ceil(self.starship.ship_class.polarized_hull * self.get_effective_value)
    
    def determin_max_effective_polarized_hull(self, precision:int, effective_value=True):
        return ceil(
            self.starship.ship_class.polarized_hull * self.get_info(precision, effective_value=effective_value) 
        )
    
    @property
    def get_actual_value(self):
        return min(self.polarization_amount, self.get_max_effective_polarized_hull)
    
    @property
    def get_energy_cost_per_turn(self):
        try:
            is_cloaked = self.starship.cloak.cloak_is_turned_on
        except AttributeError:
            is_cloaked = False
            
        return self.get_actual_value * 0.01 if self.is_polarized and self.is_opperational and is_cloaked else 0