#BTCallahan, 3/31/2018
#version 0.6.8, 5/12/2018
import math, random
from random import choice, randrange, uniform, random, sample, randint
from operator import add
from coords import Coords
from space_objects import *
from starship import Order, Starship, EnemyShip, FedShip, DEFIANT_CLASS, K_VORT_CLASS, ATTACK_FIGHTER, ADVANCED_FIGHTER, CRUISER, BATTLESHIP
from data_globals import PLANET_TYPES, PLANET_BARREN, PLANET_HOSTILE, PLANET_FRIENDLY
from game_data import GameData

SHIP_ACTIONS = {'FIRE_ENERGY', 'FIRE_TORP', 'MOVE', 'WARP', 'RECHARGE', 'REPAIR'}

HELP_TEXT = 'Background and objectives:\nLike the 1971 Star Trek game, the object of the game is to use a Starfleet ship to \
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
except for moving, warping, and firing torpedos require one two numbers to be entereduse the following format: @:# or @:#:#, with'

gameDataGlobal = GameData.newGame()

"""
SUB_SECTORS_X = 8
SUB_SECTORS_Y = 8

SUB_SECTOR_SIZE_X = 8
SUB_SECTOR_SIZE_Y = 8

SUB_SECTORS_RANGE_X = range(0, SUB_SECTORS_X)
SUB_SECTORS_RANGE_Y = range(0, SUB_SECTORS_Y)

SUB_SECTOR_SIZE_RANGE_X = range(0, SUB_SECTOR_SIZE_X)
SUB_SECTOR_SIZE_RANGE_Y = range(0, SUB_SECTOR_SIZE_Y)
"""

#NO_OF_FIGHTERS = 20
#NO_OF_AD_FIGHTERS = 12
#NO_OF_CRUISERS = 5
#NO_OF_BATTLESHIPS = 1

DESTRUCTION_CAUSES = {'ENERGY', 'TORPEDO', 'RAMMED_ENEMY', 'RAMMED_BY_ENEMY', 'CRASH_BARREN', 'CRASH_HOSTILE', 'CRASH_FRIENDLY', 'WARP_BREACH'}

CAUSE_OF_DAMAGE = ''

SHIP_NAME = 'U.S.S. Defiant'
CAPTAIN_NAME = 'Sisko'

TURNS_LEFT = 100

EASY_MOVE = False
EASY_AIM = False

EVENT_TEXT_TO_PRINT = []


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

PLAYER_DATA = PlayerData.newData()

"""
class Nation:
    def __init__(self, name, energyWeaponName, escapePodPercent)

"""

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
    #global GRID, PLAYER, TOTAL_STARSHIPS
    global gameDataGlobal

    setOfGridPositions = set()

    for iy in SUB_SECTORS_RANGE_Y:
        for jx in SUB_SECTORS_RANGE_X:
            setOfGridPositions.add((jx, iy))

    print('About to assign shiips')
    gameDataGlobal.assignShipsInSameSubSector()

#-----------Gameplay related-----------

getRads = lambda h: (h % 360) * (math.pi / 180)


#------- ui related --------


def getBeamChar(x, y):
    m = math.atan2(x / y) * 4 / math.pi
    b = ('|', '/', '-', '\\', '|', '/', '-', '\\')
    return b[round(m)]

def printScreen():
    global gameDataGlobal
    gd = gameDataGlobal

    gd.checkForSelectableShips()

    local = gd.grabLocalInfo()
    sect = gd.grabSectorInfo()

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
    playerInfo = gd.player.printShipInfo(1)

    selectedInfo = gd.grabSelectedShipInfo(len(playerInfo))

    print('player info length: {0}, enemy info length: {1}.'.format(len(playerInfo), len(selectedInfo)))
    if len(playerInfo) < len(selectedInfo):
        for l in range(len(playerInfo) - len(selectedInfo)):
            playerInfo.append('' * 18)

    t.append(ispace)
    t.append('\n')
    t.append('{0: <32}{1: >32}'.format('Local Position: ' + str(gd.player.localCoords), 'Sector Position: ' + str(gd.player.sectorCoords)))
    t.append('\n')
    print('player info length: {0}, enemy info length: {1}.'.format(len(playerInfo), len(selectedInfo)))
    for p, s in zip(playerInfo, selectedInfo):
        if type(p) is not str or type(s) is not str:
            raise ValueError('p value is: {0}, p type is {1}, s value is: {2}, s value is: {3}'.format(p, type(p), s, type(s)))
        t.append(p)
        t.append('||')
        t.append(s)
        t.append('\n')

    print(''.join(t))

gameDataGlobal.setUpGame()
gameDataGlobal.printSplashScreen()
print('\n')
quitQame = False
#printScreen()
while gameDataGlobal.player.isAlive and gameDataGlobal.turnsLeft > 0 and len(gameDataGlobal.enemyShipsInAction) > 0 and not quitQame:

    printScreen()
    quitQame = gameDataGlobal.handleCommands()
    gameDataGlobal.checkForDestroyedShips()

    print(''.join(gameDataGlobal.eventTextToPrint))
    gameDataGlobal.eventTextToPrint = []

if not quitQame:

    startingEnemyFleetValue = 0.0
    currentEnemyFleetValue = 0.0
    endingText = []
    for s in gameDataGlobal.totalStarships:
        if not s.isControlable:
            startingEnemyFleetValue+= s.shipData.maxHull
            currentEnemyFleetValue+= s.getShipValue

    destructionPercent = 1.0 - currentEnemyFleetValue / startingEnemyFleetValue
    timeLeftPercent = gameDataGlobal.turnsLeft / 100.0
    overallScore = destructionPercent * timeLeftPercent#TODO - implement a more complex algorithum for scoring
    noEnemyLosses = len(gameDataGlobal.enemyShipsInAction) + 1 == len(gameDataGlobal.totalStarships)

    if gameDataGlobal.player.isAlive:
        if len(gameDataGlobal.enemyShipsInAction) == 0:
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
        if len(gameDataGlobal.enemyShipsInAction) == 0:
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
print('Ending game...')
