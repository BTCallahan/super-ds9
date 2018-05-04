from random import choice, choices, randint, uniform, random
from coords import Coords
from data_globals import PLANET_BARREN, PLANET_HOSTILE, PLANET_FRIENDLY, \
PLANET_TYPES, TYPE_ALLIED, TYPE_ENEMY_SMALL
"""
TODO - star and planet naming conventions: randomly generateed name for star in sector. If there are more then one star,
append Alpha, Beta, Gama, or Delta in front of the name. For planets use the star name followed by a Roman neumeral.

Steller evoloution:
Low mass:
Red dward -> Blue Dwarf - > White Dwarf - > Black Dwarf
0.4 -> 1M:
Yellow Dwarf - > Red Giant -> White Dwarf
More then 8-12M:
Blue Sub-giant - > Blue Giant -> Yellow Superginat -> Red Superginat -> Yellow Hypergiant
Blue Sub-giant - > Blue Giant -> Red Giant
Brown Dwarf
Brown Sub-dwarf
Red Sub-dwarf
Yellow Sub-dwarf

"""

class Sector:

    @staticmethod
    def __buildSlice(x):
        ba = list('.' * x)
        return ba

    @staticmethod
    def __grabRandomAndRemove(randList):
        r = choice(randList)
        randList.remove(r)
        return r

    @staticmethod
    def __genSafeSpotList(xRange, yRange):

        for y in yRange:
            for x in xRange:
                yield tuple([x, y])

    def __init__(self, gd, x, y):

        self.astroObjects = [Sector.__buildSlice(gd.subsecSizeX) for s in gd.subsecSizeRangeY]
        self.safeSpots = list(Sector.__genSafeSpotList(gd.subsecSizeRangeX, gd.subsecSizeRangeY))
        self.x = x
        self.y = y

        stars = choices(range(0,4), cum_weights=[10, 14, 17, 18])[0]
        #print(stars)

        self.totalStars = 0
        for i in range(stars):
            rC = Sector.__grabRandomAndRemove(self.safeSpots)

            self.astroObjects[rC[1]][rC[0]] = '*'
            self.totalStars+=1
            #rC = Coords.randomSectorCoords()
            #print('{0}, {1}'.format(rC.x, rC.y))
            """
            if self.astroObjects[rC.y][rC.x] != '*':
                #print('String value: {0}, string slice: {1} *: {2}'.format(self.astroObjects[rC.y], self.astroObjects[rC.y][rC.x], '*'))
                self.astroObjects[rC.y][rC.x] = '*'
                """

        self.planets = []
        self.friendlyPlanets = 0
        self.unfriendlyPlanets = 0

        if self.totalStars > 0:
            for p in range(randint(0, 5)):
                rC = Sector.__grabRandomAndRemove(self.safeSpots)
                self.planets.append(Planet(choice(PLANET_TYPES), rC[0], rC[1], x, y))
                p = self.planets[-1]
                if p.planetType == PLANET_FRIENDLY:
                    self.astroObjects[rC[1]][rC[0]] = '+'
                    self.friendlyPlanets+=1
                else:
                    self.astroObjects[rC[1]][rC[0]] = '-'
                    if p.planetType == PLANET_HOSTILE:
                        self.unfriendlyPlanets+=1
                """
                if self.astroObjects[rC.y][rC.x] not in ['*', '+', '-']:
                    self.planets.append(Planet(random.choice(PLANET_TYPES), rC.x, rC.y, x, y))
                    p = self.planets[-1]
                    if p.planetType == PLANET_FRIENDLY:
                        self.astroObjects[rC.y][rC.x] = '+'
                    else:
                        self.astroObjects[rC.y][rC.x] = '-'
                        """
        #self.friendlyPlanets = len([p for p in sector.planets if p.planetType is PLANET_FRIENDLY])
        #self.unfriendlyPlanets = len([p for p in sector.planets if p.planetType is not PLANET_FRIENDLY])
        #self.stars = sector.totalStars
        self.bigShips = 0
        self.smallShips = 0
        self.playerPresent = False

    @property
    def numberOfPlanets(self):
        return len(self.planets)
    """
    def checkSafeSpot(self, x, y):
        return self.astroObjects[y][x] == '.'
    """

    def findRandomSafeSpot(self, shipList=[]):
        return choice(self.safeSpots)

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

    def getCopy(self, gd):
        return [[self.astroObjects[y][x] for x in gd.subsecSizeRangeX] for y in gd.subsecSizeRangeY]

    def addShipToSec(self, ship):
        if ship.shipData.shipType is TYPE_ALLIED:
            self.playerPresent = True
        elif ship.shipData.shipType is TYPE_ENEMY_SMALL:
            self.smallShips+= 1
        else:
            self.bigShips+= 1

    def removeShipFromSec(self, ship):
        if ship.shipData.shipType is TYPE_ALLIED:
            self.playerPresent = False
        elif ship.shipData.shipType is TYPE_ENEMY_SMALL:
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
        cha = '.'
        if self.playerPresent:
            cha = '@'
        return '{0.friendlyPlanets}{0.unfriendlyPlanets}{1}{0.bigShips}{0.smallShips}'.format(self, cha)


