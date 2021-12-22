from datetime import datetime
from math import floor, pi, sin, cos, atan2
from typing import Final, Pattern
import re
from coords import IntOrFloat
from decimal import Decimal

#-----------Gameplay related-----------

to_rads: Final = (pi / 180)
"""To convert a number in degrees to radians, multiply by this number. To convert a number in radians to degrees, divide it by this number. 
"""

def get_rads(h:float):
    return (h % 360) * to_rads

def heading_to_coords_torp(heading, distance):
    rads = (heading % 360) * to_rads
    return round(sin(rads) * distance), round(cos(rads) * distance)

def heading_to_direction(heading:float, *, heading_is_rads:bool=False):
    rads = heading if heading_is_rads else ((heading % 360) * to_rads)
    return sin(rads), cos(rads)

def heading_to_coords(
    heading:IntOrFloat, distance:int, startX:int, startY:int, max_x:int, max_y:int, *, heading_is_rads:bool=False
):
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

def get_first_group_in_pattern(
    text_to_search:str, pattern:Pattern[str],*, return_aux_if_no_match:bool=False, aux_valute_to_return_if_no_match=None
):
    
    match = pattern.search(text_to_search)
    
    if return_aux_if_no_match:
        try:
            return match.group(1)
        except AttributeError:
            return aux_valute_to_return_if_no_match
        
    return match.group(1)

def get_multiple_groups_in_pattern(
    text_to_search:str, pattern:Pattern[str],*, number_of_groups:int=1, return_aux_if_no_match:bool=False, aux_valute_to_return_if_no_match=None
):
    match = pattern.search(text_to_search)
    
    if return_aux_if_no_match:
        try:
            return tuple(match.group(grp) for grp in range(1, number_of_groups + 1))
            
        except AttributeError:
            return tuple([aux_valute_to_return_if_no_match] * number_of_groups)
        
    return tuple(match.group(grp) for grp in range(1, number_of_groups + 1))

def convert_to_color_friendly_int(s:str):
    
    i = int(s)
    
    assert 0 <= i < 256
    
    return i

DAYS_NOT_LEAP_YEAR = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)
DAYS_LEAP_YEAR = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30)

SD_MULT = 10000
SD_DIV = 1 / SD_MULT

SD_MULT_DEC = Decimal(10000)
SD_DIV_DEC = Decimal(1) / SD_MULT_DEC

def stardate(date_time:datetime):
        
    year = date_time.year
    month = date_time.month
    day = date_time.day
    hour = date_time.hour
    minute = date_time.minute
    second = date_time.second

    yr = year % 100

    star_date_ = floor(yr * 365.25)

    is_leap_year = yr % 4 == 0

    star_date_ += DAYS_LEAP_YEAR[month] if is_leap_year else DAYS_NOT_LEAP_YEAR[month]

    star_date_ += day

    star_date_ += ((hour * 60 * 60) + (minute * 60) + second) / (24 * 60 * 60)

    sd = 100000 * star_date_ / 36525

    sd_ = Decimal(sd)
    
    sd_m = sd_ * SD_MULT_DEC
    
    ret = floor(sd_m)

    dec = ret * SD_DIV_DEC

    return dec