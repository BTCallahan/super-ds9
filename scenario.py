from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache, cached_property
from itertools import accumulate
from math import floor
import re
from typing import Dict, Final, FrozenSet, Optional, Pattern, Tuple, TYPE_CHECKING
from random import randint
from datetime import datetime
from frozendict import frozendict
from global_functions import get_first_group_in_pattern, get_multiple_groups_in_pattern
from evaluate_player import SCENARIO_TYPES
from nation import ALL_NATIONS, Nation
from ship_class import ALL_SHIP_CLASSES, ShipClass

if TYPE_CHECKING:
    from evaluate_player import ScenerioEvaluation

stars_gen = tuple(accumulate((5, 12, 20, 9, 6, 3)))

@dataclass(frozen=True)
class Scenerio:
    
    name:str
    description:str
    enemy_encounters:Tuple[Encounter]
    allied_encounters:Tuple[Encounter]
    mission_critical_ships:FrozenSet[ShipClass]
    star_generation:Tuple[int]
    percent_of_friendly_planets:float
    default_ship_name:str
    default_captain_name:str
    self_destruct_code:str
    your_ship:ShipClass
    your_nation:Nation
    allied_nations:Optional[Tuple[Nation]]
    main_enemy_nation:Nation
    other_enemy_nations:Optional[Tuple[Nation]]
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
    
    @cached_property
    def get_all_enemy_nation(self):
        if self.other_enemy_nations:
            return tuple(
                [self.main_enemy_nation] + list(self.other_enemy_nations)
            )
        return tuple([self.main_enemy_nation])

    @cached_property
    def get_all_allied_nations(self):
        if self.allied_nations:
            return tuple(
                [self.your_nation] + list(self.allied_nations)
            )
        return tuple([self.your_nation])
    
    @cached_property
    def get_set_of_enemy_nations(self):
        return frozenset(self.get_all_enemy_nation)
    
    @cached_property
    def get_set_of_allied_nations(self):
        return frozenset(self.get_all_allied_nations)

@dataclass(frozen=True)
class Encounter:
    
    min_encounters:int
    max_encounters:int
    ships:frozendict[str,Tuple[int,int]]
    
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
        """Yeilds dictionaries consisting of a string keys and int values.

        Yields:
            Dict[str,int]: A dictionary consisting of string keys and int values. The string is the key of the ship class, and the int is the number of ships that will be generated.
        """
        
        number_of_encounters = randint(self.min_encounters, self.max_encounters)
        
        for n in range(number_of_encounters):
            r = {k:randint(v[0], v[1]) for k,v in self.ships.items()}
            yield r

