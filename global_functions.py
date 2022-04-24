from datetime import datetime
from math import floor, pi, sin, cos, atan2, exp
from typing import Final, Iterable, Optional, Pattern
from coords import IntOrFloat
from decimal import Decimal

#-----------Gameplay related-----------

TO_RADIANS: Final = (pi / 180)
"""To convert a number in degrees to radians, multiply by this number. To convert a number in radians to degrees, divide it by this number. 
"""

def get_rads(h:float):
    return (h % 360) * TO_RADIANS

def heading_to_coords_torp(heading, distance):
    rads = (heading % 360) * TO_RADIANS
    return round(sin(rads) * distance), round(cos(rads) * distance)

def heading_to_direction(heading:float, *, heading_is_rads:bool=False):
    rads = heading if heading_is_rads else ((heading % 360) * TO_RADIANS)
    return sin(rads), cos(rads)

def heading_to_coords(
    heading:IntOrFloat, distance:int, startX:int, startY:int, max_x:int, max_y:int, *, heading_is_rads:bool=False
):
    """Takes a heading, distance, and start coords for X and Y values and calculates the ending position

    Args:
        heading (IntOrFloat): [description]
        distance (int): [description]
        startX (int): [description]
        startY (int): [description]
        heading_is_rads (bool, optional): If this is True, the ehading will not be coverted from degrees to radians. Defaults to False.

    Returns:
        Tuple[int, int]: A tuple containg two intigers for the X and Y coodinates
    """
    rads = heading if heading_is_rads else ((heading % 360) * TO_RADIANS)
    retX, retY = startX, startY

    for d in range(distance + 1):
        new_x = round(sin(rads) * d) + startX
        new_y = round(cos(rads) * d) + startY

        if not (0 <= new_x < max_x) or not (0 <= new_y < max_y):
            break

        retX, retY = new_x, new_y
        
        #if retX not in rangeX or retY not in rangeY:
        #    return retX, retY
    return retX, retY

def inverse_square_law(base:float, distance:float):
    return base / (4 * pi * pow(distance, 2))

#------- ui related --------

beam_chars: Final = ('|', '/', '-', '\\', '|', '/', '-', '\\')

def getBeamChar(x, y):
    m = atan2(x / y) * 4 / pi
    return beam_chars[floor(m)]

def safe_division(n:IntOrFloat, d:IntOrFloat, return_number:IntOrFloat=0.0):
    if d == 0.0:
        return return_number
    return n / d

def average(iter:Iterable[float]):
    
    return sum(iter) / len(iter)

# pattern getter

def get_first_group_in_pattern(
    text_to_search:str, pattern:Pattern[str],
    *, 
    return_aux_if_no_match:bool=False, 
    aux_valute_to_return_if_no_match=None,
    type_to_convert_to:type=str,
    error_type_to_raise:type[BaseException]=AttributeError,
    error_message:str=""
):
    match = pattern.search(text_to_search)
    
    if return_aux_if_no_match:
        try:
            r = type_to_convert_to(match.group(1))
            return r
        except AttributeError:
            return aux_valute_to_return_if_no_match
    if match is None:
        raise error_type_to_raise(error_message)
    r = type_to_convert_to(match.group(1))
    return r

def get_varrying_number_of_groups_in_pattern(
    text_to_search:str, pattern:Pattern[str],*, 
    return_aux_if_no_match:bool=False, aux_valute_to_return_if_no_match=None,
    type_to_convert_to:type=str, multiple_types_to_convert_to:Optional[Iterable[type]]=None,
    error_type_to_raise:type[BaseException]=AttributeError,
    error_message:str="", split_char=","
):
    match = pattern.search(text_to_search)
    
    if return_aux_if_no_match:
        try:
            r = match.group(1)
            
            rs = r.split(split_char)
            
            if multiple_types_to_convert_to:
            
                conversion_types:Iterable[type] = multiple_types_to_convert_to * len(rs)
                
                rsc = [
                    c(re) for re, c in zip(rs, conversion_types)
                ]
                return rsc
            else:
                rsc = [
                    type_to_convert_to(re) for re in rs
                ]
                return rsc
            
        except AttributeError:
            return aux_valute_to_return_if_no_match
        
    if match is None:
        raise error_type_to_raise(error_message)
    
    r = match.group(1)
    
    if r is None:
        raise error_type_to_raise(error_message)
            
    rs = r.split(split_char)
    
    if multiple_types_to_convert_to:
    
        conversion_types:Iterable[type] = multiple_types_to_convert_to * len(rs)
        
        rsc = [
            c(re) for re, c in zip(rs, conversion_types)
        ]
        return rsc
    else:
        rsc = [
            type_to_convert_to(re) for re in rs
        ]
        return rsc
        
def get_multiple_groups_in_pattern(
    text_to_search:str, pattern:Pattern[str],*, expected_number_of_groups:int=1, 
    return_aux_if_no_match:bool=False, aux_valute_to_return_if_no_match=None,
    type_to_convert_to:type=str, multiple_types_to_convert_to:Optional[Iterable[type]]=None
):
    match = pattern.search(text_to_search)
    
    if return_aux_if_no_match:
        try:
            ma = tuple(
                ty(match.group(grp + 1)) for grp, ty in enumerate(multiple_types_to_convert_to)
                
            ) if multiple_types_to_convert_to is not None else tuple(
                
                type_to_convert_to(match.group(grp)) for grp in range(1, expected_number_of_groups + 1)
            )
            if expected_number_of_groups > 0:
                assert len(ma) == expected_number_of_groups
            return ma
            #return tuple(match.group(grp) for grp in range(1, number_of_groups + 1))
        except AttributeError:
            return aux_valute_to_return_if_no_match
        except IndexError:
            return aux_valute_to_return_if_no_match
    
    ma = tuple(
        ty(match.group(grp + 1)) for grp, ty in enumerate(multiple_types_to_convert_to)
    ) if multiple_types_to_convert_to is not None else tuple(
        type_to_convert_to(match.group(grp)) for grp in range(1, expected_number_of_groups + 1)
    )
    if expected_number_of_groups > 0:
        assert len(ma) == expected_number_of_groups
    return ma
    
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

def create_date_time(stardate_:Decimal):
    # maybe I'll finish this later
    sdd = stardate_ / SD_DIV_DEC
    
    sddd = sdd / SD_MULT_DEC
    
    aju = (sddd * 36525) / 100000
    
    

def scan_assistant(v:IntOrFloat, precision:int):
    """This takes a value, v and devides it by the precision. Next, the quotent is rounded to the nearest intiger and then multiplied by the precision. The product is then returned. A lower precision value ensures more accurate results. If precision is 1, then v is returned

    E.g.:
    v = 51.25
    p = 25

    round(51.25 / 25) * 25
    round(2.41) * 25
    2 * 25
    50

    Args:
        v (IntOrFloat): The value that is modified
        precision (int): This value is used to calucalate the crecision. Lower values are more precise.

    Returns:
        int: The modified value
    """
    assert isinstance(precision, int)
    if precision == 1:
        return round(v)
    r = round(v / precision) * precision
    assert isinstance(r, float) or isinstance(r, int)
    return r

def calculate_polarization(damage:float, polarization:int):
    
    try:
        dp = exp(damage / polarization)
    except ZeroDivisionError:
        dp = 0
    
    return max((damage - polarization) + dp, dp)

def ajust_system_integrity(value:float):
    
    return 0.0 if value < 0.15 else min(1.0, value * 1.25)
