from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, Union
from random import choice, randrange, uniform, random, randint
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
from data_globals import DAMAGE_VARATION_BEAM, DAMAGE_VARATION_CANNOM, DAMAGE_VARATION_EXPLOSION, DAMAGE_VARATION_TORPEDO, SYM_PLAYER, SYM_FIGHTER, SYM_AD_FIGHTER, SYM_CRUISER, SYM_BATTLESHIP, \
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
    r = round(v / precision) * precision
    assert isinstance(r, float) or isinstance(r, int)
    return r

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
    def integrety(self, value:float):
        assert isinstance(value, float) or isinstance(value, int)
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
    def is_comprimised(self):
        return self._integrety * 1.25 < 1.0

    @property
    def affect_cost_multiplier(self):
        return 1 / self.getEffectiveValue if self.isOpperational else inf

    #def __add__(self, value):

    def getInfo(self, precision:float):
        if precision <= 1.0:
            return self._integrety
        r = (round(self._integrety * 100 / precision) * precision * 0.01) if self.isOpperational else 0.0
        assert isinstance(r, float)
        return r

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
    maxHull=1000, 
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
    maxHull=200, 
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
    maxHull=800, 
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
    maxShields=900,
    maxHull=460, 
    maxCrew=15, 
    maxEnergy=2500, 
    damageCon=0.15,
    maxWeapEnergy=600, 
    warpBreachDist=2, 
    weaponName='Poleron', 
    nameGenerator=genNameAttackFighter)

