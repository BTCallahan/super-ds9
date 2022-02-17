from __future__ import annotations
from typing import TYPE_CHECKING
from decimal import DivisionByZero
from math import inf

if TYPE_CHECKING:
    from starship import Starship

import colors

class StarshipSystem:
    """This handles a starship system, such as warp drives or shields.
    
    Args:
            name (str): The name of the system.
    
    """
    
    starship:Starship

    def __init__(self, name:str):
        self._integrety = 1.0
        self.name = '{: >17}'.format(name)

    @property
    def integrety(self):
        return self._integrety
    
    @integrety.setter
    def integrety(self, value:float):
        assert isinstance(value, float) or isinstance(value, int)
        self._integrety = value
        if self._integrety < 0.0:
            self._integrety = 0.0
        elif self._integrety > 1.0:
            self._integrety = 1.0

    @property
    def is_opperational(self):
        return self._integrety >= 0.15

    @property
    def get_effective_value(self):
        """Starship systems can take quite a bit of beating before they begin to show signs of reduced performance. 
        Generaly, when the systems integrety dips below 80% is when you will see performance degrade. Should integrety 
        fall below 15%, then the system is useless and inoperative.
        """
        return min(1.0, self._integrety * 1.25) if self.is_opperational else 0.0

    @property
    def is_comprimised(self):
        """Has this system taken sufficent damage in impaire is performance?

        Returns:
            bool: Returns True if its integrety times 1.25 is less then 1, False otherwise.
        """
        return self._integrety * 1.25 < 1.0

    @property
    def affect_cost_multiplier(self):
        try:
            return 1 / self.get_effective_value
        except DivisionByZero:
            return inf

    def get_info(self, precision:int, effective_value:bool, below_15_is_0:bool=True):
        
        i = min(1.0, self._integrety * 1.25) if effective_value else self._integrety
        
        if below_15_is_0 and not self.is_opperational:
            i = 0.0
        
        if precision <= 1.0 or i == 0.0 or i == 1.0:
            return i
        
        try :
            r = round(i * 100 / precision) * precision * 0.01
        except ZeroDivisionError:
            r = 0.0
        
        assert isinstance(r, float)
        return r

    def print_info(self, precision:float):
        return f"{self.get_info(precision, False):.2%}" if self.is_opperational else f"OFFLINE"

    def get_color(self):
        if not self.is_comprimised:
            return colors.alert_green
        return colors.alert_yellow if self.is_opperational else colors.alert_red