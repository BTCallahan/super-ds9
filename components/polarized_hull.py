from __future__ import annotations
from typing import TYPE_CHECKING
from math import sqrt

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
        self._polarization_amount = shipclass.polarized_hull
    
    @property
    def polarization_amount(self):
        return self._polarization_amount

    @polarization_amount.setter
    def polarization_amount(self, value):
        self._polarization_amount = round(value)
        if self._polarization_amount < 0:
            self._polarization_amount = 0
        elif self._polarization_amount > self.starship.ship_class.polarized_hull:
            self._polarization_amount = self.starship.ship_class.polarized_hull
    
    @property
    def calculate_polarization_strength(self):
        
        return self._polarization_amount * self.get_effective_value
    
    def determin_polarization_strength(self, precision:int, effective_value:bool=True):
        
        return self._polarization_amount * self.get_info(precision, effective_value=effective_value)
    
    @property
    def read_polarization(self):
        return self._polarization_amount if self.is_opperational and self.is_polarized else 0
    
    @property
    def get_energy_cost_per_turn(self):
        try:
            is_cloaked = self.starship.cloak.cloak_is_turned_on
        except AttributeError:
            is_cloaked = False
            
        return self._polarization_amount * 0.05 if self.is_polarized and self.is_opperational and not is_cloaked else 0