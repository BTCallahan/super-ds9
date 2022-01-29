from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship_class import ShipClass

from components.starship_system import StarshipSystem

class ImpulseEngine(StarshipSystem):
        
    def __init__(self) -> None:
        super().__init__("Impulse Engine:")

    @property
    def get_max_speed(self):
        return 8 * self.get_effective_value
    
    @property
    def get_dodge_factor(self):
        return self.starship.ship_class.evasion * self.get_effective_value
        