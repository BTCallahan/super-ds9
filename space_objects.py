from __future__ import annotations
from collections import defaultdict
from enum import Enum, auto
from typing import Dict, Iterable, List, Optional,  Tuple, TYPE_CHECKING
from random import choice, choices, randint, randrange, uniform, random
from itertools import accumulate
from string import ascii_lowercase
from coords import Coords
from data_globals import PLANET_ANGERED, PLANET_BARREN, PLANET_BOMBED_OUT, PLANET_FRIENDLY, PLANET_PREWARP, PLANET_TYPES, STATUS_ACTIVE, PlanetHabitation
import colors
from torpedo import Torpedo
from string import ascii_lowercase, ascii_uppercase

if TYPE_CHECKING:
    from game_data import GameData
    from message_log import MessageLog
    from starship import Starship


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
    
    def hit_by_torpedo(self, is_player:bool, game_data:GameData, torpedo:Torpedo):
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


    
"""
TODO - star and planet naming conventions: randomly generateed name for star in sector. If there are more then one star,
append Alpha, Beta, Gama, or Delta in front of the name. For planets use the star name followed by a Roman neumeral.

Steller evoloution:
Low mass:
Red Dwarf -> Blue Dwarf - > White Dwarf - > Black Dwarf
0.4 -> 0.5M:
Yellow Dwarf - > Red Giant -> Blue Sub Dwarf -> White Dwarf
0.5 -> 1M
Yellow Dwarf - > Red Giant -> White Dwarf
More then 1M
Yellow Sub-giant

More then 8-12M:
Blue Sub-giant - > Blue Giant -> Yellow Superginat -> Red Superginat -> Yellow Hypergiant
Blue Sub-giant - > Blue Giant -> Red Giant

Brown Dwarf
Brown Sub-dwarf
Red Sub-dwarf
Yellow Sub-dwarf

Blue-White Sub-giant
Orange Giant
Orange Sub-dwarf

Blue supergiant -> Red Giant -> Blue Giant

Blue sub dwarf: about 0.5 solar masses, post red giant

"""


class StarType(Enum):

    SUB_DWARF = auto()
    DWARF = auto()
    SUB_GIANT = auto()
    GIANT = auto()
    SUPER_GIANT = auto()
    HYPER_GIANT = auto()

class StarColor(Enum):

    BROWN = auto()
    RED = auto()
    ORANGE = auto()
    YELLOW = auto()
    YELLOW_WHITE = auto()
    WHITE = auto()
    BLUE_WHITE = auto()
    BLUE = auto()

star_color_dict = {
    StarColor.BROWN : colors.star_brown,
    StarColor.RED : colors.star_red,
    StarColor.ORANGE : colors.star_orange,
    StarColor.YELLOW : colors.star_yellow,
    StarColor.YELLOW_WHITE : colors.star_yellow_white,
    StarColor.WHITE : colors.white,
    StarColor.BLUE_WHITE : colors.star_blue_white,
    StarColor.BLUE : colors.star_blue
}

planet_generation_chances = {
    (StarType.SUB_DWARF, StarColor.BROWN), ((50, 60, 65), 0.045),
    (StarType.SUB_DWARF, StarColor.RED), ((45, 55, 60, 61), 0.055),
    (StarType.SUB_DWARF, StarColor.BLUE), ((), 0.03)

    (StarType.DWARF, StarColor.WHITE), ((40, 60, 72, 80, 84), 0.001),
    (StarType.DWARF, StarColor.BROWN), ((50, 63, 68, 70), 0.05),
    (StarType.DWARF, StarColor.RED), ((45, 58, )),
    ()
}

