from __future__ import annotations
from typing import Dict, Iterable, List, Optional,  Tuple, TYPE_CHECKING
from random import choice, choices, randint, uniform, random
from itertools import accumulate
from coords import Coords
from data_globals import PLANET_TYPES, PlanetHabitation, ShipTypes
import colors

if TYPE_CHECKING:
    from game_data import GameData
    from message_log import MessageLog
    from starship import Starship

star_number_weights = tuple(accumulate((5, 12, 20, 9, 6, 3)))
star_number_weights_len = len(star_number_weights)

class Star:
    orderSuffexes = ['Alpha ', 'Beta ', 'Gamma ', 'Delta ']
    planetSuffexes = ['', ' I', ' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII']

    def __init__(self, localCoords:Coords, sectorCoords:Coords):
        self.localCoords = localCoords
        self.sectorCoords = sectorCoords
        self.color = choice(
            (colors.star_blue,
            colors.star_blue_white,
            colors.star_brown,
            colors.star_orange,
            colors.star_red,
            colors.star_white,
            colors.star_yellow,
            colors.star_yellow_white,
            colors.black)
            )
        self.bg = colors.white if self.color is colors.black else colors.black

class SubSector:
    """A SubSector is a region of space that contains stars and planets. 

    Returns:
        [type]: [description]

    Yields:
        [type]: [description]
    """

    @staticmethod
    def __grabRandomAndRemove(randList:List[Tuple[int,int]]):
        r = choice(randList)
        randList.remove(r)
        return r

    @staticmethod
    def __genSafeSpotList(xRange, yRange):

        for y in yRange:
            for x in xRange:
                yield Coords(x=x,y=y)

    def __init__(self, gd:GameData, x:int, y:int):

        #self.astroObjects = [Sector.__buildSlice(gd.subsecSizeX) for s in gd.subsecSizeRangeY]
        self.safeSpots = list(SubSector.__genSafeSpotList(gd.subsecSizeRangeX, gd.subsecSizeRangeY))
        self.coords = Coords(x=x,y=y)
        #self.x = x
        #self.y = y

        #print(stars)

        self.stars_dict:Dict[Coords, Star] = {}

        self.totalStars = 0
        
        #self.planets = []
        self.planets_dict:Dict[Coords, Planet] = {}
        self.friendlyPlanets = 0
        self.unfriendlyPlanets = 0
        self.barren_planets = 0
        
        self.bigShips = 0
        self.smallShips = 0
        self.playerPresent = False

    def random_setup(self):

        stars = choices(range(star_number_weights_len), cum_weights=star_number_weights)[0]

        for i in range(stars):
            x, y = SubSector.__grabRandomAndRemove(self.safeSpots)

            xy = Coords(x=x,y=y)

            #self.astroObjects[y][x] = '*'
            self.totalStars+=1
            self.stars_dict[xy] = Star(
                localCoords=xy, sectorCoords=self.coords
                )
            

        if self.number_of_stars > 0:
            for p in range(randint(0, 5)):
                x,y = SubSector.__grabRandomAndRemove(self.safeSpots)

                local_coords = Coords(x=x, y=y)

                p = Planet(
                    planet_habbitation=choice(PLANET_TYPES), 
                    xy=local_coords, sector_x_y=self.coords
                )

                self.planets_dict[local_coords] = p
                
                if p.planet_habbitation == PlanetHabitation.PLANET_FRIENDLY:
                    self.friendlyPlanets+=1
                elif p.planet_habbitation == PlanetHabitation.PLANET_HOSTILE:
                    self.unfriendlyPlanets += 1
                else:
                    self.barren_planets += 1
                
        
    @property
    def numberOfPlanets(self):
        return len(self.planets_dict)
    
    @property
    def number_of_stars(self):
        return len(self.stars_dict)
    """
    def checkSafeSpot(self, x, y):
        return self.astroObjects[y][x] == '.'
    """

    def findRandomSafeSpot(self, shipList:Optional[Iterable[Starship]]=None):
        if shipList:
            ship_positions = [ship.localCoords for ship in shipList if ship.sectorCoords.x == self.x and ship.sectorCoords.y == self.y]
            okay_spots = [c for c in self.safeSpots if c not in ship_positions]
            return choice(okay_spots)
        return choice(self.safeSpots)

    def find_random_safe_spots(self, how_many:int, shipList:Optional[Iterable[Starship]]=None):
        if shipList:
            ship_positions = [ship.localCoords for ship in shipList if ship.sectorCoords.x == self.x and ship.sectorCoords.y == self.y]
            okay_spots = [c for c in self.safeSpots if c not in ship_positions]
            return choices(okay_spots, k=how_many)
        return choices(self.safeSpots, k=how_many)
    """
    def getSetOfSafeSpots(self, shipList=[]):

        safeSpots = []
        for iy in SUB_SECTOR_SIZE_RANGE_Y:
            for jx in SUB_SECTOR_SIZE_RANGE_X:
                if self.checkSafeSpot(jx, iy):
                    safeSpots.append(tuple([jx, iy]))

        if shipList != []:
            for s in shipList:
                if s.sectorCoords.check(self.x, self.y):
                    t = tuple([s.localCoords.x, s.localCoords.y])
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
        return [[self.astroObjects[y][x] for x in gd.subsecSizeRangeX] for y in gd.subsecSizeRangeY]
    """

    def addShipToSec(self, ship:Starship):
        if ship.shipData.shipType is ShipTypes.TYPE_ALLIED:
            self.playerPresent = True
        elif ship.shipData.shipType is ShipTypes.TYPE_ENEMY_SMALL:
            self.smallShips+= 1
        else:
            self.bigShips+= 1

    def removeShipFromSec(self, ship:Starship):
        if ship.shipData.shipType is ShipTypes.TYPE_ALLIED:
            self.playerPresent = False
        elif ship.shipData.shipType is ShipTypes.TYPE_ENEMY_SMALL:
            self.smallShips-= 1
        else:
            self.bigShips-= 1

    def tickOffPlanet(self):
        self.friendlyPlanets-=1
        self.unfriendlyPlanets+=1

    @property
    def hasFriendlyPlanets(self):
        return self.friendlyPlanets > 0

    @property
    def hasEnemyShips(self):
        return self.smallShips > 0 or self.bigShips > 0

    @property
    def getInfo(self):        
        return f'{self.friendlyPlanets}{self.unfriendlyPlanets}{"@" if self.playerPresent else "."}{self.bigShips}{self.smallShips}'

