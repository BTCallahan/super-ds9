from coords import Coords
from random import choice, uniform, random, randint
from itertools import accumulate

from data_globals import TYPE_ALLIED, TYPE_ENEMY_SMALL, TYPE_ENEMY_LARGE, \
SYM_PLAYER, SYM_FIGHTER, SYM_AD_FIGHTER, SYM_CRUISER, SYM_BATTLESHIP, \
SYM_RESUPPLY, LOCAL_ENERGY_COST, SECTOR_ENERGY_COST

scanAssistant = lambda v, p: round(v / p) * p

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

class Torpedo:
    def __init__(self, name, damage, infrastructure):
        self.capName = name.capitalize()
        self.name = name
        self.capPlural = name.capitalize() + 's'
        self.plural = name + 's'
        self.capPluralColon = self.capPlural + ':'
        self.damage = damage
        self.infrastructure = infrastructure

    def _lt__(self, t):
        return self.infrastructure < t.infrastructure

    def __gt__(self, t):
        return self.infrastructure > t.infrastructure

TORP_TYPE_NONE = Torpedo('', 0, 0.0)
TORP_TYPE_POLARON = Torpedo('polaron', 60, 0.35)
TORP_TYPE_PHOTON = Torpedo('photon', 75, 0.5)
TORP_TYPE_QUANTUM = Torpedo('quantum', 100, 0.75)

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

def genNameDefiant():
    return 'U.S.S. ' + choice(['Defiant', 'Sal Polo', 'Valiant'])

def genNameResupply():
    return 'U.S.S. Deliverance'

def genNameKVort():
    return 'I.K.S. ' + choice(['Buruk', 'Ch\'Tang3', 'Hegh\'ta', 'Ki\'Tang', 'Korinar', 'M\'Char', 'Ma\'Para', 'Ning\'Tau', 'Orantho', 'Qevin', 'Rotarran', 'Vorn'])

def randomNeumeral(n):
    for i in range(n):
        yield choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])

def genNameAttackFighter():
    return 'DF ' + ''.join(list(randomNeumeral(6)))

def genNameAdvancedFighter():
    return 'DFF' + ''.join(list(randomNeumeral(4)))

def genNameCruiser():
    return 'DCC' + ''.join(list(randomNeumeral(3)))

def genNameBattleship():
    return 'DBB' + ''.join(list(randomNeumeral(2)))

class ShipData:

    def __init__(self, shipType, symbol, maxShields, maxArmor, maxHull, maxTorps, maxCrew, maxEnergy, damageCon, torpTypes, torpTubes,
                 maxWeapEnergy, warpBreachDist, weaponName, nameGenerator):
        self.shipType = shipType
        self.symbol = symbol

        self.maxShields = maxShields
        self.maxArmor = maxArmor
        self.maxHull = maxHull


        self.maxCrew = maxCrew
        self.maxEnergy = maxEnergy

        self.damageCon = damageCon
        """
        if len(torpTypes) == 0:
            print('torpTypes List has zero lenght')
        elif torpTypes == None:
            printy('torpTypes is None object')
        """
        if (len(torpTypes) == 0) != (torpTubes < 1) != (maxTorps < 1):
            raise IndexError('The length of the torpTypes list is {0}, but the value of torpTubes is {1}, \
and the value of maxTorps is {2}. All of these should be less then one, OR greater then or equal to one.'.format(len(torpTypes), torpTubes))#if (len(torpTypes) == 0 and torpTubes > 1) or (len(torpTypes) > 0 and torpTubes < 0):
        self.torpTypes = torpTypes
        self.torpTypes.sort()

        self.maxTorps = maxTorps
        self.torpTubes = torpTubes
        self.maxWeapEnergy = maxWeapEnergy
        self.warpBreachDist = warpBreachDist
        self.weaponName = weaponName
        self.weaponNamePlural = self.weaponName + 's'
        self.shipNameGenerator = nameGenerator


DEFIANT_CLASS = ShipData(TYPE_ALLIED, SYM_PLAYER, 2700, 400, 500, 20, 50, 5000, 0.45,
                        [TORP_TYPE_QUANTUM, TORP_TYPE_PHOTON], 2, 800, 2, 'Phaser', genNameDefiant)

