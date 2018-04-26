#BTCallahan, 3/31/2018
import math, random

SHIP_ACTIONS = {'FIRE_ENERGY', 'FIRE_TORP', 'MOVE', 'WARP', 'RECHARGE', 'REPAIR'}

SUB_SECTORS_X = 8
SUB_SECTORS_Y = 8

SUB_SECTOR_SIZE_X = 8
SUB_SECTOR_SIZE_Y = 8

SUB_SECTORS_RANGE_X = range(0, SUB_SECTORS_X)
SUB_SECTORS_RANGE_Y = range(0, SUB_SECTORS_Y)

SUB_SECTOR_SIZE_RANGE_X = range(0, SUB_SECTOR_SIZE_X)
SUB_SECTOR_SIZE_RANGE_Y = range(0, SUB_SECTOR_SIZE_Y)

TYPE_ALLIED = 0
TYPE_ENEMY_SMALL = 1
TYPE_ENEMY_LARGE = 2

PLANET_BARREN = 0
PLANET_UNFRIENDLY = 1
PLANET_FRIENDLY = 2

PLANET_TYPES = [PLANET_BARREN, PLANET_UNFRIENDLY, PLANET_FRIENDLY]

SYM_PLAYER = '@'
SYM_FIGHTER = 'F'
SYM_AD_FIGHTER = 'A'
SYM_CRUISER = 'C'
SYM_BATTLESHIP = 'B'

NO_OF_FIGHTERS = 20
NO_OF_AD_FIGHTERS = 12
NO_OF_CRUISERS = 5
NO_OF_BATTLESHIPS = 1

DESTRUCTION_CAUSES = {'ENERGY', 'TORPEDO', 'RAMMED_ENEMY', 'RAMMED_BY_ENEMY', 'CRASH_BARREN', 'CRASH_HOSTILE', 'CRASH_FRIENDLY', 'WARP_BREACH'}

CAUSE_OF_DAMAGE = ''
TORP_TYPE_POLARON = 60
TORP_TYPE_PHOTON = 75
TORP_TYPE_QUANTUM = 100

LOCAL_ENERGY_COST = 100
SECTOR_ENERGY_COST = 500

SHIP_NAME = 'U.S.S. Defiant'
CAPTAIN_NAME = 'Sisko'

TURNS_LEFT = 100

EASY_MOVE = False
EASY_AIM = False

EVENT_TEXT_TO_PRINT = []

SEC_INFO = []

class PlayerData:

    def __init__(self, light, heavy, angered, hostileHit, barrenHit, DBOdest, torpRes,
                 torpUsed, enRes, enUsed, warps):
        self.lightShipsDestroyed = light
        self.heavySHipsDestroyed = heavy
        self.planetsAngered = angered
        self.hostilePlanetsHit = hostileHit
        self.barrenPlanetsHit = barrenHit
        self.bigDumbObjectsDestroyed = DBOdest
        self.torpedosResulplied = torpRes
        self.torpedosFired = torpUsed
        self.energyResulplied = enRes
        self.energyUsed = enUsed
        self.timesGoneToWarp = warps

    @classmethod
    def newData(cls):
        return cls(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
class Coords:

    def __init__(self, x, y):
        self.x = round(x)
        self.y = round(y)

    @classmethod
    def randomSectorCoords(cls):
        return cls(random.randrange(0, SUB_SECTORS_X), random.randrange(0, SUB_SECTORS_Y))

    @classmethod
    def randomLocalCoords(cls):
        return cls(random.randrange(0, SUB_SECTOR_SIZE_X), random.randrange(0, SUB_SECTOR_SIZE_Y))

    @staticmethod
    def clampSector(s):
        global SUB_SECTORS_X, SUB_SECTORS_Y
        s.x = max(min(s.x, SUB_SECTORS_X - 1), 0)
        s.y = max(min(s.y, SUB_SECTORS_Y - 1), 0)

    @staticmethod
    def clampLocal(s):
        global SUB_SECTOR_SIZE_X, SUB_SECTOR_SIZE_Y
        s.x = max(min(s.x, SUB_SECTOR_SIZE_X - 1), 0)
        s.y = max(min(s.y, SUB_SECTOR_SIZE_Y - 1), 0)
    
    def __sub__(self, coords):
        return self.x - coords.x, self.y - coords.y

    def __add__(self, coords):
        return self.x + coords.x, self.y + coords.y
    
    def check(self, x, y):
        return self.x == x and self.y == y
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y
    
    def distance(self, cooards):
        return math.sqrt(pow(self.x - cooards.x, 2) + pow(self.y - cooards.y, 2))

    @property
    def normalize(self):
        d = math.sqrt(pow(self.x, 2) + pow(self.y, 2))
        return self.x / d, self.y / d

    @property
    def isInSectorBounds(self):
        return self.x in SUB_SECTORS_RANGE_X and self.y in SUB_SECTORS_RANGE_Y

    @property
    def isInLocalBounds(self):
        return self.x in SUB_SECTOR_SIZE_RANGE_X and self.y in SUB_SECTOR_SIZE_RANGE_Y
    
    def isAdjacent(self, coords):
        return self.x in range(coords.x - 1, coords.x + 1) and self.y in range(coords.y - 1, coords.y + 1)

    def __str__(self):
        return 'X: ' + str(self.x) + ', Y: ' + str(self.y)

    @classmethod
    def randomPointWithinRadius(cls, radius):
        x = random.randint(-radius, radius+1)
        y =  random.randint(-radius, radius+1)
        d = math.sqrt(pow(x, 2) + pow(y, 2))
        return cls(round(x / d), round(y / d))

class Order:

    def __init__(self, command, x, y, amount, target):

        self.command = command
        self.x = x
        self.y = y
        self.amount = amount
        self.target = target
    
    def Warp(self, x ,y):
        self.command = 'WARP'
        self.x = x
        self.y = y

    def Move(self, x, y):
        self.command = 'MOVE'
        self.x = x
        self.y = y

    def Phaser(self, amount, target):
        self.command = 'FIRE_PHASERS'
        self.amount = max(0, amount)
        self.target = target

    def Torpedo(self, x, y, amount):
        self.command = 'FIRE_TORPEDO'
        self.x = x
        self.y = y
        self.amount = max(1, amount)

    def Recharge(self, amount):
        self.command = 'RECHARGE'
        self.amount = amount

    def Repair(self, amount):
        self.comand = 'REPAIR'
        
    @classmethod
    def OrderWarp(cls, x, y):
        return cls('WARP', x, y, 0, None)

    @classmethod
    def OrderMove(cls, x, y):
        return cls('MOVE', x, y, 0, None)

    @classmethod
    def OrderPhaser(cls, amount, target):
        return cls('FIRE_ENERGY', -1, -1, amount, target)

    @classmethod
    def OrderTorpedo(cls, x, y):
        return cls('FIRE_TORPEDO', x, y, 0, None)

    @classmethod
    def OrderRecharge(cls, amount):
        return cls('RECHARGE', -1, -1, amount, None)

    @classmethod
    def OrderRepair(cls):
        return cls('REPAIR', -1, -1, 0, None)

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
    def __buildSlice():
        ba = list('.' * SUB_SECTOR_SIZE_X)
        return ba
    
    def __init__(self, x, y):
        
        self.astroObjects = [Sector.__buildSlice() for s in SUB_SECTOR_SIZE_RANGE_Y]
        
        self.x = x
        self.y = y
        
        stars = random.choices(range(0,4), cum_weights=[10, 14, 17, 18])[0]
        #print(stars)
        
        self.totalStars = 0
        for i in range(stars):
            rC = Coords.randomSectorCoords()
            #print('{0}, {1}'.format(rC.x, rC.y))
            
            if self.astroObjects[rC.y][rC.x] != '*':
                #print('String value: {0}, string slice: {1} *: {2}'.format(self.astroObjects[rC.y], self.astroObjects[rC.y][rC.x], '*'))
                self.astroObjects[rC.y][rC.x] = '*'
                self.totalStars+=1

        self.planets = []

        if self.totalStars > 0:
            for p in range(random.randint(0, 5)):
                rC = Coords.randomSectorCoords()

                if self.astroObjects[rC.y][rC.x] not in ['*', '+', '-']:
                    self.planets.append(Planet(random.choice(PLANET_TYPES), rC.x, rC.y, x, y))
                    p = self.planets[-1]
                    if p.planetType == PLANET_FRIENDLY:
                        self.astroObjects[rC.y][rC.x] = '+'
                    else:
                        self.astroObjects[rC.y][rC.x] = '-'

    @property
    def numberOfPlanets(self):
        return len(self.planets)
    
    def checkSafeSpot(self, x, y):
        return self.astroObjects[y][x] == '.'

    def findRandomSafeSpot(self, shipList=[]):
        return random.choice(list(self.getSetOfSafeSpots(shipList)))

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

    def __getSubslice(self, y):
        return''.join([self.astroObjects[y][x] for x in SUB_SECTOR_SIZE_RANGE_X])

    @property
    def getCopy(self):
        return [[self.astroObjects[y][x] for x in SUB_SECTOR_SIZE_RANGE_X] for y in SUB_SECTOR_SIZE_RANGE_Y]

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
            self.infastructure = random.uniform(0.0, 1.0)
        else:
            self.infastructure = 0.0

    def canSupplyPlayer(self, player, enemyList):
        if self.planetType is PLANET_FRIENDLY and self.sectorCoords == player.sectorCoords and \
            self.localCoords.isAdjacent(player.localCoords):
            if len(enemyList) > 0:
                return False
            
            return True
        return False

    def hitByTorpedo(self, isPlayer, damage=40):
        global SEC_INFO, EVENT_TEXT_TO_PRINT
        
        if self.planetType is PLANET_BARREN:
            EVENT_TEXT_TO_PRINT.append('The torpedo struck the planet. ')
        else:
            self.infastructure-= random.random(damage * 0.5, damage * 1.0) * 0.1 * self.infastructure
            if self.infastructure <= 0:
                self.infastructure = 0
                EVENT_TEXT_TO_PRINT.append('The torpedo impacted the planet, destroying the last vestages of civilisation. ')
                if isPlayer:
                    EVENT_TEXT_TO_PRINT.append('You will definitly be charged with a war crime. ')
                self.planetType = PLANET_BARREN
                
            elif self.planetType is PLANET_FRIENDLY:
                EVENT_TEXT_TO_PRINT.append('The torpedo struck the planet, killing millions. ')
                if isPlayer:
                    self.planetType = PLANET_UNFRIENDLY
                    SEC_INFO[self.sectorCoords.y][self.sectorCoords.x].tickOffPlanet()
                    EVENT_TEXT_TO_PRINT.append('The planet has severed relations with the Federation. ')
            else:
                EVENT_TEXT_TO_PRINT.append('The torpedo struck the planet, killing millions. ')
                if isPlayer:
                    EVENT_TEXT_TO_PRINT.append('You will probably be charged with a war crime. ' )
       
            
class StarshipSystem:

    def __init__(self, name):
        self.integrety = 1.0
        self.name = '{: <9}'.format(name)

    @property
    def isOpperational(self):
        return self.integrety > 0.15

    @property
    def getEffectiveValue(self):
        if self.isOpperational:
            return min(1.0, self.integrety * 1.25)
        return 0.0

    def affectValue(self, value):
        
        self.integrety = min(max(value + self.integrety, 0.0), 1.0)
    
    #def __add__(self, value):
        
    def getInfo(self, precision):
        if self.isOpperational:
            return (round(self.integrety * 100 / precision) * precision)#finish
        return 0

    def printInfo(self, precision):
        if self.isOpperational:
            return self.name + '{: >9.0%}'.format(round(self.integrety * 100 / precision) * precision * 0.01)#finish
        return self.name + '{: >9}'.format('OFFLINE')

    def modify(self, a):
        self.integrety = max(0.0, min(1.0, self.integrety + a))

GRID = []

TOTAL_STARSHIPS = []

ENEMY_SHIPS_IN_ACTION = []

SELECTED_ENEMY_SHIP = None

SHIPS_IN_SAME_SUBSECTOR = []

PLAYER = None

def checkForSelectableShips():
    global SELECTED_ENEMY_SHIP
    if SELECTED_ENEMY_SHIP == None and len(SHIPS_IN_SAME_SUBSECTOR) > 0:
        SELECTED_ENEMY_SHIP = SHIPS_IN_SAME_SUBSECTOR[0]

def grapShipsInSameSubSector(ship):
    global TOTAL_STARSHIPS
    return list(filter(lambda s: s.isAlive and s is not ship and s.sectorCoords == ship.sectorCoords, TOTAL_STARSHIPS))

class SectorInfo:
    def __init__(self, sector):
        self.friendlyPlanets = len([p for p in sector.planets if p.planetType is PLANET_FRIENDLY])
        self.unfriendlyPlanets = len([p for p in sector.planets if p.planetType is not PLANET_FRIENDLY])
        self.stars = sector.totalStars
        self.bigShips = 0
        self.smallShips = 0
        self.playerPresent = False

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

def genNameDefiant():
    return 'U.S.S. ' + random.choice(['Defiant', 'Sal Polo', 'Valiant'])

def randomNeumeral(n):
    for i in range(n):
        yield random.choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])

