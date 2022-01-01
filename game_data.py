from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from ai import BaseAi, HostileEnemy
from coords import Coords
from data_globals import CONDITION_BLUE, CONDITION_GREEN, CONDITION_RED, CONDITION_YELLOW, DAMAGE_TORPEDO, STATUS_ACTIVE, ShipStatus
from random import choice, randrange
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING, Tuple, Union, Set, OrderedDict

from get_config import CONFIG_OBJECT
from global_functions import stardate
from scenario import Scenerio
from starship import ALL_SHIP_CLASSES, Starship
from space_objects import Star, SubSector, Planet
import colors
import numpy as np

from torpedo import ALL_TORPEDO_TYPES

if TYPE_CHECKING:
    from engine import Engine

class GameData:

    engine: Engine

    def __init__(
        self, 
        *, 
        subsecs_x:int, subsecs_y:int, subsec_size_x:int, subsec_size_y:int,
        enemy_ship_dict:OrderedDict[str:int],
        current_datetime:datetime,
        starting_stardate:Decimal,
        ending_stardate:Decimal,
        easy_move:bool, easy_aim:bool, easy_warp:bool,
        torpedo_warning:bool, crash_warning:bool, three_d_movment:bool,
        scenerio:Scenerio
    ):
        self.subsecs_x = subsecs_x
        self.subsecs_y = subsecs_y
        self.subsecs_range_x = range(subsecs_x)
        self.subsecs_range_y = range(subsecs_y)

        self.subsec_size_x = subsec_size_x
        self.subsec_size_y = subsec_size_y
        self.subsec_size_range_x = range(subsec_size_x)
        self.subsec_size_range_y = range(subsec_size_y)

        self.easy_move = easy_move
        self.easy_aim = easy_aim
        self.easy_warp = easy_warp

        self.three_d_movment = three_d_movment
                
        self.star_number_weights = scenerio.star_generation
        self.star_number_weights_len = len(self.star_number_weights)

        self.torpedo_warning = torpedo_warning
        self.crash_warning = crash_warning

        self.grid:List[List[SubSector]] = []
        #self.sector_grid = np.empty(shape=(config_object.subsector_width, config_object.subsector_height), order="C", dtype=SubSector)
        
        self.secInfo = []
        self.scenerio = scenerio
        
        self.fifteen_seconds = timedelta(seconds=15)
        
        self.date_time:Optional[datetime] = current_datetime
        self.starting_stardate = starting_stardate
        self.stardate = stardate(current_datetime)
        self.ending_stardate = ending_stardate
        #self.stardate_text = f"{self.stardate:5.2}"

        self.selected_ship_planet_or_star:Optional[Union[Starship, Star, Planet]] = None

        self.player:Optional[Starship] = None

        self.player_scan:Optional[Dict[str,Any] ] = None
        self.ship_scan:Optional[Dict[str,Any] ] = None

        self.all_enemy_ships:List[Starship] = []
        self.total_starships:List[Starship] = []
        self.cause_of_damage = ''

        self.condition = CONDITION_GREEN

        self.ships_in_same_sub_sector_as_player:List[Starship] = []
        self.enemy_ship_dict:OrderedDict[str,int] = enemy_ship_dict

        self.captain_name = ""
        self.player_record = OrderedDict(
            {
            "planets_angered" : 0,
            "planets_depopulated" : 0,
            "prewarp_planets_depopulated" : 0,
            "times_hit_planet" : 0,
            "times_hit_poipulated_planet" : 0,
            "times_hit_prewarp_planet" : 0,
            "deathtoll" : 0,
            "times_gone_to_warp": 0,
            "energy_used" : 0,
            "torpedos_fired" : 0
        }
        )
        
    @property
    def is_time_up(self):
        return self.stardate >= self.ending_stardate
    
    @property
    def auto_destruct_code(self):
        return self.scenerio.self_destruct_code
    
    def set_condition(self):

        player = self.player
        
        all_other_ships = [ship for ship in self.all_enemy_ships if ship.ship_status.is_active]
        
        if not all_other_ships:
            self.condition = CONDITION_GREEN
        else:
            if player.docked:
                self.condition = CONDITION_BLUE
            else:
                other_ships = [ship for ship in all_other_ships if ship.sector_coords == player.sector_coords]

                self.condition = CONDITION_RED if len(other_ships) > 0 else CONDITION_YELLOW
        
        self.player_scan = player.scan_this_ship(1)
        
        if (
            self.selected_ship_planet_or_star is not None and 
            self.selected_ship_planet_or_star.sector_coords != self.player.sector_coords
        ):
            self.selected_ship_planet_or_star = None
            
        if isinstance(self.selected_ship_planet_or_star, Starship):
            self.ship_scan = self.selected_ship_planet_or_star.scan_this_ship(player.determin_precision)

    def set_up_game(self, ship_name:str, captain_name:str):
        self.captain_name = captain_name

        self.grid = [[SubSector(self, x, y) for x in self.subsecs_range_x] for y in self.subsecs_range_y]
        
        for x in self.subsec_size_range_x:
            for y in self.subsec_size_range_y:
                self.grid[y][x].random_setup(self.star_number_weights, self.star_number_weights_len)
                #self.sector_grid[x,y].random_setup()

        total = max(tuple(self.enemy_ship_dict.values()))

        sub_sectors = [self.grid[randrange(self.subsecs_y)][randrange(self.subsecs_x)].coords for i in range(total)]

        sub_sector_dictionary = Counter(sub_sectors)
        
        def get_ship(ship_count:int):
            
            for k,v in self.enemy_ship_dict.items():
                
                if ship_count < v:
                    return ALL_SHIP_CLASSES[k]
            
            return ALL_SHIP_CLASSES[tuple(self.enemy_ship_dict.keys())[-1]]

        def generate_ships():

            ship_count = 0

            for sub_sector_co, i in sub_sector_dictionary.items():

                sub_sector:SubSector = self.grid[sub_sector_co.y][sub_sector_co.x]

                if i == 1:

                    local_co = sub_sector.find_random_safe_spot()

                    ship = get_ship(ship_count)

                    ship_count += 1

                    starship = Starship(ship, HostileEnemy, local_co.x, local_co.y, sub_sector_co.x, sub_sector_co.y)

                    starship.game_data = self
                    
                    if ship.nation_code != "FEDERATION":
                        if ship.ship_type == "ESCORT":
                            sub_sector.small_ships+=1
                        elif ship.ship_type in {"CRUISER", "WARSHIP"}:
                            sub_sector.big_ships+=1

                    yield starship
                
                else:

                    local_cos = sub_sector.find_random_safe_spots(i)

                    for local_co in local_cos:

                        ship = get_ship(ship_count)

                        ship_count += 1

                        starship = Starship(
                            ship, HostileEnemy, local_co.x, local_co.y, sub_sector_co.x, sub_sector_co.y
                        )

                        starship.game_data = self

                        if ship.nation_code != "FEDERATION":
                            if ship.ship_type == "ESCORT":
                                sub_sector.small_ships+=1
                            elif ship.ship_type in {"CRUISER", "WARSHIP"}:
                                sub_sector.big_ships+=1

                        yield starship

        self.all_enemy_ships = list(generate_ships())

        # finds a sector coord 
        all_sector_cos = set(sec.coords for line in self.grid for sec in line) - set(sub_sector_dictionary.keys())

        xy = choice(tuple(all_sector_cos))

        randXsec = xy.x
        randYsec = xy.y

        locPos = self.grid[randYsec][randXsec].find_random_safe_spot()

        deff = ALL_SHIP_CLASSES["DEFIANT"]

        self.player = Starship(deff, BaseAi, locPos.x, locPos.y, randXsec, randYsec, name=ship_name)
        self.player.game_data = self
        self.engine.player = self.player

        self.total_starships = [self.player] + self.all_enemy_ships

        self.ships_in_same_sub_sector_as_player = self.grab_ships_in_same_sub_sector(self.player)

        self.set_condition()
        
        self.engine.message_log.add_message(
            f"Welcome aboard, {self.player.ship_class.nation.captain_rank_name} {self.captain_name}."
        )

    @classmethod
    def newGame(cls):
        return cls(8, 8, 8, 8,
                   20, 12, 5, 1,
                   100, False, False)

    #-----Gameplay related------
    
    def grab_ships_in_same_sub_sector(self, ship:Starship, *, include_self_in_ships_to_grab:bool=False, accptable_ship_statuses:Optional[Set[ShipStatus]]=None):
        
        if accptable_ship_statuses:
            return (
                [
                    s for s in self.total_starships 
                    if s.sector_coords == ship.sector_coords and s.ship_status in accptable_ship_statuses
                ] 
                if include_self_in_ships_to_grab else 
                [
                    s for s in self.total_starships 
                    if s.sector_coords == ship.sector_coords and s.ship_status in accptable_ship_statuses and 
                    s is not ship
                ]
            )

        return (
            [s for s in self.total_starships if s.sector_coords == ship.sector_coords] 
            if include_self_in_ships_to_grab else 
            [s for s in self.total_starships if s.sector_coords == ship.sector_coords and s is not ship]
        )

    def _check_ship(self, ship:Starship, visibility_status:Optional[bool]=None, activity_status:Optional[bool]=None):
        
        status = ship.ship_status
        
        if visibility_status is not None:
            if visibility_status != status.is_visible:
                return False
        
        if activity_status is not None:
            if activity_status != status.is_active:
                return False
        
        return True
    
    def update_mega_sector_display(self):
        
        for y in self.subsec_size_range_y:
            
            for x in self.subsec_size_range_x:
                
                subsec = self.grid[y][x]
                
                subsec.big_ships = 0
                subsec.small_ships = 0
                
        for ship in self.all_enemy_ships:
            
            if ship.ship_status.is_active:
                x,y = ship.sector_coords.x, ship.sector_coords.y
                subsec:SubSector = self.grid[y][x]
                
                if ship.ship_class.ship_type in {"CRUISER", "BATTLESHIP"}:
                    subsec.big_ships += 1
                elif ship.ship_class.ship_type == "ESCORT":
                    subsec.small_ships += 1

    def handle_torpedo(self, *, shipThatFired:Starship, torpsFired:int, heading:int, coords:Tuple[Coords], torpedo_type:str, ships_in_area:Dict[Coords, Starship]):
        #global PLAYER
        #heading_to_direction
        torpedo = ALL_TORPEDO_TYPES[torpedo_type]

        posX, posY = shipThatFired.local_coords.x, shipThatFired.local_coords.y
        
        descriptive_number = "a" if torpsFired == 1 else f"{torpsFired}"
        plural = "torpedo" if torpsFired == 1 else "torpedos"
        
        self.engine.message_log.add_message(
            f"Firing {descriptive_number} {torpedo.name} {plural} at heading {heading}..." if shipThatFired.is_controllable else f"{shipThatFired.name} has fired {descriptive_number} {torpedo.name} {plural} at heading {heading:3.2}...", colors.yellow
        )

        g: SubSector = self.grid[shipThatFired.sector_coords.y][shipThatFired.sector_coords.x]
        
        #shipsInArea = [ship for ship in self.grab_ships_in_same_sub_sector(shipThatFired) if ship.local_coords in coords]

        shipsInArea = ships_in_area

        for t in range(torpsFired):

            hitSomething=False
            missed_the_target=False

            x = 0
            y = 0

            for co in coords:
                #x_, y_ = co.x, co.y
                
                if not (0<= co.x < CONFIG_OBJECT.subsector_width) or not (0<= co.y < CONFIG_OBJECT.subsector_height):
                    #self.engine.message_log.add_message("The torpedo vears off into space!" if missed_the_target else "The torpedo misses!")
                    break

                x,y = co.x, co.y

                #xy = Coords(x,y)

                try:
                    star = g.stars_dict[co]
                    self.engine.message_log.add_message(f"The torpedo impacts against a star at {co.x}, {co.y}.")
                    hitSomething=True
                except KeyError:

                    try:
                        planet = g.planets_dict[co]
                        planet.hit_by_torpedo(shipThatFired.is_controllable, self, torpedo)
                        hitSomething=True
                    except KeyError:
                        try:
                            ship = shipsInArea[co]
                            #hitSomething = shipThatFired.attack_torpedo(self, ship, torpedo)
                            crew_readyness = shipThatFired.crew_readyness * 0.5 + 0.5
                            
                            hitSomething = shipThatFired.roll_to_hit(
                                ship, 
                                damage_type=DAMAGE_TORPEDO,
                                systems_used_for_accuray=(
                                    shipThatFired.sys_sensors.get_effective_value,
                                    shipThatFired.sys_torpedos.get_effective_value
                                ),
                                crew_readyness=crew_readyness
                            )
                            
                            if hitSomething:
                                #chance to hit:
                                #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
                                self.engine.message_log.add_message(f'{ship.name} was hit by a {torpedo.name} torpedo from {shipThatFired.name}. ')

                                ship.take_damage(torpedo.damage, f'Destroyed by a {torpedo.name} torpedo hit from the {shipThatFired.name}', damage_type=DAMAGE_TORPEDO)
                            else:
                                self.engine.message_log.add_message(f'A {torpedo.name} torpedo from {shipThatFired.name} missed {ship.name}. ')
                                missed_the_target = True
                                
                        except KeyError:
                            pass
                if hitSomething:
                    break
                    
            if not hitSomething:
                self.engine.message_log.add_message(
                    "The torpedo misses the target!" if missed_the_target else 
                    f"The torpedo vears off into space at {x}, {y}!", colors.orange
                )
        
        shipThatFired.torps[torpedo_type] -= torpsFired