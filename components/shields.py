from __future__ import annotations
from math import ceil
from typing import TYPE_CHECKING

from components.starship_system import StarshipSystem

if TYPE_CHECKING:
    from ship_class import ShipClass

class Shields(StarshipSystem):
        
    def __init__(self, shipclass:ShipClass) -> None:
        super().__init__("Shield Gen.:")
        
        self._shields = shipclass.max_shields
        self.shields_up = True
        
    @property
    def shields(self):
        return self._shields

    @shields.setter
    def shields(self, value):
        self._shields = round(value)
        if self._shields < 0:
            self._shields = 0
        elif self._shields > self.get_max_effective_shields:
            self._shields = self.get_max_effective_shields
        
    @property
    def get_max_shields(self):
        return self.starship.ship_class.max_shields

    @property
    def get_max_effective_shields(self):
        return ceil(self.starship.ship_class.max_shields * self.get_effective_value)
    
    @property
    def get_energy_cost_per_turn(self):
        try:
            is_cloaked = self.starship.cloak.cloak_is_turned_on
        except AttributeError:
            is_cloaked = False
            
        return self.shields * 0.01 if self.shields_up and self.is_opperational and is_cloaked else 0
    
    @property
    def shields_percentage(self):
        try:
            return self._shields / self.starship.ship_class.max_shields
        except ZeroDivisionError:
            return 0.0