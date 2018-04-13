#BTCallahan, 3/31/2018
import math
import random

SHIP_ACTIONS = {'FIRE_ENERGY', 'FIRE_TORP', 'MOVE', 'WARP', 'RECHARGE', 'REPAIR'}

SECTORS_X = 8
SECTORS_Y = 8

SECTOR_SIZE_X = 8
SECTOR_SIZE_Y = 8

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

DESTRUCTION_CAUSE = {'ENERGY', 'TORP', 'RAM_ENEMY', 'CRASH_BARREN', 'CRASH_HOSTILE', 'CRASH_FRIENDLY', 'WARP_BREACH'}

TORP_TYPE_POLARON = 60
TORP_TYPE_PHOTON = 75
TORP_TYPE_QUANTUM = 100

LOCAL_ENERGY_COST = 100
SECTOR_ENERGY_COST = 500

TURNS_LEFT = 100

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
        self.x = int(x)
        self.y = int(y)

    @classmethod
    def randomSectorCoords(cls):
        return cls(random.randrange(0, SECTORS_X), random.randrange(0, SECTORS_Y))

    @classmethod
    def randomLocalCoords(cls):
        return cls(random.randrange(0, SECTOR_SIZE_X), random.randrange(0, SECTOR_SIZE_Y))

    @staticmethod
    def clampSector(s):
        s.x = max(min(s.x, SECTORS_X - 1), 0)
        s.y = max(min(s.y, SECTORS_Y - 1), 0)

    @staticmethod
    def clampLocal(s):
        s.x = max(min(s.x, SECTOR_SIZE_X - 1), 0)
        s.y = max(min(s.y, SECTOR_SIZE_Y - 1), 0)
    
    def __sub__(self, cooards):
        return self.x - cooards.x, self.y - cooards.y
    
    def check(self, x, y):
        return self.x == x and self.y == y
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y
    
    def distance(self, cooards):
        return math.sqrt(pow(self.x -cooards.x, 2) + pow(self.y - cooards.y, 2))

    @property
    def normalize(self):
        d = math.sqrt(pow(self.x, 2) + pow(self.y, 2))
        return self.x / d, self.y / d

    @property
    def isInSectorBounds(self):
        return self.x >= 0 and self.x < SECTORS_X and self.y >= 0 and self.y < SECTORS_Y

    @property
    def isInLocalBounds(self):
        return self.x >= 0 and self.x < SECTOR_SIZE_X and self.y >= 0 and self.y < SECTOR_SIZE_Y
    
    def isAdjacent(self, cooards):
        return self.x in range(coords.x - 1, coords.x + 1) and self.y in range(coords.y - 1, coords.y + 1)

    def __str__(self):
        return 'X: ' + str(self.x) + ', Y: ' + str(self.y)

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
        self.command = 'FIRE_PHASER'
        self.target = target

    def Torpedo(self, x, y, amount):
        self.command = 'FIRE_TORPEDO'
        self.x = x
        self.y = y
        self.amount = amount

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

class Sector:

    @staticmethod
    def __buildSlice():
        ba = list('.'* SECTOR_SIZE_X)
        return ba
    
    def __init__(self, x, y):
        
        self.astroObjects = [Sector.__buildSlice() for s in range(SECTOR_SIZE_Y)]
        
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

    def findRandomSafeSpot(self, shipList=None):
        return random.choice(list(self.getSetOfSafeSpots(shipList)))

    def getSetOfSafeSpots(self, shipList=None):
        
        safeSpots = []
        for iy in range(8):
            for jx in range(8):
                if self.checkSafeSpot(jx, iy):
                    safeSpots.append(tuple([jx, iy]))
                    
        if shipList != None:
            for s in shipList:
                if s.sectorCoords.check(self.x, self.y):
                    t = tuple([s.localCoords.x, s.localCoords.y])
                    if t in safeSpots:
                        safeSpots.remove(t)
                
        return safeSpots

    def __getSubslice(self, y):
        return''.join([self.astroObjects[y][x] for x in range(SECTOR_SIZE_X)])

    @property
    def getCopy(self):
        return [[self.astroObjects[y][x] for x in range(SECTOR_SIZE_X)] for y in range(SECTOR_SIZE_Y)]
        
