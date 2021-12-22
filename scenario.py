from collections import OrderedDict
from itertools import accumulate
from math import floor
import re
from typing import Dict, Tuple
from random import randint
from datetime import datetime
from global_functions import get_first_group_in_pattern

stars_gen = tuple(accumulate((5, 12, 20, 9, 6, 3)))

class Scenerio:

    def __init__(self, *,
                 name:str,
                 description:str,
    hostile_ships:OrderedDict[str,Tuple[int,int]],
    star_generation:Tuple[int], percent_of_friendly_planets:float,
    default_ship_name:str, default_captain_name:str,
    self_destruct_code:str,
    your_ship:str,
    your_nation:str,
    enemy_nation:str,
    your_commanding_officer:str,
    startdate:datetime,
    enddate:datetime,
    enemy_give_up_threshold:float
    ) -> None:
        self.name = name
        self.description = description
        self.your_ship = your_ship
        self.hostile_ships = hostile_ships
        self.star_generation = star_generation
        self.percent_of_friendly_planets = percent_of_friendly_planets
        self.default_ship_name = default_ship_name
        self.default_captain_name = default_captain_name
        self.self_destruct_code = self_destruct_code,
        self.your_nation=your_nation
        self.enemy_nation=enemy_nation
        self.your_commanding_officer = your_commanding_officer
        self.startdate = startdate
        self.enddate = enddate
        self.enemy_give_up_threshold = enemy_give_up_threshold
        

    def get_number_of_ships(self, ship_code:str):
        
        min_, max_ = self.hostile_ships[ship_code]
        
        return randint(min_, max_)

    def create_date_time(self):
        
        return datetime(
            year=self.startdate.year,
            month=self.startdate.month,
            day=self.startdate.day,
            hour=self.startdate.hour,
            minute=self.startdate.minute,
            second=self.startdate.second
        )

    def generate_ship_numbers(self):
        
        ordered:OrderedDict[str,int] = OrderedDict()
                
        ns = accumulate(randint(v1, v2) for v1, v2 in self.hostile_ships.values())
                
        for k,v in zip(self.hostile_ships.keys(), ns):
            ordered[k] = v

        return ordered
#scenario
scenerio_pattern = re.compile(r"SCENARIO:([\w_]+)\n([^#]+)END_SCENARIO")
name_pattern = re.compile(r"NAME:([\w\ .\-]+)\n" )

description_pattern = re.compile(r"DESCRIPTION:([a-zA-Z \.\,\?\!]+)\nDESCRIPTIONEND")
your_ship_pattern = re.compile(r"YOUR_SHIP:([a-zA-Z_]+)\n")
enemy_ships_pattern = re.compile(r"ENEMY_SHIPS:([\w\,\n]+)ENEMY_SHIPSEND")

ship_pattern = re.compile(r"([a-zA-Z_]+),(\d),(\d)\n")

default_ship_name_pattern = re.compile(r"DEFAULT_SHIP_NAME:([a-zA-Z\-\'\ ]+)\n")

default_captain_name_pattern = re.compile(r"DEFAULT_CAPTAIN_NAME:([a-zA-Z\-\'\ ]+)\n")

star_generation_pattern = re.compile(r"STAR_GENERATION:([\d\,]+)\n")

your_nation_pattern = re.compile(r"YOUR_NATION:([a-zA-Z]+)\n")
enemy_nation_pattern = re.compile(r"ENEMY_NATION:([a-zA-Z]+)\n")

your_commanding_officer_pattern = re.compile(r"YOUR_COMMANDING_OFFICER:([a-zA-Z\ \'\.\-]+)\n")

enemy_give_up_threshold_pattern = re.compile(r"ENEMY_GIVE_UP_THRESHOLD:([\d.]+)\n")

destruct_code_pattern = re.compile(r"DESTRUCT_CODE:([\d\w\-]+)\n")

