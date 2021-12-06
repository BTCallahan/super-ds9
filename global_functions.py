from math import floor, pi, sin, cos, atan2
from typing import Final, Pattern
import re
from coords import IntOrFloat

#-----------Gameplay related-----------

to_rads: Final = (pi / 180)
"""To convert a number in degrees to radians, multiply by this number. To convert a number in radians to degrees, divide it by this number. 
"""

def getRads(h:float):
    return (h % 360) * to_rads

def headingToCoordsTorp(heading, distance):
    rads = (heading % 360) * to_rads
    return round(sin(rads) * distance), round(cos(rads) * distance)

def headingToDirection(heading:float, *, heading_is_rads:bool=False):
    rads = heading if heading_is_rads else ((heading % 360) * to_rads)
    return sin(rads), cos(rads)

def headingToCoords(heading:IntOrFloat, distance:int, startX:int, startY:int, max_x:int, max_y:int, *, heading_is_rads:bool=False):
    """Takes a heading, distance, and start coords for x and y

    Args:
        heading ([type]): [description]
        distance ([type]): [description]
        startX ([type]): [description]
        startY ([type]): [description]
        use_rads (bool, optional): If this is True, . Defaults to False.

    Returns:
        [type]: [description]
    """
    rads = heading if heading_is_rads else ((heading % 360) * to_rads)
    retX, retY = startX, startY

    for d in range(distance + 1):
        new_x = round(sin(rads) * d) + startX
        new_y = round(cos(rads) * d) + startY

        if not (0 < new_x < max_x) or (0 < new_y < max_y):
            break

        retX, retY = new_x, new_y
        
        #if retX not in rangeX or retY not in rangeY:
        #    return retX, retY
    return retX, retY

#------- ui related --------

beam_chars: Final = ('|', '/', '-', '\\', '|', '/', '-', '\\')

def getBeamChar(x, y):
    m = atan2(x / y) * 4 / pi
    return beam_chars[floor(m)]

def safe_division(n:IntOrFloat, d:IntOrFloat, return_number:IntOrFloat=0.0):
    if d == 0.0:
        return return_number
    return n / d

def get_first_group_in_pattern(text_to_search:str, pattern:Pattern[str],*, return_aux_if_no_match:bool=False, aux_valute_to_return_if_no_match=None):
    
    match = pattern.search(text_to_search)
    
    if return_aux_if_no_match:
        try:
            return match.group(1)
        except AttributeError:
            return aux_valute_to_return_if_no_match
        
    return match.group(1)