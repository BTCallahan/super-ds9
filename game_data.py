from __future__ import annotations
from collections import Counter
from ai import BaseAi, HostileEnemy
from coords import Coords
from data_globals import DAMAGE_TORPEDO, STATUS_ACTIVE, ShipStatus, ShipTypes, CONDITIONS, Condition
from random import choice, randrange
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union, Set
from get_config import config_object
from starship import ADVANCED_FIGHTER, ATTACK_FIGHTER, BATTLESHIP, CRUISER, DEFIANT_CLASS, Starship
from space_objects import InterstellerObject, Star, SubSector, Planet

import numpy as np

from torpedo import ALL_TORPEDO_TYPES, TorpedoType

if TYPE_CHECKING:
    from engine import Engine

class GameData:

    engine: Engine

    def __init__(self, *, subsecs_x:int, subsecs_y:int, subsec_size_x:int, subsec_size_y:int,
                 noOfFighters:int, noOfAdFighters:int, noOfCruisers:int, noOfBattleships:int,
                 turns_left:int, 
                 easy_move:bool, easy_aim:bool, easy_warp:bool,
                 torpedo_warning:bool, crash_warning:bool, two_d_movment:bool,
                 auto_destruct_code:str
                 ):
        self.subsecs_x = subsecs_x
        self.subsecs_y = subsecs_y
        self.subsecs_range_x = range(subsecs_x)
        self.subsecs_range_y = range(subsecs_y)

        self.subsec_size_x = subsec_size_x
        self.subsec_size_y = subsec_size_y
        self.subsec_size_range_x = range(subsec_size_x)
        self.subsec_size_range_y = range(subsec_size_y)

        self.noOfFighters:int = noOfFighters
        self.noOfAdFighters = noOfAdFighters
        self.noOfCruisers = noOfCruisers
        self.noOfBattleships = noOfBattleships

        self.turns_left = turns_left
        self.easy_move = easy_move
        self.easy_aim = easy_aim
        self.easy_warp = easy_warp

        self.two_d_movment = two_d_movment

        self.torpedo_warning = torpedo_warning
        self.crash_warning = crash_warning

        self.grid:List[List[SubSector]] = []
        #self.sector_grid = np.empty(shape=(config_object.subsector_width, config_object.subsector_height), order="C", dtype=SubSector)
        
        self.secInfo = []

        self.selected_ship_planet_or_star:Optional[Union[Starship, Star, Planet]] = None

        self.player:Optional[Starship] = None

        self.player_scan:Optional[Dict[str,Any] ] = None
        self.ship_scan:Optional[Dict[str,Any] ] = None

        self.all_enemy_ships:List[Starship] = []
        self.total_starships:List[Starship] = []
        self.cause_of_damage = ''

        self.condition = Condition.GREEN

        self.ships_in_same_sub_sector_as_player:List[Starship] = []

        self.auto_destruct_code = auto_destruct_code

        self.player_record = {
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
        
        self.condition_str:Optional[str] = None
        self.condition_color:Optional[str] = None
    
    def set_condition(self):

        player = self.player

        if player.docked:
            self.condition = Condition.BLUE
        
        else:

            other_ships = self.grab_ships_in_same_sub_sector(
                player,
                accptable_ship_statuses={STATUS_ACTIVE}
                )

            self.condition = Condition.RED if len(other_ships) > 0 else (Condition.YELLOW if player.shields > 0 else Condition.GREEN) 
        
        self.player_scan = player.scan_this_ship(1)
        
        self.condition_str, self.condition_color = CONDITIONS[self.condition]
        
        if self.selected_ship_planet_or_star is not None and self.selected_ship_planet_or_star.sector_coords != self.player.sector_coords:
            self.selected_ship_planet_or_star = None
            
        if isinstance(self.selected_ship_planet_or_star, Starship):
            self.ship_scan = self.selected_ship_planet_or_star.scan_this_ship(player.determin_precision)

    def setUpGame(self):

        self.grid = [[SubSector(self, x, y) for x in self.subsecs_range_x] for y in self.subsecs_range_y]
        
        for x in self.subsec_size_range_x:
            for y in self.subsec_size_range_y:
                self.grid[y][x].random_setup()
                #self.sector_grid[x,y].random_setup()

        total = self.noOfFighters + self.noOfAdFighters + self.noOfCruisers + self.noOfBattleships

        sub_sectors = [self.grid[randrange(self.subsecs_y)][randrange(self.subsecs_x)].coords for i in range(total)]

        sub_sector_dictionary = Counter(sub_sectors)
        
        def get_ship(ship_count:int):

            if ship_count < self.noOfFighters:
                return ATTACK_FIGHTER
            if ship_count < self.noOfFighters + self.noOfAdFighters:
                return ADVANCED_FIGHTER
            return CRUISER if ship_count < self.noOfFighters + self.noOfAdFighters + self.noOfCruisers else BATTLESHIP

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
                    
                    if ship.ship_type == ShipTypes.TYPE_ENEMY_SMALL:
                        sub_sector.smallShips+=1
                    elif ship.ship_type == ShipTypes.TYPE_ENEMY_LARGE:
                        sub_sector.bigShips+=1

                    yield starship
                
                else:

                    local_cos = sub_sector.find_random_safe_spots(i)

                    for local_co in local_cos:

                        ship = get_ship(ship_count)

                        ship_count += 1

                        starship = Starship(ship, HostileEnemy, local_co.x, local_co.y, sub_sector_co.x, sub_sector_co.y)

                        starship.game_data = self

                        if ship.ship_type == ShipTypes.TYPE_ENEMY_SMALL:
                            sub_sector.smallShips+=1
                        elif ship.ship_type == ShipTypes.TYPE_ENEMY_LARGE:
                            sub_sector.bigShips+=1

                        yield starship

        self.all_enemy_ships = list(generate_ships())

        # finds a sector coord 
        all_sector_cos = set(sec.coords for line in self.grid for sec in line) - set(sub_sector_dictionary.keys())

        xy = choice(tuple(all_sector_cos))

        randXsec = xy.x
        randYsec = xy.y

        locPos = self.grid[randYsec][randXsec].find_random_safe_spot()

        self.player = Starship(DEFIANT_CLASS, BaseAi, locPos.x, locPos.y, randXsec, randYsec)
        self.player.game_data = self
        self.engine.player = self.player

        self.total_starships = [self.player] + self.all_enemy_ships

        self.ships_in_same_sub_sector_as_player = self.grab_ships_in_same_sub_sector(self.player)

        self.set_condition()

    @classmethod
    def newGame(cls):
        return cls(8, 8, 8, 8,
                   20, 12, 5, 1,
                   100, False, False)

    #-----Gameplay related------
    """
    def checkForSelectableShips(self):

        player = self.player

        if (isinstance(self.selected_ship_planet_or_star, Starship) and self.selected_ship_planet_or_star.sector_coords != player.sector_coords
        ) or (isinstance(self.selected_ship_planet_or_star, Planet) and self.selected_ship_planet_or_star.sector_coords != player.sector_coords
        ) or self.selected_ship_planet_or_star is None:

            ships_in_same_subsector = self.grab_ships_in_same_sub_sector(player)

            if ships_in_same_subsector:

                self.selected_ship_planet_or_star = ships_in_same_subsector[0]
            else:
                sector:SubSector = self.grid[player.sector_coords.y][player.sector_coords.x]

                if sector.planets_dict:

                    self.selected_ship_planet_or_star = sector.planets_dict.values()[0]
                else:

                    self.selected_ship_planet_or_star = None
    """
    def grab_ships_in_same_sub_sector(self, ship:Starship, *, include_self_in_ships_to_grab:bool=False, accptable_ship_statuses:Optional[Set[ShipStatus]]=None):
        
        if accptable_ship_statuses:
            return (
                [s for s in self.total_starships if s.sector_coords == ship.sector_coords and s.ship_status in accptable_ship_statuses] if include_self_in_ships_to_grab else 
                [s for s in self.total_starships if s.sector_coords == ship.sector_coords and s.ship_status in accptable_ship_statuses and s is not ship]
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
                
                subsec.bigShips = 0
                subsec.smallShips = 0
                
        for ship in self.all_enemy_ships:
            
            if ship.ship_status.is_active:
                x,y = ship.sector_coords.x, ship.sector_coords.y
                subsec:SubSector = self.grid[y][x]
                
                if ship.ship_data.ship_type == ShipTypes.TYPE_ENEMY_LARGE:
                    subsec.bigShips += 1
                elif ship.ship_data.ship_type == ShipTypes.TYPE_ENEMY_SMALL:
                    subsec.smallShips += 1

    def handle_torpedo(self, *, shipThatFired:Starship, torpsFired:int, heading:int, coords:Tuple[Coords], torpedo_type:TorpedoType, ships_in_area:Dict[Coords, Starship]):
        #global PLAYER
        #headingToDirection
        torpedo = ALL_TORPEDO_TYPES[torpedo_type]

        posX, posY = shipThatFired.local_coords.x, shipThatFired.local_coords.y
        """
        dirX = destX - posX
        dirY = destY - posY
        atan2xy = math.atan2(dirX, dirY)

        dirX, dirY = math.sin(atan2xy), math.cos(atan2xy)
        """
        descriptive_number = "a" if torpsFired == 1 else f"{torpsFired}"
        plural = "torpedo" if torpsFired == 1 else "torpedos"
        
        self.engine.message_log.add_message(
            f"Firing {descriptive_number} {torpedo.name} {plural} at heading {heading}..." if shipThatFired.is_controllable else f"{shipThatFired.name} has fired {descriptive_number} {torpedo.name} {plural} at heading {heading}..."
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
                
                if not (0<= co.x < config_object.subsector_width) or not (0<= co.y < config_object.subsector_height):
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
                            
                            hitSomething = shipThatFired.roll_to_hit(
                                ship, 
                                damage_type=DAMAGE_TORPEDO,
                                systems_used_for_accuray=(
                                    shipThatFired.sys_sensors.get_effective_value,
                                    shipThatFired.sys_torpedos.get_effective_value
                                )
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
                self.engine.message_log.add_message("The torpedo misses the target!" if missed_the_target else f"The torpedo vears off into space at {x}, {y}!")
        
        shipThatFired.torps[torpedo_type] -= torpsFired