class Planet:

    def __init__(self, planetType, x, y, secX, secY):
        self.planetType = planetType
        self.localCoords = Coords(x, y)
        self.sectorCoords = Coords(secX, secY)

    def canSupplyPlayer(self, player, enemyList):
        if self.planetType is PLANET_FRIENDLY and self.sectorCoords == player.sectorCoords and \
           self.localCoords.isAdjacent(player.localCoords):
            for e in enemyList:
                if player.sectorCoords == e.sectorCoords:
                    return False
            return True
        return False

    def hitByTorpedo(self, isPlayer):
        
        if self.planetType is PLANET_FRIENDLY and isPlayer:
            self.planetType = PLANET_UNFRIENDLY
        
class StarshipSystem:

    def __init__(self):
        self.integrety = 1.0
    
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
            return '{: ^18.0%}'.format(round(self.integrety / precision) * precision)#finish
        return '{: ^18}'.format('OFFLINE')

GRID = []

SEC_INFO = []

TOTAL_STARSHIPS = []

SELECTED_ENEMY_SHIP = None

SHIPS_IN_SAME_SUBSECTOR = []

PLAYER = None

def checkForSelectableShips():
    global SELECTED_ENEMY_SHIP
    if SELECTED_ENEMY_SHIP == None and len(SHIPS_IN_SAME_SUBSECTOR) > 0:
        SELECTED_ENEMY_SHIP = SHIPS_IN_SAME_SUBSECTOR[0]

class SectorInfo:
    def __init__(self, sector):
        self.friendlyPlanets = len([p for p in sector.planets if p.planetType is PLANET_FRIENDLY])
        self.unfriendlyPlanets = len([p for p in sector.planets if p.planetType is not PLANET_FRIENDLY])
        self.stars = sector.totalStars
        self.bigShips = 0
        self.smallShips = 0
        self.playerPresent = False

    def setShipList(self, ship):
        if ship.shipData.shipType is TYPE_ALLIED:
            self.playerPresent = True
        elif ship.shipData.shipType is TYPE_ENEMY_SMALL:
            self.smallShips+= 1
        else:
            self.bigShips+= 1

    @property
    def hasEnemyShips(self):
        return self.smallShips > 0 or self.bigShips > 0
    
    @property
    def getInfo(self):
        cha = '.'
        if self.playerPresent:
            cha = '@'
        return '{0.friendlyPlanets}{0.unfriendlyPlanets}{1}{0.bigShips}{0.smallShips}'.format(self, cha)

class ShipData:

    def __init__(self, shipType, symbol, maxShields, maxTorps, maxHull, maxEnergy, damageCon, torpDam, torpTubes,
                 maxWeapEnergy, warpBreachDist):
        self.shipType = shipType
        self.symbol = symbol
        
        self.maxShields = maxShields

        self.maxHull = maxHull

        self.maxTorps = maxTorps
        
        self.maxEnergy = maxEnergy

        self.damageCon = damageCon
        self.torpDam = torpDam
        self.torpTubes = torpTubes
        self.maxWeapEnergy = maxWeapEnergy
        self.warpBreachDist = warpBreachDist
        
DEFIANT_CLASS = ShipData(TYPE_ALLIED, SYM_PLAYER, 2700, 500, 20, 5000, 0.45, 100, 2, 800, 2)

ATTACK_FIGHTER = ShipData(TYPE_ENEMY_SMALL, SYM_FIGHTER, 1200, 230, 0, 3000, 0.15, 0, 0, 600, 1)
ADVANCED_FIGHTER = ShipData(TYPE_ENEMY_SMALL, SYM_AD_FIGHTER, 1200, 230, 5, 3000, 0.15, 60, 1, 650, 1)
CRUISER = ShipData(TYPE_ENEMY_LARGE, SYM_CRUISER, 3000, 500, 10, 5250, 0.125, 60, 2, 875, 3)
BATTLESHIP = ShipData(TYPE_ENEMY_LARGE, SYM_BATTLESHIP, 5500, 750, 20, 8000, 0.075, 60, 6, 950, 5)

