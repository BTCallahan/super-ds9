from data_globals import TYPE_ALLIED
from coords import Coords
from space_objects import Sector
import math
from starship import createResupplyShip, FedShip, EnemyShip, DEFIANT_CLASS, \
BATTLESHIP, CRUISER, ADVANCED_FIGHTER, ATTACK_FIGHTER
from random import randrange, randint, choice

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


class GameData:

    def __init__(self, subsecsX, subsecsY, subsecSizeX, subsecSizeY,
                 noOfFighters, noOfAdFighters, noOfCruisers, noOfBattleships,
                 turnsLeft, easyMove, easyAim):
        self.subsecsX = subsecsX
        self.subsecsY = subsecsY
        self.subsecsRangeX = range(subsecsX)
        self.subsecsRangeY = range(subsecsY)

        self.subsecSizeX = subsecSizeX
        self.subsecSizeY = subsecSizeY
        self.subsecSizeRangeX = range(subsecSizeX)
        self.subsecSizeRangeY = range(subsecSizeY)

        self.noOfFighters = noOfFighters
        self.noOfAdFighters = noOfAdFighters
        self.noOfCruisers = noOfCruisers
        self.noOfBattleships = noOfBattleships

        self.turnsLeft = turnsLeft
        self.easyMove = easyMove
        self.easyAim = easyAim

        self.eventTextToPrint = []
        self.grid = []
        self.secInfo = []

        self.selectedEnemyShip = None
        self.shipsInSameSubsector = []
        self.player = None
        self.enemyShipsInAction = []
        self.totalStarships = []
        self.causeOfDamage = ''

        self.ressupplyShip = None
        self.resupplyShipsLeft = 5
        self.ressupplyArivalTime = -1

        self.cXdict = {
            'p' : 'You didn\'t enter a number for the amount of energy to use.',
            'c' : 'You didn\'t enter a ship selection number.',
            's' : 'You didn\'t enter a number for the amount of energy to use.'
            }
        self.cYdict = dict()

    def setUpGame(self):

        if self.easyMove:
            self.cXdict['m'] = 'You didn\'t enter a directional heading for the impulse engine.'
            self.cXdict['w'] = 'You didn\'t enter a directional heading for the warp drive.'

            self.cYdict['m'] = 'You didn\'t enter the distance you wanted to move.'
            self.cYdict['w'] = 'You didn\'t enter the distance you wanted to warp.'
        else:
            self.cXdict['m'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                          X and Y cooards with a semi-colon, or \':\' character.'
            self.cXdict['w'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                          X and Y cooards with a semi-colon, or \':\' character.'
            self.cYdict['m'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                          X and Y cooards with a semi-colon, or \':\' character.'
            self.cYdict['w'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                          X and Y cooards with a semi-colon, or \':\' character.'

        if self.easyAim:
            self.cXdict['t'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                          X and Y cooards with a semi-colon, or \':\' character.'
            self.cYdict['t'] = 'Did you format the command corectly? Remember to seperate the command leter from the \
                          X and Y cooards with a semi-colon, or \':\' character.'
        else:
            self.cXdict['t'] = 'You didn\'t enter a heading for torpedo you wanted to fire.'
            self.cYdict['t'] = 'You didn\'t enter a number for the number of torpedo tubes you wanted to fire.'


        self.grid = [[Sector(self, x, y) for x in self.subsecsRangeX] for y in self.subsecsRangeY]

        randXsec = randrange(self.subsecSizeX)
        randYsec = randrange(self.subsecSizeY)

        locPos = self.grid[randYsec][randXsec].findRandomSafeSpot()

        self.player = FedShip(DEFIANT_CLASS, locPos[0], locPos[1], randXsec, randYsec)

        self.totalStarships.append(self.player)

        def genPositions():
            for x in self.subsecsRangeX:
                for y in self.subsecsRangeY:
                    yield (x, y)

        setOfGridPositions = list(genPositions())

        setOfGridPositions.remove(tuple([self.player.sectorCoords.x, self.player.sectorCoords.y]))

        for s in range(self.noOfBattleships):
            randXsec, randYsec = choice(setOfGridPositions)

            localPos = self.grid[randYsec][randXsec].findRandomSafeSpot(self.totalStarships)
            ship = EnemyShip(BATTLESHIP, randXsec, randYsec, localPos[0], localPos[1])
            self.enemyShipsInAction.append(ship)
            self.totalStarships.append(ship)

        for s in range(self.noOfCruisers):
            randXsec, randYsec = choice(setOfGridPositions)

            localPos = self.grid[randYsec][randXsec].findRandomSafeSpot(self.totalStarships)
            ship = EnemyShip(CRUISER, randXsec, randYsec, localPos[0], localPos[1])
            self.enemyShipsInAction.append(ship)
            self.totalStarships.append(ship)

        for s in range(self.noOfAdFighters):
            randXsec, randYsec = choice(setOfGridPositions)

            localPos = self.grid[randYsec][randXsec].findRandomSafeSpot(self.totalStarships)
            ship = EnemyShip(ADVANCED_FIGHTER, randXsec, randYsec, localPos[0], localPos[1])
            self.enemyShipsInAction.append(ship)
            self.totalStarships.append(ship)

        for s in range(self.noOfFighters):
            randXsec, randYsec = choice(setOfGridPositions)

            localPos = self.grid[randYsec][randXsec].findRandomSafeSpot(self.totalStarships)
            ship = EnemyShip(ATTACK_FIGHTER, randXsec, randYsec, localPos[0], localPos[1])
            self.enemyShipsInAction.append(ship)
            self.totalStarships.append(ship)

        for s in self.totalStarships:
            self.grid[s.sectorCoords.y][s.sectorCoords.x].addShipToSec(s)

    @classmethod
    def newGame(cls):
        return cls(8, 8, 8, 8,
                   20, 12, 5, 1,
                   100, False, False)

    #-----Gameplay related------
    def callForResupply(self):
        if self.ressupplyArivalTime < 0 and self.resupplyShipsLeft > 0:
            if self.ressupplyShip != None and not self.ressupplyShip.isAlive:
                self.ressupplyArivalTime = 9

    def warpInRessuplyShip(self):
        pos = self.grid[self.player.sectorCoords.y][self.player.sectorCoords.x].findRandomSafeSpot(self.shipsInSameSubsector)
        x = self.player.sectorCoords.x
        y = self.player.sectorCoords.y
        if self.ressupplyShip == None:
            self.ressupplyShip = createResupplyShip(pox[0], pos[1], x, y)
        elif not self.ressupplyShip.isAlive:
            self.resupplyShipsLeft-=1
            self.ressupplyShip.regenerateShip()

        else:
            self.ressupplyShip.regenerateShip()
        self.ressupplyShip.torpedoLoaded = 1
        self.ressupplyShip.sectorCoords.x = x
        self.ressupplyShip.sectorCoords.y = y
        self.ressupplyShip.localCoords.x = pos[0]
        self.ressupplyShip.localCoords.y = pos[1]

    def checkForSelectableShips(self):

        if self.selectedEnemyShip == None and len(self.shipsInSameSubsector) > 0:
            self.selectedEnemyShip = self.shipsInSameSubsector[0]

    def assignShipsInSameSubSector(self):
        global TYPE_ALLIED
        self.shipsInSameSubsector = list(filter(lambda s: s.isAlive and s.shipData.shipType is not TYPE_ALLIED and
                                              s.sectorCoords == self.player.sectorCoords, self.enemyShipsInAction))
        #SHIPS_IN_SAME_SUBSECTOR = [s for s in ENEMY_SHIPS_IN_ACTION if (s.shipData.shipType is not TYPE_ALLIED and s.sectorCoords == PLAYER.sectorCoords)]
        print('ships in same subsector: {0}'.format(len(self.shipsInSameSubsector)))
        if len(self.shipsInSameSubsector) > 0:
            if self.selectedEnemyShip == None or self.selectedEnemyShip not in self.shipsInSameSubsector:
                self.selectedEnemyShip = choice(self.shipsInSameSubsector)
        else:
            self.selectedEnemyShip = None

    def grabShipsInSameSubSector(self, ship=None, x=0, y=0):
        if not ship:
            return list(filter(lambda s: s.isAlive and s.sectorCoords.y == y,
                               s.sectorCoords.x == x, self.totalStarships))
        return list(filter(lambda s: s.isAlive and s is not ship and
                           s.sectorCoords == ship.sectorCoords, self.totalStarships))


    def checkForDestroyedShips(self):

        destroyed = []
        for s in self.enemyShipsInAction:
            if not s.isAlive:
                destroyed.append(s)
        if len(destroyed) > 0:
            for d in destroyed:
                self.enemyShipsInAction.remove(d)
        #ENEMY_SHIPS_IN_ACTION -= destroyed


    def handleTorpedo(self, shipThatFired, torpsFired, dirX, dirY, torpedo):
        #global PLAYER

        posX, posY = shipThatFired.localCoords.x, shipThatFired.localCoords.y
        """
        dirX = destX - posX
        dirY = destY - posY
        atan2xy = math.atan2(dirX, dirY)

        dirX, dirY = math.sin(atan2xy), math.cos(atan2xy)
        """

        ## TODO: figure out if the lack of sin and cos will cause a problem
        if shipThatFired.isControllable:
            print(shipThatFired.localCoords)

        g = gameDataGlobal.grid[shipThatFired.sectorCoords.y][shipThatFired.sectorCoords.x]
        shipsInArea = list(filter(lambda s: s.isAlive and s.sectorCoords == shipThatFired.sectorCoords and
                                  s is not shipThatFired, gameDataGlobal.totalStarships))

        damage = shipThatFired.shipData.torpDam
        torpsLeftToFire = shipThatFired.torps[torpedo]

        torpsFired = min(shipThatFired.getNoOfAvalibleTorpTubes(torpsFired), torpsLeftToFire)

        eS = lambda n: '' if n is 1 else 's'

        self.eventTextToPrint.append('{0} fired {1} {3} torpedo{2}. '.format(shipThatFired.name, torpsFired, eS(torpsFired), torpedo.name))

        while torpsFired > 0:
            hitSomething = False
            hitList = []

            while round(posX) in self.subsectorSizeRangeX and round(posY) in self.subsectorSizeRangeY and not hitSomething:

                iX = round(posX)
                iY = round(posY)

                if g.astroObjects[iY][iX] in ['*', '+', '-']:
                    if g.astroObjects[iY][iX] == '+':
                        for p in g.planets:
                            if Coords(iX, iY) == p.localCoords:
                                p.hitByTorpedo(shipThatFired.shipType is self.typePlayer, damage)
                    hitSomething = True
                else:
                    for s in shipsInArea:
                        if Coords(iX, iY) == s.localCoords:
                            hitSomething = shipThatFired.attackTorpedo(s, torpedo)
                posX+= dirX
                posY+= dirY

                hitList.append('dirX: {:f}, dirY: {:f}, iX: {:d}, iY {:d}, posX: {:f}, posY: {:f}'.format(dirX, dirY, iX, iY, posX, posY))

            torpsFired-=1
            torpsLeftToFire-=1

            if shipThatFired.isControllable:
                print('\n'.join(hitList))
        shipThatFired.torps[torpedo] = torpsLeftToFire

    def dontOppressAnybody(self, number):
        pass

    def oppressCurrentlyUnoppressedSystem(self, number):
        if number > 0:

            enemyShipsAvliable = list(filter(lambda e: e.order == 'REPAIR' and not
                                             self.grid[e.sectorCoords.y][e.sectorCoords.x].hasFriendlyPlanets,
                                             self.enemyShipsInAction))
            if len(enemyShipsAvliable) > 0:
                systemsToOppress = []
                for y in self.subectorRangeY:
                    for x in self.subectorRangeX:
                        if self.grid[y][x].hasFriendlyPlanets and self.grid[y][x].hasEnemyShips:
                            systemsToOppress.append(tuple([x, y]))

                for n in range(number):
                    if len(systemsToOppress) > 0 and len(enemyShipsAvliable) > 0:
                        randSystem = choice(systemsToOppress)
                        for s in enemyShipsAvliable:
                            #locationTup = tuple([s.sectorCoords.x, s.sectorCoords.y])
                            if s.order.command == 'REPAIR' and s.checkIfCanReachLocation(self, randSystem[0], randSystem[1], True)[1]:
                                s.order.Warp(randSystem[0], randSystem[1])

                                systemsToOppress.remove(randSystem)
                                break

    def huntDownThePlayer(self, chance, limit=1):
        if limit > 0:
            enemyShipsAvliable = list(filter(lambda e: e.combatEffectivness >= 0.5 and e.order.command == 'REPAIR'
                                             and not e.isDerelect and e.sectorCoords != self.player.sectorCoords, self.enemyShipsInAction))
            if len(enemyShipsAvliable) > 0:
                for s in enemyShipsAvliable:
                    if limit < 1:
                        break
                    if s.checkIfCanReachLocation(self, self.player.sectorCoords.x, self.player.sectorCoords.y, True) and uniform() < chance:
                        limit-=1
                        s.order.Warp(self.player.sectorCoords.x, self.player.sectorCoords.y)

    def reactivateDerelict(self, limit=1):
        if limit > 0:

            enemyShipsAviliable = list(filter(lambda e: e.crewReadyness > 0.5 and e.order.command == 'REPAIR'
                                              and e.sectorCoords != self.player.sectorCoords, self.enemyShipsInAction))

            derelicts = list(filter(lambda e: e.isDerelect and e.sectorCoords != self.player.sectorCoords, self.enemyShipsInAction))

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
                            if s.checkIfCanReachLocation(self, d.sectorCoords.x, d.sectorCoords.y, True):
                                s.order.Warp(d.sectorCoords.x, d.sectorCoords.y)
                                recrewedDereliect = d
                                limit-=1
                                break

                        if recrewedDereliect:
                            derelicts.remove(recrewedDereliect)

    def assignOrdersEasy(self):
        #TODO - give enemy ships behavour other then shooting at the player, like moving around

        for s in self.totalStarships:
            if not s.isControllable and s.isAlive:
                if s.sectorCoords == self.player.sectorCoords:
                    order = 'REPAIR'
                    canPhaser = s.energy > 0
                    canTorp = s.getTotalTorps > 0
                    if canPhaser:
                        if canTorp:
                            if randint(0, 1) is 0:
                                order = 'FIRE_TORPEDO'
                            else:
                                order = 'FIRE_PHASERS'
                        else:
                            order = 'FIRE_PHASERS'
                    elif canTorp:
                        order = 'FIRE_TORPEDO'

                    if order == 'FIRE_TORPEDO':
                        amount = randint(1, s.shipData.torpTubes)

                        x, y = self.player.localCoords - s.localCoords
                        x1, y1 = Coords(x, y).normalize()
                        s.order.Torpedo(x1, y1, amount)
                    elif order == 'FIRE_PHASERS':
                        amount = randint(round(s.shipData.maxWeapEnergy / 2), s.shipData.maxWeapEnergy)
                        print('Amount to fire at player: {0}'.format(amount))
                        s.order.Phaser(amount, self.player)
                    else:
                        s.order.Repair()

    def assignOrdersHard(self):

        for s in self.totalStarships:
            if not s.isControllable and s.isAlive and not s.isDerelict:
                if s.sectorCoords == self.player.sectorCoords:
                    if s.energy <= 0:
                        s.order.Repair(1)
                    else:
                        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
                        scan = self.player.scanThisShip(s.determinPrecision)
                        eS_HP = s.shields
                        fireTorp = 0
                        firePhaser = 0
                        recharge = 0
                        repair = 1
                        if s.torps > 0 and s.sysTorp.isOpperational and s.checkTorpedoLOS(self.player):

                            fireTorp = s.simulateTorpedoHit(self.player)

                            extraDamChance = 1.0 - min(scan[0] * 2.0 / self.player.shipData.maxShields, 1.0)

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
                            firePhaser = s.simulatePhaserHit(self.player, 10)
                            #firePhaser = (s.sysEnergyWeap.getEffectiveValue + s.sysSensors.getEffectiveValue - scan[5]) * 10
                            #assume that:
                            #attacker has
                        if s.energy > 0 and s.sysShields.isOpperational:
                            recharge = (s.shipData.maxShields / s.shields * 1.0 + s.sysShields.getEffectiveValue + scan[3] + scan[9]) * 10

                        total = fireTorp + firePhaser + recharge + repair

                        ch = choice([0, 1, 2, 3], weights=[int(fireTorp * 10), int(firePhaser * 10), int(recharge * 10), repair])
                        if ch is 0:
                            ktValue = max((1, scan[0] + scan[1]) / s.shipData.torpDam)
                            s.order.Torpedo(s.localCoords.x, s.localCoords.y, ktValue)
                            #finsih this later
                        elif ch is 1:
                            keValue = scan[0] + scan[1]
                            en = max(0, min(kValue, s.energy))
                            s.order.Phaser(en, self.player)
                        elif ch is 2:
                            reValue = min(s.maxShields - s.shields, s.energy)
                            s.order.Recharge(reValue)
                        else:
                            s.order.Repair()
                else:
                    s.order.Repair()

    def grabLocalInfo(self):

        pX, pY = self.player.sectorCoords.x, self.player.sectorCoords.y

        lX, lY = self.player.localCoords.x, self.player.localCoords.y

        localGrab = self.grid[pY][pX].getCopy(self)
        #print('Loc X: {2}, Y: {3} Sec X: {0}, Y: {1}'.format(pX, pY, lX, lY))
        localGrab[lY][lX] = self.player.shipData.symbol

        for enemy in self.shipsInSameSubsector:
            #if enemy.sectorCoords == PLAYER.sectorCoords:
            localGrab[enemy.localCoords.y][enemy.localCoords.x] = enemy.shipData.symbol

        textSlices = ['    '.join(localGrab[s - 1]) for s in range(self.subsecSizeY, 0, -1)]#finish
        return textSlices

    def grabSectorInfo(self):

        textSlices = [''.join([self.grid[y - 1][x].getInfo for x in range(self.subsecsX)]) for y in range(self.subsecsY, 0, -1)]
        return textSlices

    def grabSelectedShipInfo(self, padding):

        if self.selectedEnemyShip:
            print('enemy ships is selected')

            return self.selectedEnemyShip.printShipInfo(self.player.determinPrecision)

        whiteSpace = ' ' * 18

        blankScan = []
        for i in range(padding + 1):
            blankScan.append(whiteSpace)

        return blankScan


    def implementOrders(self):
        #global TOTAL_STARSHIPS, PLAYER

        def appender(shipList, filterCommand):
            for sh in shipList:
                if sh.order.command == filterCommand:
                    yield sh

        phaseShips = list(appender(self.totalStarships, 'FIRE_PHASERS'))
        torpShips = list(appender(self.totalStarships, 'FIRE_TORPEDO'))
        warpShips = list(appender(self.totalStarships, 'WARP'))
        moveShips = list(appender(self.totalStarships, 'MOVE'))
        rechargeShips = list(appender(self.totalStarships, 'RECHARGE'))
        #repairShips = list(appender(TOTAL_STARSHIPS, 'REPAIR'))

        for s in phaseShips:
            if s.hasValidTarget:
                print('fired {0}'.format(s.order.amount))
                s.attackEnergyWeapon(s.order.target, s.order.amount)
                s.turnTaken = True

        for s in torpShips:
            if s.order.amount > 0:
                self.handleTorpedo(s, s.order.amount, s.order.x, s.order.y, s.getMostPowerfulTorpAvaliable)
                #s.attackTorpedo(s.order.target, s.order.amount)
                s.turnTaken = True

        for s in warpShips:
            s.warp(self, s.order.x, s.order.y)
            s.turnTaken = True
        #print('checking list of ships to move')
        for s in moveShips:
            s.move(self, s.order.x, s.order.y)
            s.turnTaken = True

        for s in rechargeShips:
            s.rechargeShield(s.order.amount)
            s.turnTaken = True

        self.oppressCurrentlyUnoppressedSystem(1)

        if self.player.turnTaken:
            self.player.turnRepairing = 0

        for s in self.totalStarships:
            if not s.turnTaken:
                s.repair(1)
            else:
                s.turnTaken = False

    def checkForFriendyPlanetsNearby(self):

        sec = self.grid[self.player.sectorCoords.y][self.player.sectorCoords.x]
        if sec.friendlyPlanets > 0:#!!!!
            pla = list(filter(lambda p: p.canSupplyPlayer(self.player, self.shipsInSameSubsector), sec.planets)).sort()

            if pla is not None:
                self.player.repair(5 * pla[0].infrastructure)
                self.player.restockTorps(pla[0].infrastructure)

    #-------UI related------

    def printSplashScreen(self):
        s = ' ' * (self.subsecsX + 2 + self.subsecSizeX)
        splScr = [s,
                  s,
                  s,
                  '{:^18}'.format('SUPER DS9'),
                  s,
                  s,
                  '{:^18}'.format('Press any key to begin '),
                  s,
                  s]
        print('\n'.join(splScr))
        del splScr

    def handleCommands(self):

        errorRaised = False
        passTurn = False

        command = input('Enter command (h), (t), (p), (m), (w), (c), (s), (r):\n').lower().split(':')

        #global SELECTED_ENEMY_SHIP, PLAYER, SHIPS_IN_SAME_SUBSECTOR, GRID, TURNS_LEFT, cXdict, cYdict

        try:
            c = command[0]
        except IndexError:
            print('No input detected.')
            errorRaised = True

        if not errorRaised:
            if command[0] == 'q':
                return True
            try:
                cX = int(command[1])
            except IndexError:
                if c[0:3] == 'help' or c[0] == 'h':
                    pass
                    #TODO - bring up help screen
                elif c[0] in self.cXdict.keys():
                    print(self.cXdict[c[0]])
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

                elif c[0] in self.cYdict:
                    print(self.cYdict[c[0]])
                    errorRaised = True

            except ValueError:
                errorRaised = True
                print('Value for \'Y\' is not a valid integer.')

            cZ = 5

            if self.easyAim and c[0] == 't':
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
                if self.easyAim:
                    tX, tY = cX, cY
                    torpNum = cZ
                else:
                    #tX, tY = headingToCoordsTorp(cX, 3)
                    #tX+= PLAYER.localCoords.x
                    #tY+= PLAYER.localCoords.y

                    tX, tY = headingToCoords(cX, 2, self.player.localCoords.x, self.player.localCoords.y, self.subsecSizeRangeX, self.subsecSizeRangeY)
                    torpNum = cY
                tX-= self.player.localCoords.x
                tY-= self.player.localCoords.y
                tX, tY = Coords(tX, tY).normalize
                print('tX: {:f}, tY: {:f}'.format(tX, tY))

                self.player.order.Torpedo(tX, tY, torpNum)

                passTurn = True

            elif c[0] == 'p':
                if not self.selectedEnemyShip:
                    if self.grid[self.player.sectorCoords.y][self.player.sectorCoords.x].hasEnemyShips:
                        self.assignShipsInSameSubSector()

                if self.selectedEnemyShip:
                    passTurn = True
                    print('Amount to fire at enemy: {0}'.format(cX))
                    self.player.order.Phaser(cX, self.selectedEnemyShip)

                else:
                    pass

                #TODO - finish

            elif c[0] == 'm':
                mX, mY = cX, cY
                if not self.easyAim:
                    mX, mY = headingToCoords(cX, cY, self.player.localCoords.x, self.player.localCoords.y, self.subsecSizeRangeX, self.subsecSizeRangeY)

                if self.player.localCoords != Coords(mX, mY):

                    self.player.order.Move(mX, mY)
                else:
                    self.player.order.Repair(1)
                passTurn = True


            elif c[0] == 'w':
                wX, wY = cX, cY

                if not self.easyAim:
                    wX, wY = headingToCoords(cX, cY, self.player.sectorCoords.x, self.player.sectorCoords.y, self.subsecsRangeX, self.subsecsRangeY)
                if self.player.sectorCoords != Coords(wX, wY):

                    self.player.order.Warp(wX, wY)
                    self.assignShipsInSameSubSector()
                else:
                    self.player.order.Repair(1)
                passTurn = True

                #TODO - finish
            elif c[0] == 'c':
                try:
                    self.selectedEnemyShip = self.shipsInSameSubsector[cX - 1]
                except IndexError:
                    print('Error: ship selection is out of range. The selection number must be greater then zero and \
    equal to or less then the number of hostile ships on the screen')
                finally:
                    if self.selectedEnemyShip == None:
                        print('No enemy ship selected')
                    else:
                        print('Ship selection changed')

            elif c[0] == 's':
                self.player.order.Recharge(cX)
                passTurn = True
            elif c[0] == 'r':
                self.player.order.Repair(1)
                passTurn = True
            elif c[0] == 'h':#TODO - finish writing this later
                print()
            else:
                print('Unknown command')
        if passTurn and not errorRaised:
            self.turnsLeft-=1
            self.assignOrdersEasy()
            self.player.resetRepair()
            self.implementOrders()
            self.checkForFriendyPlanetsNearby()
            self.checkForDestroyedShips()
            self.assignShipsInSameSubSector()
        return False