star_number_weights = tuple(accumulate((5, 12, 20, 9, 6, 3)))
star_numbers = tuple(range(len(star_number_weights)))
class Star(InterstellerObject):
    orderSuffexes = ['Alpha ', 'Beta ', 'Gamma ', 'Delta ']
    planetSuffexes = ['', ' I', ' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII']

    def __init__(self, 
        local_coords:Coords, sector_coords:Coords, *,
        star_order:int=-1,
        star_name:str,
        star_temp:int,
        star_mass:float,
        star_radius:float,
        star_luminosity:float,
        star_type:str,
        star_class:Optional[Tuple[str]] = None,
        nova_threshold:float,
        nova_range:int,
        system:SubSector,
    ):
        super().__init__(local_coords, sector_coords, system)

        self.name = star_name if star_order == -1 else f"{star_name} {ascii_lowercase[star_order]}"
        self.star_type = star_type
        self.kelvins = star_temp
        self.mass = star_mass
        self.radius = star_radius
        self.luminosity = star_luminosity,
        self.abs_mag = 0
        self.star_color = None
        self.nova_threshold = nova_threshold
        self.nova_range = nova_range
        self.nova_status = 0.0

        if star_class:
            self.star_class = choice(star_class)
        else:
            if self.kelvins > 28000:
                
                self.star_color = colors.star_blue
                self.star_class = "O"
                
            elif self.kelvins > 10000:
                
                self.star_color = colors.star_blue_white
                self.star_class = "B"
                
            elif self.kelvins > 7500:
                
                self.star_color = colors.star_white
                self.star_class = "A"
                
            elif self.kelvins > 6000:
                
                self.star_color = colors.star_yellow_white
                self.star_class = "F"
                
            elif self.kelvins > 5000:
                
                self.star_color = colors.star_yellow
                self.star_class = "G"
                
            elif self.kelvins > 3500:
                
                self.star_color = colors.star_orange
                self.star_class= "K"
                
            elif self.kelvins > 2500:
                
                self.star_color = colors.star_red
                self.star_class= "M"
                
            else:
                self.star_color = colors.star_brown if self.kelvins > 0 else colors.black
                self.star_class = "L" if self.kelvins > 500 else "T"

        

        self.bg = colors.white if self.star_color is colors.black else colors.black

    @property
    def can_go_nova(self):
        return self.nova_threshold > 0

    def getPlanetName(self, planetOrder):
        return self.name + self.planetSuffexes[planetOrder]
    
    def hit_by_torpedo(self, is_player:bool, game_data:GameData, torpedo:Torpedo):

        if not self.can_go_nova:
            return

        self.nova_status += torpedo.infrastructure

        if self.nova_status >= self.nova_threshold:
            
            ships = [ship for ship in game_data.total_starships if ship.sector_coords == self.sector_coords and (ship.ship_status.is_collidable)]

            for ship in ships:
                distance = ship.local_coords.distance(coords=self.local_coords)

                if distance <= self.nova_range:
                    
                    ship.take_damage(amount=(self.nova_range - distance) * 1000, text="A minor nova.")

            self.nova_status -= self.nova_threshold

JUPITER_MASS = 1/1000

def variance_roll(min_:float, max_:float, variance:float, rolled_percentage:float):
    
    amount:float = (max_ - min_) * rolled_percentage
    
    variance_amount = amount * variance
    
    v = min_ + amount + uniform(variance_amount, -variance_amount)
    
    return min(max(min_, v), max_)

class StarTemplate:

    def __init__(self, *, 
        name:str, 
        temp_min:int, temp_max:int,
        mass_min:float, mass_max:float,
        radius_min:float, radius_max:float,
        luminosity_min:float, luminosity_max:float,
        nova_threshold:float, nova_range:int,
        star_class_override:Optional[Tuple[str]]=None,
        planet_generation_chances:Iterable[float],
        planet_type_chances:Dict[PlanetType,float]

    ) -> None:
        self.name = name
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.mass_min = mass_min
        self.mass_max = mass_max
        self.radius_min = radius_min
        self.radius_max = radius_max
        self.luminosity_min = luminosity_min
        self.luminosity_max = luminosity_max
        self.nova_threshold = nova_threshold
        self.nova_range = nova_range
        self.star_class_override = star_class_override
        self.planet_generation_chances = accumulate(planet_generation_chances)
        self.planet_type_chances = {
            k : v for k,v in zip(
                planet_type_chances.keys(),
                accumulate(planet_type_chances.values())
            )
        }

    def create_star(self, *, 
        order:int=0, 
        local_coords:Coords, sector_coords:Coords,
        name:str
    ):
        varation_percentage = random()
        variance = 0.025
        
        return Star(
            localCoords=local_coords,
            sectorCoords=sector_coords,
            starOrder=order,
            star_name=name,
            star_temp=variance_roll(self.temp_min, self.temp_max, variance, varation_percentage),
            star_mass=variance_roll(self.mass_min, self.mass_max, variance, varation_percentage),
            star_radius=variance_roll(self.radius_min, self.radius_max, variance, varation_percentage),
            star_luminosity=variance_roll(self.luminosity_min, self.luminosity_max, variance, varation_percentage),
            star_type=self.name,
            star_class=self.star_class_override
        )

