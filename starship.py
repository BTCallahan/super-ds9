from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, Union
from random import choice, uniform, random, randint
from math import ceil, inf
from itertools import accumulate
from functools import lru_cache

from global_functions import headingToDirection
from space_objects import SubSector
from ai import BaseAi
from torpedo import Torpedo, TorpedoType, find_most_powerful_torpedo
from coords import Coords, IntOrFloat, MutableCoords
from torpedo import torpedo_types
import colors
from data_globals import SYM_PLAYER, SYM_FIGHTER, SYM_AD_FIGHTER, SYM_CRUISER, SYM_BATTLESHIP, \
SYM_RESUPPLY, LOCAL_ENERGY_COST, SECTOR_ENERGY_COST, ShipTypes

def scanAssistant(v:IntOrFloat, precision:int):
    """This takes a value, v and devides it by the precision. Next, the quotent is rounded to the nearest intiger and 
    then multiplied by the precision. The product is then returned. A lower precision value ensures more accurate results.
    If precision is 1, then v is returned

    E.g.:
    v = 51.25
    p = 25

    round(51.25 / 25) * 25
    round(2.41) * 25
    2 * 25
    50

    Args:
        v (IntOrFloat): The value that is modified
        precision (int): This value is used to calucalate the crecision. Lower values are better.

    Returns:
        int: The modified value
    """
    if precision == 1:
        return round(v)
    return round(v / precision) * precision

if TYPE_CHECKING:
    from game_data import GameData


class StarshipSystem:
    """[summary]
    """

    def __init__(self, name:str):
        """This handles a starship system, such as warp drives or shields.

        Args:
            name (str): The name of the system.
        """
        self._integrety = 1.0
        self.name = '{: <9}'.format(name)

    @property
    def integrety(self):
        return self._integrety
    
    @integrety.setter
    def integrety(self, value):
        self._integrety = value
        if self._integrety < 0.0:
            self._integrety = 0.0
        elif self._integrety > 1.0:
            self._integrety = 1.0

    @property
    def isOpperational(self):
        return self._integrety >= 0.15

    @property
    def getEffectiveValue(self):
        """
        Starship systems can take quite a bit of beating before they begin to show signs of reduced performance. Generaly, 
        when the systems integrety dips below 80% is when you will see performance degrade. Should integrety fall below 
        15%, then the system is useless and inoperative.
        """
        return min(1.0, self._integrety * 1.25) if self.isOpperational else 0.0

    @property
    def affect_cost_multiplier(self):
        return 1 / self.getEffectiveValue if self.isOpperational else inf

    #def __add__(self, value):

    def getInfo(self, precision:float):
        return (round(self._integrety * 100 / precision) * precision * 0.01) if self.isOpperational else 0.0

    def printInfo(self, precision):
        return f"{self.name}: {self.getInfo(precision)}" if self.isOpperational else f"{self.name} OFFLINE"

def genNameDefiant():
    return 'U.S.S. ' + choice(['Defiant', 'Sal Polo', 'Valiant'])

def genNameResupply():
    return 'U.S.S. Deliverance'

def genNameKVort():
    return 'I.K.S. ' + choice(['Buruk', 'Ch\'Tang3', 'Hegh\'ta', 'Ki\'Tang', 'Korinar', 'M\'Char', 'Ma\'Para', 'Ning\'Tau', 'Orantho', 'Qevin', 'Rotarran', 'Vorn'])

def randomNeumeral(n:int) -> str:
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

def gen_name_cardassian():
    return choice(("Aldara", "Bok'Nor", "Groumall", "Koranak", "Kornaire", "Kraxon", "Prakesh", "Prakesh", "Rabol", "Ravinok", "Reklar", "Trager", "Vetar"))

@lru_cache
def get_system_names(
    has_torpedo_launchers:bool=False,
    has_cloaking_device:bool=False,
    beam_weapon_name:str="",
    cannon_weapon_name:str=""
):
    names = [
        "Shield Gen.:",
        "Impulse Eng.:", 
        "Sensors:",
        "Warp Drive:",      
    ]

    keys = [
        "sys_shield",
        "sys_impulse",
        "sys_sensors",
        "sys_warp",
    ]

    if beam_weapon_name:
        names.append(f"{beam_weapon_name}:")
        keys.append("sys_energy_weapon")

    if cannon_weapon_name:
        names.append(f"{cannon_weapon_name}")
        keys.append("sys_cannon_weapon")

    if has_cloaking_device:
        names.append("Cloak Dev.")
        keys.append("sys_cloak")

    if has_torpedo_launchers:
        names.append("Torp. Launchers:")
        keys.append("sys_torpedo")
    
    return names, keys

class ShipData:

    def __init__(self, *,
        shipType:ShipTypes, symbol:str, maxShields:int, maxArmor:int=0, maxHull:int, maxTorps:int=0, 
        maxCrew:int, maxEnergy:int, damageCon:float, torpTypes:Optional[List[TorpedoType]]=None, 
        torpTubes:int=0,
        maxWeapEnergy:int, warpBreachDist:int=2, weaponName:str, 
        nameGenerator:Callable[[], str]
        ):
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
        if (torpTypes is None or len(torpTypes) == 0) != (torpTubes < 1) != (maxTorps < 1):
            raise IndexError(f'The length of the torpTypes list is {len(torpTypes)}, but the value of torpTubes is {torpTubes}, and the value of maxTorps is {maxTorps}. All of these should be less then one, OR greater then or equal to one.')