def create_sceneraio():
    
    scenerio_pattern = re.compile(r"SCENARIO:([\w_]+)\n([^#]+)END_SCENARIO")
    name_pattern = re.compile(r"NAME:([\w\ .\-]+)\n" )

    scenario_type_pattern = re.compile(r"SCENARIO_TYPE:([\w]+)\n" )

    description_pattern = re.compile(r"DESCRIPTION:([a-zA-Z \.\,\?\!]+)\nEND_DESCRIPTION")
    your_ship_pattern = re.compile(r"YOUR_SHIP:([a-zA-Z_]+)\n")

    enemy_encounters_pattern = re.compile(r"ENEMY_ENCOUNTERS:\n([\w\n\:\, \!]+)END_ENEMY_ENCOUNTERS")

    enemy_ships_pattern = re.compile(r"    ENEMY_SHIPS:([\d]+),([\d]+)\n([a-zA-Z0-9_\n\:\, ]+?)    END_ENEMY_SHIPS\n")

    allied_encounters_pattern = re.compile(r"ALLIED_ENCOUNTERS:\n([\w\n\:\, \!]+)END_ALLIED_ENCOUNTERS")

    allied_ships_pattern = re.compile(r"    ALLIED_SHIPS:([\d]+),([\d]+)\n([a-zA-Z0-9_\n\:\, ]+?)    END_ALLIED_SHIPS\n")

    ship_pattern = re.compile(r"([a-zA-Z_]+):(\d),(\d)\n")

    mission_critical_ships_pattern = re.compile(r"MISSION_CRITICAL_SHIPS:([\w,]+)")

    default_ship_name_pattern = re.compile(r"DEFAULT_SHIP_NAME:([a-zA-Z\-\'\ ]+)\n")

    default_captain_name_pattern = re.compile(r"DEFAULT_CAPTAIN_NAME:([a-zA-Z\-\'\ ]+)\n")

    star_generation_pattern = re.compile(r"STAR_GENERATION:([\d\,]+)\n")

    your_nation_pattern = re.compile(r"YOUR_NATION:([a-zA-Z_]+)\n")
    allied_nations_pattern = re.compile(r"ALLIED_NATIONS:([a-zA-Z_,]+)\n")
    enemy_nation_pattern = re.compile(r"MAIN_ENEMY_NATION:([a-zA-Z_]+)\n")
    other_enemy_nations_pattern = re.compile(r"OTHER_ENEMY_NATIONS:([a-zA-Z_,]+)\n")

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
        
    with open("library/scenarios.txt") as scenario_text:
        
        contents = scenario_text.read()
        
    scenarios = scenerio_pattern.finditer(contents)
    
    scenario_dict:Dict[str,Scenerio] = {}
        
    for scenario in scenarios:
        
        scenario_code = scenario.group(1)
        
        scenario_txt = scenario.group(2)
        
        name = get_first_group_in_pattern(
            scenario_txt, name_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'NAME_LONG:'"
        )
        scenario_type_ = get_first_group_in_pattern(
            scenario_txt, scenario_type_pattern, 
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'SCENARIO_TYPE:'"
        )
        scenario_type = SCENARIO_TYPES[scenario_type_]
    
        description = get_first_group_in_pattern(
            scenario_txt, description_pattern, 
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'DESCRIPTION:'"
        )
        your_ship_ = get_first_group_in_pattern(
            scenario_txt, your_ship_pattern, 
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'YOUR_SHIP:'"
        )
        your_ship = ALL_SHIP_CLASSES[your_ship_]
        
        _mission_critical_ships = get_first_group_in_pattern(
            scenario_txt, mission_critical_ships_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'MISSION_CRITICAL_SHIPS:'"
        )
        _t_mission_critical_ships = _mission_critical_ships.split(",")
        
        mission_critical_ships = frozenset([
            ALL_SHIP_CLASSES[ship] for ship in _t_mission_critical_ships
        ])
        
        def create_encounters(en_ship_pattern:Pattern[str], encounters_text_block:str):
            
            for encounter in en_ship_pattern.finditer(encounters_text_block):
            
                min_encs = encounter.group(1)
                max_encs = encounter.group(2)
                
                ships = encounter.group(3)
                
                ship_dict = {}
                
                for ship in ship_pattern.finditer(ships):
                
                    sh = ship.group(1)
                    
                    ship_min = ship.group(2)
                    
                    ship_max = ship.group(3)
                    
                    ship_dict[sh] = (
                        int(ship_min),
                        int(ship_max)
                    )   
                fd = frozendict(
                    ship_dict
                )
                yield Encounter(
                    min_encounters=int(min_encs),
                    max_encounters=int(max_encs),
                    ships=fd
                )
        
        enemy_encounters = get_first_group_in_pattern(
            scenario_txt, enemy_encounters_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'ENEMY_ENCOUNTERS:'"
        )
        all_enemy_encounters = tuple(
            create_encounters(enemy_ships_pattern, enemy_encounters)
        )
        allied_encounters = get_first_group_in_pattern(
            scenario_txt, allied_encounters_pattern, return_aux_if_no_match=True
        )
        all_allied_encounters = tuple(
            create_encounters(allied_ships_pattern, allied_encounters)
        ) if allied_encounters else tuple()
        
        victory_percent = get_first_group_in_pattern(
            scenario_txt, victory_percent_pattern, type_to_convert_to=float,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'VICTORY_PERCENT:'"
        )
        your_nation_ = get_first_group_in_pattern(
            scenario_txt, your_nation_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'YOUR_NATION:'"
        )
        your_nation = ALL_NATIONS[your_nation_]
        
        allied_nations_:str = get_first_group_in_pattern(
            scenario_txt, allied_nations_pattern, return_aux_if_no_match=True
        )
        try:
            allied_nations__ = allied_nations_.split(",")
            allied_nations = tuple(
                ALL_NATIONS[n] for n in allied_nations__
            )
        except AttributeError:
            allied_nations = tuple()
        
        enemy_nation_:str = get_first_group_in_pattern(
            scenario_txt, enemy_nation_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'MAIN_ENEMY_NATION:'"
        )
        enemy_nation = ALL_NATIONS[enemy_nation_]
        
        other_enemy_nations_:str = get_first_group_in_pattern(
            scenario_txt, other_enemy_nations_pattern, return_aux_if_no_match=True
        )
        try:
            other_enemy_nations__ = other_enemy_nations_.split(",")
            other_enemy_nations = tuple(
                ALL_NATIONS[n] for n in other_enemy_nations__
            )
        except AttributeError:
            other_enemy_nations = tuple()
        
        your_commanding_officer = get_first_group_in_pattern(
            scenario_txt, your_commanding_officer_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'YOUR_COMMANDING_OFFICER:'"
        )
        star_generation_:str = get_first_group_in_pattern(
            scenario_txt, star_generation_pattern, return_aux_if_no_match=True
        )
        try:
            split_stars = star_generation_.split(",")
            
            stars_ = [int(s) for s in split_stars]
            
            star_generation = tuple(accumulate(stars_))
            
        except AttributeError:
            star_generation = stars_gen
            
        friendly_planets = get_first_group_in_pattern(
            scenario_txt, friendly_planet_pattern, type_to_convert_to=float,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'FRIENDLY_PLANET_PERCENT:'"
        )
        default_ship_name = get_first_group_in_pattern(
            scenario_txt, default_ship_name_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'DEFAULT_SHIP_NAME:'"
        )
        default_captain_name = get_first_group_in_pattern(
            scenario_txt, default_captain_name_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'DEFAULT_CAPTAIN_NAME:'"
        )
        enemy_give_up_threshold = get_first_group_in_pattern(
            scenario_txt, enemy_give_up_threshold_pattern, 
            return_aux_if_no_match=True, aux_valute_to_return_if_no_match=0.0, type_to_convert_to=float
        )
        code = get_first_group_in_pattern(
            scenario_txt, destruct_code_pattern,
            error_message=f"The entry {scenario_code} file 'library/scenarios.txt' did not contain an entry for 'DESTRUCT_CODE:'"
        )
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
            main_enemy_nation=enemy_nation,
            allied_nations=allied_nations,
            other_enemy_nations=other_enemy_nations,
            star_generation=star_generation,
            description=description,
            percent_of_friendly_planets=friendly_planets,
            default_ship_name=default_ship_name,
            default_captain_name=default_captain_name,
            your_commanding_officer=your_commanding_officer,
            self_destruct_code=code,
            mission_critical_ships=mission_critical_ships,
            enemy_encounters=all_enemy_encounters,
            allied_encounters=all_allied_encounters,
            startdate=startdate,
            enddate=enddate,
            enemy_give_up_threshold=enemy_give_up_threshold,
            scenario_type=scenario_type,
            victory_percent=victory_percent
        )
    return frozendict(scenario_dict)

ALL_SCENERIOS:Final = create_sceneraio()