class Planet:

    def __init__(self, planet_habbitation:PlanetHabitation, xy:Coords, sector_x_y:Coords):
        
        self.planet_habbitation = planet_habbitation# if random() < change_of_life_supporting_planets[self.planetType] else PlanetHabitation.PLANET_BARREN
        
        self.localCoords = xy
        self.sectorCoords = sector_x_y

        self.infastructure = uniform(0.0, 1.0) if self.planet_habbitation is not PlanetHabitation.PLANET_BARREN else 0.0

    def __lt__(self, p:"Planet"):
        return self.infastructure < p.infastructure

    def __gt__(self, p:"Planet"):
        return self.infastructure > p.infastructure

    def __eq__(self, p: "Planet") -> bool:
        return self.localCoords == p.localCoords and self.sectorCoords == p.sectorCoords and self.planet_habbitation == p.planet_habbitation and self.infastructure == p.infastructure

    def canSupplyPlayer(self, player:Starship):
        return self.planet_habbitation is PlanetHabitation.PLANET_FRIENDLY and self.sectorCoords == player.sectorCoords and \
            self.localCoords.isAdjacent(player.localCoords) and len(player.game_data.grapShipsInSameSubSector(player)) < 1            

    def hitByTorpedo(self, isPlayer, game_data:GameData, message_log:MessageLog, damage=40):
        """Somebody did a bad, bad, thing.

        Args:
            isPlayer (bool): Did the player fire a torpedo?
            game_data (GameData): [description]
            message_log (MessageLog): [description]
            damage (int, optional): The amount of damage to do to the planet. Defaults to 40.
        """

        if self.planet_habbitation in {PlanetHabitation.PLANET_BARREN, PlanetHabitation.PLANET_BOMBED_OUT}:
            message_log.add_message('The torpedo struck the planet. ')
            if isPlayer:
                game_data.player_record['times_hit_planet'] += 1
                if self.planet_habbitation is PlanetHabitation.PLANET_BOMBED_OUT:
                    message_log.add_message('Now you are just being petty. ')
        else:
            infrustructure_damage = uniform(damage * 0.5, damage * 1.0) * 0.1 * self.infastructure

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

                message_log.add_message(f'The torpedo impacted the planet, killing {how_many_killed} and destroying the last vestages of civilisation. ')
                if isPlayer:

                    game_data.player_record['planets_depopulated'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    message_log.add_message('You will definitly be charged with a war crime. ')
                
                self.planet_habbitation = PlanetHabitation.PLANET_BOMBED_OUT

            elif self.planet_habbitation is PlanetHabitation.PLANET_FRIENDLY:

                message_log.add_message(f'The torpedo struck the planet, killing {how_many_killed}. ')

                if isPlayer:
                    self.planet_habbitation = PlanetHabitation.PLANET_ANGERED

                    game_data.player_record['planets_angered'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    
                    message_log.add_message('The planet has severed relations with the Federation. ')

            elif self.planet_habbitation is PlanetHabitation.PLANET_PREWARP:

                message_log.add_message(f'The torpedo struck the planet, killing {how_many_killed} of unsuspecting inhabitents. ')
                if isPlayer:
                    game_data.player_record['times_hit_prewarp_planet'] += 1
                    game_data.player_record['times_hit_poipulated_planet'] += 1

                    message_log.add_message('This is a grevous viloation of the prime directive! ')
            else:
                message_log.add_message(f'The torpedo struck the planet, killing {how_many_killed}. ')
                if isPlayer:
                    game_data.player_record['times_hit_poipulated_planet'] += 1
                    message_log.add_message('You will probably be charged with a war crime. ' )
