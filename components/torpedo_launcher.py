from __future__ import annotations
from math import ceil
from typing import TYPE_CHECKING, Dict, Iterable, List
from components.starship_system import StarshipSystem
from global_functions import scan_assistant

from torpedo import ALL_TORPEDO_TYPES

if TYPE_CHECKING:
    from ship_class import ShipClass
    from torpedo import Torpedo

def set_torps(torpedo_types_:Iterable[str], max_torps:int):
    tDict: Dict[str, int] = {}
    if not torpedo_types_:
        return tDict

    for t in torpedo_types_:
        
        tDict[t] = max_torps if t == torpedo_types_[0] else 0
        
    return tDict

class TorpedoLauncher(StarshipSystem):
        
    def __init__(self, shipclass:ShipClass) -> None:
        super().__init__("Torp. Launcher:")
                
        self.torps = {
            k : v for k,v in shipclass.torp_dict.items()
        } if shipclass.torp_dict else {}
        
        try:
            self.torpedo_loaded = tuple(self.torps.keys())[0]
        except IndexError:
            self.torpedo_loaded = ALL_TORPEDO_TYPES["NONE"]
    
    @property
    def get_most_powerful_torp_avaliable(self):
        
        torps = [t for t,v in self.torps.items() if v]
        
        torps.sort(key=lambda a: a.damage, reverse=True)
        
        t = torps[0]
        return t, self.torps[t]
    
    @property
    def get_total_number_of_torpedos(self):
        
        return sum(self.torps.values())

    def restock_torps(self, torpedo:Torpedo, amount:int):
        
        space = self.starship.ship_class.max_torpedos - self.get_total_number_of_torpedos
        
        if space >= amount:
            
            self.torps[torpedo] += amount
        
    def get_no_of_avalible_torp_tubes(self, number=0):
        if not self.is_opperational:
            return 0

        number = (
            self.starship.ship_class.torp_tubes if number == 0 else min(number, self.starship.ship_class.torp_tubes)
        )
        
        return max(1, ceil(number * self.get_effective_value))
    
    @property
    def can_fire_torpedos(self):
        
        return self.is_opperational and self.get_total_number_of_torpedos > 0
    
    def get_number_of_torpedos(self, precision:int = 1):
        """This generates the number of torpedos that the ship has @ precision - must be an intiger not less then 0 and 
        not more then 100 
        Yields tuples containing the torpedo type and the number of torpedos

        Args:
            precision (int, optional): The precision value. 1 is best, higher values are worse. Defaults to 1.

        Raises:
            TypeError: Raised if precision is a float.
            ValueError: Rasied if precision is lower then 1 or higher then 100

        Yields:
            [type]: [description]
        """
        #scanAssistant = lambda v, p: round(v / p) * p
        if  isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be a intiger inbetween 1 and 100")
        if precision not in {1, 2, 5, 10, 15, 20, 25, 50, 100, 200, 500}:
            raise ValueError(
f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. \
It's actually value is {precision}."
            )
        
        if precision == 1:
            for k,v in self.torps.items():
                yield (k, v)
        else:
            for k,v in self.torps.items():
                yield (k, scan_assistant(v, precision))
