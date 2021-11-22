from __future__ import annotations
from collections import Counter
from ai import BaseAi, HostileEnemy
from get_config import config_object
from coords import AnyCoords, Coords
from data_globals import ShipTypes
from random import choice, randint, randrange, uniform
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING, Tuple, Union
from render_functions import Condition
from starship import ADVANCED_FIGHTER, ATTACK_FIGHTER, BATTLESHIP, CRUISER, DEFIANT_CLASS, Starship
from space_objects import Star, SubSector, Planet

from torpedo import Torpedo, TorpedoType, torpedo_types
import numpy as np

if TYPE_CHECKING:
    from engine import Engine

class GameData:

    engine: Engine

    def __init__(self, *, subsecsX:int, subsecsY:int, subsecSizeX:int, subsecSizeY:int,
                 noOfFighters:int, noOfAdFighters:int, noOfCruisers:int, noOfBattleships:int,
                 turnsLeft:int, 
                 easyMove:bool, easyAim:bool, easyWarp:bool,
                 torpedo_warning:bool, crash_warning:bool, two_d_movment:bool
                 ):
        self.subsecsX = subsecsX
        self.subsecsY = subsecsY
        self.subsecsRangeX = range(subsecsX)
        self.subsecsRangeY = range(subsecsY)

        self.subsecSizeX = subsecSizeX
        self.subsecSizeY = subsecSizeY
        self.subsecSizeRangeX = range(subsecSizeX)
        self.subsecSizeRangeY = range(subsecSizeY)

        self.noOfFighters:int = noOfFighters
        self.noOfAdFighters = noOfAdFighters
        self.noOfCruisers = noOfCruisers
        self.noOfBattleships = noOfBattleships

        self.turnsLeft = turnsLeft
        self.easyMove = easyMove
        self.easyAim = easyAim
        self.easyWarp = easyWarp

        self.two_d_movment = two_d_movment

        self.torpedo_warning = torpedo_warning
        self.crash_warning = crash_warning

        self.eventTextToPrint = []
        self.grid:List[List[SubSector]] = []
        #self.sector_grid = np.empty(shape=(config_object.subsector_width, config_object.subsector_height), order="C", dtype=SubSector)
        
        self.secInfo = []

        self.selected_ship_or_planet:Optional[Union[Starship, Planet, Star]] = None

        self.shipsInSameSubsector:List[Starship] = []
        self.player:Optional[Starship] = None

        self.player_scan:Optional[Dict[str,Any] ] = None
        self.ship_scan:Optional[Dict[str,Any] ] = None

        self.enemyShipsInAction:List[Starship] = []
        self.totalStarships:List[Starship] = []
        self.causeOfDamage = ''

        self.condition = Condition.GREEN

        self.ships_in_same_sub_sector_as_player:List[Starship] = []

        self.player_record = {
            "planets_angered" : 0,
            "planets_depopulated" : 0,
            "prewarp_planets_depopulated" : 0,
            "times_hit_planet" : 0,
            "times_hit_poipulated_planet" : 0,
            "times_hit_prewarp_planet" : 0,
            "deathtoll" : 0
        }
    
    def set_condition(self):

        player = self.player

        if player.docked:
            self.condition = Condition.BLUE
        
        else:

            other_ships = self.grapShipsInSameSubSector(player)

            self.condition = Condition.RED if len(other_ships) > 0 else Condition.YELLOW 
        
        self.player_scan = player.scan_this_ship(1)

        if isinstance(self.selected_ship_or_planet, Starship):
            self.ship_scan = self.selected_ship_or_planet.scan_this_ship(player.determinPrecision)

    def setUpGame(self):

        self.grid = [[SubSector(self, x, y) for x in self.subsecsRangeX] for y in self.subsecsRangeY]
        
        for x in self.subsecSizeRangeX:
            for y in self.subsecSizeRangeY:
                self.grid[y][x].random_setup()
                #self.sector_grid[x,y].random_setup()

        total = self.noOfFighters + self.noOfAdFighters + self.noOfCruisers + self.noOfBattleships

        sub_sectors = [self.grid[randrange(self.subsecsY)][randrange(self.subsecsX)].coords for i in range(total)]

        sub_sector_dictionary = Counter(sub_sectors)
        
        def get_ship(ship_count:int):

            if ship_count < self.noOfFighters:
                return ATTACK_FIGHTER
            if ship_count < self.noOfFighters + self.noOfAdFighters:
                return ADVANCED_FIGHTER
            return CRUISER if ship_count < self.noOfFighters + self.noOfAdFighters + self.noOfCruisers else BATTLESHIP

        def generate_ships():

            ship_count = 0

            for sub_sector_co, i in sub_sector_dictionary.items():

                sub_sector:SubSector = self.grid[sub_sector_co.y][sub_sector_co.x]

                if i == 1:

                    local_co = sub_sector.findRandomSafeSpot()

                    ship = get_ship(ship_count)

                    ship_count += 1

                    starship = Starship(ship, HostileEnemy, local_co.x, local_co.y, sub_sector_co.x, sub_sector_co.y)

                    starship.game_data = self
                    
                    if ship.shipType == ShipTypes.TYPE_ENEMY_SMALL:
                        sub_sector.smallShips+=1
                    elif ship.shipType == ShipTypes.TYPE_ENEMY_LARGE:
                        sub_sector.bigShips+=1

                    yield starship
                
                else:

                    local_cos = sub_sector.find_random_safe_spots(i)

                    for local_co in local_cos:

                        ship = get_ship(ship_count)

                        ship_count += 1

                        starship = Starship(ship, HostileEnemy, local_co.x, local_co.y, sub_sector_co.x, sub_sector_co.y)

                        starship.game_data = self

                        if ship.shipType == ShipTypes.TYPE_ENEMY_SMALL:
                            sub_sector.smallShips+=1
                        elif ship.shipType == ShipTypes.TYPE_ENEMY_LARGE:
                            sub_sector.bigShips+=1

                        yield starship

        self.enemyShipsInAction = list(generate_ships())

        # finds a sector coord 
        all_sector_cos = set(sec.coords for line in self.grid for sec in line) - set(sub_sector_dictionary.keys())

        xy = choice(tuple(all_sector_cos))

        randXsec = xy.x
        randYsec = xy.y

        locPos = self.grid[randYsec][randXsec].findRandomSafeSpot()

        self.player = Starship(DEFIANT_CLASS, BaseAi, locPos.x, locPos.y, randXsec, randYsec)
        self.player.game_data = self
        self.engine.player = self.player

        self.totalStarships = [self.player] + self.enemyShipsInAction

        self.ships_in_same_sub_sector_as_player = self.grapShipsInSameSubSector(self.player)

        self.set_condition()

    @classmethod
    def newGame(cls):
        return cls(8, 8, 8, 8,
                   20, 12, 5, 1,
                   100, False, False)

    #-----Gameplay related------
    def checkForSelectableShips(self):

        player = self.player

        if (isinstance(self.selected_ship_or_planet, Starship) and self.selected_ship_or_planet.sectorCoords != player.sectorCoords
        ) or (isinstance(self.selected_ship_or_planet, Planet) and self.selected_ship_or_planet.sectorCoords != player.sectorCoords
        ) or self.selected_ship_or_planet is None:

            ships_in_same_subsector = self.grapShipsInSameSubSector(player)

            if ships_in_same_subsector:

                self.selected_ship_or_planet = ships_in_same_subsector[0]
            else:
                sector:SubSector = self.grid[player.sectorCoords.y][player.sectorCoords.x]

                if sector.planets_dict:

                    self.selected_ship_or_planet = sector.planets_dict.values()[0]
                else:

                    self.selected_ship_or_planet = None

    def assignShipsInSameSubSector(self):
        
        self.shipsInSameSubsector = [s for s in self.enemyShipsInAction if s.isAlive and s.shipData.shipType is not ShipTypes.TYPE_ALLIED and
                                              s.sectorCoords == self.player.sectorCoords]                             
        #SHIPS_IN_SAME_SUBSECTOR = [s for s in ENEMY_SHIPS_IN_ACTION if (s.shipData.shipType is not TYPE_ALLIED and s.sectorCoords == PLAYER.sectorCoords)]
        print('ships in same subsector: {0}'.format(len(self.shipsInSameSubsector)))
        if len(self.shipsInSameSubsector) > 0:
            if self.selected_ship_or_planet is None or self.selected_ship_or_planet not in self.shipsInSameSubsector:
                self.selected_ship_or_planet = choice(self.shipsInSameSubsector)
        else:
            self.selected_ship_or_planet = None

    def grapShipsInSameSubSector(self, ship:Starship, include_self_in_ships_to_grab:bool=False):

        return (
            [s for s in self.totalStarships if s.isAlive and s.sectorCoords == ship.sectorCoords] 
            if include_self_in_ships_to_grab else 
            [s for s in self.totalStarships if s.isAlive and s.sectorCoords == ship.sectorCoords and s is not ship]
        )

        #return list(filter(lambda s: s.isAlive and s is not ship and
        #                   s.sectorCoords == ship.sectorCoords, self.totalStarships))

    """
    def select_ship_or_planet(self, ship_or_planet:Union[Starship, Planet]):

        self.selected_planet, self.selectedEnemyShip = (None, ship_or_planet) if isinstance(ship_or_planet, Starship) else (ship_or_planet, None)
    """

    def checkForDestroyedShips(self):

        destroyed = []
        for s in self.enemyShipsInAction:
            if not s.isAlive:
                destroyed.append(s)
        if len(destroyed) > 0:
            for d in destroyed:
                self.enemyShipsInAction.remove(d)
        #ENEMY_SHIPS_IN_ACTION -= destroyed

    def handleTorpedo(self, shipThatFired:Starship, torpsFired:int, coords:Tuple[Coords], torpedo_type:TorpedoType, ships_in_area:Dict[Coords, Starship]):
        #global PLAYER
        #headingToDirection
        torpedo = torpedo_types[torpedo_type]

        posX, posY = shipThatFired.localCoords.x, shipThatFired.localCoords.y
        """
        dirX = destX - posX
        dirY = destY - posY
        atan2xy = math.atan2(dirX, dirY)

        dirX, dirY = math.sin(atan2xy), math.cos(atan2xy)
        """
        self.engine.message_log.add_message(
            f"Firing {torpedo.name} torpedo..." if shipThatFired.isControllable else f"{shipThatFired.name} has fired a {torpedo.name} torpedo..."
        )

        g: SubSector = self.grid[shipThatFired.sectorCoords.y][shipThatFired.sectorCoords.x]
        
        #shipsInArea = [ship for ship in self.grapShipsInSameSubSector(shipThatFired) if ship.localCoords in coords]

        shipsInArea = ships_in_area

        for t in range(torpsFired):

            hitSomething=False
            missed_the_target=False

            x = 0
            y = 0

            for co in coords:
                #x_, y_ = co.x, co.y
                
                if not (0<= co.x < config_object.subsector_width) or not (0<= co.y < config_object.subsector_height):
                    #self.engine.message_log.add_message("The torpedo vears off into space!" if missed_the_target else "The torpedo misses!")
                    break

                x,y = co.x, co.y

                #xy = Coords(x,y)

                try:
                    star = g.stars_dict[co]
                    self.engine.message_log.add_message(f"The torpedo impacts against a star at {co.x}, {co.y}.")
                    hitSomething=True
                except KeyError:

                    try:
                        planet = g.planets_dict[co]
                        planet.hitByTorpedo(shipThatFired.isControllable, self, self.engine.message_log, torpedo.damage)
                        hitSomething=True
                    except KeyError:
                        try:
                            ship = shipsInArea[co]
                            hitSomething = shipThatFired.attackTorpedo(self, ship, torpedo)
                            if not hitSomething:
                                missed_the_target = True
                        except KeyError:
                            pass
                if hitSomething:
                    break
                    
            if not hitSomething:
                self.engine.message_log.add_message("The torpedo misses the target!" if missed_the_target else f"The torpedo vears off into space at {x}, {y}!")
        
        shipThatFired.torps[torpedo_type] -= torpsFired

    """
    def oppressCurrentlyUnoppressedSystem(self, number):
        if number > 0:

            enemyShipsAvliable = list(filter(lambda e: e.order == 'REPAIR' and not
                                             self.grid[e.sectorCoords.y][e.sectorCoords.x].hasFriendlyPlanets,
                                             self.enemyShipsInAction))
            if len(enemyShipsAvliable) > 0:
                systemsToOppress = []
                for y in self.subsecSizeRangeY:
                    for x in self.subsecSizeRangeX:
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
                        x1, y1 = Coords(x, y).normalize
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
                        if ch == 0:
                            ktValue = max((1, scan[0] + scan[1]) / s.shipData.torpDam)
                            s.order.Torpedo(s.localCoords.x, s.localCoords.y, ktValue)
                            #finsih this later
                        elif ch == 1:
                            keValue = scan[0] + scan[1]
                            en = max(0, min(keValue, s.energy))
                            s.order.Phaser(en, self.player)
                        elif ch == 2:
                            reValue = min(s.shipData.maxShields - s.shields, s.energy)
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
    """

    """
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
            s.warp(s.order.x, s.order.y)
            s.turnTaken = True
        #print('checking list of ships to move')
        for s in moveShips:
            s.move(s.order.x, s.order.y)
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
    """
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

    """

    def handleCommands(self):

        errorRaised = False
        passTurn = False

        command = input('Enter command (h), (t), (p), (m), (w), (c), (s), (r):\n').lower().split(':')
        gd = self

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

                    tX, tY = headingToCoords(cX, 2, gd.player.localCoords.x, gd.player.localCoords.y, gd.subsecSizeRangeX, gd.subsecSizeRangeY)
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
            #self.implementOrders()
            self.checkForFriendyPlanetsNearby()
            self.checkForDestroyedShips()
            self.assignShipsInSameSubSector()
        return False

    """