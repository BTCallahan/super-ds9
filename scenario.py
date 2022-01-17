from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from itertools import accumulate
from math import floor
import re
from typing import Dict, Final, List, Tuple, TYPE_CHECKING
from random import randint
from datetime import datetime
from global_functions import get_first_group_in_pattern, get_multiple_groups_in_pattern
from evaluate_player import SCENARIO_TYPES

if TYPE_CHECKING:
    from evaluate_player import ScenerioEvaluation

stars_gen = tuple(accumulate((5, 12, 20, 9, 6, 3)))

@dataclass(frozen=True)
class Scenerio:
    
    name:str
    description:str
    encounters:List[Encounter]
    star_generation:Tuple[int]
    percent_of_friendly_planets:float
    default_ship_name:str
    default_captain_name:str
    self_destruct_code:str
    your_ship:str
    your_nation:str
    enemy_nation:str
    your_commanding_officer:str
    startdate:datetime
    enddate:datetime
    enemy_give_up_threshold:float
    scenario_type:type[ScenerioEvaluation]
    victory_percent:float
    
    def create_date_time(self):
        
        return datetime(
            year=self.startdate.year,
            month=self.startdate.month,
            day=self.startdate.day,
            hour=self.startdate.hour,
            minute=self.startdate.minute,
            second=self.startdate.second
        )

#scenario
scenerio_pattern = re.compile(r"SCENARIO:([\w_]+)\n([^#]+)END_SCENARIO")
name_pattern = re.compile(r"NAME:([\w\ .\-]+)\n" )

scenario_type_pattern = re.compile(r"SCENARIO_TYPE:([\w]+)\n" )

description_pattern = re.compile(r"DESCRIPTION:([a-zA-Z \.\,\?\!]+)\nEND_DESCRIPTION")
your_ship_pattern = re.compile(r"YOUR_SHIP:([a-zA-Z_]+)\n")

encouners_pattern = re.compile(r"ENCOUNTERS:\n([\w\n\:\, \!]+)END_ENCOUNTERS")

enemy_ships_pattern = re.compile(r"    ENEMY_SHIPS:([\d]+),([\d]+)\n([a-zA-Z0-9_\n\:\, ]+?)    END_ENEMY_SHIPS\n")

ship_pattern = re.compile(r"([a-zA-Z_]+):(\d),(\d)\n")

default_ship_name_pattern = re.compile(r"DEFAULT_SHIP_NAME:([a-zA-Z\-\'\ ]+)\n")

default_captain_name_pattern = re.compile(r"DEFAULT_CAPTAIN_NAME:([a-zA-Z\-\'\ ]+)\n")

star_generation_pattern = re.compile(r"STAR_GENERATION:([\d\,]+)\n")

your_nation_pattern = re.compile(r"YOUR_NATION:([a-zA-Z]+)\n")
enemy_nation_pattern = re.compile(r"ENEMY_NATION:([a-zA-Z]+)\n")

your_commanding_officer_pattern = re.compile(r"YOUR_COMMANDING_OFFICER:([a-zA-Z\ \'\.\-]+)\n")

enemy_give_up_threshold_pattern = re.compile(r"ENEMY_GIVE_UP_THRESHOLD:([\d\.]+)\n")

victory_percent_pattern = re.compile(r"VICTORY_PERCENT:([\d\.]+)\n")

destruct_code_pattern = re.compile(r"DESTRUCT_CODE:([\w\-]+)\n")

start_date_pattern = re.compile(r"START_DATE_TIME:([\d]+).([\d]+).([\d]+).([\d]+).([\d]+).([\d]+)\n")
end_date_pattern = re.compile(r"END_DATE_TIME:([\d]+).([\d]+).([\d]+).([\d]+).([\d]+).([\d]+)\n")

friendly_planet_pattern = re.compile(r"FRIENDLY_PLANET_PERCENT:([\d\.]+)\n")

#the following is not used - yet, anyway!
enc_pattern = re.compile(r"NO_OF_ENCS:([\d]+),([\d]+)\n([\w\n\,]+)END_NO_OF_ENCS")
ship_enc_pattern = re.compile(r"SHIP:([\w]+),([\d]+),([\d]+)")

@dataclass(frozen=True)
class Encounter:
    
    min_encounters:int
    max_encounters:int
    ships:Dict[str,Tuple[int,int]]
    
    def __len__(self):
        return len(self.ships)
    
    def roll_number_of_encounters(self):
        return randint(self.min_encounters, self.max_encounters)
    
    def roll_ships_in_encouter(self):
        r = {k:randint(v[0], v[1]) for k,v in self.ships.items()}
        return r
    
    def roll_both(self):
        n, r = randint(self.min_encounters, self.max_encounters), {k:randint(v[0], v[1]) for k,v in self.ships.items()}
        
        return n, r
    
    def generate_ships(self):
        
        number_of_encounters = randint(self.min_encounters, self.max_encounters)
        
        for n in range(number_of_encounters):
            r = {k:randint(v[0], v[1]) for k,v in self.ships.items()}
            yield r