o_type_main_sequence_star = StarTemplate(
    name="O-type main-sequence star",
    temp_max=50000,
    temp_min=30000,
    luminosity_max=1000000,
    luminosity_min=40000,
    mass_max=90,
    mass_min=15,
    radius_max=10,
    radius_min=8,
)
b_type_main_sequence_star = StarTemplate(
    name="B-type main-sequence star",
    temp_max=30000,
    temp_min=10000,
    mass_max=16,
    mass_min=2
)
a_type_main_sequence_star = StarTemplate(
    name="A-type main-sequence star",
    temp_max=10000,
    temp_min=7600,
    luminosity_max=38,
    luminosity_min=8,
    mass_max=2.1,
    mass_min=1.4,
    radius_max=2.2,
    radius_min=1.74
)
f_type_main_sequence_star = StarTemplate(
    name="F-type main-sequence star",
    temp_max=7600,
    temp_min=6000,
    luminosity_max=8,
    luminosity_min=1.5,
    mass_max=1.4,
    mass_min=1,
    radius_max=1.73,
    radius_min=1.1
)
g_type_main_sequence_star = StarTemplate(
    name="G-type main-sequence star (Yellow Dwarf)",
    temp_max=6000,
    temp_min=5300,
    luminosity_max=1.5,
    luminosity_min=0.55,
    mass_max=1.1,
    mass_min=0.9,
    radius_max=1.1,
    radius_min=0.85
)
k_type_main_sequence_star = StarTemplate(
    name="K-type main-sequence star (Orange Dwarf)",
    temp_max=5200,
    temp_min=3900,
    luminosity_max=0.46,
    luminosity_min=0.075,
    mass_max=0.8,
    mass_min=0.5,
    radius_max=0.81,
    radius_min=0.6
)
m_type_main_sequence_star = StarTemplate(
    name="M-type main-sequence star (Red Dwarf)",
    temp_max=3900,
    temp_min=2000,
    luminosity_max=0.075,
    luminosity_min=0.00003,
    mass_max=0.6,
    mass_min=0.075,
    radius_max=0.6,
    radius_min=0.09
)
wolf_rayet_star = StarTemplate(
    name="Wolf–Rayet star",
    temp_max=210000,
    temp_min=2000,
    mass_max=200,
    mass_min=10,
    radius_max=20,
    radius_min=0.89,
    star_class_override=("WR", "WO", "WN")
)
brown_dwarf = StarTemplate(
    name="Brown Dwarf",
    temp_max=2800,
    temp_min=300,
    mass_max=80*JUPITER_MASS,
    mass_min=13*JUPITER_MASS,
    radius_max=0.12,
    radius_min=0.08
)
methane_dwarf = StarTemplate(
    name="Methane Dwarf",
    temp_max=1300,
    temp_min=550,
)
b_type_subdwarf = StarTemplate(
    name="B-type subdwarf",
    temp_max=40000,
    temp_min=20000,
    mass_max=0.51,
    mass_min=0.49,
    radius_max=0.25,
    radius_min=0.15,
)
o_type_subdwarf = StarTemplate(
    name="O-type Subdwarf",
    temp_max=100000,
    temp_min=40000,
    mass_max=0.51,
    mass_min=0.49,
)
blue_giant = StarTemplate(
    name="Blue Giant",
    temp_max=30000,#placeholder
    temp_min=10000,
    mass_max=50,#placeholder
    mass_min=2
)
yellow_giant = StarTemplate(
    name="Yellow Giant",
    temp_max=7000,
    temp_min=4000
)
red_giant = StarTemplate(
    name="Red Giant",
    temp_max=5000,
    temp_min=4000,#placeholder value, check this
    mass_max=8,
    mass_min=0.3,   
)
blue_supergiant = StarTemplate(
    name="Blue Supergiant",
    temp_max=50000,
    temp_min=10000,
    mass_max=300,
    mass_min=10,
    luminosity_max=1000000,
    luminosity_min=10000
)
yellow_supergiant = StarTemplate(
    name="Yellow Supergiant",
    temp_max=7000,
    temp_min=4000,
    mass_max=12,
    mass_min=5,
    luminosity_max=100000,
    luminosity_min=1000
)
red_supergiant = StarTemplate(
    name="Red Supergiant",
    mass_max=40,
    mass_min=10
)
yellow_hypergiant = StarTemplate(
    name="Yellow Hypergiant"
)

def create_star_chances():
    
    for star, chance in zip(
        (
            o_type_main_sequence_star, 
            b_type_main_sequence_star,
            a_type_main_sequence_star,
            f_type_main_sequence_star,
            g_type_main_sequence_star,
            k_type_main_sequence_star,
            m_type_main_sequence_star
        ),
        accumulate(
            (
                1/10000000,
                0.1/100,
                0.7/100,
                2/100,
                3.5/100,
                8/100,
                80/100
            )
        )
    ):
        yield star, chance

