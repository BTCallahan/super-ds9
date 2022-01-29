from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship_class import ShipClass

from components.starship_system import StarshipSystem

class Transporter(StarshipSystem):
        
    def __init__(self, shipclass:ShipClass) -> None:
        super().__init__("Transporter:")
    
    @property
    def get_range(self):
        return self.get_effective_value * 12
        