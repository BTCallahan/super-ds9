from typing import TYPE_CHECKING, Dict, Iterable, List
from components.starship_system import StarshipSystem

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
            self.torpedo_loaded = self.torps.keys()[0]
        except IndexError:
            self.torpedo_loaded = ALL_TORPEDO_TYPES["NONE"]
    
    @property
    def get_most_powerful_torp_avaliable(self):
        
        torps = [t for t,v in self.torps.items() if v]
        
        torps.sort(key=lambda a: a.damage)
        
        return torps[0]
    
    @property
    def get_total_number_of_torpedos(self):
        
        return sum(self.torps.values())

    def restock_torps(self, torpedo:Torpedo, amount:int):
        
        space = self.starship.ship_class.max_torpedos - self.get_total_number_of_torpedos
        
        if space >= amount:
            
            self.torps[torpedo] += amount
        
    
    