STAR_CHANCES = tuple(
    create_star_chances()
)

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

        stars = choices(star_numbers, cum_weights=star_number_weights)[0]

        for i in range(stars):
            x, y = SubSector.__grab_random_and_remove(self.safe_spots)

            xy = Coords(x=x,y=y)

            #self.astroObjects[y][x] = '*'
            self.total_stars+=1
            self.stars_dict[xy] = Star(
                local_coords=xy, sector_coords=self.coords, system=self
            )
            
        if self.number_of_stars > 0:
            for p in range(randint(0, 5)):
                x,y = SubSector.__grab_random_and_remove(self.safe_spots)

                local_coords = Coords(x=x, y=y)

                p = Planet(
                    planet_habbitation=choice(PLANET_TYPES), 
                    local_coords=local_coords, sector_coords=self.coords,
                    system=self
                )

                self.planets_dict[local_coords] = p
                
                if p.planet_habbitation == PLANET_FRIENDLY:
                    self.friendly_planets+=1
                else:
                    self.unfriendly_planets += 1

    def count_planets(self):
        self.friendly_planets = len(
            [planet for planet in self.planets_dict.values() if planet.planet_habbitation is PLANET_FRIENDLY]
        )
        self.unfriendly_planets = len(
            [planet for planet in self.planets_dict.values() if planet.planet_habbitation is not PLANET_FRIENDLY]
        )
    
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

class PlanetType(Enum):

    CLASS_D = auto()
    CLASS_H = auto()
    CLASS_J = auto()
    CLASS_K = auto()
    CLASS_L = auto()
    CLASS_M = auto()
    CLASS_N = auto()
    CLASS_R = auto()
    CLASS_Y = auto()

change_of_life_supporting_planets = defaultdict(float,
    {
        PlanetType.CLASS_M : 0.5,
        PlanetType.CLASS_H : 0.1,
        PlanetType.CLASS_N : 0.25,
        PlanetType.CLASS_R : 0.05,
        PlanetType.CLASS_Y : 0.01
    }
)


class Planet(InterstellerObject, CanDockWith):

    def __init__(
        self, planet_habbitation:PlanetHabitation, planetType:PlanetType, local_coords:Coords, sector_coords:Coords, system:SubSector, name:str=""
    ):    
        super().__init__(local_coords, sector_coords, system)

        self.infastructure = self.planet_habbitation.generate_development()

        self.planetType = planetType

        self.planet_habbitation = planet_habbitation
                
        self.name = name

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
        
        if ship.ship_type_can_fire_torps:
            
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

            self.infastructure-= infrustructure_damage

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
                    self.system.count_planets()
                
                self.planet_habbitation = PLANET_BOMBED_OUT

            elif self.planet_habbitation is PLANET_FRIENDLY:

                if player_is_in_same_system:
                    message_log.add_message(f'The torpedo struck the planet, killing {how_many_killed}.')

                if is_player:
                    self.planet_habbitation = PLANET_ANGERED

                    game_data.player_record['planets_angered'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    
                    message_log.add_message('The planet has severed relations with the Federation.')
                    self.system.count_planets()

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
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    message_log.add_message('You will probably be charged with a war crime.', colors.red)
                    self.system.count_planets()

CONSTELLATIONS = (
    "Eridani",
    "Cygni",
    "Pegasi",
    "Cancri",
    "Onias",
    "Majoris",
    "Leonis",
    "Doradus",
    
    "Lalande",
    "Luyten",
    "Kelsin",
    "Lalande",
    "Questar",
    "Ross",
    "Tambor",
    
    "Lupi",
    "Moab",
    "Cassius",
    "Geminorum",
    "Hutzel",
    "Lyrae",
    "Niobe",
    "Penthe",
    "Portolan",
    "Praxillus",
    "Stromgren",
    "Dikon",
    "Hydrae",
    "Indi",
    "Legato",
    "Arigulon",
    "Orionis",
)

ORDER_SUFFEXES = (
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Tau", "Phi", "Omicron", "Theta", "Zeta", "Omega"
)

def generate_system_name():
    
    star_method = randrange(6)
    
    if star_method == 0:
        
        return f"{choice(CONSTELLATIONS)} {randint(1200)}-{choice(ORDER_SUFFEXES)}"
        
    if star_method == 1:
        
        return f"{choice(CONSTELLATIONS)} {randint(1200)}-{randint(15)}"
        
    if star_method == 2:
        
        return f"{randint(100)} {choice(CONSTELLATIONS)}"
        
    if star_method == 3:
        
        return f"{choice(CONSTELLATIONS)} {randint(100)}"

    if star_method == 4:
        
        return f"{choice(ORDER_SUFFEXES)} {choice(CONSTELLATIONS)}"
    
    return f"{choice(ORDER_SUFFEXES)} {randint(10)}{choice(ascii_uppercase)}"

def set_star_names(stars: Iterable[Star], system_name: str):

    if len(stars) > 1:
        
        for i, star in enumerate(stars):

            star.name = f"{system_name} {ascii_lowercase[i]}"
    else:
        stars[0].name = system_name

def set_planet_names(planets: Iterable[Planet], system_name: str):

    if len(planets) > 1:

        planet_suffexes = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X')

        for i, planet in enumerate(planets):

            planet.name = f"{planet.name} {planet_suffexes[i]}"
