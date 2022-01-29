from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship_class import ShipClass
    from starship import Starship

from components.starship_system import StarshipSystem

class PowerGenerator(StarshipSystem):
        
    def __init__(self, shipclass:ShipClass) -> None:
        
        super().__init__(
            "Warp Engine:" if shipclass.evasion > 0.0 else "Power Generator:"
        )
    
    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy = round(value)
        if self._energy < 0:
            self._energy = 0
        elif self._energy > self.starship.ship_class.max_energy:
            self._energy = self.starship.ship_class.max_energy
    
    @property
    def energy_percentage(self):
        return self._energy / self.starship.ship_class.max_energy
