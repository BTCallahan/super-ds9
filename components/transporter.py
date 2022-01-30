from __future__ import annotations
from typing import TYPE_CHECKING

from components.starship_system import StarshipSystem

class Transporter(StarshipSystem):
        
    def __init__(self) -> None:
        super().__init__("Transporter:")
    
    @property
    def get_range(self):
        return self.get_effective_value * 12
        