#if (len(torpTypes) == 0 and torpTubes > 1) or (len(torpTypes) > 0 and torpTubes < 0):
        #torpTypes.sort()

        if torpTypes:
            torpTypes.sort(key=lambda t: torpedo_types[t])

        self.torpTypes = tuple([TorpedoType.TORP_TYPE_NONE] if not torpTypes else torpTypes)

        self.maxTorps = maxTorps
        self.torpTubes = torpTubes
        self.maxWeapEnergy = maxWeapEnergy
        self.warpBreachDist = warpBreachDist
        self.weaponName = weaponName
        self.weaponNamePlural = self.weaponName + 's'
        self.shipNameGenerator = nameGenerator

        self.system_names, self.system_keys = get_system_names(
            has_torpedo_launchers= maxTorps > 0 and torpTubes > 0,
            beam_weapon_name=self.weaponNamePlural
        )

    

    @property
    @lru_cache
    def shipTypeCanFireTorps(self):
        return len(self.torpTypes) > 0 and self.torpTypes[0] != TorpedoType.TORP_TYPE_NONE and self.maxTorps > 0 and self.torpTubes > 0

    @property
    @lru_cache
    def get_most_powerful_torpedo_type(self):
        if not self.shipTypeCanFireTorps:
            return TorpedoType.TORP_TYPE_NONE

        if len(self.torpTypes) == 1:
            return self.torpTypes[0]

        return find_most_powerful_torpedo(self.torpTypes)


DEFIANT_CLASS = ShipData(
    shipType=ShipTypes.TYPE_ALLIED, 
    symbol=SYM_PLAYER, 
    maxShields=2700, 
    maxArmor=400, 
    maxHull=500, 
    maxTorps=20, 
    maxCrew=50, 
    maxEnergy=5000, 
    damageCon=0.45,
    torpTypes=[TorpedoType.TORP_TYPE_QUANTUM, TorpedoType.TORP_TYPE_PHOTON], 
    torpTubes=2, 
    maxWeapEnergy=800, 
    warpBreachDist=2, 
    weaponName='Phaser', 
    nameGenerator=genNameDefiant)

RESUPPLY = ShipData(
    shipType=ShipTypes.TYPE_ALLIED, 
    symbol=SYM_RESUPPLY, 
    maxShields=1200, 
    maxHull=100, 
    maxCrew=10, 
    maxEnergy=3000, 
    damageCon=0.2,
    maxWeapEnergy=200, 
    warpBreachDist=5, 
    weaponName='Phaser', 
    nameGenerator=genNameResupply)

K_VORT_CLASS = ShipData(
    shipType=ShipTypes.TYPE_ALLIED, 
    symbol=SYM_PLAYER, 
    maxShields=1900, 
    maxHull=400, 
    maxTorps=20, 
    maxCrew=12, 
    maxEnergy=4000, 
    damageCon=0.35,
    torpTypes=[TorpedoType.TORP_TYPE_PHOTON], 
    torpTubes=1, 
    maxWeapEnergy=750, 
    warpBreachDist=2, 
    weaponName='Disruptor', 
    #cloak_strength=0.875,
    nameGenerator=genNameKVort)

ATTACK_FIGHTER = ShipData(
    shipType=ShipTypes.TYPE_ENEMY_SMALL, 
    symbol=SYM_FIGHTER, 
    maxShields=1200,
    maxHull=230, 
    maxCrew=15, 
    maxEnergy=3000, 
    damageCon=0.15,
    maxWeapEnergy=600, 
    warpBreachDist=2, 
    weaponName='Poleron', 
    nameGenerator=genNameAttackFighter)

ADVANCED_FIGHTER = ShipData(
    shipType=ShipTypes.TYPE_ENEMY_SMALL, 
    symbol=SYM_AD_FIGHTER, 
    maxShields=1200,
    maxHull=230, 
    maxTorps=5, 
    maxCrew=15, 
    maxEnergy=3000, 
    damageCon=0.15,
    torpTypes=[TorpedoType.TORP_TYPE_POLARON], 
    torpTubes=1, 
    maxWeapEnergy=650, 
    warpBreachDist=2, 
    weaponName='Poleron', 
    nameGenerator=genNameAdvancedFighter)

CRUISER = ShipData(
    shipType=ShipTypes.TYPE_ENEMY_LARGE, 
    symbol=SYM_CRUISER, 
    maxShields=3000, 
    maxHull=500, 
    maxTorps=10, 
    maxCrew=1200, 
    maxEnergy=5250, 
    damageCon=0.125,
    torpTypes=[TorpedoType.TORP_TYPE_POLARON], 
    torpTubes=2, 
    maxWeapEnergy=875, 
    warpBreachDist=3, 
    weaponName='Poleron', 
    nameGenerator=genNameCruiser)

BATTLESHIP = ShipData(
    shipType=ShipTypes.TYPE_ENEMY_LARGE, 
    symbol=SYM_BATTLESHIP, 
    maxShields=5500, 
    maxHull=750, 
    maxTorps=20, 
    maxCrew=1200, 
    maxEnergy=8000, 
    damageCon=0.075,
    torpTypes=[TorpedoType.TORP_TYPE_POLARON], 
    torpTubes=6, 
    maxWeapEnergy=950, 
    warpBreachDist=5, 
    weaponName='Poleron', 
    nameGenerator=genNameBattleship)

