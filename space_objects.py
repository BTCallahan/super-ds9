from __future__ import annotations
from typing import Dict, Iterable, List, Optional,  Tuple, TYPE_CHECKING
from random import choice, choices, randint, uniform, random
from itertools import accumulate
from coords import Coords
from data_globals import PLANET_ANGERED, PLANET_BARREN, PLANET_BOMBED_OUT, PLANET_FRIENDLY, PLANET_PREWARP, PLANET_TYPES, PlanetHabitation
import colors
from torpedo import ALL_TORPEDO_TYPES, Torpedo

if TYPE_CHECKING:
    from game_data import GameData
    from message_log import MessageLog
    from starship import Starship

star_number_weights = tuple(accumulate((5, 12, 20, 9, 6, 3)))
star_number_weights_len = len(star_number_weights)

class InterstellerObject:
    
    def __init__(self, local_coords:Coords, sector_coords:Coords) -> None:
        self.local_coords = local_coords
        self.sector_coords = sector_coords
    
    def hit_by_torpedo(self, is_player:bool, game_data:GameData, message_log:MessageLog, torpedo:Torpedo):
        raise NotImplementedError

STAR_TYPES = (
    "Main sequence O",
    "Main sequence B",
    "Main sequence A",
    "Main sequence F",
    "Main sequence G (Yellow dwarf)",
    "Main sequence K (Orange dwarf)",
    "Main sequence M (Red dwarf)",
    
    "Brown dwarf",
    "Brown subdwarf",
    
    "Blue subdwarf",
    "Blue giant",
    "Blue supergiant",
    "Blue hypergiant",
    
    "Yellow giant",
    "Yellow supergiant",
    "Yellow hypergiant",
    
    "Red giant",
    "Red supergiant",
    "Red hypergiant",
    
    "White dwarf",
    "Neutron star",
    "Black hole"
)

STAR_WEIGHTS = tuple(
    accumulate(
        (
            6,
            48,
            118,
            325,
            731,
            1646,
            5730,
            
            1024,
            1237,
            
            33,
            24,
            11,
            4,
            
            12,
            6,
            2,
            
            51,
            26,
            8,
            
            34,
            9,
            3,
        )
    )
)

STAR_COLORS = {
    "Main sequence O" : colors.star_blue,
    "Main sequence B" : colors.star_blue_white,
    "Main sequence A" : colors.star_white,
    "Main sequence F" : colors.star_yellow_white,
    "Main sequence G (Yellow dwarf)" : colors.star_yellow,
    "Main sequence K (Orange dwarf)" : colors.star_orange,
    "Main sequence M (Red dwarf)" : colors.star_red,
    "Brown dwarf" : colors.star_brown,
    "Brown subdwarf" : colors.star_brown,
    "Blue subdwarf" : colors.star_blue,
    "Blue giant" : colors.star_blue,
    "Blue supergiant" : colors.star_blue,
    "Blue hypergiant" : colors.star_blue,
    
    "Yellow giant" : colors.star_yellow,
    "Yellow supergiant" : colors.star_yellow,
    "Yellow hypergiant" : colors.star_yellow,
    
    "Red giant" : colors.star_red,
    "Red supergiant" : colors.star_red,
    "Red hypergiant" : colors.star_red,
    
    "White dwarf" : colors.star_white,
    "Neutron star" : colors.star_white,
    "Black hole" : colors.black
}

'''
STAR_COLORS = (
    colors.star_blue,
    colors.star_blue_white,
    colors.star_white,
    colors.star_yellow_white,
    colors.star_yellow,
    colors.star_orange,
    colors.star_red,
    colors.star_brown,
    colors.black
)
'''

class Star(InterstellerObject):
    
    orderSuffexes = ['Alpha ', 'Beta ', 'Gamma ', 'Delta ']
    planetSuffexes = ['', ' I', ' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII']

    def __init__(self, local_coords:Coords, sector_coords:Coords):
        super().__init__(local_coords, sector_coords)
        self.name = choices(
            STAR_TYPES,
            cum_weights=STAR_WEIGHTS
        )[0]
        
        self.color = STAR_COLORS[self.name]
        
        self.bg = colors.white if self.color is colors.black else colors.black
        '''
        if self.color in {colors.star_blue, colors.star_blue_white}:
            self.name = choice(("Blue giant", "Blue supergiant", "Blue hypergiant", "Blue subdwarf"))
        elif self.color is colors.star_white:
            self.name = "White dwarf"
        elif self.color in {colors.star_yellow, colors.star_yellow_white}:
            self.name = choice(("Yellow dwarf", "Yellow giant", "Yellow supergiant", "Yellow hypergiant"))
        elif self.color is colors.star_orange:
            self.name = "Orange dwarf"
        elif self.color is colors.star_red:
            self.name = choice(("Red dwarf", "Red giant", "Red supergiant", "Red hypergiant"))
        elif self.color is colors.star_brown:
            self.name = choice(("Brown dwarf", "Brown subdwarf"))
        else:
            self.name = "Black hole"
        '''

    def hit_by_torpedo(self, is_player:bool, game_data:GameData, message_log:MessageLog, torpedo:Torpedo):
        pass