ADVANCED_FIGHTER = ShipData(
    shipType=ShipTypes.TYPE_ENEMY_SMALL, 
    symbol=SYM_AD_FIGHTER, 
    maxShields=1000,
    maxHull=500, 
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
    maxHull=1200, 
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
    maxHull=1500, 
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

    def scan_this_ship(self, precision: int=1, *, scan_for_crew:bool=True, scan_for_systems:bool=True)->Dict[str,Union[int,Tuple]]:
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
            
            "number_of_torps" : tuple(self.getNumberOfTorps(precision)),
            #"torp_tubes" : s
            
        }
        
        if scan_for_crew:
            d["able_crew"] = scanAssistant(self.ableCrew, precision)
            d["injured_crew"] = scanAssistant(self.injuredCrew, precision)

        if scan_for_systems:
            d["sys_warp"] = self.sysWarp.getInfo(precision)# * 0.01,
            d["sys_impulse"] = self.sysImpulse.getInfo(precision)# * 0.01,
            d["sys_energy_weapon"] = self.sysEnergyWep.getInfo(precision)# * 0.01,
            d["sys_shield"] = self.sysShield.getInfo(precision)# * 0.01,
            d["sys_sensors"] = self.sysSensors.getInfo(precision)# * 0.01,
            d["sys_torpedo"] = self.sysTorp.getInfo(precision)# * 0.01

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

        if is_controllable:
            gd.engine.message_log.print_messages = False

        if warp_core_breach:
        
            self.warpCoreBreach()
                
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

                s.takeDamage(round(damPercent * damage), f'Caught in the {"auto destruct radius" if selfDestruct else "warp core breach"} of the {self.name}', random_varation=DAMAGE_VARATION_EXPLOSION)

    def calcSelfDestructDamage(self, target:Starship, *, scan:Optional[Dict]=None, number_of_simulations:int=1):
        #TODO - write an proper method to look at factors such as current and max hull strength to see if using a self destruct is worthwhile
        
        precision = self.determinPrecision
        
        scan = scan if scan else target.scan_this_ship(precision)
        
        old_shield = scan["shields"]
        
        distance = self.localCoords.distance(coords=target.localCoords)
        
        damPercent = 1 - (distance / self.shipData.warpBreachDist)
        
        damage = self.shipData.maxHull * (2 / 3)
        
        amount = round(damPercent * damage)
        
        averaged_shield = 0
        averaged_hull = 0
        averaged_shield_damage = 0
        averaged_hull_damage = 0
        
        for i in range(number_of_simulations):
        
            new_shields, new_hull, shieldsDam, hullDam, new_shields_as_a_percent, new_hull_as_a_percent, killedOutright, killedInSickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, torpedo_sys_damage = self.calculate_damage(amount, scan_dict=scan, precision=precision, calculate_crew=False, calculate_systems=False, random_varation=DAMAGE_VARATION_EXPLOSION)
            
            averaged_shield += new_shields
            averaged_hull += new_hull
            averaged_shield_damage += shieldsDam
            averaged_hull_damage += hullDam
                
        averaged_shield /= number_of_simulations
        averaged_hull /= number_of_simulations
        averaged_shield_damage /= number_of_simulations
        averaged_hull_damage /= number_of_simulations
                
        return averaged_shield , averaged_hull, averaged_shield_damage, averaged_hull_damage, averaged_hull <= 0

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
            self.takeDamage(otherHP, 'Rammed the {0}'.format(self.name), random_varation=DAMAGE_VARATION_EXPLOSION)
            otherShip.destroy('Rammed by the {0}'.format(self.name))
        elif selfHP < otherHP:
            otherShip.takeDamage(selfHP, 'Rammed by the {0}'.format(self.name), random_varation=DAMAGE_VARATION_EXPLOSION)
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
            dist = energyCost * selfCoords.distance(coords=co)

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

    def calculate_damage(self, amount:int, *, scan_dict:Optional[Dict]=None, precision:int=1, isTorp:bool=False, is_beam:bool=False, calculate_crew:bool=True, calculate_systems:bool=True, random_varation:float=0.0):
        
        #assume damage is 64, current shields are 80, max shields are 200
        #armor is 75, max armor is 100
        #80 * 2 / 200 = 160 / 200 = 0.8
        #0.8 * 64 = 51.2 = the amount of damage that hits the shields
        #64 - 51.2 = 12.8 = the amount of damage that hits the armor and hull
        #1 - (75 / 100) = 1 - 0.25 = 0.75
        #12.8 * 0.75 = 9.6 = the amount of damage that hits the armor
        #12.8 - 9.6 = 3.2 = the amount of damage that hits the hull
        
        if random_varation > 0.0:
            amount = round(amount * uniform(0.0, 1.0 - random_varation))
        
        old_scan = scan_dict if scan_dict else self.scan_this_ship(precision)
        
        current_shields:int = old_scan["shields"]
        current_hull:int = old_scan["hull"]
        
        shield_effectiveness = 0 if old_scan["sys_shield"] < 0.15 else min(old_scan["sys_shield"] * 1.25, 1.0)
        
        shields_are_already_down = shield_effectiveness <= 0 or current_shields <= 0
        
        shieldsDam = 0
        armorDam = 1.0 * amount
        hullDam = 1.0 * amount
        
        shieldDamMulti = 0.75 if isTorp else 1.0

        armorHullDamMulti = (1.75 if shields_are_already_down else 1.05) if isTorp else 1.0
        
        shields_percentage = current_shields / self.shipData.maxShields
        
        #shieldPercent = self.shields_percentage * 0.5 + 0.5
        
        bleedthru_factor = min(shields_percentage + 0.5, 1.0)
        
        if shields_are_already_down:
            
            hullDam = amount * armorHullDamMulti
        else:
            
            shieldsDam = amount * bleedthru_factor * shieldDamMulti
            if shieldsDam > current_shields:
                shieldsDam = current_shields
            hullDam = amount * (1 - bleedthru_factor) * armorHullDamMulti
        
        new_shields = scanAssistant(current_shields - shieldsDam, precision) if shieldsDam > 0 else current_shields
        new_hull = scanAssistant(current_hull - hullDam, precision) if hullDam > 0 else current_hull
        
        hull_damage_as_a_percent = hullDam / self.shipData.maxHull
        new_shields_as_a_percent = new_shields / self.shipData.maxShields
        new_hull_as_a_percent = new_hull / self.shipData.maxHull
        
        killedOutright = 0
        killedInSickbay = 0
        wounded = 0
        
        if calculate_crew:
            
            crew_killed = hullDam > 0 and new_hull_as_a_percent < random()
            
            if crew_killed:
                able_crew = old_scan["able_crew"]
                injured_crew = old_scan["injured_crew"]
                
                percentage_of_crew_killed = hull_damage_as_a_percent * random()
                
                total_crew = able_crew + injured_crew
                
                wounded_fac = uniform(0.25, 0.75)
                
                _able_crew_percentage = able_crew / total_crew
                
                percentage_of_able_crew_killed = _able_crew_percentage * (percentage_of_crew_killed * (1 - wounded_fac))
                percentage_of_able_crew_wounded = _able_crew_percentage * (percentage_of_crew_killed * (wounded_fac))
                percentage_of_injured_crew_killed = (injured_crew / total_crew) * percentage_of_crew_killed
                
                killedOutright = round(self.ableCrew * percentage_of_able_crew_killed)
                killedInSickbay = round(0.5 * self.ableCrew * percentage_of_injured_crew_killed)
                wounded = round(self.ableCrew * percentage_of_able_crew_wounded)
        
        shield_sys_damage = 0
        energy_weapons_sys_damage = 0
        impulse_sys_damage = 0
        warp_drive_sys_damage = 0
        sensors_sys_damage = 0
        torpedo_sys_damage = 0
        
        if calculate_systems:
            systems_damaged = hullDam > 0 and new_hull_as_a_percent < uniform(0.0, 2.75 if is_beam else 1.75)
            
            if systems_damaged:
                system_damage_chance = 0.275 if is_beam else 0.125
                
                def chance_of_system_damage():
                    return uniform(0.0, 1.25) > new_hull_as_a_percent
                
                def randomSystemDamage():
                    return uniform(0.0, system_damage_chance * hull_damage_as_a_percent)
                
                if chance_of_system_damage():
                    shield_sys_damage = randomSystemDamage()
                if chance_of_system_damage():
                    energy_weapons_sys_damage = randomSystemDamage()
                if chance_of_system_damage():
                    impulse_sys_damage = randomSystemDamage()
                if chance_of_system_damage():
                    warp_drive_sys_damage = randomSystemDamage()
                if chance_of_system_damage():
                    sensors_sys_damage = randomSystemDamage()
                if self.shipTypeCanFireTorps and chance_of_system_damage():
                    torpedo_sys_damage = randomSystemDamage()
            
        return new_shields, new_hull, shieldsDam, hullDam, new_shields_as_a_percent, new_hull_as_a_percent, killedOutright, killedInSickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, torpedo_sys_damage

    def takeDamage(self, amount, text, *, isTorp=False, is_beam=False, random_varation:float=0.0):
        #is_controllable = self.isControllable
        gd = self.game_data
        message_log = gd.engine.message_log
        
        new_shields, new_hull, shieldsDam, hullDam, new_shields_as_a_percent, new_hull_as_a_percent, killedOutright, killedInSickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, torpedo_sys_damage = self.calculate_damage(amount, isTorp=isTorp, is_beam=is_beam, random_varation=random_varation)
        
        ship_destroyed = new_hull < 0
        
        ship_is_player = self is self.game_data.player

        pre = 1 if ship_is_player else self.determinPrecision
        
        old_scan = self.scan_this_ship(pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player)
        
        self.shields = new_shields
        self.hull = new_hull
        
        self.ableCrew -= wounded
        self.injuredCrew += wounded
        self.ableCrew -= killedOutright
        self.injuredCrew -= killedInSickbay
        
        self.sysShield.integrety -= shield_sys_damage
        self.sysEnergyWep.integrety -= energy_weapons_sys_damage
        self.sysImpulse.integrety -= impulse_sys_damage
        self.sysSensors.integrety -= sensors_sys_damage
        self.sysWarp.integrety -= warp_drive_sys_damage
        self.sysTorp.integrety -= torpedo_sys_damage
        
        new_scan = self.scan_this_ship(pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player)
        
        #name = "our" if ship_is_player else f"the {self.name}'s"
        
        #name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
        #name_second_occ = "our" if ship_is_player else f"the {self.name}'s"
        
        if not ship_destroyed:
            
            old_shields = old_scan["shields"]
            
            newer_shields = new_scan['shields'] 
            
            old_hull = old_scan["hull"]
            
            newer_hull = new_scan["hull"]
            
            scaned_shields_percentage = newer_shields / self.shipData.maxShields
            
            shield_status = "holding" if scaned_shields_percentage > 0.9 else (f"at {scaned_shields_percentage:.0%}" if self.shields > 0 else "down")
            
            shields_are_down = newer_shields == 0
            
            #shields_just_got_knocked_down = old_shields > 0 and shields_are_down
            
            shields_are_already_down = old_shields == 0 and shields_are_down
            
            old_hull_percent = old_hull / self.shipData.maxHull
            newer_hull_hull_percent = newer_hull / self.shipData.maxHull
            
            if old_hull_percent < newer_hull_hull_percent:
                
                #this is where things get a bit complecated. Rather then use a serise of nested if-elif-else statements to decide what the message to preing regarding the hull status is, I'm going to compress this into a grid. The variable 'old_hull_status' acts as the 'y' value, and the variable 'newer_hull_status' acts as the 'x' value
                
                if old_hull_percent <= 0.1:
                    old_hull_status = 3
                elif old_hull_percent <= 0.25:
                    old_hull_status = 2
                elif old_hull_percent <= 0.5:
                    old_hull_status = 1
                else:
                    old_hull_status = 0
                
                if newer_hull_hull_percent <= 0.1:
                    newer_hull_status = 3
                elif newer_hull_hull_percent <= 0.25:
                    newer_hull_status = 2
                elif newer_hull_hull_percent <= 0.5:
                    newer_hull_status = 1
                else:
                    newer_hull_status = 0 
                
                grid = (
                    (0,1,2,3),
                    (0,0,2,3),
                    (0,0,0,3),
                    (0,0,0,0)
                )
                
                hull_breach_message_code = grid[old_hull_status][newer_hull_status]
                
                hull_breach_messages = (
                    f"structural integrity is at {newer_hull_hull_percent:.0%}.",
                    f"a hull breach.",
                    f"hull breaches on multiple decks!"
                    f"hull is buckling!"
                )
                
                hull_breach_message = hull_breach_messages[hull_breach_message_code]
                
                message_to_print = []
                
                if not shields_are_already_down:
                    
                    name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
                    
                    message_to_print.append(
                        
                        f"{name_first_occ} shields are {shield_status}, and"
                    )
                    
                    if hull_breach_message_code in {1,2}:
                        
                        message_to_print.append(
                            'we have' if ship_is_player else 'they have'
                        )
                    else:
                        message_to_print.append(
                            'our' if ship_is_player else 'their'
                        )
                    
                    message_to_print.append(
                        hull_breach_message
                    )
                else:
                    
                    if hull_breach_message_code in {1,2}:
                        
                        message_to_print.append(
                            'We have' if ship_is_player else f'The {self.name} has'
                        )
                    else:
                        message_to_print.append(
                            'Our' if ship_is_player else f"The {self.name}'s"
                        )
                    
                    message_to_print.append(
                        hull_breach_message
                    )
                
                fg = colors.white if not ship_is_player else (
                    colors.red if new_hull_as_a_percent < 0.1 else (
                        colors.orange if new_hull_as_a_percent < 0.25 else (
                            colors.yellow if new_hull_as_a_percent < 0.5 else colors.white
                        )
                    )
                )
                
                
                message_log.add_message(
                    " ".join(message_to_print),fg
                    
                    )
                
            else:
                name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
                message_log.add_message(f"{name_first_occ} shields are {shield_status}." )
            
            if ship_is_player:
                
                if killedOutright > 0:
                    message_log.add_message(f'{killedOutright} active duty crewmembers were killed.')
                    
                if killedInSickbay > 0:
                    message_log.add_message(f'{killedInSickbay} crewmembers in sickbay were killed.')
                    
                if wounded > 0:
                    message_log.add_message(f'{wounded} crewmembers were injured.')
                
                if impulse_sys_damage > 0:
                    message_log.add_message('Impulse engines damaged. ')
                    
                if warp_drive_sys_damage > 0:
                    message_log.add_message('Warp drive damaged. ')
                    
                if energy_weapons_sys_damage > 0:
                    message_log.add_message(f'{self.shipData.weaponName} emitters damaged. ')
                    
                if sensors_sys_damage > 0:
                    message_log.add_message('Sensors damaged. ')
                            
                if shield_sys_damage > 0:
                    message_log.add_message('Shield generator damaged. ')
                            
                if torpedo_sys_damage > 0:
                    message_log.add_message('Torpedo launcher damaged. ')
                
        else:
            wc_breach = random() > 0.85 and random() > self.sysWarp.getEffectiveValue and random() > self.sysWarp.integrety
            
            if ship_is_player:
                
                if wc_breach:
                    message_log.add_message("Warp core breach iminate!", colors.orange)
                
                message_log.add_message("Abandon ship, abandon ship, all hands abandon ship...", colors.red)
                
                
            else:
                message_log.add_message(f"The {self.name} {'suffers a warp core breach' if wc_breach else 'is destroyed'}!")
                
            self.destroy(text, warp_core_breach=wc_breach)
        
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
            target_is_player = not attacker_is_player and enemy is self.game_data.player

            self.energy-=energy_cost

            if cannon:
                amount*=1.25
                
            varation = DAMAGE_VARATION_CANNOM if cannon else DAMAGE_VARATION_BEAM

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

                enemy.takeDamage(amount * self.sysEnergyWep.getEffectiveValue, f'Destroyed by a {self.shipData.weaponName} hit from the {self.name}.', is_beam=is_beam, random_varation=varation)
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

            enemy.takeDamage(torp.damage, f'Destroyed by a {torp.name} torpedo hit from the {self.name}', isTorp=True, random_varation=DAMAGE_VARATION_TORPEDO)

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

    def simulateTorpedoHit(self, target:Starship, number_of_simulations:int, *, simulate_systems:bool=False):
        precision = self.determinPrecision
        targScan = target.scan_this_ship(precision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan["shields"]
        targHull = targScan["hull"]
        torp = self.getMostPowerfulTorpAvaliable
        if torp == None:
            return targShield, targHull
        torpedos = self.torps[torp]
        
        damage = torpedo_types[torp].damage

        timesToFire = min(self.getNoOfAvalibleTorpTubes(), torpedos)

        shield_damage = 0
        hull_damage = 0
        
        averaged_hull = 0
        averaged_shields = 0

        for s in range(number_of_simulations):
            
            for attack in range(timesToFire):
                hull_dam  = 0
                shield_dam = 0
                if self.rollToHitTorpedo(target, targScan["sys_impulse"]):
                    
                    new_shields, new_hull, shieldsDam, hullDam, new_shields_as_a_percent, new_hull_as_a_percent, killedOutright, killedInSickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, torpedo_sys_damage =self.calculate_damage(damage, precision=precision, calculate_crew=False, calculate_systems=simulate_systems, scan_dict=targScan, random_varation=DAMAGE_VARATION_TORPEDO)
                
                    targScan["shields"] = new_shields
                    targScan["hull"] = new_hull
                    
                    shield_dam += shieldsDam
                    hull_dam += hullDam
                    
                    if simulate_systems:
                        targScan["sys_impulse"] = impulse_sys_damage
                        targScan["sys_shield"] = shield_sys_damage
                        targScan["sys_warp"] = warp_drive_sys_damage
            
            shield_damage += shield_dam
            hull_damage += hull_dam
            
            averaged_hull += targScan["hull"]
            averaged_shields += targScan["shields"]
            
            targScan = target.scan_this_ship(precision)
        
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        shield_damage /= number_of_simulations
        hull_damage /= number_of_simulations
        
        return averaged_shields, averaged_hull, shield_damage, hull_damage, averaged_hull <= 0

    def simulatePhaserHit(self, target:Starship, number_of_simulations:int, energy:float, cannon:bool=False, *, simulate_systems:bool=False):
        
        is_beam = not cannon
        
        precision = self.determinPrecision

        targScan = target.scan_this_ship(precision)
        #shields, hull, energy, torps, sysWarp, sysImpuls, sysPhaser, sysShield, sysSensors, sysTorp
        targShield = targScan["shields"]
        targHull = targScan["hull"]

        total_shield_dam = 0
        total_hull_dam = 0
        
        averaged_shields = 0
        averaged_hull = 0

        amount = min(self.energy, self.shipData.maxWeapEnergy, energy)

        for i in range(number_of_simulations):
            if self.roll_to_hit_energy(target, targScan["sys_impulse"], cannon):
                
                new_shields, new_hull, shieldsDam, hullDam, new_shields_as_a_percent, new_hull_as_a_percent, killedOutright, killedInSickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, torpedo_sys_damage =self.calculate_damage(energy, precision=precision, calculate_crew=False, calculate_systems=simulate_systems, scan_dict=targScan, random_varation=DAMAGE_VARATION_BEAM)
                
                averaged_shields += new_shields
                averaged_hull += new_hull
                total_shield_dam += shieldsDam
                total_hull_dam += hullDam
            else:
                averaged_shields += targShield
                averaged_hull += targHull

                #if targShield > 0:
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        total_shield_dam /= number_of_simulations
        total_hull_dam /= number_of_simulations
        
        return averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_hull <= 0

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