def genNameAttackFighter():
    return 'DF ' + ''.join(list(randomNeumeral(6)))

def genNameAdvancedFighter():
    return 'DFF' + ''.join(list(randomNeumeral(4)))

def genNameCruiser():
    return 'DCC' + ''.join(list(randomNeumeral(3)))

def genNameBattleship():
    return 'DBB' + ''.join(list(randomNeumeral(2)))

"""
class Nation:
    def __init__(self, name, energyWeaponName, escapePodPercent)

"""


class ShipData:

    def __init__(self, shipType, symbol, maxShields, maxHull, maxTorps, maxCrew, maxEnergy, damageCon, torpDam, torpTubes,
                 maxWeapEnergy, warpBreachDist, weaponName, nameGenerator):
        self.shipType = shipType
        self.symbol = symbol
        
        self.maxShields = maxShields

        self.maxHull = maxHull

        self.maxTorps = maxTorps
        self.maxCrew = maxCrew
        self.maxEnergy = maxEnergy

        self.damageCon = damageCon
        self.torpDam = torpDam
        self.torpTubes = torpTubes
        self.maxWeapEnergy = maxWeapEnergy
        self.warpBreachDist = warpBreachDist
        self.weaponName = weaponName
        self.weaponNamePlural = self.weaponName + 's'
        self.shipNameGenerator = nameGenerator
        
DEFIANT_CLASS = ShipData(TYPE_ALLIED, SYM_PLAYER, 2700, 500, 20, 50, 5000, 0.45, 100, 2, 800, 2, 'Phaser', genNameDefiant)

ATTACK_FIGHTER = ShipData(TYPE_ENEMY_SMALL, SYM_FIGHTER, 1200, 230, 0, 30, 3000, 0.15, 0, 0, 600, 1, 'Poleron', genNameAttackFighter)
ADVANCED_FIGHTER = ShipData(TYPE_ENEMY_SMALL, SYM_AD_FIGHTER, 1200, 230, 5, 30, 3000, 0.15, 60, 1, 650, 1, 'Poleron', genNameAdvancedFighter)
CRUISER = ShipData(TYPE_ENEMY_LARGE, SYM_CRUISER, 3000, 500, 10, 120, 5250, 0.125, 60, 2, 875, 3, 'Poleron', genNameCruiser)
BATTLESHIP = ShipData(TYPE_ENEMY_LARGE, SYM_BATTLESHIP, 5500, 750, 20, 500, 8000, 0.075, 60, 6, 950, 5, 'Poleron', genNameBattleship)

#refrence - DEFIANT_CLASS ATTACK_FIGHTER ADVANCED_FIGHTER CRUISER BATTLESHIP




