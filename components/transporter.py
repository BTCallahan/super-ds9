from __future__ import annotations
from math import ceil

from components.starship_system import StarshipSystem
from get_config import CONFIG_OBJECT

class Transporter(StarshipSystem):
        
    def __init__(self) -> None:
        super().__init__("Transporter:")
    
    @property
    def get_range(self):
        return self.get_effective_value * CONFIG_OBJECT.max_move_distance
    
    @property
    def get_max_number(self):
        return ceil(self.get_effective_value * self.starship.ship_class.transporters * 6)
        