class Star:
    orderSuffexes = ['', 'Alpha ', 'Beta ', 'Gamma ', 'Delta ']
    planetSuffexes = ['', ' I', ' II', ' III', ' IV', ' V', ' VI', ' VII', ' VIII']
    def __init__(self, x, y, secX, secY, starOrder=0):
        self.localCoords = Coords(x, y)
        self.sectorCoords = Coords(secX, secY)
        self.name = ' ' + orderSuffixes[starOrder]

    def getPlanetName(self, planetOrder):
        return self.name + planetSuffexes[planetOrder]

class Planet:

    def __init__(self, planetType, x, y, secX, secY):
        self.planetType = planetType
        self.localCoords = Coords(x, y)
        self.sectorCoords = Coords(secX, secY)
        if self.planetType is not PLANET_BARREN:
            self.infastructure = uniform(0.0, 1.0)
        else:
            self.infastructure = 0.0

    def __lt__(self, p):
        return self.infastructure < p.infastructure

    def __gt__(self, p):
        return self.infastructure > p.infastructure

    def canSupplyPlayer(self, player, enemyList):
        if self.planetType is PLANET_FRIENDLY and self.sectorCoords == player.sectorCoords and \
            self.localCoords.isAdjacent(player.localCoords):
            if len(enemyList) > 0:
                return False

            return True
        return False

    def hitByTorpedo(self, isPlayer, damage=40):
        global GRID, EVENT_TEXT_TO_PRINT

        if self.planetType is PLANET_BARREN:
            EVENT_TEXT_TO_PRINT.append('The torpedo struck the planet. ')
        else:
            self.infastructure-= random(damage * 0.5, damage * 1.0) * 0.1 * self.infastructure
            if self.infastructure <= 0:
                self.infastructure = 0
                EVENT_TEXT_TO_PRINT.append('The torpedo impacted the planet, destroying the last vestages of civilisation. ')
                if isPlayer:
                    EVENT_TEXT_TO_PRINT.append('You will definitly be charged with a war crime. ')
                GRID.killPlanet(self.planetType)
                self.planetType = PLANET_BARREN

            elif self.planetType is PLANET_FRIENDLY:
                EVENT_TEXT_TO_PRINT.append('The torpedo struck the planet, killing millions. ')
                if isPlayer:
                    self.planetType = PLANET_UNFRIENDLY
                    GRID[self.sectorCoords.y][self.sectorCoords.x].tickOffPlanet()
                    EVENT_TEXT_TO_PRINT.append('The planet has severed relations with the Federation. ')
            else:
                EVENT_TEXT_TO_PRINT.append('The torpedo struck the planet, killing millions. ')
                if isPlayer:
                    EVENT_TEXT_TO_PRINT.append('You will probably be charged with a war crime. ' )