class Starship:
    """
    TODO - implement crewmembers, cloaking device, ablative armor, diffrent torpedo types
    how crewmembers could work:
    crew effectiveness = (crew / max crew) * 0.5 + 0.5
    
    chance of enemy ship detecting you when you are cloaked:
    (1 / distance) * enemy ship sensors

    ablative armor:
    while shields 'bleed through' starts when the shields are at 50%, ablative armor will always absorb damage
    based on the percent of the armor that is left. E.g. is 300 points of damage strike the ship and the shields
    absorbe 50 points leaving 250 points of damage left, and the ship has 300 out of 400 armor left, then the
    armor will be reduced by 187.5 leaving 62.5 points of damage to be inflicted to the hull.

    Diffrent torpedo types:
    as well as doing diffrent amounts of damage, sone might require a higher planetary infastructure to restock,
    for example the player is next to a friendly planet with an infristructure rating of 0.62 and quantum torpdos
    have an infristructure requirement of 0.7. therefore the player will be restocked with photon torpedos instead 
    """
    def __init__(self, shipData, xCo, yCo, secXCo, secYCo):
        self.localCoords = Coords(xCo, yCo)
        self.sectorCoords = Coords(secXCo, secYCo)

        self.shipData = shipData        
        self.shields = shipData.maxShields
        self.hull = shipData.maxHull
        self.torps = shipData.maxTorps
        self.ableCrew = shipData.maxCrew
        self.injuredCrew = 0
        self.energy = shipData.maxEnergy
        
        self.sysWarp = StarshipSystem('Warp:')
        self.sysTorp = StarshipSystem('Tubes:')
        self.sysImpulse = StarshipSystem('Impulse:')
        self.sysEnergyWep = StarshipSystem(self.shipData.weaponNamePlural + ':')
        self.sysShield = StarshipSystem('Shield:')
        self.sysSensors = StarshipSystem('Sensors:')

        self.name = self.shipData.shipNameGenerator()
        
        self.order = Order.OrderRepair()
        self.turnTaken = False
        
    def __del__(self):
        del self.localCoords
        del self.sectorCoords
        del self.sysWarp
        del self.sysTorp
        del self.sysImpulse
        del self.sysEnergyWep
        del self.sysShield
        del self.sysSensors
        del self.order

    @property
    def crewReadyness(self):
        return self.ableCrew / self.shipData.maxCrew

    @property
    def isDerelict(self):
        return self.ableCrew + self.injuredCrew > 0
    
    @property
    def combatEffectivness(self):
        if self.shipData.torpDam > 0:
            return (self.sysTorp.getEffectiveValue + self.sysSensors.getEffectiveValue + 
                   self.sysEnergyWep.getEffectiveValue + self.sysShield.getEffectiveValue +
                    self.sysSensors.getEffectiveValue + (self.shield / self.shipData.maxShield) +
                    self.crewReadyness + (self.hull / self.shipData.maxHull)) / 8.0
        return (self.sysSensors.getEffectiveValue + 
                self.sysEnergyWep.getEffectiveValue + self.sysShield.getEffectiveValue +
                self.sysSensors.getEffectiveValue + (self.shield / self.shipData.maxShield) +
                self.crewReadyness + (self.hull / self.shipData.maxHull)) / 7.0

    @property
    def determinPrecision(self):
        precision = 1    
        if self.sysSensors.getEffectiveValue < 0.4:
            precision = 100
        elif self.sysSensors.getEffectiveValue < 0.5:
            precision = 50
        elif self.sysSensors.getEffectiveValue < 0.6:
            precision = 25
        elif self.sysSensors.getEffectiveValue < 0.7:
            precision = 20
        elif self.sysSensors.getEffectiveValue < 0.8:
            precision = 15
        elif self.sysSensors.getEffectiveValue < 0.9:
            precision = 10
        elif self.sysSensors.getEffectiveValue < 0.95:
            precision = 5
        elif self.sysSensors.getEffectiveValue < 0.99:
            precision = 2
        else:
            precision = 1
        return precision

    #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
    def scanThisShip(self, precision, printSystems=False):
        scanAssistant = lambda v, p: round(v / p) * p
        if not printSystems:
            return (scanAssistant(self.shields, precision),
                    scanAssistant(self.hull, precision),
                    scanAssistant(self.energy, precision),
                    scanAssistant(self.ableCrew, precision),
                    scanAssistant(self.injuredCrew, precision),
                    scanAssistant(self.torps, precision),
                    self.sysWarp.getInfo(precision) * 0.01,
                    self.sysImpulse.getInfo(precision) * 0.01, 
                    self.sysEnergyWep.getInfo(precision) * 0.01,
                    self.sysShield.getInfo(precision) * 0.01, 
                    self.sysSensors.getInfo(precision) * 0.01,
                    self.sysTorp.getInfo(precision) * 0.01)
        return (scanAssistant(self.shields, precision),
                scanAssistant(self.hull, precision), 
                scanAssistant(self.energy, precision),
                
                scanAssistant(self.ableCrew, precision),
                scanAssistant(self.injuredCrew, precision),
                scanAssistant(self.torps, precision),
                
                self.sysWarp.printInfo(precision),
                self.sysImpulse.printInfo(precision), 
                self.sysEnergyWep.printInfo(precision),
                self.sysShield.printInfo(precision), 
                self.sysSensors.printInfo(precision),
                self.sysTorp.printInfo(precision))

    def printShipInfo(self, precision):
        textList = []
        blank = ' ' * 18
        scan = self.scanThisShip(precision, True)
        textList.append('{0:^18}'.format(self.name))
        textList.append('Shields: {0: =4}/{1: =4}'.format(scan[0], self.shipData.maxShields))
        textList.append('Hull:    {0: =4}/{1: =4}'.format(scan[1], self.shipData.maxHull))
        textList.append('Energy:  {0: =4}/{1: =4}'.format(scan[2], self.shipData.maxEnergy))
        textList.append('Crew:    {0: =4}/{1: =4}'.format(scan[3], self.shipData.maxCrew))
        textList.append('Injured: {0: =4}/{1: =4}'.format(scan[4], self.shipData.maxCrew))
        if self.shipData.maxTorps > 0:
            textList.append('Torpedos:  {0: =2}/  {1: =2}'.format(scan[5], self.shipData.maxTorps))
        else:
            textList.append(blank)
        textList.append(blank)
        textList.append('{0:^18}'.format('System Status:'))
        textList.append(scan[6])
        textList.append(scan[7])
        textList.append(scan[8])
        textList.append(scan[9])
        textList.append(scan[10])
        if self.shipData.maxTorps > 0:
            textList.append(scan[11])
        else:
            textList.append(blank)
        return textList
            
    @property
    def getShipValue(self):
        if self.isAlive:
            return (self.hull + self.shipData.maxHull) * 0.5
        return 0.0

    def destroy(self, cause):
        global SEC_INFO, EVENT_TEXT_TO_PRINT, CAUSE_OF_DAMAGE
        
        SEC_INFO[self.sectorCoords.y][self.sectorCoords.x].removeShipFromSec(self)
        EVENT_TEXT_TO_PRINT.append(self.name)
        
        if random.uniform(self.sysWarp.getEffectiveValue * 0.5, 1.0) < self.sysWarp.getEffectiveValue:
            EVENT_TEXT_TO_PRINT.append(' suffers a warp core breach. ')
            self.warpCoreBreach()
        else:
            EVENT_TEXT_TO_PRINT.append(' is destroyed. ')
        self.hull = 0
        if self.isControllable:
            CAUSE_OF_DAMAGE = cause

    def warpCoreBreach(self, selfDestruct=False):

        shipList = grapShipsInSameSubSector(self)
        oneThird = 1 / 3
        for s in shipList:
            distance = self.localCoords.distance(s.localCoords)
            damPercent = 1 - (distance / s.shipData.warpBreachDist)
            if damPercent > 0.0:
                if selfDestruct:
                    s.takeDamage(damPercent * self.shipData.maxHull * oneThird, 'Caught in the blast radius of the {0}'.format(self.name))
                else:
                    s.takeDamage(damPercent * self.shipData.maxHull * oneThird, 'Caught in the core breach of the {0}'.format(self.name))
        
    @property
    def isAlive(self):
        return self.hull > 0

    def ram(self, otherShip):
        selfHP = self.shield + self.hull
        otherHP = otherShip.shield + otherShip.hull
        if selfHP > otherHP:
            self.takeDamage(otherHP, 'Rammed the {0}'.format(self.name))
            otherShip.destroy('Rammed by the {0}'.format(self.name))
        elif selfHP < otherHP:
            otherShip.takeDamage(selfHP, 'Rammed by the {0}'.format(self.name))
            self.destroy('Rammed the {0}'.format(self.name))
        else:
            otherShip.destroy('Rammed by the {0}'.format(self.name))
            self.destroy('Rammed the {0}'.format(self.name))
            
    def checkIfCanReachLocation(self, x, y, usingWarp):
        #return a tuple with the following structure:
        #(canMoveAtAll, canReachDestination, newX, newY, energyCost)
        #(bool, bool, int, int, float)
        checker = lambda a, b: a if usingWarp else b
        global SECTOR_ENERGY_COST, LOCAL_ENERGY_COST
        
        systemOpperational = checker(self.sysWarp.isOpperational, self.sysImpulse.isOpperational)
        energyCost = checker(SECTOR_ENERGY_COST, LOCAL_ENERGY_COST)
        #fromText = checker(' warps from subsector ', ' moves from position ')
        #toText = checker(' to subsector ', ' to position ')
        selfCoords = checker(self.sectorCoords, self.localCoords)
        effictiveValue = checker(self.sysWarp.getEffectiveValue, self.sysImpulse.getEffectiveValue)

        canMoveAtAll = False
        canReachDestination = False
        eCost = 0
        print('Destination location X: {0}, Y: {1}'.format(x, y))
        if systemOpperational and self.energy >= energyCost:
            canMoveAtAll = True
            co = Coords(x, y)#assume x is 5 and y is 2

            if usingWarp:
                Coords.clampSector(co)
            else:
                Coords.clampLocal(co)

            print('Clamped location : {0}'.format(co))
            #current location is x = 1 and y = 7
            # 1 - 5, 7 - 2 = -4, 5
            #pow(-4, 2), pow(5, 2) = 16, 25
            #pow(16+25, 0.5) = pow(41) = 6.4031242374328485
            #dist = 6.4031242374328485
            dist = energyCost * selfCoords.distance(co)

            #
            x, y = selfCoords - co
            del co

            eCost = dist / effictiveValue

            if eCost > self.energy:
                fract = self.energy / eCost
                
                nx = round(x * fract)#2 * 447.213595499958 / 100 = 894.217190 / 100 = 8.9421719
                ny = round(y * fract)

                canReachDestination = nx == x and ny == y
                x = nx, y = ny
                
                eCost = self.energy
            else:
                canReachDestination = True
        print('Final destination location X: {0}, Y: {1}'.format(x, y))
        return (canMoveAtAll, canReachDestination, x, y, eCost)

    def handleMovment(self, x, y, usingWarp):
        checker = lambda a, b: a if usingWarp else b
        global LOCAL_ENERGY_COST, SECTOR_ENERGY_COST, EVENT_TEXT_TO_PRINT, TOTAL_STARSHIPS, GRID

        #systemOpperational = checker(self.sysWarp.isOpperational, self.sysImpulse.isOpperational)
        #energyCost = checker(SECTOR_ENERGY_COST, LOCAL_ENERGY_COST)
        fromText = checker(' warps from subsector ', ' moves from position ')
        toText = checker(' to subsector ', ' to position ')
        selfCoords = checker(self.sectorCoords, self.localCoords)
        #effictiveValue = checker(self.sysWarp.getEffectiveValue, self.sysImpulse.getEffectiveValue)

        mo = self.checkIfCanReachLocation(x, y, usingWarp)

        if not mo[0]:
            return False
        EVENT_TEXT_TO_PRINT+=[self.name, fromText, str(selfCoords)]

        if usingWarp:
            SEC_INFO[self.sectorCoords.y][self.sectorCoords.x].removeShipFromSec(self)
            
        selfCoords.x-= mo[2]
        selfCoords.y-= mo[3]

        if usingWarp:
            shipList = list(filter(lambda s: s.isAlive and s is not self, TOTAL_STARSHIPS))
            sp = GRID[selfCoords.y][selfCoords.x].findRandomSafeSpot(shipList)
            
            self.localCoords.x = sp[0]
            self.localCoords.y = sp[1]
            
            SEC_INFO[self.sectorCoords.y][self.sectorCoords.x].addShipToSec(self)
        
        EVENT_TEXT_TO_PRINT+=[toText, str(selfCoords), '.']
        self.energy-=mo[4]
        
    #TODO - add in a checker to see if the player has plowed into a planet or star, or rammed another starship
    def move(self, x, y):#assume that x = 2, y = 3
        self.handleMovment(x, y, False)
        """
        global EVENT_TEXT_TO_PRINT
        print('checking if ship can move')
        if self.sysImpulse.isOpperational and self.energy >= LOCAL_ENERGY_COST:
            print('ship can move')
            #print('Moving to X: {0}, Y: {1}'.format(x,y))
            
            co = Coords(x, y)#current location is 4, 7
            
            Coords.clampLocal(co)
            
            dist = LOCAL_ENERGY_COST * self.localCoords.distance(co)
            #print('Clamped co to X: {0}, Y: {1}, Distance {2}'.format(co.x, co.y, dist))
            #2 - 4, 3 - 7 = -2, -4
            #pow(-2, 2), pow(-4, 2) = 4, 16
            #4 + 16 = 20
            #math.sqrt(20) = 4.47213595499958
            #4.47213595499958 * 100 = 447.213595499958
            
            x, y = self.localCoords - co#4, 7 - 2, 3 = 2, 4
            
            del co
            
            eCost = dist / self.sysImpulse.getEffectiveValue
            #print('Amound to move X: {0}, Y: {1}, eCost: {2}'.format(x, y, eCost))
            #447.213595499958 / 1 = 447.213595499958
            if eCost > self.energy:
                fract = self.energy / eCost
                
                x = round(x * fract)#2 * 447.213595499958 / 100 = 894.217190 / 100 = 8.9421719
                y = round(y * fract)
                
                eCost = self.energy

            EVENT_TEXT_TO_PRINT+=[self.name, ' moves from position ', str(self.localCoords)]
            
            self.localCoords.x-= x
            self.localCoords.y-= y

            EVENT_TEXT_TO_PRINT+=[' to position ', str(self.localCoords), '. ']
            
            self.energy-=eCost

            return True
        return False
    """
            
    def warp(self, x ,y):
        self.handleMovment(x, y, True)
        """
        global EVENT_TEXT_TO_PRINT
        if self.sysWarp.isOpperational and self.energy >= SECTOR_ENERGY_COST:
            #assume that curent energy is 2000, curent position is 4, 1, and the ship is warping to 2, 5
            co = Coords(x, y)

            Coords.clampSector(co)

            dist = SECTOR_ENERGY_COST * self.sectorCoords.distance(co)
            #dist = 500 * sqrt(pow(4 -  2, 2) + pow(1 - 5, 2))
            #dsit = 500 * sqrt(pow(2, 2) + pow(-4, 2))
            #dist = 500 * sqrt(4 + 16)
            #dist = 500 * 4.47213595499958
            #dist = 2236.06797749979

            x, y = self.sectorCoords - co
            #x, y = 2, -4

            del co

            eCost = dist / self.sysWarp.getEffectiveValue
            #assume that self.sysWarp.getEffectiveValue is 0.8
            #2236.06797749979 / 0.8 = 2795.084971874737
            if eCost > self.energy:
                #so for this part, assume that the energy is actually 2000
                fract = self.energy / eCost
                #fract = 2000 / 2795.084971874737 = 0.7155417527999327

                x = round(x * fract)
                y = round(y * fract)
                #round(2 * 0.7155417527999327)
                #round(1.4310835055998654) = 1

                #round(-4 * 0.7155417527999327)
                #round(-2.862167011199731) = -3
                eCost = self.energy

            SEC_INFO[self.sectorCoords.y][self.sectorCoords.x].removeShipFromSec(self)

            EVENT_TEXT_TO_PRINT+=[self.name, ' warps from subsector ', str(self.sectorCoords)]
            
            self.sectorCoords.x-= x#4 - 1 = 3
            self.sectorCoords.y-= y#1 - -3 = 4

            EVENT_TEXT_TO_PRINT+=[' to subsector ', str(self.sectorCoords), '. ']
            
            self.energy -= eCost
            
            
            #self.sectorCoords.x, self.sectorCoords.y = x, y
            SEC_INFO[self.sectorCoords.y][self.sectorCoords.x].addShipToSec(self)
            
            #DOTO - finish this
            return True
        return False
    """
        
    def takeDamage(self, amount, text, isTorp=False):
        global EVENT_TEXT_TO_PRINT
        scanAssistant = lambda v, p: round(v / p) * p

        pre = 1
        if not self.isControllable:
            pre = self.determinPrecision
        #say damage is 64, current shields are 80, max shields are 200
        #80 * 2 / 200 = 160 / 200 = 0.8
        #0.8 * 64 = 51.2 = shieldsDam
        if self.hull > 0:
            shieldsDam = 0.0
            hullDam = 1.0 * amount

            if self.sysShield.isOpperational and self.shields > 0:
                
                s = (self.shields / self.shipData.maxShields) * 0.5 + 0.5
                
                shieldsDam = s * amount
                hullDam = (1 - s) * amount
                
                
                
                if shieldsDam > self.shields:

                    hullDam+= shieldsDam - self.shields
                    shieldsDam = self.shields
                if isTorp:
                    shieldsDam*= 0.75
                    hullDam*= 1.05
            elif isTorp:
                hullDam*= 1.75#getting hit with a torp while your shields are down - game over

            def randomSystemDamage():
                return random.uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull))
                
            self.hull-= hullDam
            self.shields-= shieldsDam
            
            EVENT_TEXT_TO_PRINT+=[self.name, ' suffers {0} points of damage to the shields, and \
{1} points to the hull. '.format(scanAssistant(shieldsDam, pre), scanAssistant(hullDam, pre))]
            
            r = (hullDam / self.shipData.maxHull - self.hull / self.shipData.maxHull) - random.random()
            #(50 / 120 - 10 / 120) - 0.25
            #(0.4166666666666667 - .08333333333333333) - 0.25
            #0.33333333333333337 - 0.25
            #0.08333333333333337
            
            if r > 0.0:
                killedOutright = round(self.ableCrew * r)
                killedInSickbay = min(self.injuredCrew, round(0.5 * self.ableCrew * r))
                wounded = round(1.5 * (self.ableCrew - killedOutright) * r)
                
                self.ableCrew-= killedOutright
                self.injuredCrew-= killedInSickbay
                self.injuredCrew+= wounded
                self.ableCrew-= wounded

                if killedOutright > 0:
                    EVENT_TEXT_TO_PRINT.append('{} active duty crewmembers were killed. '.format(killedOutright))
                if killedInSickbay > 0:
                    EVENT_TEXT_TO_PRINT.append('{} crewmembers in sickbay were killed. '.format(killedInSickbay))
                if wounded > 0:
                    EVENT_TEXT_TO_PRINT.append('{} crewmembers were injured. '.format(wounded))
            
            if self.hull <= 0:
                self.destroy(text)
            else:
                if self.isControllable:
                    setattr(self, 'turnRepairing', True)
                
                if random.random() < hullDam / self.shipData.maxHull:#damage subsystem at random
                    if random.randint(0, 3) is 0:
                        EVENT_TEXT_TO_PRINT.append('Impulse engines damaged. ')
                        self.sysImpulse.affectValue(randomSystemDamage())
                    if random.randint(0, 3) is 0:
                        EVENT_TEXT_TO_PRINT.append('Warp drive damaged. ')
                        self.sysWarp.affectValue(randomSystemDamage())
                    if random.randint(0, 3) is 0:
                        EVENT_TEXT_TO_PRINT.append(shipData.weaponName)
                        #shipData.weaponNamePlural
                        EVENT_TEXT_TO_PRINT.append(' emitters damaged. ')
                        self.sysEnergyWep.affectValue(randomSystemDamage())
                    if random.randint(0, 3) is 0:
                        EVENT_TEXT_TO_PRINT.append('Sensors damaged. ')
                        self.sysSensors.affectValue(randomSystemDamage())
                    if random.randint(0, 3) is 0:
                        EVENT_TEXT_TO_PRINT.append('Shield generator damaged. ')
                        self.sysShield.affectValue(randomSystemDamage())
                    if self.shipData.torpDam > 0 and random.randint(0, 3) is 0:
                        EVENT_TEXT_TO_PRINT.append('Torpedo launcher damaged. ')
                        self.sysTorp.affectValue(randomSystemDamage())
            
    def repair(self, factor, externalRepair=False):
        #self.crewReadyness
        repairFactor = self.shipData.damageCon * factor * self.crewReadyness
        
        self.energy = min(self.shipData.maxEnergy, self.energy + factor * 100)
        
        healCrew = min(self.injuredCrew, round(self.injuredCrew * 0.2) + random.randint(2, 5))
        self.ableCrew+= healCrew
        self.injuredCrew-= healCrew
        
        self.hull = min(self.shipData.maxHull, self.hull + repairFactor)
        self.sysWarp.affectValue(repairFactor)
        self.sysSensors.affectValue(repairFactor)
        self.sysImpulse.affectValue(repairFactor)
        self.sysEnergyWep.affectValue(repairFactor)
        self.sysShield.affectValue(repairFactor)
        if self.shipData.torpDam > 0:
            self.sysTorp.affectValue(repairFactor)

    def rechargeShield(self, amount):
        if self.sysShield.isOpperational:
            if amount >= 0:
                    
                if amount > self.energy:
                    amount = self.energy

                self.energy-= amount
                amount*= self.sysShield.getEffectiveValue
                
                self.shields = min(self.shields + amount, self.shipData.maxShields)
            else:
                
                if -amount > self.shields:
                    amount = -self.shields

                self.shields+=amount
                amount*= -self.sysShield.getEffectiveValue
                self.energy = min(self.energy + amount, self.shupData.maxEnergy)
                
            return True
        return False
        
    def aiBehavour(self):
        #TODO - trun this into an actual AI dicision making process instaid of a glorified RNG
        #return true if the torpedo is selected, false if otherwise
        if self.torps > 0 and self.sysTorp.isOpperational:
            if self.energy > 0 and self.sysEnergyWep.isOpperational:
                return random.random(0, 1) == 0
            else:
                return True
        elif self.energy > 0 and self.sysEnergyWep.isOpperational:
            return False
        return random.random(0, 1) == 0

    def rollToHitBeam(self, enemy, estimatedEnemyImpulse=-1):
        if estimatedEnemyImpulse == -1:
            estimatedEnemyImpulse = enemy.sysImpulse.getEffectiveValue
        """
        assume that the distance is 5, the sensors are at 70% and enemy impulse is at 80%
        so (1 / 5) * (0.7 * 1.25 / 0.8)
        0.2 * (0.875 / 0.8)
        0.2 * 1.09375
        2.1875"""
        return (1 / self.localCoords.distance(enemy.localCoords)) * (
            self.sysSensors.getEffectiveValue * 1.25 / estimatedEnemyImpulse) > random.random()

    def rollToHitCannon(self, enemy, estimatedEnemyImpulse=-1):
        if estimatedEnemyImpulse == -1:
            estimatedEnemyImpulse = enemy.sysImpulse.getEffectiveValue
        return (3 / self.localCoords.distance(enemy.localCoords)) * (
            self.sysSensors.getEffectiveValue * 1.25 / estimatedEnemyImpulse * 1.25) > random.random()
    
    def attackEnergyWeapon(self, enemy, amount, cannon=False):
        global EVENT_TEXT_TO_PRINT
        if self.sysEnergyWep.isOpperational:
            
            amount = min(amount, self.energy)
            self.energy-=amount
            
            if cannon:
                amount*=1.25
            if self.rollToHitBeam(enemy):
            
                EVENT_TEXT_TO_PRINT+= [self.name, ' hits ', enemy.name, '. ']
                enemy.takeDamage(amount * self.sysEnergyWep.getEffectiveValue,
                                 'Destroyed by a {0} hit from the {1}'.format(self.shipData.weaponName, self.name))
            else:
                EVENT_TEXT_TO_PRINT+= [self.name, ' misses ', enemy.name, '. ']
    
    def getNoOfAvalibleTorpTubes(self, number=0):
        if not self.sysTorp.isOpperational:
            return 0
        
        if number is 0:
            number = self.shipData.torpTubes
        else:
            number = min(number, self.shipData.torpTubes)
        
        return max(1, round(number * self.sysTorp.getEffectiveValue))

    def rollToHitTorpedo(self, enemy, estimatedEnemyImpulse=-1):
        if estimatedEnemyImpulse == -1:
            estimatedEnemyImpulse = enemy.sysImpulse.getEffectiveValue
        
        return self.sysTorp.getEffectiveValue + (self.sysSensors.getEffectiveValue * 1.25) > \
            estimatedEnemyImpulse - random.uniform(0.0, 0.75)
    
    def attackTorpedo(self, enemy):
        global EVENT_TEXT_TO_PRINT
        if self.rollToHitTorpedo(enemy):
            #chance to hit:
            #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
            EVENT_TEXT_TO_PRINT.append('{0} was hit by a torpedo from {1}. '.format(enemy.name, self.name))
            
            enemy.takeDamage(self.shipData.torpDam, 'Destroyed by a torpedo hit from the {0}'.format(self.name), True)
            
            return True
        EVENT_TEXT_TO_PRINT.append('A torpedo from {1} missed {0}. '.format(enemy.name, self.name))
        return False
        
    @property
    def isControllable(self):
        return False

    @property
    def hasValidTarget(self):
        return self.order and self.order.target and self.order.target.sectorCoords == self.sectorCoords
    