RESUPPLY = ShipData(TYPE_ALLIED, SYM_RESUPPLY, 1200, 0, 100, 0, 10, 3000, 0.2,
                        [], 0, 200, 5, 'Phaser', genNameResupply)

K_VORT_CLASS = ShipData(TYPE_ALLIED, SYM_PLAYER, 1900, 0, 400, 20, 12, 4000, 0.35,
                        [TORP_TYPE_PHOTON], 1, 750, 2, 'Disruptor', genNameKVort)

ATTACK_FIGHTER = ShipData(TYPE_ENEMY_SMALL, SYM_FIGHTER, 1200, 0, 230, 0, 15, 3000, 0.15,
                        [], 0, 600, 2, 'Poleron', genNameAttackFighter)

ADVANCED_FIGHTER = ShipData(TYPE_ENEMY_SMALL, SYM_AD_FIGHTER, 1200, 0, 230, 5, 15, 3000, 0.15,
                        [TORP_TYPE_POLARON], 1, 650, 2, 'Poleron', genNameAdvancedFighter)

CRUISER = ShipData(TYPE_ENEMY_LARGE, SYM_CRUISER, 3000, 0, 500, 10, 1200, 5250, 0.125,
                        [TORP_TYPE_POLARON], 2, 875, 3, 'Poleron', genNameCruiser)

BATTLESHIP = ShipData(TYPE_ENEMY_LARGE, SYM_BATTLESHIP, 5500, 0, 750, 20, 1200, 8000, 0.075,
                        [TORP_TYPE_POLARON], 6, 950, 5, 'Poleron', genNameBattleship)




#refrence - DEFIANT_CLASS ATTACK_FIGHTER ADVANCED_FIGHTER CRUISER BATTLESHIP

