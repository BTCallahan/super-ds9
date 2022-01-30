from __future__ import annotations
from math import ceil, floor
from typing import TYPE_CHECKING, Optional, Tuple
from components.starship_system import StarshipSystem
from coords import Coords

from data_globals import WARP_FACTOR

class WarpDrive(StarshipSystem):
        
    def __init__(self) -> None:
        super().__init__("Warp Drive")
        
        self.warp_destinations:Optional[Tuple[Coords]] = None
        self.warp_progress:float=0.0
        self.current_warp_factor:int=0
    
    def get_warp_current_warp_sector(self):
        
        try:
            return self.warp_destinations[floor(self.warp_progress)]
        except IndexError:
            return self.warp_destinations[-1]
    
    @property
    def is_at_warp(self):
        return self.current_warp_factor > 0
    
    def increment_warp_progress(self):
        self.warp_progress += WARP_FACTOR[self.current_warp_factor][0]
    
    @property
    def max_warp_speed(self):
        return ceil(self.get_effective_value * 9)