class FedShip(Starship):

    def __init__(self, shipInfo, xCo, yCo, secXCo, secYCo):
        super().__init__(shipInfo, xCo, yCo, secXCo, secYCo)
        self.ablatArmor = 1200
        self.turnRepairing = 0
        self.damageTakenThisTurn = False
        
    def repair(self, factor, externalRepair=False):
        timeBonus = 1 + (self.turnRepairing / 25)
        
        repairFactor = self.shipData.damageCon * factor * self.crewReadyness * timeBonus
        healCrew = min(self.injuredCrew, round(self.injuredCrew * 0.2) + random.randint(2, 5))
        
        if externalRepair:
            repairFactor = self.shipData.damageCon * factor * timeBonus
            healCrew = min(self.injuredCrew, round(self.injuredCrew * (0.2 + factor)) + random.randint(6, 10))
        self.energy = min(self.shipData.maxEnergy, self.energy + factor * 100 * timeBonus)
        self.hull = min(self.shipData.maxHull, self.shipData.maxHull * factor * self.shipData.damageCon * timeBonus)
        
        self.ableCrew+= healCrew
        self.injuredCrew-= healCrew
        
        self.sysWarp.affectValue(repairFactor)
        self.sysTorp.affectValue(repairFactor)
        self.sysImpulse.affectValue(repairFactor)
        self.sysEnergyWep.affectValue(repairFactor)
        self.sysShield.affectValue(repairFactor)
        self.turnRepairing+=1

    def resetRepair(self):
        self.turnRepairing = 0

    def restockTorps(self):
        self.torps = self.shipData.maxTorps

    def resetRepair(self):
        if self.damageTakenThisTurn:
            self.turnRepairing = 0
            self.damageTakenThisTurn = False

    @property
    def isControllable(self):
        return True