class Starship:
    """
    TODO - implement cloaking device,

    chance of enemy ship detecting you when you are cloaked:
    (1 / distance) * enemy ship sensors
    """

    def __init__(self, shipData, xCo, yCo, secXCo, secYCo):
        def setTorps(torpedoTypes, maxTorps):
            tDict = dict()
            if torpedoTypes == [] or torpedoTypes == None:
                return tDict

            for t in torpedoTypes:
                if t == torpedoTypes[0]:
                    tDict[t] = maxTorps
                else:
                    tDict[t] = 0
            return tDict

        self.localCoords = Coords(xCo, yCo)
        self.sectorCoords = Coords(secXCo, secYCo)

        self.shipData = shipData
        self.shields = shipData.maxShields
        self.armor = shipData.maxArmor
        self.hull = shipData.maxHull

        self.torps = setTorps(shipData.torpTypes, shipData.maxTorps)

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

    def regenerateShip(self):
        def setTorps(torpedoTypes, maxTorps):
            tDict = dict()
            if torpedoTypes == [] or torpedoTypes == None:
                return tDict

            for t in torpedoTypes:
                if t == torpedoTypes[0]:
                    tDict[t] = maxTorps
                else:
                    tDict[t] = 0
            return tDict
        self.shields = shipData.maxShields
        self.armor = shipData.maxArmor
        self.hull = shipData.maxHull

        self.torps = setTorps(shipData.torpTypes, shipData.maxTorps)

        self.ableCrew = shipData.maxCrew
        self.injuredCrew = 0
        self.energy = shipData.maxEnergy

        self.sysWarp.moddify(1.0)
        self.sysTorp.moddify(1.0)
        self.sysImpulse.moddify(1.0)
        self.sysEnergyWep.moddify(1.0)
        self.sysShield.moddify(1.0)
        self.sysSensors.moddify(1.0)

    @property
    def shipTypeCanFireTorps(self):
        return len(self.shipData.torpTypes) > 0 and self.shipData.maxTorps > 0 and self.shipData.torpTubes > 0

    @property
    def crewReadyness(self):
        return self.ableCrew / self.shipData.maxCrew

    @property
    def isDerelict(self):
        return self.ableCrew + self.injuredCrew > 0

    @property
    def getTotalTorps(self):
        if not self.shipTypeCanFireTorps:
            return 0
        return list(accumulate(self.torps.values()))[-1]

    @property
    def getMostPowerfulTorpAvaliable(self):
        if self.shipData.maxTorps < 1:
            return None
        rt = None
        for to in self.shipData.torpTypes:
            if rt == None:
                rt = to
            elif to.damage > rt.damage and self.torps[to] > 0:
                rt = to
        return rt

    def getNumberOfTorps(self, precision):
        #scanAssistant = lambda v, p: round(v / p) * p
        if self.shipTypeCanFireTorps:
            if precision == 1:
                for t in self.shipData.torpTypes:
                    yield (t, self.torps[t])
            else:
                for t in self.shipData.torpTypes:
                    yield (t, scanAssistant(self.torps[t], precision))
        else:
            yield (TORP_TYPE_NONE, 0)

    @property
    def combatEffectivness(self):
        if self.shipTypeCanFireTorps:
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

        if not printSystems:
            return (scanAssistant(self.shields, precision),
                    scanAssistant(self.hull, precision),
                    scanAssistant(self.energy, precision),
                    scanAssistant(self.ableCrew, precision),
                    scanAssistant(self.injuredCrew, precision),
                    list(self.getNumberOfTorps(precision)),
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
                list(self.getNumberOfTorps(precision)),
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
        if self.shipTypeCanFireTorps:
            textList.append('Max Torpedos:   {0: =2}'.format(self.shipData.maxTorps))
            for t in scan[5]:
                #print(str(t[0].capPlural))
                #print(t[1])
                textList.append('{0:<16}{1: =2}'.format(t[0].capPluralColon, t[1]))
            #textList.append('Torpedos:  {0: =2}/  {1: =2}'.format(scan[5], self.shipData.maxTorps))
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

    def destroy(self, gd, cause):

        gd.grid[self.sectorCoords.y][self.sectorCoords.x].removeShipFromSec(self)
        gd.eventTextToPrint.append(self.name)

        if uniform(self.sysWarp.getEffectiveValue * 0.5, 1.0) < self.sysWarp.getEffectiveValue:
            gd.eventTextToPrint.append(' suffers a warp core breach. ')
            self.warpCoreBreach()
        else:
            gd.eventTextToPrint.append(' is destroyed. ')
        self.hull = 0
        if self.isControllable:
            gd.causeOfDamage = cause

    def warpCoreBreach(self, gd, selfDestruct=False):

        shipList = gd.grapShipsInSameSubSector(self)
        oneThird = 1.0 / 3.0
        for s in shipList:
            distance = self.localCoords.distance(s.localCoords)
            damPercent = 1 - (distance / self.shipData.warpBreachDist)
            if damPercent > 0.0:
                if selfDestruct:
                    s.takeDamage(damPercent * self.shipData.maxHull * oneThird, 'Caught in the blast radius of the {0}'.format(self.name))
                else:
                    s.takeDamage(damPercent * self.shipData.maxHull * oneThird, 'Caught in the core breach of the {0}'.format(self.name))

    @property
    def calcSelfDestructDamage(self, player):
        #TODO - write an proper method to look at factors such as current and max hull strength to see if using a self destruct is worthwhile
        if self.hull / self.shipData.maxHull < 0.25 + self.shields / self.maxShields < 0.25:
            if player.sectorCoords == self.sectorCoords:
                damAmount = 1 - (self.localCoords.distance(s.localCoords) / self.warpBreachDist) * self.shipData.maxHull * (1.0 / 3.0)
                if damAmount > 0.0:
                    playerHealth = player.hull + player.shields
                    return playerHealth < damAmount
        return False

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

    def checkIfCanReachLocation(self, gd, x, y, usingWarp):
        #return a tuple with the following structure:
        #(canMoveAtAll, canReachDestination, newX, newY, energyCost)
        #(bool, bool, int, int, float)
        checker = lambda a, b: a if usingWarp else b

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
                Coords.clamp(co, gd.subsecSizeX, gd.subsecSizeY)
            else:
                Coords.clamp(co, gd.subsecsX, gd.subsecsY)

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

    def handleMovment(self, gd, x, y, usingWarp):
        checker = lambda a, b: a if usingWarp else b

        #systemOpperational = checker(self.sysWarp.isOpperational, self.sysImpulse.isOpperational)
        #energyCost = checker(SECTOR_ENERGY_COST, LOCAL_ENERGY_COST)
        fromText = checker(' warps from subsector ', ' moves from position ')
        toText = checker(' to subsector ', ' to position ')
        selfCoords = checker(self.sectorCoords, self.localCoords)
        #effictiveValue = checker(self.sysWarp.getEffectiveValue, self.sysImpulse.getEffectiveValue)

        mo = self.checkIfCanReachLocation(gd, x, y, usingWarp)

        if not mo[0]:
            return False
        gd.eventTextToPrint+=[self.name, fromText, str(selfCoords)]

        if usingWarp:
            gd.grid[self.sectorCoords.y][self.sectorCoords.x].removeShipFromSec(self)

        selfCoords.x-= mo[2]
        selfCoords.y-= mo[3]

        if usingWarp:
            shipList = list(filter(lambda s: s.isAlive and s is not self, gd.totalStarships))
            sp = gd.grid[selfCoords.y][selfCoords.x].findRandomSafeSpot(shipList)

            self.localCoords.x = sp[0]
            self.localCoords.y = sp[1]

            gd.grid[self.sectorCoords.y][self.sectorCoords.x].addShipToSec(self)

        gd.eventTextToPrint+=[toText, str(selfCoords), '.']
        self.energy-=mo[4]

    #TODO - add in a checker to see if the player has plowed into a planet or star, or rammed another starship
    def move(self, gd, x, y):#assume that x = 2, y = 3
        self.handleMovment(gd, x, y, False)

    def warp(self, gd, x, y):
        self.handleMovment(gd, x, y, True)

    def takeDamage(self, gd, amount, text, isTorp=False):

        safeDiv = lambda n, d: 0 if d == 0 else n / d

        pc = lambda: 1 if self.isControllable else self.determinPrecision
        pre = pc()
        """
        if not self.isControllable:
            pre = self.determinPrecision
        """
        #assume damage is 64, current shields are 80, max shields are 200
        #armor is 75, max armor is 100
        #80 * 2 / 200 = 160 / 200 = 0.8
        #0.8 * 64 = 51.2 = the amount of damage that hits the shields
        #64 - 51.2 = 12.8 = the amount of damage that hits the armor and hull
        #1 - (75 / 100) = 1 - 0.25 = 0.75
        #12.8 * 0.75 = 9.6 = the amount of damage that hits the armor
        #12.8 - 9.6 = 3.2 = the amount of damage that hits the hull
        if self.hull <= 0:
            raise AssertionError('The ship {0} has taken damage when it is clearly destroyed!'.format(self.name))
        else:
            shieldsDam = 0.0
            armorDam = 1.0 * amount
            hullDam = 1.0 * amount

            sdm = lambda: 0.75 if isTorp else 1.0
            shieldDamMulti = sdm()

            ahdm = lambda: (lambda: 1.75 if not self.sysShield.isOpperational and self.shields else 1.05) if isTorp else 1.0
            armorHullDamMulti = ahdm()

            armorPercent = safeDiv(self.armor, self.shipData.maxArmor)

            shieldPercent = safeDiv(self.shields, self.shipData.maxShields) * 0.5 + 0.5

            torpHitWithShieldsDown = not self.sysShield.isOpperational and self.shields <= 0 and isTorp

            if self.shields <= 0:
                shieldsDam = 0
            else:
                shieldsDam = shieldPercent * amount * shieldDamMulti

            #hitKnockedDownShields = shieldsDam > self.shields

            if shieldsDam > self.shields:
                shieldsDam = self.shields
            else:
                shieldsDam = shieldPercent * amount

            amount -= shieldsDam / shieldDamMulti

            amount*= armorHullDamMulti

            armorDam = amount * armorPercent

            amount-= armorDam

            hullDam = amount

            def randomSystemDamage():
                return uniform(0.0, 0.12 * (hullDam / self.shipData.maxHull))

            self.hull-= hullDam
            self.armor-= armorDam
            self.shields-= shieldsDam

            gd.eventTextToPrint+=[self.name, ' suffers {0} points of damage to the shields, and \
{1} points to the hull. '.format(scanAssistant(shieldsDam, pre), scanAssistant(hullDam, pre))]

            r = (hullDam / self.shipData.maxHull - self.hull / self.shipData.maxHull) - random()
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
                    gd.eventTextToPrint.append('{} active duty crewmembers were killed. '.format(killedOutright))
                if killedInSickbay > 0:
                    gd.eventTextToPrint.append('{} crewmembers in sickbay were killed. '.format(killedInSickbay))
                if wounded > 0:
                    gd.eventTextToPrint.append('{} crewmembers were injured. '.format(wounded))

            if self.hull <= 0:
                self.destroy(text)
            else:
                if self.isControllable:
                    setattr(self, 'turnRepairing', True)

                if random() < hullDam / self.shipData.maxHull:#damage subsystem at random
                    if randint(0, 3) is 0:
                        gd.eventTextToPrint.append('Impulse engines damaged. ')
                        self.sysImpulse.affectValue(randomSystemDamage())
                    if randint(0, 3) is 0:
                        gd.eventTextToPrint.append('Warp drive damaged. ')
                        self.sysWarp.affectValue(randomSystemDamage())
                    if randint(0, 3) is 0:
                        gd.eventTextToPrint.append(shipData.weaponName)
                        #shipData.weaponNamePlural
                        gd.eventTextToPrint.append(' emitters damaged. ')
                        self.sysEnergyWep.affectValue(randomSystemDamage())
                    if randint(0, 3) is 0:
                        gd.eventTextToPrint.append('Sensors damaged. ')
                        self.sysSensors.affectValue(randomSystemDamage())
                    if randint(0, 3) is 0:
                        gd.eventTextToPrint.append('Shield generator damaged. ')
                        self.sysShield.affectValue(randomSystemDamage())
                    if self.shipData.torpDam > 0 and randint(0, 3) is 0:
                        gd.eventTextToPrint.append('Torpedo launcher damaged. ')
                        self.sysTorp.affectValue(randomSystemDamage())

    def repair(self, factor, externalRepair=False):
        #self.crewReadyness
        repairFactor = self.shipData.damageCon * factor * self.crewReadyness

        self.energy = min(self.shipData.maxEnergy, self.energy + factor * 100)

        healCrew = min(self.injuredCrew, round(self.injuredCrew * 0.2) + randint(2, 5))
        self.ableCrew+= healCrew
        self.injuredCrew-= healCrew

        self.hull = min(self.shipData.maxHull, self.hull + repairFactor)
        self.sysWarp.affectValue(repairFactor)
        self.sysSensors.affectValue(repairFactor)
        self.sysImpulse.affectValue(repairFactor)
        self.sysEnergyWep.affectValue(repairFactor)
        self.sysShield.affectValue(repairFactor)
        if self.shipTypeCanFireTorps:
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
                return random(0, 1) == 0
            else:
                return True
        elif self.energy > 0 and self.sysEnergyWep.isOpperational:
            return False
        return random(0, 1) == 0

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
            self.sysSensors.getEffectiveValue * 1.25 / estimatedEnemyImpulse) > random()

    def rollToHitCannon(self, enemy, estimatedEnemyImpulse=-1):
        if estimatedEnemyImpulse == -1:
            estimatedEnemyImpulse = enemy.sysImpulse.getEffectiveValue
        return (3 / self.localCoords.distance(enemy.localCoords)) * (
            self.sysSensors.getEffectiveValue * 1.25 / estimatedEnemyImpulse * 1.25) > random()

    def attackEnergyWeapon(self, gd, enemy, amount, cannon=False):
        if self.sysEnergyWep.isOpperational:

            amount = min(amount, self.energy)
            self.energy-=amount

            if cannon:
                amount*=1.25
            if self.rollToHitBeam(enemy):

                gd.eventTextToPrint+= [self.name, ' hits ', enemy.name, '. ']
                enemy.takeDamage(amount * self.sysEnergyWep.getEffectiveValue,
                                 'Destroyed by a {0} hit from the {1}'.format(self.shipData.weaponName, self.name))
            else:
                gd.eventTextToPrint+= [self.name, ' misses ', enemy.name, '. ']

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
            estimatedEnemyImpulse - uniform(0.0, 0.75)

    def attackTorpedo(self, gd, enemy, torp):
        if self.rollToHitTorpedo(enemy):
            #chance to hit:
            #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
            gd.eventTextToPrint.append('{0} was hit by a {2} torpedo from {1}. '.format(enemy.name, self.name, torp.name))

            enemy.takeDamage(torp.damage, 'Destroyed by a {1} torpedo hit from the {0}'.format(self.name, torp.name), True)

            return True
        gd.eventTextToPrint.append('A {2} torpedo from {1} missed {0}. '.format(enemy.name, self.name, torp.name))
        return False

    @property
    def isControllable(self):
        return self.shipData.symbol == SYM_PLAYER

    @property
    def hasValidTarget(self):
        return self.order and self.order.target and self.order.target.sectorCoords == self.sectorCoords