start_date_pattern = re.compile(r"START_DATE_TIME:([\d]+).([\d]+).([\d]+).([\d]+).([\d]+).([\d]+)\n")
end_date_pattern = re.compile(r"END_DATE_TIME:([\d]+).([\d]+).([\d]+).([\d]+).([\d]+).([\d]+)\n")

friendly_planet_pattern = re.compile(r"FRIENDLY_PLANET_PERCENT:([\d\.]+)\n")

def create_sceneraio():
        
    with open("library/scenarios.txt") as scenario_text:
        
        contents = scenario_text.read()
        
    scenarios = scenerio_pattern.finditer(contents)
    
    scenario_dict:Dict[str,Scenerio] = {}
        
    for scenario in scenarios:
        
        scenario_code = scenario.group(1)
        
        scenario_txt = scenario.group(2)
        
        name = get_first_group_in_pattern(scenario_txt, name_pattern)
    
        description = get_first_group_in_pattern(scenario_txt, description_pattern)

        your_ship = get_first_group_in_pattern(scenario_txt, your_ship_pattern)
        
        enemy_ships = get_first_group_in_pattern(scenario_txt, enemy_ships_pattern)
        
        #e_ships:Dict[str,Tuple[int,int]] = {}
        e_ships:OrderedDict[str,Tuple[int,int]] = OrderedDict()
        
        a_ships = ship_pattern.finditer(enemy_ships)
        
        for s in a_ships:
            
            k = s.group(1)
            mi = s.group(2)
            ma = s.group(3)
            
            e_ships[k] = (int(mi), int(ma))
        
        your_nation = get_first_group_in_pattern(scenario_txt, your_nation_pattern)
        
        enemy_nation = get_first_group_in_pattern(scenario_txt, enemy_nation_pattern)
        
        your_commanding_officer = get_first_group_in_pattern(scenario_txt, your_commanding_officer_pattern)
        
        star_generation_ = get_first_group_in_pattern(scenario_txt, star_generation_pattern, return_aux_if_no_match=True)
        
        try:
            split_stars = star_generation_.split(",")
            stars_ = [int(s) for s in split_stars]
            star_generation = tuple(accumulate(stars_))
        except AttributeError:
            star_generation = stars_gen
            
        friendly_planets = get_first_group_in_pattern(scenario_txt, friendly_planet_pattern)
        
        default_ship_name = get_first_group_in_pattern(scenario_txt, default_ship_name_pattern)
        
        default_captain_name = get_first_group_in_pattern(scenario_txt, default_captain_name_pattern)
        
        enemy_give_up_threshold = get_first_group_in_pattern(
            scenario_txt, enemy_give_up_threshold_pattern, return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0.0)
        
        code = get_first_group_in_pattern(scenario_txt, destruct_code_pattern)
        
        start_date = start_date_pattern.search(scenario_txt)
        
        startdate = datetime(
            year=int(start_date.group(1)),
            month=int(start_date.group(2)),
            day=int(start_date.group(3)),
            hour=int(start_date.group(4)),
            minute=int(start_date.group(5)),
            second=int(start_date.group(6))
        )
        
        end_date = end_date_pattern.search(scenario_txt)
        
        enddate = datetime(
            year=int(end_date.group(1)),
            month=int(end_date.group(2)),
            day=int(end_date.group(3)),
            hour=int(end_date.group(4)),
            minute=int(end_date.group(5)),
            second=int(end_date.group(6))
        )
        
        scenario_dict[scenario_code] = Scenerio(
            name=name,
            your_ship=your_ship,
            your_nation=your_nation,
            enemy_nation=enemy_nation,
            star_generation=star_generation,
            description=description,
            percent_of_friendly_planets=float(friendly_planets),
            default_ship_name=default_ship_name,
            default_captain_name=default_captain_name,
            your_commanding_officer=your_commanding_officer,
            self_destruct_code=code,
            hostile_ships=e_ships,
            startdate=startdate,
            enddate=enddate,
            enemy_give_up_threshold=float(enemy_give_up_threshold)
        )
    return scenario_dict

ALL_SCENERIOS = create_sceneraio()