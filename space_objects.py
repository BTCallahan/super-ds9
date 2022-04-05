from __future__ import annotations
from typing import Dict, Iterable, List, Optional,  Tuple, TYPE_CHECKING
from random import choice, choices, randint, uniform, random
from itertools import accumulate
from coords import Coords
from data_globals import PLANET_NEUTRAL, PLANET_BARREN, PLANET_BOMBED_OUT, PLANET_FRIENDLY, PLANET_PREWARP, PLANET_RELATIONS, PLANET_TYPES, PLANET_WARP_CAPABLE, PlanetHabitation, PlanetRelation, PLANET_RELATION_DICT
import colors
from nation import Nation
from torpedo import ALL_TORPEDO_TYPES, Torpedo

if TYPE_CHECKING:
    from game_data import GameData
    from message_log import MessageLog
    from starship import Starship

star_number_weights = tuple(accumulate((5, 12, 20, 9, 6, 3)))
star_number_weights_len = len(star_number_weights)

class CanDockWith:
    
    def can_dock_with(self, starship:Starship, require_adjacent:bool=True):
        raise NotImplementedError

    @property
    def get_dock_repair_factor(self):
        raise NotImplementedError

class InterstellerObject:
    
    def __init__(self, local_coords:Coords, sector_coords:Coords, system:SubSector) -> None:
        self.local_coords = local_coords
        self.sector_coords = sector_coords
        self.system = system
    
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

    def __init__(self, local_coords:Coords, sector_coords:Coords, system:SubSector):
        super().__init__(local_coords, sector_coords, system)
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

class SubSectorInfo:
    
    def __init__(self, x:int, y:int) -> None:
        self.coords = Coords(x=x,y=y)
        self.total_stars = 0
        
        self.planets_dict:Dict[Coords, Planet] = {}
        self.friendly_planets = 0
        self.neutral_planets = 0
        self.unfriendly_planets = 0
        self.barren_planets = 0
    
        self.objectives = 0
        
        self.hostile_ships = 0
        self.allied_ships = 0
        
        self.needs_updating = True

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
        self.game_data = gd

        self.stars_dict:Dict[Coords, Star] = {}

        self.total_stars = 0
        
        #self.planets = []
        self.planets_dict:Dict[Coords, Planet] = {}
        self.friendly_planets = 0
        self.neutral_planets = 0
        self.unfriendly_planets = 0
        self.barren_planets = 0
    
        self.objectives = 0
        
        self.hostile_ships = 0
        self.allied_ships = 0
        self.player_present = False

    @property
    def display_hostile_ships(self):
        return min(9, self.hostile_ships)
    
    @property
    def display_allied_ships(self):
        return min(9, self.allied_ships)

    def random_setup(self, star_number_weights:Iterable[int], star_number_weights_len:int):

        stars = choices(range(star_number_weights_len), cum_weights=star_number_weights)[0]

        for i in range(stars):
            x, y = SubSector.__grab_random_and_remove(self.safe_spots)

            xy = Coords(x=x,y=y)

            #self.astroObjects[y][x] = '*'
            self.total_stars+=1
            self.stars_dict[xy] = Star(
                local_coords=xy, sector_coords=self.coords, system=self
            )
        
        number_of_stars = self.number_of_stars
            
        if number_of_stars > 0:
            
            if number_of_stars == 1:
                
                number_of_planets = randint(0, 4)
            
            elif number_of_stars == 2:
                
                number_of_planets = randint(1, 6)
            else:
                number_of_planets = randint(2, 8)
            
            for p in range(number_of_planets):
                x,y = SubSector.__grab_random_and_remove(self.safe_spots)

                local_coords = Coords(x=x, y=y)
                
                planet_habbitation = choice(PLANET_TYPES)
                
                has_disposition_towards_warp_capiable_civs = planet_habbitation.has_disposition_towards_warp_capiable_civs
                
                player_planet_relation, enemy_planet_relation = (
                    choice(PLANET_RELATIONS), choice(PLANET_RELATIONS)
                ) if has_disposition_towards_warp_capiable_civs else (
                    PlanetRelation.HOSTILE, PlanetRelation.HOSTILE
                )
                p = Planet(
                    planet_habbitation=planet_habbitation, 
                    player_planet_relation = player_planet_relation,
                    enemy_planet_relation = enemy_planet_relation,
                    local_coords = local_coords, sector_coords=self.coords,
                    system=self
                )
                self.planets_dict[local_coords] = p
                
                if has_disposition_towards_warp_capiable_civs:
                    
                    if player_planet_relation == PlanetRelation.FRIENDLY:
                        
                        self.friendly_planets += 1
                        
                    elif player_planet_relation == PlanetRelation.NEUTRAL:
                        
                        self.neutral_planets += 1
                    else:
                        self.unfriendly_planets += 1
                else:
                    self.unfriendly_planets += 1

    def count_planets(self):
        
        planet_habitations = [
            planet.get_habbitation(self.game_data.player) for planet in self.planets_dict.values()
        ]
        
        total_planets = len(planet_habitations)
        
        self.friendly_planets = len(
            [planet for planet in planet_habitations if planet == PLANET_FRIENDLY]
        )
        self.neutral_planets = len(
            [planet for planet in planet_habitations if planet == PLANET_NEUTRAL]
        )
        self.unfriendly_planets = total_planets - (self.friendly_planets + self.neutral_planets)
    
    @property
    def number_of_planets(self):
        return len(self.planets_dict)
    
    @property
    def number_of_stars(self):
        return len(self.stars_dict)
    
    def find_random_safe_spot(self, ship_list:Optional[Iterable[Starship]]=None):
        if ship_list:
            ship_positions = set(
                ship.local_coords.create_coords() for ship in ship_list if 
                ship.sector_coords.x == self.x and ship.sector_coords.y == self.y
            )
            okay_spots = [c for c in self.safe_spots if c not in ship_positions]
            return choice(okay_spots)
        return choice(self.safe_spots)

    def find_random_safe_spots(self, how_many:int, ship_list:Optional[Iterable[Starship]]=None):
        if ship_list:
            ship_positions = set(
                ship.local_coords.create_coords() for ship in ship_list if ship.sector_coords.x == self.x and 
                ship.sector_coords.y == self.y
            )
            okay_spots = [c for c in self.safe_spots if c not in ship_positions]
            return choices(okay_spots, k=how_many)
        return choices(self.safe_spots, k=how_many)
    
    def add_ship_to_sec(self, ship:Starship):
        if ship is ship.game_data.player:
            self.player_present = True
        elif ship.ship_class.ship_type == "ESCORT":
            self.allied_ships+= 1
        else:
            self.hostile_ships+= 1

    def remove_ship_from_sec(self, ship:Starship):
        if ship is ship.game_data.player:
            self.player_present = False
        elif ship.ship_class.ship_type == "ESCORT":
            self.allied_ships-= 1
        else:
            self.hostile_ships-= 1