class FedShip(Starship):

    def __init__(self, shipInfo, xCo, yCo, secXCo, secYCo):
        super().__init__(shipInfo, xCo, yCo, secXCo, secYCo)
        self.ablatArmor = 1200
        self.turnRepairing = 0
        self.damageTakenThisTurn = False
        self.torpedoLoaded = 0

    @property
    def getMostPowerfulTorpAvaliable(self):
        if self.getTotalTorps > 0:
            if self.torps[self.shipData.torps[self.torpedoLoaded]] < 1:
                rt = super().getMostPowerfulTorpAvaliable
                if rt != None:
                    self.torpedoLoaded = self.shipData.index(rt)
                return rt
            return self.shipData.torps[self.torpedoLoaded]
        return None

    def repair(self, factor, externalRepair=False):
        timeBonus = 1.0 + (self.turnRepairing / 25.0)

        repairFactor = self.shipData.damageCon * factor * self.crewReadyness * timeBonus
        healCrew = min(self.injuredCrew, round(self.injuredCrew * 0.2) + randint(2, 5))

        if externalRepair:
            repairFactor = self.shipData.damageCon * factor * timeBonus
            healCrew = min(self.injuredCrew, round(self.injuredCrew * (0.2 + factor)) + random.randint(6, 10))

        print('max energy :{} current energy: {}, restored energy: {}'.format(self.shipData.maxEnergy,
                                                self.energy, self.energy + factor * 100 * timeBonus))

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

    def restockTorps(self, infrastructure):
        if self.shipData.maxTorps != self.getTotalTorps:
            torpSpace = self.shipData.maxTorps - self.getTotalTorps
            for t in self.shipData.torpTypes:
                if t.infrastructure <= infrastructure:
                    self.torps[t]+= self.getTotalTorps
                    break

    def resetRepair(self):
        if self.damageTakenThisTurn:
            self.turnRepairing = 0
            self.damageTakenThisTurn = False

