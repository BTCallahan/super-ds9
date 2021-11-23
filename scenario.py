from math import floor
from typing import Dict, Tuple
from random import randint

class Scenerio:

    def __init__(self, *,
    hostile_ships:Dict[str:Tuple[int,int]],
    number_of_stars:int, percent_of_friendly_planets:float,
    default_ship_name:str, default_captain_name:str,
    self_destruct_code:str,
    your_ship:str,
    your_nation:str,
    enemy_nation:str
    ) -> None:
        self.your_ship = your_ship
        self.hostile_ships = hostile_ships
        self.number_of_stars = number_of_stars
        self.percent_of_friendly_planets = percent_of_friendly_planets
        self.default_ship_name = default_ship_name
        self.default_captain_name = default_captain_name
        self.self_destruct_code = self_destruct_code,
        self.your_nation=your_nation
        self.enemy_nation=enemy_nation

    def generate_ship_numbers(self):

        return {k:randint(v[0], v[1]) for k,v in self.hostile_ships.items()}



days_not_leap_year = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)
days_leap_year = month_ = (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30)

def stardate(year:int, month:int, day:int, hour:int, minute:int, second:int):

    yr = year % 100

    star_date_ = floor(yr * 365.25)

    is_leap_year = yr % 4 == 0

    star_date_ += days_leap_year[month] if is_leap_year else days_not_leap_year[month]

    star_date_ += day

    star_date_ += ((hour * 60 * 60) + (minute * 60) + second) / (24 * 60 * 60)

    return 100000 * star_date_ / 36525

    

    



