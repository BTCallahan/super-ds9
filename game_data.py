from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from ai import BaseAi
from coords import Coords
from data_globals import CONDITION_BLUE, CONDITION_GREEN, CONDITION_RED, CONDITION_YELLOW, DAMAGE_TORPEDO, PLANET_FRIENDLY, PLANET_HOSTILE, PLANET_NEUTRAL, STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK, PlanetHabitation, ShipStatus
from random import choice, choices, shuffle
from typing import Any, Dict, FrozenSet, List, Optional, TYPE_CHECKING, Tuple, Type, Union, Set, OrderedDict

from get_config import CONFIG_OBJECT
from global_functions import stardate
from nation import Nation
from scenario import Scenerio
from starship import Starship
from ship_class import ALL_SHIP_CLASSES
from space_objects import Star, SubSector, Planet, SubSectorInfo
import colors
from torpedo import Torpedo

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
        difficulty:Type[BaseAi],
        alliled_ai:Type[BaseAi]
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
        
        self.player_subsector_info:List[List[SubSectorInfo]] = []
        self.enemy_subsector_info:List[List[SubSectorInfo]] = []
        
        self.scenerio = scenerio
                
        self.date_time:Optional[datetime] = current_datetime
        self.starting_stardate = starting_stardate
        self.stardate = stardate(current_datetime)
        self.ending_stardate = ending_stardate

        self.selected_ship_planet_or_star:Optional[Union[Starship, Star, Planet]] = None

        self.player:Optional[Starship] = None

        self.player_scan:Optional[Dict[str,Any] ] = None
        self.ship_scan:Optional[Dict[str,Any] ] = None

        self.all_other_ships:List[Starship] = []

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
        
        self.allied_ai = alliled_ai

        self.ships_in_same_sub_sector_as_player:List[Starship] = []
        self.visible_ships_in_same_sub_sector_as_player:List[Starship] = []

        self.captain_name = ""
        self.player_record = OrderedDict(
            {
                "planets_aggravated" : 0,
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
        self.debug_warning = 0
        
        self.info_description = self.describe_info()
        
    @property
    def is_time_up(self):
        return self.stardate >= self.ending_stardate
    
    @property
    def auto_destruct_code(self):
        return self.scenerio.self_destruct_code
    
    def set_condition(self):

        player = self.player
        
        all_other_ships = [
            ship for ship in self.all_other_ships if ship.ship_status.is_active and 
            ship.nation in self.scenerio.get_set_of_enemy_nations
        ]
        if not all_other_ships:
            self.condition = CONDITION_GREEN
        else:
            if player.docked:
                self.condition = CONDITION_BLUE
            else:
                other_ships = [ship for ship in all_other_ships if ship.sector_coords == player.sector_coords]

                self.condition = CONDITION_RED if len(other_ships) > 0 else CONDITION_YELLOW
        
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
        
        self.player_subsector_info = [[SubSectorInfo(x, y) for x in self.subsecs_range_x] for y in self.subsecs_range_y]
        self.enemy_subsector_info = [[SubSectorInfo(x, y) for x in self.subsecs_range_x] for y in self.subsecs_range_y]
        
        # create stars and planets
        for x in self.subsec_size_range_x:
            for y in self.subsec_size_range_y:
                self.grid[y][x].random_setup(self.star_number_weights, self.star_number_weights_len)

        # create a tuple that contains self.subsecs_range_x * self.subsecs_range_y Coords
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
        
        def generate_ships(
            selected_encounters:List[Dict[str,int]],
            selected_coords:List[Coords],
            ai_difficulty:type[BaseAi]
        ):
            for encounter, co in zip(selected_encounters, selected_coords):
                
                star_system = self.grid[co.y][co.x]
                
                all_ships:List[str] = []
                
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
                        ship_class, ai_difficulty, local_co.x, local_co.y, star_system.coords.x, star_system.coords.y
                    )
                    starship.game_data = self
                    
                    yield starship
            
        self.all_enemy_ships = list(
            generate_ships(
                all_enemy_encounters,
                selected_enemy_coords,
                self.difficulty
            )
        )
        self.target_enemy_ships = [
            ship for ship in self.all_enemy_ships if ship.is_mission_critical
        ]
        self.all_allied_ships = list(
            generate_ships(
                all_allied_encounters,
                selected_allied_coords,
                self.allied_ai
            )
        )
        self.target_allied_ships = [
            ship for ship in self.all_allied_ships if ship.is_mission_critical
        ]
        randXsec = player_starting_coord.x
        randYsec = player_starting_coord.y

        locPos = self.grid[randYsec][randXsec].find_random_safe_spot()

        player_ship_class = self.scenerio.your_ship

        self.player = Starship(player_ship_class, BaseAi, locPos.x, locPos.y, randXsec, randYsec, name=ship_name)
        self.player.game_data = self
        self.engine.player = self.player
        
        all_other_ships = self.all_enemy_ships + self.all_allied_ships
        
        shuffle(all_other_ships)
        
        self.all_other_ships = all_other_ships

        self.total_starships = [self.player] + self.all_other_ships

        self.ships_in_same_sub_sector_as_player = self.grab_ships_in_same_sub_sector(
            self.player, accptable_ship_statuses={
                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
            }
        )
        self.visible_ships_in_same_sub_sector_as_player = [
            ship for ship in self.ships_in_same_sub_sector_as_player if ship.ship_status.is_visible
        ]
        self.set_condition()
                
        for ship in self.total_starships:
            
            self.run_update_for_ship(ship)
        
        self.engine.message_log.add_message(
            f"Welcome aboard, {self.player.ship_class.nation.captain_rank_name} {self.captain_name}."
        )

    def describe_warp_factor(self):
        try:
            wf = self.player.warp_drive.current_warp_factor
            return f"Warp factor: {wf}" if wf else "Impulse"
        except AttributeError:
            return "Impulse"

    def describe_shields(self):
        try:
            return (
                "Shields up" if self.player.shield_generator.is_opperational else "Shields offline"
            ) if self.player.shield_generator.shields_up else "Shields down"
        except AttributeError:
            return "Shields unavialble"
    
    def describe_info(self):
        try:
            wf = self.player.warp_drive.current_warp_factor
            warp_factor =  f"Warp factor: {wf}" if wf else "Impulse"
        except AttributeError:
            warp_factor = "Impulse"
        try:
            shields = (
                "Shields up" if self.player.shield_generator.is_opperational else "Shields offline"
            ) if self.player.shield_generator.shields_up else "Shields down"
        except AttributeError:
            shields = "Shields unavialble"
        try:
            hull = (
                "Hull polarized" if self.player.polarized_hull.is_opperational else "Hull polarization offline"
            ) if self.player.polarized_hull.is_polarized else "Hull unpolarized"
        except AttributeError:
            hull = "Hull polarization unavialble"
        try:
            local_coords = self.player.local_coords
        except AttributeError:
            local_coords = "?, ?"
        try:
            sector_coords = self.player.sector_coords
        except AttributeError:
            sector_coords = "?, ?"
        
        return f"System Position: {local_coords}\nSector Position: {sector_coords}\nStardate: {self.stardate}\nEnding Stardate: {self.ending_stardate}\n{warp_factor}\n{shields}\n{hull}"
    
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
    
    def run_update_for_ship(self, ship:Starship):
        
        ship_is_enemy = ship.is_enemy
        
        subsector_infos = self.enemy_subsector_info if ship_is_enemy else self.player_subsector_info
        
        scan_distance = 5
                
        for y in range(ship.sector_coords.y - scan_distance, ship.sector_coords.y + scan_distance):
            
            for x in range(
                ship.sector_coords.x - scan_distance, ship.sector_coords.x + scan_distance
            ):
                try:
                    subsec_info = subsector_infos[y][x]
                    
                    if subsec_info.needs_updating and (
                        ship.sector_coords == subsec_info.coords or 
                        ship.sector_coords.distance(coords=subsec_info.coords) <= scan_distance
                    ):
                        if subsec_info.planet_count_needs_updating:
                            
                            subsector = self.grid[y][x]
                            
                            subsec_info.barren_planets = subsector.barren_planets
                            
                            subsec_info.total_stars = subsector.total_stars
                            
                            planets:List[PlanetHabitation] = [
                                (
                                    planet.enemy_display_status if ship_is_enemy else planet.player_display_status
                                ) for planet in subsector.planets_dict.values() if 
                                planet.planet_habbitation.has_disposition_towards_warp_capiable_civs
                            ]
                            subsec_info.friendly_planets = len(
                                [planet for planet in planets if planet == PLANET_FRIENDLY]
                            )
                            subsec_info.neutral_planets = len(
                                [planet for planet in planets if planet == PLANET_NEUTRAL]
                            )
                            subsec_info.unfriendly_planets = len(
                                [planet for planet in planets if planet == PLANET_HOSTILE]
                            )
                            subsec_info.planet_count_needs_updating = False
                        
                        if subsec_info.ship_count_needs_updating:
                            
                            ships_in_subsector = [
                                ship for ship in self.total_starships if 
                                ship.sector_coords.x == x and ship.sector_coords.y == y and 
                                ship.ship_status in {STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_DERLICT}
                            ]
                            subsec_info.hostile_ships = len([
                                ship for ship in ships_in_subsector if
                                ship.ship_status != STATUS_DERLICT and
                                ship.is_enemy != ship_is_enemy
                            ])
                            subsec_info.derelicts = len([
                                ship for ship in ships_in_subsector if
                                ship.ship_status == STATUS_DERLICT
                            ])
                            subsec_info.ship_count_needs_updating = False
                except IndexError:
                    pass
        
    def handle_torpedo(
        self, *, shipThatFired:Starship, torpsFired:int, heading:int, coords:Tuple[Coords], 
        torpedo_type:Torpedo, ships_in_area:Dict[Coords, Starship]
    ):
        torpedo = torpedo_type

        #posX, posY = shipThatFired.local_coords.x, shipThatFired.local_coords.y
        
        descriptive_number = "a" if torpsFired == 1 else f"{torpsFired}"
        plural = "torpedo" if torpsFired == 1 else "torpedos"
        
        self.engine.message_log.add_message(
            f"Firing {descriptive_number} {torpedo.name} {plural} at heading {heading}..." if shipThatFired.is_controllable else f"{shipThatFired.name} has fired {descriptive_number} {torpedo.name} {plural} at heading {heading:3.2f}...", colors.yellow
        )
        g: SubSector = self.grid[shipThatFired.sector_coords.y][shipThatFired.sector_coords.x]
        
        shipsInArea = ships_in_area

        for t in range(torpsFired):

            hitSomething=False
            missed_the_target=False

            x = 0
            y = 0

            for co in coords:
                #x_, y_ = co.x, co.y
                
                if not (0<= co.x < CONFIG_OBJECT.subsector_width) or not (0<= co.y < CONFIG_OBJECT.subsector_height):
                    break

                x,y = co.x, co.y
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
                            try:
                                crew_readyness = shipThatFired.life_support.crew_readyness
                            except AttributeError:
                                crew_readyness = 1
                            try:
                                target_crew_readyness = ship.life_support.crew_readyness
                            except AttributeError:
                                target_crew_readyness = 1
                            
                            estimated_enemy_impulse = ship.impulse_engine.get_effective_value
                            
                            hitSomething = shipThatFired.roll_to_hit(
                                ship, 
                                damage_type=DAMAGE_TORPEDO,
                                estimated_enemy_impulse=estimated_enemy_impulse,
                                systems_used_for_accuray=(
                                    shipThatFired.sensors.get_effective_value,
                                    shipThatFired.torpedo_launcher.get_effective_value
                                ),
                                crew_readyness=crew_readyness,
                                target_crew_readyness=target_crew_readyness
                            )                            
                            if hitSomething:
                                
                                ship_name = "We were" if ship.is_controllable else f"{ship.name} was"
                                
                                shipThatFired_name = "us" if shipThatFired.is_controllable else shipThatFired.name
                                
                                self.engine.message_log.add_message(
                                    f'{ship_name} hit by a {torpedo.name} torpedo from {shipThatFired.name}. '
                                )
                                ship.take_damage(
                                    torpedo.damage, 
                                    f'Destroyed by a {torpedo.name} torpedo hit from the {shipThatFired_name}', 
                                    damage_type=DAMAGE_TORPEDO
                                )
                            else:
                                ship_name = "us" if ship.is_controllable else ship.name
                                
                                shipThatFired_name = "us" if shipThatFired.is_controllable else shipThatFired.name
                                
                                self.engine.message_log.add_message(
                                    f'A {torpedo.name} torpedo from {shipThatFired_name} missed {ship_name}. '
                                )
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