def createResupplyShip(x, y, secX, secY):
    return FedShip(RESUPPLY, x, y, secX, secY)

class EnemyShip(Starship):

    def __init__(self, shipInfo, xCo, yCo, secXCo, secYCo):
        super().__init__(shipInfo, xCo, yCo, secXCo, secYCo)

    def simulateTorpedoHit(self, target):
        targScan = target.scanThisShip(self.determinPrecision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan[0]
        targHull = [1]

        torp = self.getMostPowerfulTorpAvaliable()
        if torp == None:
            return 0
        torpedos = self.torps[torp]

        timesToFire = min(self.getNoOfAvalibleTorpTubes(), torpedos)

        for t in range(timesToFire):
            if self.rollToHitTorpedo(target, targScan[7]):

                #chance to hit:
                #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
                amount = torp.damage

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

    def checkTorpedoLOS(self, gd, target):

        dirX, dirY = Coords(target.localCoords - self.localCoords).normalize

        g = gd.grid[shipThatFired.sectorCoords.y][shipThatFired.sectorCoords.x]

        posX, posY = self.localCoords.x, self.localCoords.y

        while round(posX) in gd.subsecSizeRangeX and round(posY) in gd.subsecSizeRangeY:
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
                for s in gd.grabShipsInSameSubSector(self):
                    if Coords(iX, iY) == s.localCoords:
                        return True
        return False