class SubSector:
    """A SubSector is a region of space that contains stars and planets. 

    Returns:
        [type]: [description]

    Yields:
        [type]: [description]
    """

    @staticmethod
    def __grab_random_and_remove(rand_list:List[Tuple[int,int]]):
        r = choice(rand_list)
        rand_list.remove(r)
        return r

    @staticmethod
    def __gen_safe_spot_list(x_range, y_range):

        for y in y_range:
            for x in x_range:
                yield Coords(x=x,y=y)

    def __init__(self, gd:GameData, x:int, y:int):

        #self.astroObjects = [Sector.__buildSlice(gd.subsec_size_x) for s in gd.subsec_size_range_y]
        self.safe_spots = list(SubSector.__gen_safe_spot_list(gd.subsec_size_range_x, gd.subsec_size_range_y))
        self.coords = Coords(x=x,y=y)
        #self.x = x
        #self.y = y

        #print(stars)

        self.stars_dict:Dict[Coords, Star] = {}

        self.total_stars = 0
        
        #self.planets = []
        self.planets_dict:Dict[Coords, Planet] = {}
        self.friendly_planets = 0
        self.unfriendly_planets = 0
        self.barren_planets = 0
    
        
        self.big_ships = 0
        self.small_ships = 0
        self.player_present = False

    def random_setup(self, star_number_weights:Iterable[int], star_number_weights_len:int):

        stars = choices(range(star_number_weights_len), cum_weights=star_number_weights)[0]

        for i in range(stars):
            x, y = SubSector.__grab_random_and_remove(self.safe_spots)

            xy = Coords(x=x,y=y)

            #self.astroObjects[y][x] = '*'
            self.total_stars+=1
            self.stars_dict[xy] = Star(
                local_coords=xy, sector_coords=self.coords
            )
            
        if self.number_of_stars > 0:
            for p in range(randint(0, 5)):
                x,y = SubSector.__grab_random_and_remove(self.safe_spots)

                local_coords = Coords(x=x, y=y)

                p = Planet(
                    planet_habbitation=choice(PLANET_TYPES), 
                    local_coords=local_coords, sector_coords=self.coords
                )

                self.planets_dict[local_coords] = p
                
                if p.planet_habbitation == PLANET_FRIENDLY:
                    self.friendly_planets+=1
                elif p.planet_habbitation.supports_life and not p.planet_habbitation.can_ressuply:
                    self.unfriendly_planets += 1
                else:
                    self.barren_planets += 1
                
    @property
    def number_of_planets(self):
        return len(self.planets_dict)
    
    @property
    def number_of_stars(self):
        return len(self.stars_dict)
    """
    def checkSafeSpot(self, x, y):
        return self.astroObjects[y][x] == '.'
    """

    def find_random_safe_spot(self, ship_list:Optional[Iterable[Starship]]=None):
        if ship_list:
            ship_positions = [ship.local_coords for ship in ship_list if ship.sector_coords.x == self.x and ship.sector_coords.y == self.y]
            okay_spots = [c for c in self.safe_spots if c not in ship_positions]
            return choice(okay_spots)
        return choice(self.safe_spots)

    def find_random_safe_spots(self, how_many:int, ship_list:Optional[Iterable[Starship]]=None):
        if ship_list:
            ship_positions = [
                ship.local_coords for ship in ship_list if ship.sector_coords.x == self.x and 
                ship.sector_coords.y == self.y
            ]
            okay_spots = [c for c in self.safe_spots if c not in ship_positions]
            return choices(okay_spots, k=how_many)
        return choices(self.safe_spots, k=how_many)
    """
    def getSetOfSafeSpots(self, shipList=[]):

        safeSpots = []
        for iy in SUB_SECTOR_SIZE_RANGE_Y:
            for jx in SUB_SECTOR_SIZE_RANGE_X:
                if self.checkSafeSpot(jx, iy):
                    safeSpots.append(tuple([jx, iy]))

        if shipList != []:
            for s in shipList:
                if s.sector_coords.check(self.x, self.y):
                    t = tuple([s.local_coords.x, s.local_coords.y])
                    if t in safeSpots:
                        print('Trimming safespot')
                        safeSpots.remove(t)

        return safeSpots
    """

    """
    def __getSubslice(self, y):
        return''.join([self.astroObjects[y][x] for x in SUB_SECTOR_SIZE_RANGE_X])
    """

    """
    def getCopy(self, gd):
        return [[self.astroObjects[y][x] for x in gd.subsec_size_range_x] for y in gd.subsec_size_range_y]
    """

    def add_ship_to_sec(self, ship:Starship):
        if ship.ship_class.nation_code == "FEDERATION":
            self.player_present = True
        elif ship.ship_class.ship_type == "ESCORT":
            self.small_ships+= 1
        else:
            self.big_ships+= 1

    def remove_ship_from_sec(self, ship:Starship):
        if ship.ship_class.nation_code == "FEDERATION":
            self.player_present = False
        elif ship.ship_class.ship_type == "ESCORT":
            self.small_ships-= 1
        else:
            self.big_ships-= 1

