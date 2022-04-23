from __future__ import annotations
from typing import TYPE_CHECKING
from components.starship_system import StarshipSystem

if TYPE_CHECKING:
    from ship_class import ShipClass

class Scanner(StarshipSystem):
    
    def __init__(self) -> None:
        
        super().__init__("Scanner:")

    @property
    def get_range(self):
        return self.starship.ship_class.scanner_range * self.get_effective_value