#refrence - DEFIANT_CLASS ATTACK_FIGHTER ADVANCED_FIGHTER CRUISER BATTLESHIP
class Starship:
    #TODO - implement crewmembers
    def __init__(self, shipData, xCo, yCo, secXCo, secYCo):
        self.localCoords = Coords(xCo, yCo)
        self.sectorCoords = Coords(secXCo, secYCo)

        self.shipData = shipData        
        self.shields = shipData.maxShields
        self.hull = shipData.maxHull
        self.torps = shipData.maxTorps
        self.energy = shipData.maxEnergy
        
        self.sysWarp = StarshipSystem()
        self.sysTorp = StarshipSystem()
        self.sysImpulse = StarshipSystem()
        self.sysEnergyWep = StarshipSystem()
        self.sysShield = StarshipSystem()
        self.sysSensors = StarshipSystem()
        
        self.order = Order.OrderRepair()
        self.turnTaken = False

    @property
    def determinPrecision(self):
        precision = 1    
        if self.sysSensors.getEffectiveValue < 40:
            precision = 100
        elif self.sysSensors.getEffectiveValue < 50:
            precision = 50
        elif self.sysSensors.getEffectiveValue < 60:
            precision = 25
        elif self.sysSensors.getEffectiveValue < 70:
            precision = 20
        elif self.sysSensors.getEffectiveValue < 80:
            precision = 15
        elif self.sysSensors.getEffectiveValue < 90:
            precision = 10
        elif self.sysSensors.getEffectiveValue < 95:
            precision = 5
        elif self.sysSensors.getEffectiveValue < 99:
            precision = 2
        else:
            precision = 1
        return precision

    #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
    def scanThisShip(self, precision, printSystems=False):
        scanAssistant = lambda v, p: round(v / p) * p
        if not printSystems:
            return (scanAssistant(self.shields, precision), scanAssistant(self.hull, precision), 
                    scanAssistant(self.energy, precision), scanAssistant(self.torps, precision), 
                    self.sysWarp.getInfo(precision) * 0.01, self.sysImpulse.getInfo(precision) * 0.01, 
                    self.sysEnergyWep.getInfo(precision) * 0.01, self.sysShield.getInfo(precision) * 0.01, 
                    self.sysSensors.getInfo(precision) * 0.01, self.sysTorp.getInfo(precision) * 0.01)
        return (scanAssistant(self.shields, precision), scanAssistant(self.hull, precision), 
                    scanAssistant(self.energy, precision), scanAssistant(self.torps, precision),
                    self.sysWarp.printInfo(precision),  self.sysImpulse.printInfo(precision), 
                    self.sysEnergyWep.printInfo(precision), self.sysShield.printInfo(precision), 
                    self.sysSensors.printInfo(precision), self.sysTorp.printInfo(precision))

    def printShipInfo(self, precision):
        textList = []

        scan = self.scanThisShip(precision, True)
        
        textList.append('Shields: {0: =4}/{1: =4}'.format(scan[0], self.shipData.maxShields))
        textList.append('Hull:    {0: =4}/{1: =4}'.format(scan[1], self.shipData.maxHull))
        textList.append('Energy:  {0: =4}/{1: =4}'.format(scan[2], self.shipData.maxEnergy))
        textList.append('Torpedos:  {0: =2}/  {1: =2}'.format(scan[3], self.shipData.maxTorps))
        textList.append(' ' * 18)
        textList.append('{0:^18}'.format('System Status:'))
        textList.append(scan[4])
        textList.append(scan[5])
        textList.append(scan[6])
        textList.append(scan[7])
        textList.append(scan[8])
        if self.shipData.maxTorps > 0:
            textList.append(scan[9])
        else:
            textList.append(' ' * 18)
        return textList
            
    @property
    def getShipValue(self):
        return (self.hull + self.shipData.maxHull) * 0.5

    def destroy(self):
        if random.uniform(self.sysWarp.getEffectiveValue * 0.5, 1.0) < self.sysWarp.getEffectiveValue:
            self.hull = 0

    @property
    def isAlive(self):
        return self.hull > 0

    def ram(self, otherShip):
        selfHP = self.shield + self.hull
        otherHP = otherShip.shield + otherShip.hull
        if selfHP > otherHP:
            self.takeDamage(otherHP)
            otherShip.destroy()
        elif selfHP < otherHP:
            otherShip.takeDamage(selfHP)
            self.destroy()
        else:
            otherShip.destroy()
            self.destroy()

    #TODO - add in a checker to see if the player has plowed into a planet or star, or rammed another starship
    def move(self, x, y):#assume that x = 2, y = 3
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
                
                eCost = self.energy

                x = int(x * (self.energy / eCost) / LOCAL_ENERGY_COST)#2 * 447.213595499958 / 100 = 894.217190 / 100 = 8.9421719
                y = int(y * (self.energy / eCost) / LOCAL_ENERGY_COST)
                
            self.localCoords.x-= x
            self.localCoords.y-= y

            self.energy-=eCost

            return True
        return False
            
    def warp(self, x ,y):

        if self.sysWarp.isOpperational and self.energy >= SECTOR_ENERGY_COST:
           
            co = Coords(x, y)

            Coords.clampSector(co)

            dist = SECTOR_ENERGY_COST * self.sectorCoords.distance(co)

            x, y = self.sectorCoords - co

            del co

            eCost = dist / self.sysWarp.getEffectiveValue
            
            if eCost > self.energy:
                
                eCost = self.energy

                x = int(x * (self.energy / eCost) / SECTOR_ENERGY_COST)
                y = int(y * (self.energy / eCost) / SECTOR_ENERGY_COST)

            self.sectorCoords.x-= x
            self.sectorCoords.y-= y
            
            self.energy -= eCost

            if self.shipType is TYPE_ALLIED:             
                secInfoGrid[self.sectorCoords.y][self.sectorCoords.x].playerPresent = False
            elif self.shipType is TYPE_ENEMY_SMALL:
                secInfoGrid[self.sectorCoords.y][self.sectorCoords.x].smallShips-= 1
            else:
                secInfoGrid[self.sectorCoords.y][self.sectorCoords.x].bigShips-= 1

            self.sectorCoords.x, self.sectorCoords.y = x, y

            if self.shipType is TYPE_ALLIED:
                secInfoGrid[self.sectorCoords.y][self.sectorCoords.x].playerPresent = True
            elif self.shipType is TYPE_ENEMY_SMALL:
                secInfoGrid[self.sectorCoords.y][self.sectorCoords.x].smallShips+= 1
            else:
                secInfoGrid[self.sectorCoords.y][self.sectorCoords.x].bigShips+= 1

            #DOTO - finish this
            return True
        return False
        
    def takeDamage(self, amount, isTorp=False):
        #say damage is 64, current shields are 80, max shields are 200
        #80 * 2 / 200 = 160 / 200 = 0.8
        #0.8 * 64 = 51.2 = shieldsDam
        if self.hull > 0:
            shieldsDam = 0.0
            hullDam = 1.0 * amount

            if self.sysShield.isOpperational and self.shields > 0:
                
                shieldsDam = (min(self.shields * 2 / self.shipData.maxShields, 1)) * amount
                hullDam = (1 - min(self.shields * 2 / self.shipData.maxShields, 1)) * amount

                if shieldsDam > self.shields:

                    hullDam+= shieldsDam - self.shields
                    shieldsDam = self.shields
                if isTorp:
                    shieldsDam*= 0.75
                    hullDam*= 1.05
            elif isTorp:
                hullDam*= 1.75#getting hit with a torp while your shields are down - game over
            
            self.hull-= hullDam
            self.shields-= shieldsDam
            
            if self.hull <= 0:
                self.destroy()
            else:
                
                if random.random() < hullDam / self.shipData.maxHull:#damage subsystem at random

                    self.sysImpulse.affectValue(random.uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull)))
                    self.sysWarp.affectValue(random.uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull)))
                    self.sysEnergyWep.affectValue(random.uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull)))
                    self.sysImpulse.affectValue(random.uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull)))
                    self.sysShield.affectValue(random.uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull)))
                    if self.shipData.torpDam > 0:
                        self.sysTorp.accectValue(random.uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull)))
            
    def repair(self, factor):
        self.hull = min(self.shipData.maxHull, self.shipData.maxHull * factor * self.shipData.damageCon)
        self.sysWarp.affectValue(self.shipData.damageCon * factor)
        self.sysSensors.affectValue(self.shipData.damageCon * factor)
        self.sysImpulse.affectValue(self.shipData.damageCon * factor)
        self.sysEnergyWep.affectValue(self.shipData.damageCon * factor)
        self.sysShield.affectValue(self.shipData.damageCon * factor)
        if self.shipData.torpDam > 0:
            self.sysTorp.affectValue(self.shipData.damageCon * factor)

    def rechargeShield(self, amount):
        if self.sysShield.isOpperational:
            if amount >= 0:
                    
                if amount > energy:
                    amount = energy

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
        
    def attackEnergyWeapon(self, enemy, amount):
        if self.sysEnergyWep.isOpperational:
            amount = min(amount, self.shipData.maxWeapEnergy)
            if (self.localCoords.distance(enemy.localCoords) / 1) * (
                        self.sysSensors.getEffectiveValue * 1.25 / enemy.sysImpulse.getEffectiveValue) > random.random():
        
                enemy.takeDamage(amount * self.sysEnergyWep.getEffectiveValue)
                
    def getNoOfAvalibleTorpTubes(self, number=0):
        if not self.sysTorp.isOpperational:
            return 0
        
        if number is 0:
            number = self.shipData.tubes
        else:
            number = min(number, self.shipData.tubes)
        
        return round(max(1, number * self.sysTorp.getEffectiveValue))
    
    def attackTorps(self, enemy):

        if ((4.0 / self.localCoords.distance(enemy.localCoords)) + (self.sysSensors.getEffectiveValue * 1.25) > \
            enemy.sysImpulse.getEffectiveValue + random.uniform(-0.25, 0.25)):
            #chance to hit:
            #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
            enemy.takeDamage(amount * self.shipData.torpDam)
            return True
        return False
        
    @property
    def isPlayerControlled(self):
        return False

    @property
    def hasValidTarget(self):
        return self.order and self.order.target and self.order.target.sectorCoords == self.sectorCoords
    
