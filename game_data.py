from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import accumulate
from ai import BaseAi, HardEnemy
from coords import Coords
from data_globals import CONDITION_BLUE, CONDITION_GREEN, CONDITION_RED, CONDITION_YELLOW, DAMAGE_TORPEDO, STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK, CloakStatus, ShipStatus
from random import choice, choices, randrange
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type, Union, Set, OrderedDict

from get_config import CONFIG_OBJECT
from global_functions import stardate
from nation import ALL_NATIONS, Nation
from scenario import Scenerio
from starship import Starship
from ship_class import ALL_SHIP_CLASSES
from space_objects import Star, SubSector, Planet
import colors
import numpy as np

from torpedo import ALL_TORPEDO_TYPES, Torpedo

if TYPE_CHECKING:
    from engine import Engine

class GameData:

    engine: Engine

    def __init__(
        self, 
        *, 
        subsecs_x:int, subsecs_y:int, subsec_size_x:int, subsec_size_y:int,
        current_datetime:datetime,
        starting_stardate:Decimal,
        ending_stardate:Decimal,
        easy_move:bool, easy_aim:bool, easy_warp:bool,
        torpedo_warning:bool, crash_warning:bool, three_d_movment:bool,
        scenerio:Scenerio,
        difficulty:Type[BaseAi]
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
        
        # Ships that must be destroyed
        self.target_enemy_ships:List[Starship] = []
        
        self.all_allied_ships:List[Starship] = []
        
        # Ships that the player must prevent from being destroyed
        self.target_allied_ships:List[Starship] = []
        
        self.total_starships:List[Starship] = []
        self.cause_of_damage = ''

        self.condition = CONDITION_GREEN

        self.difficulty = difficulty

        self.ships_in_same_sub_sector_as_player:List[Starship] = []
        self.visible_ships_in_same_sub_sector_as_player:List[Starship] = []

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
        
        #self.player_scan = player.scan_this_ship(1, use_effective_values=False)
        self.player_scan = player.scan_for_print(1)
        
        if (
            self.selected_ship_planet_or_star is not None and 
            self.selected_ship_planet_or_star.sector_coords != self.player.sector_coords
        ):
            self.selected_ship_planet_or_star = None
            
        if isinstance(self.selected_ship_planet_or_star, Starship):
            self.ship_scan = self.selected_ship_planet_or_star.scan_for_print(
                player.sensors.determin_precision
            )

    def set_up_game(self, ship_name:str, captain_name:str):
        self.captain_name = captain_name

        self.grid = [[SubSector(self, x, y) for x in self.subsecs_range_x] for y in self.subsecs_range_y]
        
        for x in self.subsec_size_range_x:
            for y in self.subsec_size_range_y:
                self.grid[y][x].random_setup(self.star_number_weights, self.star_number_weights_len)
                #self.sector_grid[x,y].random_setup()

        system_coords = tuple(
            Coords(x=x,y=y) for x in self.subsecs_range_x for y in self.subsecs_range_y
        )
        
        all_enemy_encounters:List[Dict[str,int]] = []
        
        for a in self.scenerio.enemy_encounters:
            
            l = list(a.generate_ships())
            
            all_enemy_encounters.extend(
                l
            )
        
        total_enemy = len(all_enemy_encounters)
        
        all_allied_encounters:List[Dict[str,int]] = []
        
        for a in self.scenerio.allied_encounters:
            
            l = list(a.generate_ships())
            
            all_allied_encounters.extend(
                l
            )
        
        total_allied = len(all_allied_encounters)
        
        selected_coords = choices(
            system_coords, k=total_enemy + total_allied + 1
        )
        
        # we use k = total + 1 because the last coord in selected_coords will be used as the players starting point
        selected_enemy_coords = selected_coords[:total_enemy]
        
        # we use k = total + 1 because the last coord in selected_coords will be used as the players starting point
        selected_allied_coords = selected_coords[total_enemy:total_enemy+total_allied]
        
        try:
            player_starting_coord = choice(selected_allied_coords)
        except IndexError:
            
            coords_without_enemies = [
                co for co in system_coords if co not in selected_enemy_coords
            ]
            
            player_starting_coord = choice(coords_without_enemies)
        
        def generate_ships(enemy_nation:Nation, player_nation:Nation, selected_encounters:List[Dict[str,int]]):
        
            for encounter, co in zip(selected_encounters, selected_enemy_coords):
                
                star_system = self.grid[co.y][co.x]
                
                all_ships = []
                
                for k,v in encounter.items():
                    all_ships.extend(
                        [k] * v
                    )
                
                safe_spots = star_system.find_random_safe_spots(
                    how_many=len(all_ships)
                )
                
                for k, local_co in zip(all_ships, safe_spots):
                    
                    ship_class = ALL_SHIP_CLASSES[k]

                    starship = Starship(
                        ship_class, self.difficulty, local_co.x, local_co.y, star_system.coords.x, star_system.coords.y
                    )

                    starship.game_data = self

                    if starship.nation is player_nation:
                        star_system.allied_ships+=1
                    elif starship.nation is enemy_nation:
                        star_system.hostile_ships+=1
                    
                    yield starship
            
        self.all_enemy_ships = list(
            generate_ships(
                ALL_NATIONS[self.scenerio.main_enemy_nation],
                ALL_NATIONS[self.scenerio.your_nation], 
                all_enemy_encounters
            )
        )
        
        self.all_allied_ships = list(
            generate_ships(
                ALL_NATIONS[self.scenerio.main_enemy_nation],
                ALL_NATIONS[self.scenerio.your_nation], 
                all_allied_encounters
            )
        )
        
        randXsec = player_starting_coord.x
        randYsec = player_starting_coord.y

        locPos = self.grid[randYsec][randXsec].find_random_safe_spot()

        player_ship_class = ALL_SHIP_CLASSES[self.scenerio.your_ship]

        self.player = Starship(player_ship_class, BaseAi, locPos.x, locPos.y, randXsec, randYsec, name=ship_name)
        self.player.game_data = self
        self.engine.player = self.player

        self.total_starships = [self.player] + self.all_enemy_ships

        self.ships_in_same_sub_sector_as_player = self.grab_ships_in_same_sub_sector(
            self.player, accptable_ship_statuses={
                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
            }
        )
        self.visible_ships_in_same_sub_sector_as_player = [
            ship for ship in self.ships_in_same_sub_sector_as_player if ship.ship_status.is_visible
        ]

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
                
                subsec.hostile_ships = 0
                subsec.allied_ships = 0
                
        for ship in self.all_enemy_ships:
            
            status = ship.ship_status
            
            if status.is_active:# and status.is_visible:
                x,y = ship.sector_coords.x, ship.sector_coords.y
                subsec:SubSector = self.grid[y][x]
                
                subsec.hostile_ships += 1
                
        for ship in self.all_allied_ships:
            
            status = ship.ship_status
            
            if status.is_active:# and status.is_visible:
                x,y = ship.sector_coords.x, ship.sector_coords.y
                subsec:SubSector = self.grid[y][x]
                
                subsec.allied_ships += 1

    def handle_torpedo(self, *, shipThatFired:Starship, torpsFired:int, heading:int, coords:Tuple[Coords], torpedo_type:Torpedo, ships_in_area:Dict[Coords, Starship]):
        #global PLAYER
        #heading_to_direction
        torpedo = torpedo_type

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
                            try:
                                crew_readyness = shipThatFired.crew.crew_readyness# * 0.5 + 0.5
                            except AttributeError:
                                crew_readyness = 1
                            try:
                                target_crew_readyness = ship.crew.crew_readyness
                            except AttributeError:
                                target_crew_readyness = 1
                            
                            hitSomething = shipThatFired.roll_to_hit(
                                ship, 
                                damage_type=DAMAGE_TORPEDO,
                                systems_used_for_accuray=(
                                    shipThatFired.sensors.get_effective_value,
                                    shipThatFired.torpedos.get_effective_value
                                ),
                                crew_readyness=crew_readyness,
                                target_crew_readyness=target_crew_readyness
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
        
        shipThatFired.torpedo_launcher.torps[torpedo] -= torpsFired