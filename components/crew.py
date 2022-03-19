from __future__ import annotations
from math import ceil, floor
from typing import TYPE_CHECKING, Dict, List
from components.starship_system import StarshipSystem
from data_globals import PRECISION_SCANNING_VALUES

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
        
        # format is Dict[nation of ship that send over boarding party, List[able boarders, injured boarders]]
        self.hostiles_on_board: Dict[Nation, List[int,int]] = {}
    
    @property
    def crew_readyness(self):
        
        return self.caluclate_crew_readyness(
            self.able_crew, self.injured_crew
        )
    
    @property
    def has_boarders(self):
        if self.hostiles_on_board:
            
            for v in self.hostiles_on_board.values():
                
                if v[0] + v[1] > 0:
                    return True
        return False
    
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

    def get_boarding_parties(self, viewer_nation:Nation, precision:int = 1):
        """This generates the number of boarding parties that the ship has

        Args:
            precision (int, optional): The precision value. 1 is best, higher values are worse. Must be an intiger that is not less then 0 and not more then 100. Defaults to 1.

        Raises:
            TypeError: Raised if precision is a float.
            ValueError: Rasied if precision is lower then 1 or higher then 100

        Yields:
            [Tuple[Nation, Tuple[int, int]]]: Tuples containing the nation, and a tuple with two intiger values
        """
        #scanAssistant = lambda v, p: round(v / p) * p
        if  isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be a intiger inbetween 1 and 100")
        if precision not in PRECISION_SCANNING_VALUES:
            raise ValueError(
f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. \
It's actually value is {precision}."
            )
        
        if precision == 1:
            
            for k,v in self.hostiles_on_board.items():
                
                yield (k, tuple(v))
        else:
            for k,v in self.hostiles_on_board.items():
                
                if k == viewer_nation:
                    
                    yield (k, tuple(v))
                else:
                    yield (k, (scan_assistant(v[0], precision), scan_assistant(v[1], precision)))
