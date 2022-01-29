from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ship_class import ShipClass
    from starship import Starship

class Crew:
    
    starship:Starship
    
    def __init__(self, ship_class:ShipClass) -> None:
        
        self.able_crew = ship_class.max_crew
        self.injured_crew = 0
    
    @property
    def crew_readyness(self):
        
        return self.caluclate_crew_readyness(
            self.able_crew, self.injured_crew
        )
    
    def scan_crew_readyness(self, precision:int):
        
        return self.caluclate_crew_readyness(
            scan_assistant(self.able_crew, precision), scan_assistant(self.injured_crew, precision)
        )
    
    def caluclate_crew_readyness(self, able_crew:int, injured_crew:int):
        if self.starship.is_automated:
            return 1.0
        total = able_crew + injured_crew * 0.25
        return 0.0 if total == 0.0 else (total / self.ship_class.max_crew) * 0.5 + 0.5