class FedShip(Starship):

    def __init__(self, shipInfo, xCo, yCo, secXCo, secYCo):
        super().__init__(shipInfo, xCo, yCo, secXCo, secYCo)
        self.ablatArmor = 1200
        self.turnRepairing = 0
        
    def repair(self, factor):
        timeBonus = 1 + (self.turnRepairing / 25)
        self.hull = min(self.shipData.maxHull, self.shipData.maxHull * factor * self.shipData.damageCon * timeBonus)
        self.sysWarp.set(self.shipData.damageCon * factor * timeBonus)
        self.sysTorp.set(self.shipData.damageCon * factor * timeBonus)
        self.sysImpulse.set(self.shipData.damageCon * factor * timeBonus)
        self.sysEnergy.set(self.shipData.damageCon * factor * timeBonus)
        self.sysShield.set(self.shipData.damageCon * factor * timeBonus)
        self.turnRepairing+=1

    def resetRepair(self):
        self.turnRepairing = 0

    @property
    def isPlayerControlled(self):
        return True

class EnemyShip(Starship):

    def __init__(self, shipInfo, xCo, yCo, secXCo, secYCo):
        super().__init__(shipInfo, xCo, yCo, secXCo, secYCo)

    def simulateTorpedoHit(self, target):
        targScan = target.scanThisShip(self.determinPrecision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan[0]
        targHull = [1]

        timesToFire = min(self.shipData.torpTubes, self.torpedos)
        
        if ((4.0 / self.localCoords.distance(enemy.localCoords)) + (self.sysSensors.getEffectiveValue * 1.25) > \
            targScan[5] + random.uniform(-0.25, 0.25)):
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
            if (self.localCoords.distance(target.localCoords) / 1) * (
                        self.sysSensors.getEffectiveValue * 1.25 / targScan[5]) > random.random():
                        
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
        global shipsInArea
        dirX, dirY = Coords(target.localCoords - self.localCoords).normalize
        
        g = GRID[shipThatFired.sectorCoords.y][shipThatFired.sectorCoords.x]
        
        posX, posY = self.localCoords.x, self.localCoords.y
        
        while int(posX) in range (0, SECTOR_SIZE_X) and int(posY) in range (0, SECTOR_SIZE_Y):
            posX+= dirX
            posY+= dirY
            iX = int(posX)
            iY = int(posY)
            if g.astroObjects[iY][iX] in ['*', '+', '-']:
                if g.astroObjects[iY][iX] == '+':
                    for p in g.planets:
                        if Coords(iX, iY) == p.localCoords:
                            return False
            else:
                for s in shipsInArea:
                    if Coords(iX, iY) == s.localCoords:
                        return True
        return False
    
def assignShipsInSameSector():
    global SHIPS_IN_SAME_SUBSECTOR
    global TOTAL_STARSHIPS
    global PLAYER
    global SELECTED_ENEMY_SHIP
    SHIPS_IN_SAME_SUBSECTOR = [s for s in TOTAL_STARSHIPS if (s.shipData.shipType is not TYPE_ALLIED and s.sectorCoords == PLAYER.sectorCoords)]
    if len(SHIPS_IN_SAME_SUBSECTOR) > 0:
        if not SELECTED_ENEMY_SHIP or SELECTED_ENEMY_SHIP not in SHIPS_IN_SAME_SUBSECTOR:
            SELECTED_ENEMY_SHIP = random.choice(SHIPS_IN_SAME_SUBSECTOR)
    else:
        SELECTED_ENEMY_SHIP = None

def grabSelectedShipInfo():
    global SELECTED_ENEMY_SHIP
    
    if SELECTED_ENEMY_SHIP:
        return SELECTED_ENEMY_SHIP.printShipInfo(PLAYER.determinPrecision)
    
    whiteSpace = ' ' * 18
    
    blankScan = []
    for i in range(12):
        blankScan.append(whiteSpace)
    
    return blankScan

def checkWarpCoreBreach(ship):
    global TOTAL_STARSHIPS

    for i in TOTAL_STARSHIPS:

        if i.sectorCoords == ship.sectorCoords and i.localCoords != ship.localCoords:

            dist = ship.localCoords.distance(i.localCoords)
            dam = max(0, dist / ship.warpBreachDist - 1)
            if dam > 0:
                i.takeDamage(ship.shipData.maxHull / 3)

def setUpGame():
    global GRID
    global SEC_INFO
    
    GRID = [[Sector(x, y) for x in range(SECTORS_X)] for y in range(SECTORS_Y)]
    SEC_INFO = [[SectorInfo(GRID[y][x]) for x in range(SECTORS_X)] for y in range(SECTORS_Y)]

    setOfGridPositions = set()

    for iy in range(SECTORS_X):
        for jx in range(8):
            setOfGridPositions.add((jx, iy))

    randXsec, randYsec = random.randrange(0, SECTORS_X), random.randrange(0, SECTORS_Y)

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

        TOTAL_STARSHIPS.append(ship)

    for s in range(NO_OF_CRUISERS):
        randXsec, randYsec = random.sample(setOfGridPositions, 1)[0]

        localPos = GRID[randYsec][randXsec].findRandomSafeSpot(TOTAL_STARSHIPS)
        ship = EnemyShip(CRUISER, randXsec, randYsec, localPos[0], localPos[1])

        TOTAL_STARSHIPS.append(ship)
                             
    for s in range(NO_OF_AD_FIGHTERS):
        randXsec, randYsec = random.sample(setOfGridPositions, 1)[0]

        localPos = GRID[randYsec][randXsec].findRandomSafeSpot(TOTAL_STARSHIPS)
        ship = EnemyShip(ADVANCED_FIGHTER, randXsec, randYsec, localPos[0], localPos[1])

        TOTAL_STARSHIPS.append(ship)

    for s in range(NO_OF_FIGHTERS):
        randXsec, randYsec = random.sample(setOfGridPositions, 1)[0]

        localPos = GRID[randYsec][randXsec].findRandomSafeSpot(TOTAL_STARSHIPS)
        ship = EnemyShip(ATTACK_FIGHTER, randXsec, randYsec, localPos[0], localPos[1])

        TOTAL_STARSHIPS.append(ship)

    
    for s in TOTAL_STARSHIPS:
        SEC_INFO[s.sectorCoords.y][s.sectorCoords.x].setShipList(s)

    assignShipsInSameSector()

#-----------Gameplay related-----------
def checkForDestroyedShips():
    global TOTAL_STARSHIPS
    destroyed = []
    for s in TOTAL_STARSHIPS:
        if not s.isAlive:
            destroyed.append(s)
    TOTAL_STARSHIPS -= destroyed

def handleTorpedo(shipThatFired, shipsInArea, damage, torpsFired, dirX, dirY):
    global GRID
    posX, posY = shipThatFired.localCoords.x, shipThatFired.localCoords.y
    g = GRID[shipThatFired.sectorCoords.y][shipThatFired.sectorCoords.x]
    while torpsFired > 0:
        shipThatFired.torps-=1
        hitSomething = False
        
        while int(posX) in range (0, SECTOR_SIZE_X) and int(posY) in range (0, SECTOR_SIZE_Y) and not hitSomething:
            posX+= dirX
            posY+= dirY
            iX = int(posX)
            iY = int(posY)
            if g.astroObjects[iY][iX] in ['*', '+', '-']:
                if g.astroObjects[iY][iX] == '+':
                    for p in g.planets:
                        if Coords(iX, iY) == p.localCoords:
                            p.hitByTorpedo(shipThatFired.shipType is TYPE_PLAYER)
                hitSomething = True
            else:
                for s in shipsInArea:
                    if Coords(iX, iY) == s.localCoords:
                        hitSomething = shipsThatFired.attackTorps(s)
def assignOrdersEasy():
    global TOTAL_STARSHIPS
    global PLAYER
    #TODO - give enemy ships behavour other then shooting at the player, like moving around
    
    for s in TOTAL_STARSHIPS:
        if not s.isPlayerControlled and s.isAlive:
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
                    amount = random.randint(int(s.shipData.maxWeapEnergy / 2), s.shipData.maxWeapEnergy)
                    s.order.Phasers(amount, PLAYER)
                else:
                    s.order.Repair()
                
def assignOrdersHard():
    global TOTAL_STARSHIPS
    global PLAYER
    for s in TOTAL_STARSHIPS:
        if not s.isPlayerControlled and s.isAlive:
            if s.sectorCoords == PLAYER.sectorCoords:
                if s.energy <= 0:
                    s.order.Repair()
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
                        s.order.Phaser(keValue, PLAYER)
                    elif ch is 2:
                        reValue = min(s.maxShields - s.shields, s.energy)
                        s.order.Recharge(reValue)
                    else:
                        s.order.Repair()
            else:
                s.order.Repair()
                
def implementOrders():
    global TOTAL_STARSHIPS
    
    def appender(shipList, filterCommand):
        for sh in shipList:
            if sh.order.command == filterCommand:
                yield sh

    phaseShips = list(appender(TOTAL_STARSHIPS, 'FIRE_PHASERS'))
    torpShips = list(appender(TOTAL_STARSHIPS, 'FIRE_TORPEDOS'))
    warpShips = list(appender(TOTAL_STARSHIPS, 'WARP'))
    moveShips = list(appender(TOTAL_STARSHIPS, 'MOVE'))
    rechargeShips = list(appender(TOTAL_STARSHIPS, 'RECHARGE'))
    repairShips = list(appender(TOTAL_STARSHIPS, 'REPAIR'))

    for s in phaseShips:
        if s.hasValidTarget:
            s.attackEnergyWeapon(s.order.target, s.order.amount)
            s.turnTaken = True
    
    for s in torpShips:
        if s.order.amount > 0:
            s.attackTorpedo(s.order.target, s.order.amount)
            s.turnTaken = True
                
    for s in warpShips:
        s.warp(s.order.x, s.order.y)
        s.turnTaken = True
    print('checking list of ships to move')
    for s in moveShips:
        s.move(s.order.x, s.order.y)
        s.turnTaken = True

    for s in rechargeShips:
        s.rechargeShield(s.order.amount)
        s.turnTaken = True

    for s in TOTAL_STARSHIPS:
        if not s.turnTaken:
            s.repair(1)
        else:
            s.turnTaken = False

def checkForFriendyPlanetsNearby():

    sec = SEC_INFO[PLAYER.sectorCoords.y][PLAYER.sectorCoords.x]

    for p in sec.planets:
        if p.canSupplyPlayer(PLAYER, 
#------- ui related --------
def grabLocalInfo():
    global PLAYER
    global TOTAL_STARSHIPS
    
    pX, pY = PLAYER.sectorCoords.x, PLAYER.sectorCoords.y
    lX, lY = PLAYER.localCoords.x, PLAYER.localCoords.y
    
    localGrab = GRID[pY][pX].getCopy
    print('Loc X: {2}, Y: {3} Sec X: {0}, Y: {1}'.format(pX, pY, lX, lY))
    localGrab[lY][lX] = SYM_PLAYER

    for enemy in SHIPS_IN_SAME_SUBSECTOR:
        #if enemy.sectorCoords == PLAYER.sectorCoords:
        localGrab[enemy.localCoords.y][enemy.localCoords.x] = enemy.shipData.symbol
        
    textSlices = ['    '.join(localGrab[s]) for s in range(SECTOR_SIZE_Y)]#finish
    return textSlices

def grabSectorInfo():
    global SEC_INFO
    
    textSlices = [''.join([SEC_INFO[y][x].getInfo for x in range(SECTORS_X)]) for y in range(SECTORS_Y)]
    return textSlices

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
        
def handleCommands():
    
    command = input('Enter command (h), (t), (p), ,(w), (c), (s), (r):\n').lower().split(':')
    global SELECTED_ENEMY_SHIP
    global PLAYER
    global SHIPS_IN_SAME_SUBSECTOR
    global SEC_INFO
    global TURNS_LEFT
    
    c = command[0]
    errorRaised = False
    passTurn = False
    
    try:
        cX = int(command[1])
    except IndexError:
        if c[0:3] == 'help' or c[0] == 'h':
            pass
            #TODO - bring up help screen
        else:
            errorRaised = True
            print('Did you format the command corectly? Remember to seperate the command leter from the X and Y cooards with a semi-colon, or \':\' character')#Not a recognized command'
    except ValueError:
        errorRaised = True
        print('Value for \'X\' is not a valid integer')

    try:
        cY = int(command[2])
    except IndexError:
        if c[0:3] == 'help' or c[0] == 'h':
            pass
            #TODO - bring up help screen
        elif c[0] == 'p' or c[0] == 'c':
            pass
        else:
            errorRaised = True
            print('Did you format the command corectly? Remember to seperate the command leter \
from the X and Y cooards with a semi-colon, or \':\' character.')#Not a recognized command'
    except ValueError:
        errorRaised = True
        print('Value for \'Y\' is not a valid integer.')

    try:
        cZ = int(command[3])
    except IndexError:
        if c[0] == 't':
            print('You didn\'t enter a number for the number of torpedo tubes you wanted to fire.')
            errorRaised = True
        elif c[0] == 'p':
            print('You didn\'t enter a number for the amount of energy to use.')
            errorRaised = True
    except ValueError:
        if c[0] == 't':
            print('The value for the numebr of torpedos to fire is not a valid integer.')
            errorRaised = True
        elif c[0] == 'p':
            print('The value for the amount of energy to use is not a valid integer.')
            errorRaised = True
            
    if not errorRaised:
        if c[0] == 't':
            #classic mode
            rads = (cX % 360) * (math.px / 180)
            
            tX = math.sin(rads)
            tY = math.cos(rads)
            
            #easy mode
            
            PLAYER.order.Torpedo(tX, tY, cZ)
            
            passTurn = True
            
        elif c[0] == 'p':
            if not SELECTED_ENEMY_SHIP:
                if SEC_INFO[PLAYER.sectorCoords.y][PLAYER.sectorCoords.x].hasEnemyShips:
                    assignShipsInSameSector()
                    
            if SELECTED_ENEMY_SHIP:
                passTurn = True
                
                PLAYER.order.Phasers(cZ, SELECTED_ENEMY_SHIP)
                
            else:
                pass
                
            #TODO - finish
            
        elif c[0] == 'm':
            if PLAYER.localCoords != Coords(cX, cY):
                
                PLAYER.order.Move(cX, cY)
            else:
                PLAYER.order.Repair()
            passTurn = True
            
            
        elif c[0] == 'w':
            PLAYER.order.Warp(cX, cY)
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
            PLAYER.order.Regen(cX)
            #PLAYER.regenShield(cX)
            passTurn = True
        elif c[0] == 'r':
            PLAYER.order.Repair()
            passTurn = True
            
            #PLAYER.repair()
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
        implementOrders()
        
setUpGame()
printScreen()
while PLAYER.isAlive and TURNS_LEFT > 0:
    
    handleCommands()
    printScreen()
    #TODO - implement actual win loss conditions
    