class Planet(InterstellerObject):

    def __init__(self, planet_habbitation:PlanetHabitation, local_coords:Coords, sector_coords:Coords):
        
        super().__init__(local_coords, sector_coords)
        self.planet_habbitation = planet_habbitation# if random() < change_of_life_supporting_planets[self.planetType] else PlanetHabitation.PLANET_BARREN

        self.infastructure = self.planet_habbitation.generate_development()

    def __lt__(self, p:"Planet"):
        return self.infastructure < p.infastructure

    def __gt__(self, p:"Planet"):
        return self.infastructure > p.infastructure

    def __eq__(self, p: "Planet") -> bool:
        return self.local_coords == p.local_coords and self.sector_coords == p.sector_coords and self.planet_habbitation == p.planet_habbitation and self.infastructure == p.infastructure

    def canSupplyPlayer(self, player:Starship):
        return (
            self.planet_habbitation is PLANET_FRIENDLY and self.sector_coords == player.sector_coords and 
            self.local_coords.is_adjacent(player.local_coords) and 
            len(player.game_data.grab_ships_in_same_sub_sector(player)) < 1
        )

    def can_supply_torpedos(self, ship:Starship):
        
        if ship.ship_type_can_fire_torps:
            supply = ship.ship_class.max_torpedos - ship.get_total_torpedos
            
            if supply > 0:
                
                most_powerful = None
                
                old_damage = 0
                
                for t in ship.ship_class.torp_types:
                    
                    dam = ALL_TORPEDO_TYPES[t].damage
                    req = ALL_TORPEDO_TYPES[t].infrastructure
                    
                    if dam > old_damage and req <= self.infastructure:
                        
                        most_powerful = t
                
                return most_powerful, 0 if most_powerful is None else supply
                
        return None, 0

    def hit_by_torpedo(self, is_player:bool, game_data:GameData, torpedo:Torpedo):
        """Somebody did a bad, bad, thing (and it was probably you).

        Args:
            is_player (bool): Did the player fire a torpedo? Or was it someone else?
            game_data (GameData): [description]
            torpedo (Torpedo): The torpedo object. This contains the amount of damage to do to the planet.
        """
        player_is_in_same_system = game_data.player.sector_coords == self.sector_coords
        
        message_log = game_data.engine.message_log

        if is_player:
            game_data.player_record['times_hit_planet'] += 1

        if not self.planet_habbitation.supports_life and player_is_in_same_system:
            message_log.add_message('The torpedo struck the planet.')
            if is_player and self.planet_habbitation is PLANET_BOMBED_OUT:
                message_log.add_message('Now you are just being petty.')
        else:
            infrustructure_damage = uniform(
                torpedo.infrastructure * 0.5, torpedo.infrastructure) * 10 * self.infastructure

            if is_player:
                game_data.player_record["deathtoll"] += infrustructure_damage

            how_many_killed = "hundreds"

            des = (
                "hundreds of millions",
                "tens of millions",
                "millions",
                "hundreds of thousands",
                "tens of thousands",
                "thousands"
            )

            for i, deathtoll in enumerate(des):
                if infrustructure_damage // pow(10, -i) > 0:
                    how_many_killed = deathtoll
                    break
            
            self.infastructure-= infrustructure_damage

            if self.infastructure <= 0:
                self.infastructure = 0

                if player_is_in_same_system:
                    message_log.add_message(
                        f'The torpedo impacted the planet, killing {how_many_killed} and destroying the last vestages of civilisation.'
                    )
                if is_player:

                    game_data.player_record['planets_depopulated'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    message_log.add_message('You will definitly be charged with a war crime.', colors.red)
                
                self.planet_habbitation = PLANET_BOMBED_OUT

            elif self.planet_habbitation is PLANET_FRIENDLY:

                if player_is_in_same_system:
                    message_log.add_message(f'The torpedo struck the planet, killing {how_many_killed}.')

                if is_player:
                    self.planet_habbitation = PLANET_ANGERED

                    game_data.player_record['planets_angered'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    
                    message_log.add_message('The planet has severed relations with the Federation.')

            elif self.planet_habbitation is PLANET_PREWARP:
                if player_is_in_same_system:
                    message_log.add_message(
                        f'The torpedo struck the planet, killing {how_many_killed} of unsuspecting inhabitents.'
                    )
                if is_player:
                    game_data.player_record['times_hit_prewarp_planet'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1

                    message_log.add_message('This is a grevous viloation of the prime directive!', colors.red)
            else:
                if player_is_in_same_system:
                    message_log.add_message(f'The torpedo struck the planet, killing {how_many_killed}.')
                if is_player:
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    message_log.add_message('You will probably be charged with a war crime.', colors.red)