class EnemyShip(Starship):

    def __init__(self, shipInfo, xCo, yCo, secXCo, secYCo):
        super().__init__(shipInfo, xCo, yCo, secXCo, secYCo)

    def simulateTorpedoHit(self, target):
        targScan = target.scanThisShip(self.determinPrecision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan[0]
        targHull = [1]

        timesToFire = min(self.getNoOfAvalibleTorpTubes(), self.torpedos)
        for t in range(timesToFire):
            if self.rollToHitTorpedo(target, targScan[7]):
            
                #chance to hit:
                #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
                amount = self.shipData.torpDam
                
                shieldsDam = 0.0
                hullDam = 1.0 * amount

                if targShield > 0:
                    
                    shieldsDam = (min(targShield * 2 / target.shipData.maxShields, 1)) * amount
                    hullDam = (1 - min(targShield * 2 / target.shipData.maxShields, 1)) * amount

                    if shieldsDam > targShield:

                        hullDam+= shieldsDam - targShield
                        shieldsDam = self.shields
                    
                        shieldsDam*= 0.75
                        hullDam*= 1.05
                else:
                    hullDam*= 1.75#getting hit with a torp while your shields are down - game over
                
                targHull -= hullDam
                targShield -= shieldsDam
            
        return (targScan[1] - targHull) + (targScan[0] - targShield)#return the simulated amount of damage

    
    def simulatePhaserHit(self, target, timesToFire):

        targScan = target.scanThisShip(self.determinPrecision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan[0]
        targHull = [1]
        
        totalShDam = 0
        totalHuDam = 0
        
        amount = min(self.energy, self.shipData.maxWeapEnergy)

        for i in range(timesToFire):
            if rollToHitBeam(target, targScan[7]):
                        
                #if targShield > 0:
                
                shieldsDam = (min(targShield * 2 / target.shipData.maxShields, 1)) * amount
                hullDam = (1 - min(targShield * 2 / target.shipData.maxShields, 1)) * amount

                if shieldsDam > targShield:

                    hullDam+= shieldsDam - targShield
                    shieldsDam = targShield
                    
                totalShDam+= shieldsDam
                totalHuDam+= hullDam
                
        return (totalHuDam + totalShDam) / timesToFire

    def checkTorpedoLOS(self, target):
        global GRID
        global SHIPS_IN_SAME_SUBSECTOR
        dirX, dirY = Coords(target.localCoords - self.localCoords).normalize
        
        g = GRID[shipThatFired.sectorCoords.y][shipThatFired.sectorCoords.x]
        
        posX, posY = self.localCoords.x, self.localCoords.y
        
        while round(posX) in SUB_SECTOR_SIZE_RANGE_X and round(posY) in SUB_SECTOR_SIZE_RANGE_Y:
            posX+= dirX
            posY+= dirY
            iX = round(posX)
            iY = round(posY)
            if g.astroObjects[iY][iX] in ['*', '+', '-']:
                if g.astroObjects[iY][iX] == '+':
                    for p in g.planets:
                        if Coords(iX, iY) == p.localCoords:
                            return False
            else:
                for s in SHIPS_IN_SAME_SUBSECTOR:
                    if Coords(iX, iY) == s.localCoords:
                        return True
        return False
    
def assignShipsInSameSubSector():
    global SHIPS_IN_SAME_SUBSECTOR
    global ENEMY_SHIPS_IN_ACTION
    global PLAYER
    global SELECTED_ENEMY_SHIP
    SHIPS_IN_SAME_SUBSECTOR = list(filter(lambda s: s.isAlive and s.shipData.shipType is not TYPE_ALLIED and 
                                          s.sectorCoords == PLAYER.sectorCoords, ENEMY_SHIPS_IN_ACTION))
    #SHIPS_IN_SAME_SUBSECTOR = [s for s in ENEMY_SHIPS_IN_ACTION if (s.shipData.shipType is not TYPE_ALLIED and s.sectorCoords == PLAYER.sectorCoords)]
    print('ships in same subsector: {0}'.format(len(SHIPS_IN_SAME_SUBSECTOR)))
    if len(SHIPS_IN_SAME_SUBSECTOR) > 0:
        if SELECTED_ENEMY_SHIP == None or SELECTED_ENEMY_SHIP not in SHIPS_IN_SAME_SUBSECTOR:
            SELECTED_ENEMY_SHIP = random.choice(SHIPS_IN_SAME_SUBSECTOR)
    else:
        SELECTED_ENEMY_SHIP = None

def grabSelectedShipInfo():
    global SELECTED_ENEMY_SHIP
    
    if SELECTED_ENEMY_SHIP:
        print('enemy ships is selected')
        
        return SELECTED_ENEMY_SHIP.printShipInfo(PLAYER.determinPrecision)
    
    whiteSpace = ' ' * 18
    
    blankScan = []
    for i in range(12):
        blankScan.append(whiteSpace)
    
    return blankScan
"""
def checkWarpCoreBreach(ship):
    global TOTAL_STARSHIPS

    for i in TOTAL_STARSHIPS:

        if i.sectorCoords == ship.sectorCoords and i.localCoords != ship.localCoords:

            dist = ship.localCoords.distance(i.localCoords)
            dam = max(0, dist / ship.warpBreachDist - 1)
            if dam > 0:
                i.takeDamage(ship.shipData.maxHull / 3)
                """

def setUpGame():
    print('beginning setup')
    global GRID
    global SEC_INFO
    
    GRID = [[Sector(x, y) for x in SUB_SECTORS_RANGE_X] for y in SUB_SECTORS_RANGE_Y]
    SEC_INFO = [[SectorInfo(GRID[y][x]) for x in SUB_SECTORS_RANGE_X] for y in SUB_SECTORS_RANGE_X]

    setOfGridPositions = set()

    for iy in SUB_SECTORS_RANGE_Y:
        for jx in SUB_SECTORS_RANGE_X:
            setOfGridPositions.add((jx, iy))

    randXsec, randYsec = random.randrange(0, SUB_SECTORS_X), random.randrange(0, SUB_SECTORS_Y)

    locPos = GRID[randYsec][randXsec].findRandomSafeSpot()
    global PLAYER
    PLAYER = FedShip(DEFIANT_CLASS, locPos[0], locPos[1], randXsec, randYsec)

    global TOTAL_STARSHIPS
    
    TOTAL_STARSHIPS.append(PLAYER)

    setOfGridPositions.remove((PLAYER.sectorCoords.x, PLAYER.sectorCoords.y))#remove the PLAYER's position fron the set - dont want 

    for s in range(NO_OF_BATTLESHIPS):
        randXsec, randYsec = random.sample(setOfGridPositions, 1)[0]
        
        localPos = GRID[randYsec][randXsec].findRandomSafeSpot(TOTAL_STARSHIPS)
        ship = EnemyShip(BATTLESHIP, randXsec, randYsec, localPos[0], localPos[1])
        ENEMY_SHIPS_IN_ACTION.append(ship)
        TOTAL_STARSHIPS.append(ship)

    for s in range(NO_OF_CRUISERS):
        randXsec, randYsec = random.sample(setOfGridPositions, 1)[0]

        localPos = GRID[randYsec][randXsec].findRandomSafeSpot(TOTAL_STARSHIPS)
        ship = EnemyShip(CRUISER, randXsec, randYsec, localPos[0], localPos[1])
        ENEMY_SHIPS_IN_ACTION.append(ship)
        TOTAL_STARSHIPS.append(ship)
                             
    for s in range(NO_OF_AD_FIGHTERS):
        randXsec, randYsec = random.sample(setOfGridPositions, 1)[0]

        localPos = GRID[randYsec][randXsec].findRandomSafeSpot(TOTAL_STARSHIPS)
        ship = EnemyShip(ADVANCED_FIGHTER, randXsec, randYsec, localPos[0], localPos[1])
        ENEMY_SHIPS_IN_ACTION.append(ship)
        TOTAL_STARSHIPS.append(ship)

    for s in range(NO_OF_FIGHTERS):
        randXsec, randYsec = random.sample(setOfGridPositions, 1)[0]

        localPos = GRID[randYsec][randXsec].findRandomSafeSpot(TOTAL_STARSHIPS)
        ship = EnemyShip(ATTACK_FIGHTER, randXsec, randYsec, localPos[0], localPos[1])
        ENEMY_SHIPS_IN_ACTION.append(ship)
        TOTAL_STARSHIPS.append(ship)

    for s in TOTAL_STARSHIPS:
        SEC_INFO[s.sectorCoords.y][s.sectorCoords.x].addShipToSec(s)

    print('About to assign shiips')
    assignShipsInSameSubSector()

#-----------Gameplay related-----------
def checkForDestroyedShips():
    global ENEMY_SHIPS_IN_ACTION
    destroyed = []
    for s in ENEMY_SHIPS_IN_ACTION:
        if not s.isAlive:
            destroyed.append(s)
    if len(destroyed) > 0:
        for d in destroyed:
            ENEMY_SHIPS_IN_ACTION.remove(d)
    #ENEMY_SHIPS_IN_ACTION -= destroyed

getRads = lambda h: (h % 360) * (math.pi / 180)

def headingToCoordsTorp(heading, distance):
    rads = (heading % 360) * (math.pi / 180)
    return round(math.sin(rads) * distance), round(math.cos(rads) * distance)

def headingToCoords(heading, distance, startX, startY, rangeX, rangeY):
    rads = (heading % 360) * (math.pi / 180)
    retX, retY = startX, startY
    
    for d in range(distance + 1):
        retX = round(math.sin(rads) * d) + startX
        retY = round(math.cos(rads) * d) + startY
        if retX not in rangeX or retY not in rangeY:
            return retX, retY
    return retX, retY
    

def handleTorpedo(shipThatFired, torpsFired, dirX, dirY):
    global GRID, TOTAL_STARSHIPS, EVENT_TEXT_TO_PRINT
    
    posX, posY = shipThatFired.localCoords.x, shipThatFired.localCoords.y
    
    g = GRID[shipThatFired.sectorCoords.y][shipThatFired.sectorCoords.x]
    shipsInArea = list(filter(lambda s: s.isAlive and s.sectorCoords == shipThatFired.sectorCoords and
                              s is not shipThatFired, TOTAL_STARSHIPS))
    
    damage = shipThatFired.shipData.torpDam
    
    torpsFired = min(shipThatFired.getNoOfAvalibleTorpTubes(torpsFired), shipThatFired.torps)

    eS = lambda n: '' if n is 1 else 's'
    
    EVENT_TEXT_TO_PRINT.append('{0} fired {1} torpedo{2}. '.format(shipThatFired.name, torpsFired, eS(torpsFired)))
    while torpsFired > 0:
        shipThatFired.torps-=1
        hitSomething = False
        hitList = []
        
        while round(posX) in SUB_SECTOR_SIZE_RANGE_X and round(posY) in SUB_SECTOR_SIZE_RANGE_Y and not hitSomething:
            
            iX = round(posX)
            iY = round(posY)
            
            if g.astroObjects[iY][iX] in ['*', '+', '-']:
                if g.astroObjects[iY][iX] == '+':
                    for p in g.planets:
                        if Coords(iX, iY) == p.localCoords:
                            p.hitByTorpedo(shipThatFired.shipType is TYPE_PLAYER, damage)
                hitSomething = True
            else:
                for s in shipsInArea:
                    if Coords(iX, iY) == s.localCoords:
                        hitSomething = shipThatFired.attackTorpedo(s)
            posX+= dirX
            posY+= dirY
            
            hitList.append('dirX: {:f}, dirY: {:f}, iX: {:d}, iY {:d}, posX: {:f}, posY: {:f}'.format(dirX, dirY, iX, iY, posX, posY))
            
        torpsFired-=1
        print('\n'.join(hitList))
        
def dontOppressAnybody(number):
    pass

def oppressCurrentlyUnoppressedSystem(number):
    if number > 0:
        global ENEMY_SHIPS_IN_ACTION
        global SEC_INFO
        enemyShipsAvliable = list(filter(lambda e: e.order == 'REPAIR' and not
                                         SEC_INFO[e.sectorCoords.y][e.sectorCoords.x].hasFriendlyPlanets,
                                         ENEMY_SHIPS_IN_ACTION))
        if len(enemyShipsAvliable) > 0:
            systemsToOppress = []
            for y in SUB_SECTORS_RANGE_Y:
                for x in SUB_SECTORS_RANGE_X:
                    if SEC_INFO[y][x].hasFriendlyPlanets and SEC_INFO[y][x].hasEnemyShips:
                        systemsToOppress.append(tuple([x, y]))
                        
            for n in range(number):
                if len(systemsToOppress) > 0 and len(enemyShipsAvliable) > 0:
                    randSystem = random.choice(systemsToOppress)
                    for s in enemyShipsAvliable:
                        #locationTup = tuple([s.sectorCoords.x, s.sectorCoords.y])
                        if s.order.command == 'REPAIR' and s.checkIfCanReachLocation(randSystem[0], randSystem[1], True)[1]:
                            s.order.Warp(randSystem[0], randSystem[1])
                            
                            systemsToOppress.remove(randSystem)
                            break

def huntDownThePlayer(chance, limit=1):
    global ENEMY_SHIPS_IN_ACTION
    global PLAYER
    
    enemyShipsAvliable = list(filter(lambda e: e.combatEffectivness >= 0.5 and e.order.command == 'REPAIR'
                                     and not e.isDerelect and e.sectorCoords != PLAYER.sectorCoords, ENEMY_SHIPS_IN_ACTION))
    if len(enemyShipsAvliable) > 0:
        for s in enemyShipsAvliable:
            if limit < 1:
                break
            if s.checkIfCanReachLocation(PLAYER.sectorCoords.x, PLAYER.sectorCoords.y, True) and random.uniform() < chance:
                limit-=1
                s.order.Warp(PLAYER.sectorCoords.x, PLAYER.sectorCoords.y)

def reactivateDerelict(limit=1):
    if limit > 0:
        global ENEMY_SHIPS_IN_ACTION
        global PLAYER
        
        enemyShipsAviliable = list(filter(lambda e: e.crewReadyness > 0.5 and e.order.command == 'REPAIR'
                                          and e.sectorCoords != PLAYER.sectorCoords, ENEMY_SHIPS_IN_ACTION))
        
        derelicts = list(filter(lambda e: e.isDerelect and e.sectorCoords != PLAYER.sectorCoords, ENEMY_SHIPS_IN_ACTION))
        
        if len(enemyShipsAvliable) > 0 and len(derelicts) > 0:
            for s in enemyShipsAvliable:
                if limit < 1:
                    break
                recrewedDereliect = None
                for d in derelicts:
                    if s.sectorCoords.distance(d.sectorCoords) == 0:
                        crewToBeam = min(d.shipData.maxCrew, round(s.ableCrew * 0.5))
                        d.ableCrew = crewToBeam
                        s.ableCrew-= crewToBeam
                        limit-=1
                        recrewedDereliect = d
                        break
                    
                if recrewedDereliect:
                    derelicts.remove(recrewedDereliect)

            if limit > 1:
                for s in enemyShipsAvliable:
                    if limit < 1:
                        break
                    recrewedDereliect = None
                    for d in derelicts:
                        if s.checkIfCanReachLocation(d.sectorCoords.x, d.sectorCoords.y, True):
                            s.order.Warp(d.sectorCoords.x, d.sectorCoords.y)
                            recrewedDereliect = d
                            limit-=1
                            break

                    if recrewedDereliect:
                        derelicts.remove(recrewedDereliect)
                        
def assignOrdersEasy():
    global TOTAL_STARSHIPS
    global PLAYER
    #TODO - give enemy ships behavour other then shooting at the player, like moving around
    
    for s in TOTAL_STARSHIPS:
        if not s.isControllable and s.isAlive:
            if s.sectorCoords == PLAYER.sectorCoords:
                order = 'REPAIR'
                canPhaser = s.energy > 0
                canTorp = s.torps > 0
                if canPhaser:
                    if canTorp:
                        if random.randint(0, 1) is 0:
                            order = 'FIRE_TORPEDO'
                        else:
                            order = 'FIRE_PHASERS'
                    else:
                        order = 'FIRE_PHASERS'
                elif canTorp:
                    order = 'FIRE_TORPEDO'

                if order == 'FIRE_TORPEDO':
                    amount = random.randint(1, s.shipData.torpTubes)
                    
                    x, y = PLAYER.localCoords - s.localCoords
                    x1, y1 = Coords(x, y).normalize
                    s.order.Torpedo(x1, y1, amount)
                elif order == 'FIRE_PHASERS':
                    amount = random.randint(round(s.shipData.maxWeapEnergy / 2), s.shipData.maxWeapEnergy)
                    print('Amount to fire at player: {0}'.format(amount))
                    s.order.Phaser(amount, PLAYER)
                else:
                    s.order.Repair()
                
def assignOrdersHard():
    global TOTAL_STARSHIPS
    global PLAYER
    for s in TOTAL_STARSHIPS:
        if not s.isControllable and s.isAlive and not s.isDerelict:
            if s.sectorCoords == PLAYER.sectorCoords:
                if s.energy <= 0:
                    s.order.Repair(1)
                else:
                    #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
                    scan = PLAYER.scanThisShip(s.determinPrecision)
                    eS_HP = s.shields
                    fireTorp = 0
                    firePhaser = 0
                    recharge = 0
                    repair = 1
                    if s.torps > 0 and s.sysTorp.isOpperational and s.checkTorpedoLOS(PLAYER):

                        fireTorp = s.simulateTorpedoHit(PLAYER)
                        
                        extraDamChance = 1.0 - min(scan[0] * 2.0 / PLAYER.shipData.maxShields, 1.0)

                        #to hit: (4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
                        
                        #assume that:
                        #player has 1000 max shields and 350 shields
                        #attacker has 80% trop system
                        #attacker has 60% sensor system
                        #player has 85% impulsive system
                        #distance is 5.75 units

                        #1000 / 350 + 0.8 + 0.6 - 0.85 + (5.75 * 0.25)
                        #2.857142857142857 + 1.4 - 0.85 + 1.4375
                        #4.257142857142857 - 2.2875
                    if s.energy > 0 and s.sysEnergyWeap.isOpperational:
                        firePhaser = s.simulatePhaserHit(PLAYER, 10)
                        #firePhaser = (s.sysEnergyWeap.getEffectiveValue + s.sysSensors.getEffectiveValue - scan[5]) * 10
                        #assume that:
                        #attacker has 
                    if s.energy > 0 and s.sysShields.isOpperational:
                        recharge = (s.shipData.maxShields / s.shields * 1.0 + s.sysShields.getEffectiveValue + scan[3] + scan[9]) * 10

                    total = fireTorp + firePhaser + recharge + repair
                    
                    ch = random.choice([0, 1, 2, 3], weights=[int(fireTorp * 10), int(firePhaser * 10), int(recharge * 10), repair])
                    if ch is 0:
                        ktValue = max((1, scan[0] + scan[1]) / s.shipData.torpDam)
                        s.order.Torpedo(s.localCoords.x, s.localCoords.y, ktValue)
                        #finsih this later
                    elif ch is 1:
                        keValue = scan[0] + scan[1]
                        en = max(0, min(kValue, s.energy))
                        s.order.Phaser(en, PLAYER)
                    elif ch is 2:
                        reValue = min(s.maxShields - s.shields, s.energy)
                        s.order.Recharge(reValue)
                    else:
                        s.order.Repair()
            else:
                s.order.Repair()
                
def implementOrders():
    global TOTAL_STARSHIPS
    global PLAYER
    
    def appender(shipList, filterCommand):
        for sh in shipList:
            if sh.order.command == filterCommand:
                yield sh

    phaseShips = list(appender(TOTAL_STARSHIPS, 'FIRE_PHASERS'))
    torpShips = list(appender(TOTAL_STARSHIPS, 'FIRE_TORPEDO'))
    warpShips = list(appender(TOTAL_STARSHIPS, 'WARP'))
    moveShips = list(appender(TOTAL_STARSHIPS, 'MOVE'))
    rechargeShips = list(appender(TOTAL_STARSHIPS, 'RECHARGE'))
    #repairShips = list(appender(TOTAL_STARSHIPS, 'REPAIR'))

    for s in phaseShips:
        if s.hasValidTarget:
            print('fired {0}'.format(s.order.amount))
            s.attackEnergyWeapon(s.order.target, s.order.amount)
            s.turnTaken = True
    
    for s in torpShips:
        if s.order.amount > 0:
            handleTorpedo(s, s.order.amount, s.order.x, s.order.y)
            #s.attackTorpedo(s.order.target, s.order.amount)
            s.turnTaken = True
                
    for s in warpShips:
        s.warp(s.order.x, s.order.y)
        s.turnTaken = True
    #print('checking list of ships to move')
    for s in moveShips:
        s.move(s.order.x, s.order.y)
        s.turnTaken = True

    for s in rechargeShips:
        s.rechargeShield(s.order.amount)
        s.turnTaken = True

    oppressCurrentlyUnoppressedSystem(1)

    if PLAYER.turnTaken:
        PLAYER.turnRepairing = 0
    
    for s in TOTAL_STARSHIPS:
        if not s.turnTaken:
            s.repair(1)
        else:
            s.turnTaken = False
    """
    if PLAYER.order.command != 'REPAIR':
        PLAYER.turnRepairing = 0"""

def checkForFriendyPlanetsNearby():

    sec = GRID[PLAYER.sectorCoords.y][PLAYER.sectorCoords.x]

    for p in sec.planets:
        if p.canSupplyPlayer(PLAYER, SHIPS_IN_SAME_SUBSECTOR):
            PLAYER.repair(5 * p.infastructure)
            PLAYER.restockTorps()
    
#------- ui related --------
def grabLocalInfo():
    global PLAYER
    global TOTAL_STARSHIPS
    
    pX, pY = PLAYER.sectorCoords.x, PLAYER.sectorCoords.y
    
    lX, lY = PLAYER.localCoords.x, PLAYER.localCoords.y
    
    localGrab = GRID[pY][pX].getCopy
    #print('Loc X: {2}, Y: {3} Sec X: {0}, Y: {1}'.format(pX, pY, lX, lY))
    localGrab[lY][lX] = SYM_PLAYER

    for enemy in SHIPS_IN_SAME_SUBSECTOR:
        #if enemy.sectorCoords == PLAYER.sectorCoords:
        localGrab[enemy.localCoords.y][enemy.localCoords.x] = enemy.shipData.symbol
        
    textSlices = ['    '.join(localGrab[s - 1]) for s in range(SUB_SECTOR_SIZE_Y, 0, -1)]#finish
    return textSlices

def grabSectorInfo():
    global SEC_INFO
    
    textSlices = [''.join([SEC_INFO[y - 1][x].getInfo for x in range(SUB_SECTORS_X)]) for y in range(SUB_SECTORS_Y, 0, -1)]
    return textSlices

def printSplashScreen():
    s = ' ' * (SUB_SECTORS_X + 2 + SUB_SECTOR_SIZE_X)
    splScr = [s,
              s,
              s,
              ':^18'.format('SUPER DS9'),
              s,
              s,
              ':^18'.format('Press any key to begin '),
              s,
              s]
    print('\n'.join(splScr))
    del splScr

def getBeamChar(x, y):
    m = math.atan2(x / y) * 4 / math.pi
    b = ('|', '/', '-', '\\', '|', '/', '-', '\\')
    return b[round(m)]

def printScreen():
    global PLAYER
    
    checkForSelectableShips()
    local = grabLocalInfo()
    sect = grabSectorInfo()

    ispace = ' ' * 20
    halfispace = ' ' * 10
    t = []

    for l, s in zip(local, sect):
        if type(l) is not str or type(s) is not str:
            raise ValueError('l value is: {0}, l type is {1}, s value is: {2}, s value is: {3}'.format(l, type(l), s, type(s)))
        t.append(l)
        t.append('||')
        t.append(s)
        t.append('\n')
    playerInfo = PLAYER.printShipInfo(1)
    selectedInfo = grabSelectedShipInfo()

    t.append(ispace)
    t.append('\n')
    t.append('{0: <32}{1: >32}'.format('Local Position: ' + str(PLAYER.localCoords), 'Sector Position: ' + str(PLAYER.sectorCoords)))
    t.append('\n')
             
    for p, s in zip(playerInfo, selectedInfo):
        if type(p) is not str or type(s) is not str:
            raise ValueError('p value is: {0}, p type is {1}, s value is: {2}, s value is: {3}'.format(p, type(p), s, type(s)))
        t.append(p)
        t.append('||')
        t.append(s)
        t.append('\n')

    print(''.join(t))

cXdict = {
            #'t' : 'You didn\'t enter a heading for torpedo you wanted to fire.',
            'p' : 'You didn\'t enter a number for the amount of energy to use.',
            #'m' : 'You didn\'t enter a directional heading to move in.',
            #'w' : 'You didn\'t enter a directional heading to move in.',
            'c' : 'You didn\'t enter a ship selection number.',
            's' : 'You didn\'t enter a number for the amount of energy to use.'
            }
cYdict = dict()
"""
cYdict = {
            't' : 'You didn\'t enter a number for the number of torpedo tubes you wanted to fire.',
            'm' : 'You didn\'t enter the distance you wanted to move.',
            'w' : 'You didn\'t enter the distance you wanted to warp.',
            }
"""

if EASY_MOVE:
    cXdict['m'] = 'You didn\'t enter a directional heading for the impulse engine.'
    cXdict['w'] = 'You didn\'t enter a directional heading for the warp drive.'
    
    cYdict['m'] = 'You didn\'t enter the distance you wanted to move.'
    cYdict['w'] = 'You didn\'t enter the distance you wanted to warp.'
else:
    cXdict['m'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.'
    cXdict['w'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.'
    cYdict['m'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.'
    cYdict['w'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.'

if EASY_AIM:
    cXdict['t'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.'
    cYdict['t'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.'
else:
    cXdict['t'] = 'You didn\'t enter a heading for torpedo you wanted to fire.'
    cYdict['t'] = 'You didn\'t enter a number for the number of torpedo tubes you wanted to fire.'
    """
    cXdict = {
            't' : 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character',
            'p' : 'You didn\'t enter a number for the amount of energy to use.',
            
            'm' : 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character',
            'w' : 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character',
            'c' : 'You didn\'t enter a ship selection number.',
            's' : 'You didn\'t enter a number for the amount of energy to use.'
            }
    cYdict = {
            't' : 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.',
            'm' : 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.',
            'w' : 'Did you format the command corectly? Remember to seperate the command leter from the \
                  X and Y cooards with a semi-colon, or \':\' character.'
            }
"""
def handleCommands():
    
    errorRaised = False
    passTurn = False
    
    command = input('Enter command (h), (t), (p), (m), (w), (c), (s), (r):\n').lower().split(':')
    global SELECTED_ENEMY_SHIP
    global PLAYER
    global SHIPS_IN_SAME_SUBSECTOR
    global SEC_INFO
    global TURNS_LEFT
    global cXdict, cYdict
    
    try:
        c = command[0]
    except IndexError:
        print('No input detected.')
        errorRaised = True

    if not errorRaised:
        try:
            cX = int(command[1])
        except IndexError:
            if c[0:3] == 'help' or c[0] == 'h':
                pass
                #TODO - bring up help screen
            elif c[0] in cXdict.keys():
                print(cXdict[c[0]])
                errorRaised = True
        except ValueError:
            errorRaised = True
            print('Value for \'X\' is not a valid integer')

        try:
            cY = int(command[2])
        except IndexError:
            if c[0:3] == 'help' or c[0] == 'h':
                pass
                #TODO - bring up help screen
            
            elif c[0] in cYdict:
                print(cYdict[c[0]])
                errorRaised = True
                
        except ValueError:
            errorRaised = True
            print('Value for \'Y\' is not a valid integer.')

        cZ = 5
        
        if EASY_AIM and c[0] == 't':
            try:
                cZ = int(command[3])
            except IndexError:
                print('You didn\'t enter a number for the number of torpedo tubes you wanted to fire.')
                errorRaised = True
            except ValueError:
                errorRaised = True
                print('Value for \'Y\' is not a valid integer.')
            
    if not errorRaised:
        if c[0] == 't':
            #classic mode
            tX, tY = 1, 1
            torpNum = 1
            if EASY_AIM:
                tX, tY = cX, cY
                torpNum = cZ
            else:
                tX, tY = headingToCoords(cX, 5, PLAYER.localCoords.x, PLAYER.localCoords.y, SUB_SECTOR_SIZE_RANGE_X, SUB_SECTOR_SIZE_RANGE_Y)
                torpNum = cY
            print('tX: {:f}, tY: {:f}'.format(tX, tY))
            PLAYER.order.Torpedo(tX, tY, torpNum)
            
            passTurn = True
            
        elif c[0] == 'p':
            if not SELECTED_ENEMY_SHIP:
                if SEC_INFO[PLAYER.sectorCoords.y][PLAYER.sectorCoords.x].hasEnemyShips:
                    assignShipsInSameSubSector()
                    
            if SELECTED_ENEMY_SHIP:
                passTurn = True
                print('Amount to fire at enemy: {0}'.format(cX))
                PLAYER.order.Phaser(cX, SELECTED_ENEMY_SHIP)
                
            else:
                pass
                
            #TODO - finish
            
        elif c[0] == 'm':
            mX, mY = cX, cY
            if not EASY_AIM:
                mX, mY = headingToCoords(cX, cY, PLAYER.localCoords.x, PLAYER.localCoords.y, SUB_SECTOR_SIZE_RANGE_X, SUB_SECTOR_SIZE_RANGE_Y)
            
            if PLAYER.localCoords != Coords(mX, mY):
                
                PLAYER.order.Move(mX, mY)
            else:
                PLAYER.order.Repair(1)
            passTurn = True
            
            
        elif c[0] == 'w':
            wX, wY = cX, cY

            if not EASY_AIM:
                wX, wY = headingToCoords(cX, cY, PLAYER.sectorCoords.x, PLAYER.sectorCoords.y, SUB_SECTORS_RANGE_X, SUB_SECTORS_RANGE_Y)
            if PLAYER.sectorCoords != Coords(wX, wY):

                PLAYER.order.Warp(wX, wY)
                assignShipsInSameSubSector()
            else:
                PLAYER.order.Repair(1)
            passTurn = True
           
            #TODO - finish
        elif c[0] == 'c':
            try:
                SELECTED_ENEMY_SHIP = SHIPS_IN_SAME_SUBSECTOR[cX - 1]
            except IndexError:
                print('Error: ship selection is out of range. The selection number must be greater then zero and \
equal to or less then the number of hostile ships on the screen')
            finally:
                if SELECTED_ENEMY_SHIP == None:
                    print('No enemy ship selected')
                else:
                    print('Ship selection changed')
                    
        elif c[0] == 's':
            PLAYER.order.Recharge(cX)
            passTurn = True
        elif c[0] == 'r':
            PLAYER.order.Repair(1)
            passTurn = True
        elif c[0] == 'h':#TODO - finish writing this later
            print('Background and objectives:\nLike the 1971 Star Trek game, the object of the game is to use a Starfleet ship to \
destroy as many enemy warships as possible before time runs out. Unlike that game, there are a number of diffrences. \
The Enterprise has been replaced by the USS Defiant, and the player must stop a Domminion onslught. Furthermore, \
he player is not required the destroy all of the enemy ships; destroying %75 of the attackers should count as a \
sucess.\n\n\
User Interface: The player has four screens avaliable to him/her, the local or subsector screen, the sector \
screen, the desplay readouts for the systems of the the Defiant, and the sensor readouts for the currently selected \
enemy ship (if any).\n\
Local Screen:\nThis shows the position of the Defiant in the subsector, along with the positions of enemy ships, \
stars, and planets. The objects and enties can be encounted in space are as follows:\n\
@ - The player\
Your ship.\nF - Basic Fighter. Standard enemy attack ship.\n\
A - Advanced Fighter. An improved version of the \
basic fighter, it boast a small torpedo complement and more powerful energy weapons.\n\
C - Battlecruiser. A much \
more dangerous enemy./nB - Battleship. The most powerful Domminion ship that you can be expected to face.\
\n* - Star.\n+ - Allied planet.\n- - Enemy or barren planet.\n. - Empty space.\n\n\
Sector Screen:\n\
Avaliable Commands:\n\
To enter a command, type in a letter followed by one or two numbers seperated by a colon. \
The avalible commands are: (p)hasers, (t)orpedos, (m)ove, (w)arp, (c)hange target, recharge (s)hields, (r)epair, or (h)elp. Most commands \
require one number to be entered with a colon seperating them: (letter):(number). The exceptions are the commands (m)ove, (w)arp, and \
(t)orpedos require two (or three, if easy mode is selected).\
\n\
(W)arp: \
except for moving, warping, and firing torpedos require one two numbers to be entereduse the following format: @:# or @:#:#, with')
        else:
            print('Unknown command')
    if passTurn:
        TURNS_LEFT-=1
        assignOrdersEasy()
        PLAYER.resetRepair()
        implementOrders()
        checkForFriendyPlanetsNearby()
        checkForDestroyedShips()
        assignShipsInSameSubSector()
        
setUpGame()
printSplashScreen()
print('\n')
#printScreen()
while PLAYER.isAlive and TURNS_LEFT > 0 and len(ENEMY_SHIPS_IN_ACTION) > 0:

    printScreen()
    handleCommands()
    
    print(''.join(EVENT_TEXT_TO_PRINT))
    EVENT_TEXT_TO_PRINT = []
    
startingEnemyFleetValue = 0.0
currentEnemyFleetValue = 0.0
endingText = []
for s in TOTAL_STARSHIPS:
    if not s.isControlable:
        startingEnemyFleetValue+= s.shipData.maxHull
        currentEnemyFleetValue+= s.getShipValue
        
destructionPercent = 1.0 - currentEnemyFleetValue / startingEnemyFleetValue
timeLeftPercent = TURNS_LEFT / 100.0
overallScore = destructionPercent * timeLeftPercent#TODO - implement a more complex algorithum for scoring
noEnemyLosses = len(ENEMY_SHIPS_IN_ACTION) + 1 == len(TOTAL_STARSHIPS)

if PLAYER.isAlive:
    if len(ENEMY_SHIPS_IN_ACTION) == 0:
        endingText.append('Thanks to your heroic efforts, mastery of tactial skill, and shrewd manadgement of limited resources, \
you have completly destroyed the Domminion strike force.  \
Well done!')
        if timeLeftPercent < 0.25:
            endingText.append('The enemy has been forced to relocate a large amount of their ships to \
this sector. In doing so, they have weakened their fleets in several key areas, including their holdings in the Alpha Quadrent.')
        elif timeLeftPercent < 0.5:
            endingText.append('Interecpted communications have revealed that because of the total destruction of the enemy task \
force, the {0} has been designated as a priority target.'.format(SHIP_NAME))
        elif timeLeftPercent < 0.75:
            endingText.append('We making prepations for an offensive to capture critical systems. Because of abilities \
Starfleet Command is offering you a promotion to the rank of real admiral.')
        else:
            endingText.append('The enemy is in complete disarray thanks to the speed at which you annilated the opposing fleet. \
Allied forces have exploited the chaos, making bold strikes into Dominion controlled space in the Alpha Quadrent. Starfleet \
Intel has predicded mass defections among from the Cadrassian millitary. Because of abilities Starfleet Command has weighed \
the possibility of a promotion to the rank of real admiral, but ultimatly decided that your skills are more urgantly needed \
in the war.')
    else:
        if noEnemyLosses:
            endingText.append('The mission was a complete failure. The no ships of Domminion strike force were destroyed.')
        elif destructionPercent < 0.25:
            endingText.append('The mission was a failure. Neglible losses were inflited ')
        elif destructionPercent < 0.5:
            endingText.append('The mission was a failure. The casulties inflicted on the Domminion strike fore were insuficent \
to prevent ')
    
else:
    if len(ENEMY_SHIPS_IN_ACTION) == 0:
        endingText.append('Thanks to your sacrifice, mastery of tactial skill, and shrewd manadgement of limited resources, \
you have completly destroyed the Domminion strike force.  \
Well done!')
        if timeLeftPercent < 0.25:
            endingText.append('Your hard fought sacrifice will be long remembered in the reccords of Starfleet history. ')
        elif timeLeftPercent < 0.5:
            endingText.append('')
        elif timeLeftPercent < 0.75:
            endingText.append('')
        else:
            endingText.append('Althoug you were completly victorous over the Domminion strike force, senior personel have \
questioned the reckless or your actions. Admeral Ross has stated that a more cautous aproch would resulted in the survival of ')
    elif noEnemyLosses:
        if timeLeftPercent < 0.25:
            endingText.append('You are an embaressment to the Federation. ')
        else:
            endingText.append('You are terrible at this. ')
    elif destructionPercent < 0.5:
        endingText.append('Pretty bad. ')
    else:
        endingText.append('Still bad. ')

endingText.append('Overall score: {0%}'.format(overallScore))

print(''.join(endingText))