HIDEKI = ShipData(
    shipType=ShipTypes.TYPE_ENEMY_SMALL,
    symbol=SYM_AD_FIGHTER,
    maxShields=1500,
    maxHull=430,
    maxCrew=35,
    maxEnergy=800,
    damageCon=0.2,
    maxWeapEnergy=700,
    warpBreachDist=2,
    weaponName="Compresser",
    nameGenerator=gen_name_cardassian
)

#refrence - DEFIANT_CLASS ATTACK_FIGHTER ADVANCED_FIGHTER CRUISER BATTLESHIP

class Starship:
    """
    TODO - implement cloaking device,

    chance of enemy ship detecting you when you are cloaked:
    (1 / distance) * enemy ship sensors
    """

    game_data: GameData

    def __init__(self, 
    shipData:ShipData, 
    ai_cls: Type[BaseAi],
    xCo, yCo, 
    secXCo, secYCo
    ):
        def setTorps(torpedoTypes, maxTorps):
            tDict: Dict[TorpedoType, int] = {}
            if torpedoTypes == [] or torpedoTypes == None:
                return tDict

            for t in torpedoTypes:
                
                tDict[t] = maxTorps if t == torpedoTypes[0] else 0
                
            return tDict

        self.localCoords:MutableCoords = MutableCoords(xCo, yCo)
        self.sectorCoords:MutableCoords = MutableCoords(secXCo, secYCo)
        
        self.shipData:ShipData = shipData
        self._shields = shipData.maxShields
        self.armor = shipData.maxArmor
        self._hull = shipData.maxHull

        self.torps = setTorps(shipData.torpTypes, shipData.maxTorps)

        self.ableCrew = shipData.maxCrew
        self.injuredCrew = 0
        self._energy = shipData.maxEnergy

        self.sysWarp = StarshipSystem('Warp:')
        self.sysTorp = StarshipSystem('Tubes:')
        self.sysImpulse = StarshipSystem('Impulse:')
        self.sysEnergyWep = StarshipSystem(self.shipData.weaponNamePlural + ':')
        self.sysShield = StarshipSystem('Shield:')
        self.sysSensors = StarshipSystem('Sensors:')

        self.name = self.shipData.shipNameGenerator()

        self.docked = False

        self.turnTaken = False

        self.turnRepairing = 0

        try:
            self.torpedoLoaded = TorpedoType.TORP_TYPE_NONE if not self.shipTypeCanFireTorps else self.shipData.torpTypes[0]
        except IndexError:
            self.torpedoLoaded = TorpedoType.TORP_TYPE_NONE

        #print(ai_cls)

        self.ai: Optional[BaseAi] = ai_cls(entity=self)

    @property
    def shields(self):
        return self._shields

    @shields.setter
    def shields(self, value):
        self._shields = round(value)
        if self._shields < 0:
            self._shields = 0
        elif self._shields > self.shipData.maxShields:
            self._shields = self.shipData.maxShields
    
    @property
    def hull(self):
        return self._hull

    @hull.setter
    def hull(self, value):
        self._hull = round(value)
        if self._hull > self.shipData.maxHull:
            self._hull = self.shipData.maxHull

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy = round(value)
        if self._energy < 0:
            self._energy = 0
        elif self._energy > self.shipData.maxEnergy:
            self._energy = self.shipData.maxEnergy

    @property
    def shields_percentage(self):
        try:
            return self._shields / self.shipData.maxShields
        except ZeroDivisionError:
            return 0.0

    @property
    def hull_percentage(self):
        try:
            return self._hull / self.shipData.maxHull
        except ZeroDivisionError:
            return 0.0

    @property
    def get_sub_sector(self) -> SubSector:
        return self.game_data.grid[self.sectorCoords.y][self.sectorCoords.x]

    @property
    def shipTypeCanFireTorps(self):
        return self.shipData.shipTypeCanFireTorps

    @property
    def ship_can_fire_torps(self):
        return self.shipData.shipTypeCanFireTorps and self.sysTorp.isOpperational and sum(self.torps.values()) > 0

    @property
    def crewReadyness(self):
        return (self.ableCrew / self.shipData.maxCrew) + (self.injuredCrew / self.shipData.maxCrew) * 0.25

    @property
    def isDerelict(self):
        """Checks is the ship has no living crew, and returns True if it does not, False if it does.

        Returns:
            bool: [description]
        """
        return self.ableCrew + self.injuredCrew <= 0

    @property
    def getTotalTorps(self):
        
        return 0 if not self.shipTypeCanFireTorps else list(accumulate(self.torps.values()))[-1]

    @property
    def get_max_shields(self):

        return ceil(self.shipData.maxShields * self.sysShield.getEffectiveValue)

    @property
    def get_max_firepower(self):
        return ceil(self.shipData.maxWeapEnergy * self.sysEnergyWep.getEffectiveValue)

    def getNumberOfTorps(self, precision = 1):
        """This generates the number of torpedos that the ship has @ precision - must be an intiger not less then 0 and not more then 100
        Yields tuples containing the torpedo type and the number of torpedos

        Args:
            precision (int, optional): The precision value. 1 is best, higher values are worse. Defaults to 1.

        Raises:
            TypeError: Raised if precision is a float.
            ValueError: Rasied if precision is lower then 1 or higher then 100

        Yields:
            [type]: [description]
        """
        #scanAssistant = lambda v, p: round(v / p) * p
        if  isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be a intiger inbetween 1 and 100")
        if precision not in range(1, 101):
            raise ValueError("The value of the integer MUST be between 1 and 100")

        if self.shipTypeCanFireTorps:
            if precision == 1:
                for t in self.shipData.torpTypes:
                    yield (t, self.torps[t])
            else:
                for t in self.shipData.torpTypes:
                    yield (t, scanAssistant(self.torps[t], precision))
        else:
            yield (TorpedoType.TORP_TYPE_NONE, 0)

    @property
    def combatEffectivness(self):
        if self.shipTypeCanFireTorps:
            return (self.sysTorp.getEffectiveValue + self.sysSensors.getEffectiveValue +
                   self.sysEnergyWep.getEffectiveValue + self.sysShield.getEffectiveValue +
                    self.sysSensors.getEffectiveValue + (self.shields / self.shipData.maxShields) +
                    self.crewReadyness + (self.hull / self.shipData.maxHull)) / 8.0
        return (self.sysSensors.getEffectiveValue +
                self.sysEnergyWep.getEffectiveValue + self.sysShield.getEffectiveValue +
                self.sysSensors.getEffectiveValue + (self.shields / self.shipData.maxShields) +
                self.crewReadyness + (self.hull / self.shipData.maxHull)) / 7.0

    @property
    def determinPrecision(self):
        """
        Takes the effective value of the ships sensor system and returns an intiger value based on it. This
        intiger is passed into the scanAssistant function that is used for calculating the precision when 
        scanning another ship. If the 
        sensors are heavly damaged, their effective 'resoultion' drops. Say their effective value is 0.65.
        This means that this function will return 25. 
        

        Returns:
            int: The effective value that is used for 
        """
        getEffectiveValue = self.sysSensors.getEffectiveValue

        if getEffectiveValue >= 1.0:
            return 1
        if getEffectiveValue >= 0.99:
            return 2
        if getEffectiveValue >= 0.95:
            return 5
        if getEffectiveValue >= 0.9:
            return 10
        if getEffectiveValue >= 0.8:
            return 15
        if getEffectiveValue >= 0.7:
            return 20
        if getEffectiveValue >= 0.6:
            return 25
        if getEffectiveValue >= 0.5:
            return 50
        if getEffectiveValue >= 0.4:
            return 100
        
        return 200 if getEffectiveValue >= 0.3 else 500

    #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
    """
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
    """

    def scan_this_ship(self, precision: int=1)->Dict[str,Union[int,Tuple]]:
        """
        @ precision - this must be an intiger between 1 and 100
        Returns a dictionary containing 
        """

        if isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be an intiger between 1 amd 100")
        if precision not in range(1, 101):
            raise ValueError("The intiger 'precision' MUST be between 1 amd 100")

        d= {
            "shields" : scanAssistant(self.shields, precision),
            "hull" : scanAssistant(self.hull, precision),
            "energy" : scanAssistant(self.energy, precision),
            "able_crew" : scanAssistant(self.ableCrew, precision),
            "injured_crew" : scanAssistant(self.injuredCrew, precision),
            "number_of_torps" : tuple(self.getNumberOfTorps(precision)),
            #"torp_tubes" : s
            "sys_warp" : self.sysWarp.getInfo(precision),# * 0.01,
            "sys_impulse" : self.sysImpulse.getInfo(precision),# * 0.01,
            "sys_energy_weapon" : self.sysEnergyWep.getInfo(precision),# * 0.01,
            "sys_shield" : self.sysShield.getInfo(precision),# * 0.01,
            "sys_sensors" : self.sysSensors.getInfo(precision),# * 0.01,
            "sys_torpedo" : self.sysTorp.getInfo(precision),# * 0.01
        }

        if self.shipData.shipTypeCanFireTorps:

            torps = tuple(self.getNumberOfTorps(precision))
            for k, v in torps:
                d[k] = v

        return d

    """
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
    """

    @property
    def getShipValue(self):
        return (self.hull + self.shipData.maxHull) * 0.5 if self.isAlive else 0.0

    def destroy(self, cause, warp_core_breach=False):
        gd = self.game_data
        #gd.grid[self.sectorCoords.y][self.sectorCoords.x].removeShipFromSec(self)
        is_controllable = self.isControllable
        wc_value = self.sysWarp.getEffectiveValue

        if warp_core_breach:
        
            if is_controllable:
                gd.causeOfDamage = cause
            
                gd.engine.message_log.add_message("Warp core breach iminate!")

                gd.engine.message_log.add_message("Abandon ship, abandon ship, all hands abandon ship...", colors.red)
            else:
                gd.engine.message_log.add_message(f"The {self.name} suffers a warp core breach!")
            self.warpCoreBreach()
        else:
            if is_controllable:
                gd.engine.message_log.add_message("Abandon ship, abandon ship, all hands abandon ship...", colors.red)
            else:
                gd.engine.message_log.add_message(f"The {self.name} is destroyed!")
                
        if self is self.game_data.selected_ship_or_planet:
            self.game_data.selected_ship_or_planet = None

        self.hull = -self.shipData.maxHull

    def warpCoreBreach(self, selfDestruct=False):

        shipList = self.game_data.grapShipsInSameSubSector(self)

        damage = self.shipData.maxHull * ((2 if selfDestruct else 1) / 3)

        for s in shipList:

            distance = self.localCoords.distance(coords=s.localCoords)

            damPercent = 1 - (distance / self.shipData.warpBreachDist)

            if damPercent > 0.0 and s.hull < 0:

                s.takeDamage(round(damPercent * damage), f'Caught in the {"auto destruct radius" if selfDestruct else "warp core breach"} of the {self.name}')

    def calcSelfDestructDamage(self, target:Starship):
        #TODO - write an proper method to look at factors such as current and max hull strength to see if using a self destruct is worthwhile
        
        scan = target.scan_this_ship(self.determinPrecision)
        
        shields:int = scan["shields"]
        
        shields_percentage = shields / target.shipData.maxShields
        
        shieldPercent = shields_percentage * 0.5 + 0.5
        
        damage = self.shipData.maxHull * (2 / 3)
        
        distance = self.localCoords.distance(coords=target.localCoords)
        
        damPercent = 1 - (distance / self.shipData.warpBreachDist)
        
        amount = round(damPercent * damage)
        
        shields_are_already_down = not target.sysShield.isOpperational or shields <= 0
        
        if not shields_are_already_down:
            shieldsDam = round(shieldPercent * amount)# * shieldDamMulti

            amount -= shieldsDam

            #shieldsDam *= shieldDamMulti

            if shieldsDam > shields:
                
                shieldsDam = shields
            
            hullDam = amount
        else:
            shieldsDam = 0
        
            hullDam = amount
        
        return target, shieldsDam, hullDam, shieldsDam >= target.shipData.maxHull

    @property
    def isAlive(self):
        return self.hull > 0
    

    @property
    def is_capiable(self):
        return self.hull > 0 and self.ableCrew + self.injuredCrew > 0

    def ram(self, otherShip:Starship):
        """Prepare for RAMMING speed!

        The ship will attempt to ram another

        Args:
            otherShip (Starship): [description]
        """
        selfHP = self.shields + self.hull
        otherHP = otherShip.shields + otherShip.hull

        if self.sysImpulse.getEffectiveValue <= otherShip.sysImpulse.getEffectiveValue:
            return False

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

        gd = self.game_data

        systemOpperational = self.sysWarp.isOpperational if usingWarp else self.sysImpulse.isOpperational
        energyCost = SECTOR_ENERGY_COST if usingWarp else LOCAL_ENERGY_COST

        #fromText = checker(' warps from subsector ', ' moves from position ')
        #toText = checker(' to subsector ', ' to position ')
        selfCoords = self.sectorCoords if usingWarp else self.localCoords
        effictiveValue = self.sysWarp.getEffectiveValue if usingWarp else self.sysImpulse.getEffectiveValue

        canMoveAtAll = False
        canReachDestination = False
        eCost = 0
        print('Destination location X: {0}, Y: {1}'.format(x, y))
        if systemOpperational and self.energy >= energyCost:
            canMoveAtAll = True
            co:Coords = Coords(x, y)#assume x is 5 and y is 2

            co = co.clamp_new(gd.subsecSizeX, gd.subsecSizeY) if usingWarp else co.clamp_new(gd.subsecsX, gd.subsecsY)
            
            print('Clamped location : {0}'.format(co))
            #current location is x = 1 and y = 7
            # 1 - 5, 7 - 2 = -4, 5
            #pow(-4, 2), pow(5, 2) = 16, 25
            #pow(16+25, 0.5) = pow(41) = 6.4031242374328485
            #dist = 6.4031242374328485
            dist = energyCost * selfCoords.distance(co)

            #
            x, y = selfCoords.x - co.x, selfCoords.y - co.y

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
        print(f'Final destination location X: {x}, Y: {y}')
        return (canMoveAtAll, canReachDestination, x, y, eCost)

    def handleMovment(self, gd, x, y, usingWarp):
        gd = self.game_data
        #systemOpperational = checker(self.sysWarp.isOpperational, self.sysImpulse.isOpperational)
        #energyCost = checker(SECTOR_ENERGY_COST, LOCAL_ENERGY_COST)
        fromText = ' warps from subsector ' if usingWarp else ' moves from position '
        toText = ' to subsector ' if usingWarp else ' to position '
        selfCoords = self.sectorCoords if usingWarp else self.localCoords
        #effictiveValue = checker(self.sysWarp.getEffectiveValue, self.sysImpulse.getEffectiveValue)

        canMoveAtAll, canReachDestination, x_, y_, eCost = self.checkIfCanReachLocation(gd, x, y, usingWarp)

        if not canMoveAtAll:
            return False
        
        gd.eventTextToPrint+=[self.name, fromText, str(selfCoords)]

        if usingWarp and not self.isControllable:
            #gd.grid[self.sectorCoords.y][self.sectorCoords.x].removeShipFromSec(self)
            if self.shipData.shipType == ShipTypes.TYPE_ENEMY_SMALL:
                self.get_sub_sector.smallShips-= 1
            elif self.shipData.shipType == ShipTypes.TYPE_ENEMY_LARGE:
                self.get_sub_sector.bigShips-= 1

        selfCoords.x-= x_
        selfCoords.y-= y_

        if usingWarp:
            shipList = gd.grapShipsInSameSubSector(self)
            sp = self.get_sub_sector.findRandomSafeSpot(shipList)

            self.localCoords.x = sp.x
            self.localCoords.y = sp.y

            if not self.isControllable:
                if self.shipData.shipType == ShipTypes.TYPE_ENEMY_SMALL:
                    self.get_sub_sector.smallShips+= 1
                elif self.shipData.shipType == ShipTypes.TYPE_ENEMY_LARGE:
                    self.get_sub_sector.bigShips+= 1

            #gd.grid[self.sectorCoords.y][self.sectorCoords.x].addShipToSec(self)

        gd.eventTextToPrint+=[toText, str(selfCoords), '.']
        self.energy-=eCost

        self.turnRepairing = 0
        return True

    #TODO - add in a checker to see if the player has plowed into a planet or star, or rammed another starship
    def move(self, gd, x, y):#assume that x = 2, y = 3
        self.handleMovment(gd, x, y, False)

    def warp(self, gd, x, y):
        self.handleMovment(gd, x, y, True)



    def takeDamage(self, amount, text, *, isTorp=False, is_beam=False):
        is_controllable = self.isControllable
        gd = self.game_data
        safeDiv = lambda n, d: 0 if d == 0 else n / d

        pre = 1 if is_controllable else self.determinPrecision

        old_scan = self.scan_this_ship(pre)

        old_shields = self.shields_percentage
        old_hull = self.hull_percentage

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
            raise AssertionError(f'The ship {self.name} has taken damage when it is clearly destroyed!')
        else:
            shields_are_already_down = not self.sysShield.isOpperational or self.shields <= 0

            shieldsDam = 0.0
            armorDam = 1.0 * amount
            hullDam = 1.0 * amount

            shieldDamMulti = 0.75 if isTorp else 1.0

            armorHullDamMulti = (1.75 if shields_are_already_down else 1.05) if isTorp else 1.0

            #armorPercent = safeDiv(self.armor, self.shipData.maxArmor)

            shieldPercent = self.shields_percentage * 0.5 + 0.5

            if shields_are_already_down:
                shieldsDam = 0
            else:
                shieldsDam = shieldPercent * amount# * shieldDamMulti

                amount -= shieldsDam

                shieldsDam *= shieldDamMulti

                if shieldsDam > self.shields:
                    
                    shieldsDam = self.shields

            #hitKnockedDownShields = shieldsDam > self.shields
            """
            if shieldsDam > self.shields:
                shieldsDam = self.shields
            else:
                shieldsDam = shieldPercent * amount

            amount -= shieldsDam * shieldDamMulti
            """

            amount*= armorHullDamMulti

            #armorDam = amount * armorPercent

            #amount-= armorDam

            hullDam = amount

            system_damage_chance = 0.25 if is_beam else 0.12

            def randomSystemDamage():
                return uniform(0.0, system_damage_chance * (hullDam / self.shipData.maxHull))

            self.hull-= hullDam
            #self.armor-= armorDam
            self.shields-= shieldsDam

            scan = self.scan_this_ship(pre)

            scaned_shields = scan['shields'] / self.shipData.maxShields

            shield_status = "holding" if scaned_shields > 0.9 else (f"at {scaned_shields:.0%}" if self.shields > 0 else "down")

            name = "Our" if is_controllable else f"The {self.name}'s"

            if old_scan["hull"] < scan["hull"]:
                gd.engine.message_log.add_message(
                    f"{name} shields are {shield_status} and structural integrity is at {scan['hull'] / self.shipData.maxHull:.0%}." 
                )
            else:
                gd.engine.message_log.add_message(f"{name} shields are {shield_status}." )
            
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

                if is_controllable:
                    if killedOutright > 0:
                        gd.engine.message_log.add_message(f'{killedOutright} active duty crewmembers were killed.')
                    if killedInSickbay > 0:
                        gd.engine.message_log.add_message(f'{killedInSickbay} crewmembers in sickbay were killed.')
                    if wounded > 0:
                        gd.engine.message_log.add_message(f'{wounded} crewmembers were injured.')

            if self.hull <= 0:
                wc_breach = random() > 0.85 and random() > self.sysWarp.getEffectiveValue and random() > self.sysWarp.integrety
                self.destroy(text)
            else:
                #if self.isControllable:
                #    setattr(self, 'turnRepairing', True)

                if random() < hullDam / self.shipData.maxHull:#damage subsystem at random
                    if randint(0, 3) == 0:
                        if is_controllable:
                            gd.engine.message_log.add_message('Impulse engines damaged. ')
                        self.sysImpulse.integrety -= (randomSystemDamage())
                    if randint(0, 3) == 0:
                        if is_controllable:
                            gd.engine.message_log.add_message('Warp drive damaged. ')
                        self.sysWarp.integrety -= (randomSystemDamage())
                    if randint(0, 3) == 0:
                        if is_controllable:
                            gd.engine.message_log.add_message(f'{self.shipData.weaponName} emitters damaged. ')
                        self.sysEnergyWep.integrety -= (randomSystemDamage())
                    if randint(0, 3) == 0:
                        if is_controllable:
                            gd.engine.message_log.add_message('Sensors damaged. ')
                        self.sysSensors.integrety -= (randomSystemDamage())
                    if randint(0, 3) == 0:
                        if is_controllable:
                            gd.engine.message_log.add_message('Shield generator damaged. ')
                        self.sysShield.integrety -= (randomSystemDamage())
                    if self.shipData.shipTypeCanFireTorps and randint(0, 3) == 0:
                        if is_controllable:
                            gd.engine.message_log.add_message('Torpedo launcher damaged. ')
                        self.sysTorp.integrety -= (randomSystemDamage())

    def repair(self, factor):
        #self.crewReadyness
        timeBonus = 1.0 + (self.turnRepairing / 25.0)

        repairFactor = self.shipData.damageCon * factor * self.crewReadyness * timeBonus

        self.energy = min(self.shipData.maxEnergy, self.energy + factor * 100)

        healCrew = min(self.injuredCrew, round(self.injuredCrew * 0.2) + randint(2, 5))
        self.ableCrew+= healCrew
        self.injuredCrew-= healCrew
        
        repair_amount = repairFactor * (0.5 + random() * 0.5) * self.shipData.maxHull * 0.05

        self.hull += repair_amount
        self.sysWarp.integrety += repairFactor * (0.5 + random() * 0.5)
        self.sysSensors.integrety += repairFactor * (0.5 + random() * 0.5)
        self.sysImpulse.integrety += repairFactor * (0.5 + random() * 0.5)
        self.sysEnergyWep.integrety += repairFactor * (0.5 + random() * 0.5)
        self.sysShield.integrety += repairFactor * (0.5 + random() * 0.5)
        if self.shipTypeCanFireTorps:
            self.sysTorp.integrety += repairFactor * (0.5 + random() * 0.5)

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

    """
    def rollToHitBeam(self, enemy:Starship, estimatedEnemyImpulse=-1):
        return self.roll_to_hit_energy(enemy=enemy, estimatedEnemyImpulse=estimatedEnemyImpulse, cannon=False)

    def rollToHitCannon(self, enemy:Starship, estimatedEnemyImpulse=-1):
        return self.roll_to_hit_energy(enemy=enemy, estimatedEnemyImpulse=estimatedEnemyImpulse, cannon=False)
    """

    def roll_to_hit_energy(self, enemy:Starship, estimatedEnemyImpulse:float=-1.0, cannon:bool=False):
        if estimatedEnemyImpulse == -1.0:
            estimatedEnemyImpulse = enemy.sysImpulse.getEffectiveValue
        """
        assume that the distance is 5, the sensors are at 70% and enemy impulse is at 80%
        so (1 / 5) * (0.7 * 1.25 / 0.8)
        0.2 * (0.875 / 0.8)
        0.2 * 1.09375
        2.1875"""
        divisor = 300 if cannon else 100

        distance = self.localCoords.distance(coords=enemy.localCoords)

        distance_roll = 200 / (distance * divisor)

        sensor_roll = self.sysSensors.getEffectiveValue * 1.25 / estimatedEnemyImpulse

        roll =  distance_roll * sensor_roll

        return roll > random()


    def attackEnergyWeapon(self, enemy:Starship, amount:float, energy_cost:float, cannon:bool=False):
        gd = self.game_data
        if self.sysEnergyWep.isOpperational:
            
            attacker_is_player = self is self.game_data.player
            target_is_player = enemy is self.game_data.player

            self.energy-=energy_cost

            if cannon:
                amount*=1.25

            gd.engine.message_log.add_message(
                f"Firing on the {enemy.name}!" if attacker_is_player else f"The {self.name} has fired on {'us' if target_is_player else f'the {enemy.name}'}!"
            )

            hit = self.roll_to_hit_energy(enemy=enemy, estimatedEnemyImpulse=-1.0, cannon=cannon)

            if hit:

                is_beam = not cannon
                
                target_name = "We're" if target_is_player else f'The {enemy.name} is'

                gd.engine.message_log.add_message(
                    f"Direct hit on {enemy.name}!" if attacker_is_player else
                    f"{target_name} hit!", fg=colors.orange
                )

                enemy.takeDamage(amount * self.sysEnergyWep.getEffectiveValue, f'Destroyed by a {self.shipData.weaponName} hit from the {self.name}.', is_beam=is_beam)
                return True
            else:
                gd.engine.message_log.add_message(
                    "We missed!" if attacker_is_player else "A miss!"
                    )
                #f"{self.name} misses {enemy.name}!"

        return False

    def getNoOfAvalibleTorpTubes(self, number=0):
        if not self.sysTorp.isOpperational:
            return 0

        if number == 0:
            number = self.shipData.torpTubes
        else:
            number = min(number, self.shipData.torpTubes)

        return max(1, round(number * self.sysTorp.getEffectiveValue))

    def rollToHitTorpedo(self, enemy:Starship, estimatedEnemyImpulse:float=-1.0):
        if estimatedEnemyImpulse == -1.0:
            estimatedEnemyImpulse = enemy.sysImpulse.getEffectiveValue

        return self.sysTorp.getEffectiveValue + (self.sysSensors.getEffectiveValue * 1.25) >             estimatedEnemyImpulse - uniform(0.0, 0.75)

    def attackTorpedo(self, gd:GameData, enemy:Starship, torp:Torpedo):
        gd = self.game_data
        if self.rollToHitTorpedo(enemy):
            #chance to hit:
            #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
            gd.engine.message_log.add_message(f'{enemy.name} was hit by a {torp.name} torpedo from {self.name}. ')

            enemy.takeDamage(torp.damage, f'Destroyed by a {torp.name} torpedo hit from the {self.name}', isTorp=True)

            return True
        gd.engine.message_log.add_message(f'A {torp.name} torpedo from {self.name} missed {enemy.name}. ')
        return False

    @property
    def isControllable(self):
        return self is self.game_data.player

    """
    @property
    def hasValidTarget(self):
        return self.order and self.order.target and self.order.target.sectorCoords == self.sectorCoords
    """
    
    @property
    def getMostPowerfulTorpAvaliable(self):
        rt = self.shipData.get_most_powerful_torpedo_type

        if rt is TorpedoType.TORP_TYPE_NONE:
            return rt
        
        if self.getTotalTorps > 0:
            if self.torps[rt] > 0:
                return rt

            avaliable_torps = [t for t, tyt in self.torps.items() if tyt]
            
            most_powerful = find_most_powerful_torpedo(avaliable_torps)

            return most_powerful

        return TorpedoType.TORP_TYPE_NONE

    def repair__(self, factor, externalRepair=False):
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

        self.sysWarp.integrety+=repairFactor
        self.sysTorp.integrety+=repairFactor
        self.sysImpulse.integrety+=repairFactor
        self.sysEnergyWep.integrety+=repairFactor
        self.sysShield.integrety+=repairFactor
        self.turnRepairing+=1

    def resetRepair(self):
        self.turnRepairing = 0

    def restockTorps(self, infrastructure):
        if self.shipData.maxTorps != self.getTotalTorps:
            torpSpace = self.shipData.maxTorps - self.getTotalTorps
            for t in self.shipData.torpTypes:
                if torpedo_types[t].infrastructure <= infrastructure:
                    self.torps[t]+= torpSpace
                    break

    def resetRepair(self):
        if self.damageTakenThisTurn:
            self.turnRepairing = 0
            self.damageTakenThisTurn = False

    def simulateTorpedoHit(self, target:Starship):
        targScan = target.scan_this_ship(self.determinPrecision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan["shields"]
        targHull = targScan["hull"]

        torp = self.getMostPowerfulTorpAvaliable
        if torp == None:
            return 0
        torpedos = self.torps[torp]

        timesToFire = min(self.getNoOfAvalibleTorpTubes(), torpedos)

        for t in range(timesToFire):
            if self.rollToHitTorpedo(target, targScan["sys_impulse"]):

                #chance to hit:
                #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
                amount = torpedo_types[torp].damage

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

        return (targScan["hull"] - targHull) + (targScan["shields"] - targShield)#return the simulated amount of damage

    def simulatePhaserHit(self, target:Starship, timesToFire:int, cannon:bool=False):

        targScan = target.scan_this_ship(self.determinPrecision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan["shields"]
        targHull = targScan["hull"]

        totalShDam = 0
        totalHuDam = 0

        amount = min(self.energy, self.shipData.maxWeapEnergy)

        for i in range(timesToFire):
            if self.roll_to_hit_energy(target, targScan["sys_impulse"], cannon):

                #if targShield > 0:

                shieldsDam = (min(targShield * 2 / target.shipData.maxShields, 1)) * amount
                hullDam = (1 - min(targShield * 2 / target.shipData.maxShields, 1)) * amount

                if shieldsDam > targShield:

                    hullDam+= shieldsDam - targShield
                    shieldsDam = targShield

                totalShDam+= shieldsDam
                totalHuDam+= hullDam

        return (totalHuDam + totalShDam) / timesToFire

    def checkTorpedoLOS(self, target:Starship):

        gd = self.game_data

        dirX, dirY = Coords(target.localCoords.x - self.localCoords.x, target.localCoords.y - self.localCoords.y).normalize()

        g:SubSector = gd.grid[self.sectorCoords.y][self.sectorCoords.x]

        #posX, posY = self.localCoords.x, self.localCoords.y

        #torp_positions = gd.engine.get_lookup_table(direction_x=dirX, direction_y=dirY, normalise_direction=False)
        torp_positions = [co for co in gd.engine.get_lookup_table(direction_x=dirX, direction_y=dirY, normalise_direction=False)]
        #ships_in_same_subsector = gd.grapShipsInSameSubSector(self)

        ship_positions = {
            ship.localCoords.create_coords() : ship for ship in gd.grapShipsInSameSubSector(self)
        }

        for pos in torp_positions:
            ajusted_pos = Coords(x=pos.x+self.localCoords.x, y=pos.y+self.localCoords.y)

            if ajusted_pos.x not in gd.subsecSizeRangeX or ajusted_pos.y not in gd.subsecSizeRangeY:
                return False

            if ajusted_pos in g.stars_dict or pos in g.planets_dict:
                return False

            try:
                hit_ship = ship_positions[ajusted_pos]
                return not (hit_ship.isControllable == self.isControllable)

            except KeyError:
                pass

        return False
