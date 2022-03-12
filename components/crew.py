from __future__ import annotations
from math import ceil, floor
from typing import TYPE_CHECKING, Counter
from components.starship_system import StarshipSystem

from global_functions import scan_assistant

if TYPE_CHECKING:
    from ship_class import ShipClass
    from nation import Nation

class Crew(StarshipSystem):
        
    def __init__(self, ship_class:ShipClass) -> None:
        super().__init__("Life Support:")
        
        self.turn_without_lifesupport = 0

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
        
        p = percentage_of_injured_crew * self.get_effective_value
        
        heal_crew = min(self.injured_crew, ceil(self.injured_crew * p) + minimal_crew_to_heal)
        self.able_crew+= heal_crew
        self.injured_crew-= heal_crew
    
    def injuries_and_deaths(self, injured:int, killed_outright:int, killed_in_sickbay:int):
        
        self.able_crew -= injured + killed_outright
        self.injured_crew += injured - killed_in_sickbay
    
    def on_turn(self):
        
        if not self.is_opperational:
            
            self.turn_without_lifesupport += 1
            
            if self.turn_without_lifesupport > 10:
                
                crew_death = floor(self.turn_without_lifesupport / 10)
                
                total_crew = self.able_crew + self.injured_crew
                
                able_crew_percentage = self.able_crew / total_crew
                
                able_crew_deaths = min(round(crew_death * able_crew_percentage), self.able_crew)
                
                injured_crew_deaths = min(crew_death - able_crew_deaths, self.injured_crew)
                
                total_crew_deaths = able_crew_deaths + injured_crew_deaths
                
                if total_crew_deaths:
                
                    self.injuries_and_deaths(0, able_crew_deaths, injured_crew_deaths)
                
                    if self.starship.is_controllable:
                        
                        m = "members" if total_crew_deaths > 0 else "member"
                        
                        self.starship.game_data.engine.message_log.add_message(
                            f"{total_crew_deaths} crew {m} have died from enviromental exposure."
                        )
        
        elif self.turn_without_lifesupport > 0:
            
            self.turn_without_lifesupport -= 1