class Planet(InterstellerObject, CanDockWith):

    def __init__(
        self, 
        planet_habbitation:PlanetHabitation, 
        player_planet_relation:PlanetRelation,
        enemy_planet_relation:PlanetRelation,
        local_coords:Coords, sector_coords:Coords, 
        system:SubSector
    ):    
        super().__init__(local_coords, sector_coords, system)
        self.planet_habbitation = planet_habbitation
        self.player_planet_relation = player_planet_relation
        self.enemy_planet_relation = enemy_planet_relation

        self.infastructure = self.planet_habbitation.generate_development()
        
        self.display_status = PLANET_RELATION_DICT[
            self.player_planet_relation
        ] if planet_habbitation.has_disposition_towards_warp_capiable_civs else planet_habbitation

    def __lt__(self, p:"Planet"):
        return self.infastructure < p.infastructure

    def __gt__(self, p:"Planet"):
        return self.infastructure > p.infastructure

    def __eq__(self, p: "Planet") -> bool:
        return (
            self.local_coords == p.local_coords and self.sector_coords == p.sector_coords and 
            self.planet_habbitation == p.planet_habbitation and self.infastructure == p.infastructure
        )
    
    def can_dock_with(self, starship: Starship, require_adjacent:bool=True):
        return (
            self.planet_habbitation is PLANET_FRIENDLY and self.local_coords.is_adjacent(other=starship.local_coords)
        ) if require_adjacent else (
            self.planet_habbitation is PLANET_FRIENDLY
        )
        
    @property
    def get_dock_repair_factor(self):
        
        return self.infastructure

    def can_supply_torpedos(self, ship:Starship):
        
        planet_relation = self.enemy_planet_relation if ship.is_enemy else self.player_planet_relation
        
        if ship.ship_class.max_torpedos and planet_relation == PlanetRelation.FRIENDLY:
            
            supply = ship.ship_class.max_torpedos - ship.torpedo_launcher.get_total_number_of_torpedos
            
            if supply > 0:
                
                most_powerful = None
                
                old_damage = 0
                
                for t in ship.ship_class.allowed_torpedos_tuple:
                    
                    dam = t.damage
                    req = t.infrastructure
                    
                    if dam > old_damage and req <= self.infastructure:
                        
                        most_powerful = t
                
                return most_powerful, 0 if most_powerful is None else supply
                
        return None, 0

    def get_habbitation(self, ship_is_enemy:bool):
        
        return self.enemy_display_status if ship_is_enemy else self.player_display_status

    def hit_by_torpedo(
        self, 
        guilty_party:Starship,
        game_data:GameData, torpedo:Torpedo
    ):
        """Somebody did a bad, bad, thing (and it was probably you).

        Args:
            is_player (bool): Did the player fire a torpedo? Or was it someone else?
            game_data (GameData): [description]
            torpedo (Torpedo): The torpedo object. This contains the amount of damage to do to the planet.
        """
        player_is_in_same_system = game_data.player.sector_coords == self.sector_coords
        
        message_log = game_data.engine.message_log
        
        is_player = guilty_party.is_controllable

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
                
                self.display_status = PLANET_BOMBED_OUT
                self.system.count_planets()

            elif self.planet_habbitation is PLANET_WARP_CAPABLE:
                
                guilty_party_is_enemy = guilty_party.is_enemy
                
                planet_disposition = self.enemy_planet_relation if guilty_party_is_enemy else self.player_planet_relation

                if player_is_in_same_system:
                    message_log.add_message(
                        f'The torpedo struck the planet, killing {how_many_killed}.', 
                        colors.red if is_player else colors.white
                    )

                if planet_disposition == PlanetRelation.FRIENDLY:
                    
                    if player_is_in_same_system:
                        message_log.add_message(
                            f'Relations between planet {guilty_party.nation.name_short} have cooled considerably.'
                        )
                    if guilty_party_is_enemy:
                    
                        self.enemy_planet_relation = PlanetRelation.NEUTRAL
                    else:
                        self.player_planet_relation = PlanetRelation.NEUTRAL
                        
                        if is_player:
                            
                            message_log.add_message(
                                "This will definitly go on your record.", colors.red
                            )
                            game_data.player_record['planets_aggravated'] += 1
                            game_data.player_record['times_hit_poipulated_planet'] += 1
                    self.display_status = PLANET_RELATION_DICT[
                        self.player_planet_relation
                    ] if self.planet_habbitation.has_disposition_towards_warp_capiable_civs else self.planet_habbitation
                    
                    self.system.count_planets()
                            
                elif planet_disposition == PlanetRelation.NEUTRAL:
                    
                    if player_is_in_same_system:
                        message_log.add_message(
                            f'The planet has severed relations with the {guilty_party.nation.name_short}.'
                        )
                    if guilty_party_is_enemy:
                        
                        self.enemy_planet_relation = PlanetRelation.HOSTILE
                    else:
                        self.planet_habbitation = PlanetRelation.HOSTILE
                        
                        if is_player:
                            self.planet_habbitation = PLANET_NEUTRAL
                            
                            message_log.add_message('You will probably be charged with a war crime.', colors.red)

                            game_data.player_record['planets_angered'] += 1
                            game_data.player_record['times_hit_poipulated_planet'] += 1
                            
                    self.display_status = PLANET_RELATION_DICT[
                        self.player_planet_relation
                    ] if self.planet_habbitation.has_disposition_towards_warp_capiable_civs else self.planet_habbitation
                    
                    self.system.count_planets()
                else:
                    if is_player:
                        
                        message_log.add_message('You will probably be charged with a war crime.', colors.red)
                        
                        game_data.player_record['times_hit_poipulated_planet'] += 1
                
            elif self.planet_habbitation is PLANET_PREWARP:
                if player_is_in_same_system:
                    message_log.add_message(
                        f'The torpedo struck the planet, killing {how_many_killed} of unsuspecting inhabitents.'
                    )
                if is_player:
                    game_data.player_record['times_hit_prewarp_planet'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1

                    message_log.add_message('This is a grevous viloation of the prime directive!', colors.red)
                    self.system.count_planets()
            else:
                if player_is_in_same_system:
                    message_log.add_message(f'The torpedo struck the planet, killing {how_many_killed}.')
                if is_player:
                    
                    message_log.add_message('You will probably be charged with a war crime.', colors.red)
                    self.system.count_planets()
                    
                raise ValueError("You should not see this ")