def create_sceneraio():
        
    with open("library/scenarios.txt") as scenario_text:
        
        contents = scenario_text.read()
        
    scenarios = scenerio_pattern.finditer(contents)
    
    scenario_dict:Dict[str,Scenerio] = {}
        
    for scenario in scenarios:
        
        scenario_code = scenario.group(1)
        
        scenario_txt = scenario.group(2)
        
        name = get_first_group_in_pattern(scenario_txt, name_pattern)
        
        scenario_type_ = get_first_group_in_pattern(scenario_txt, scenario_type_pattern)
        
        scenario_type = SCENARIO_TYPES[scenario_type_]
    
        description = get_first_group_in_pattern(scenario_txt, description_pattern)

        your_ship = get_first_group_in_pattern(scenario_txt, your_ship_pattern)
        
        encounters = get_first_group_in_pattern(scenario_txt, encouners_pattern)
        
        all_encounters = []
        
        for encounter in enemy_ships_pattern.finditer(encounters):
            
            min_encs = encounter.group(1)
            max_encs = encounter.group(2)
            
            ships = encounter.group(3)
            
            """
            ship_dict = {
                ship.group(1):(int(ship.group(2)), int(ship.group(3))) for ship in ship_pattern.finditer(ships)
            }
            """
            ship_dict = {}
            
            for ship in ship_pattern.finditer(ships):
                
                sh = ship.group(1)
                
                ship_min = ship.group(2)
                
                ship_max = ship.group(2)
                
                ship_dict[sh] = (
                    int(ship_min),
                    int(ship_max)
                )
            
            
            all_encounters.append(
                Encounter(
                    min_encounters=int(min_encs),
                    max_encounters=int(max_encs),
                    ships=ship_dict
                )
            )
        
        #enemy_ships = get_first_group_in_pattern(scenario_txt, enemy_ships_pattern)
        
        victory_percent = get_first_group_in_pattern(scenario_txt, victory_percent_pattern, type_to_convert_to=float)
        
        #e_ships:Dict[str,Tuple[int,int]] = {}
        """
        e_ships:OrderedDict[str,Tuple[int,int]] = OrderedDict()
        
        a_ships = ship_pattern.finditer(enemy_ships)
        
        for s in a_ships:
            
            k = s.group(1)
            min_ = s.group(2)
            max_ = s.group(3)
            
            e_ships[k] = (int(min_), int(max_))
        """
        
        your_nation = get_first_group_in_pattern(scenario_txt, your_nation_pattern)
        
        enemy_nation = get_first_group_in_pattern(scenario_txt, enemy_nation_pattern)
        
        your_commanding_officer = get_first_group_in_pattern(scenario_txt, your_commanding_officer_pattern)
        
        star_generation_ = get_first_group_in_pattern(
            scenario_txt, star_generation_pattern, return_aux_if_no_match=True
        )
        
        try:
            split_stars = star_generation_.split(",")
            
            stars_ = [int(s) for s in split_stars]
            
            star_generation = tuple(accumulate(stars_))
            
        except AttributeError:
            star_generation = stars_gen
            
        friendly_planets = get_first_group_in_pattern(scenario_txt, friendly_planet_pattern, type_to_convert_to=float)
        
        default_ship_name = get_first_group_in_pattern(scenario_txt, default_ship_name_pattern)
        
        default_captain_name = get_first_group_in_pattern(scenario_txt, default_captain_name_pattern)
        
        enemy_give_up_threshold = get_first_group_in_pattern(
            scenario_txt, enemy_give_up_threshold_pattern, 
            return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0.0, type_to_convert_to=float
        )
        
        code = get_first_group_in_pattern(scenario_txt, destruct_code_pattern)
        
        #start_date = start_date_pattern.search(scenario_txt)
        
        year, mon, day, hour, mini, sec = get_multiple_groups_in_pattern(
            scenario_txt, start_date_pattern,
            expected_number_of_groups=6,
            type_to_convert_to=int
        )
        
        startdate = datetime(
            year=year,
            month=mon,
            day=day,
            hour=hour,
            minute=mini,
            second=sec
        )
        
        #end_date = end_date_pattern.search(scenario_txt)
        
        year_, mon_, day_, hour_, mini_, sec_ = get_multiple_groups_in_pattern(
            scenario_txt, end_date_pattern,
            expected_number_of_groups=6,
            type_to_convert_to=int
        )
        
        enddate = datetime(
            year=year_,
            month=mon_,
            day=day_,
            hour=hour_,
            minute=mini_,
            second=sec_
        )
        
        scenario_dict[scenario_code] = Scenerio(
            name=name,
            your_ship=your_ship,
            your_nation=your_nation,
            enemy_nation=enemy_nation,
            star_generation=star_generation,
            description=description,
            percent_of_friendly_planets=friendly_planets,
            default_ship_name=default_ship_name,
            default_captain_name=default_captain_name,
            your_commanding_officer=your_commanding_officer,
            self_destruct_code=code,
            encounters=tuple(all_encounters),
            startdate=startdate,
            enddate=enddate,
            enemy_give_up_threshold=enemy_give_up_threshold,
            scenario_type=scenario_type,
            victory_percent=victory_percent
        )
    return scenario_dict

ALL_SCENERIOS:Final = create_sceneraio()