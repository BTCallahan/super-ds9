from __future__ import annotations
from math import ceil
from random import randint
from typing import TYPE_CHECKING

from global_functions import scan_assistant

if TYPE_CHECKING:
    from ship_class import ShipClass
    from starship import Starship

class Crew(StarshipSystem):
        
    def __init__(self, ship_class:ShipClass) -> None:
        super().__init__("Life Support:")
        
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
        return 0.0 if total == 0.0 else (total / self.starship.ship_class.max_crew) * 0.5 + 0.5

    @property
    def get_total_crew(self):
        return self.able_crew + self.injured_crew
    
    def heal_crew(self, percentage_of_injured_crew:float, minimal_crew_to_heal:int):
        heal_crew = min(self.injured_crew, ceil(self.injured_crew * percentage_of_injured_crew) + minimal_crew_to_heal)
        self.able_crew+= heal_crew
        self.injured_crew-= heal_crew
    
    def injuries_and_deaths(self, injured:int, killed_outright:int, killed_in_sickbay:int):
        
        self.able_crew -= injured + killed_outright
        self.injured_crew += injured - killed_in_sickbay
    
        