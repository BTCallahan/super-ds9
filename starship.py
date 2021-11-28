from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, Union
from enum import Enum, auto
from random import choice, uniform, random, randint
from math import ceil, inf
from itertools import accumulate
from functools import lru_cache

from space_objects import SubSector
from ai import BaseAi
from torpedo import Torpedo, TorpedoType, find_most_powerful_torpedo
from coords import Coords, IntOrFloat, MutableCoords
from torpedo import ALL_TORPEDO_TYPES
import colors
from data_globals import DAMAGE_BEAM, DAMAGE_CANNON, DAMAGE_EXPLOSION, DAMAGE_TORPEDO, REPAIR_DEDICATED, REPAIR_DOCKED, REPAIR_PER_TURN, SYM_PLAYER, SYM_FIGHTER, SYM_AD_FIGHTER, SYM_CRUISER, SYM_BATTLESHIP, \
SYM_RESUPPLY, DamageType, RepairStatus, ShipTypes

def scan_assistant(v:IntOrFloat, precision:int):
    """This takes a value, v and devides it by the precision. Next, the quotent is rounded to the nearest intiger and then multiplied by the precision. The product is then returned. A lower precision value ensures more accurate results. If precision is 1, then v is returned

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
    assert isinstance(precision, int)
    if precision == 1:
        return round(v)
    r = round(v / precision) * precision
    assert isinstance(r, float) or isinstance(r, int)
    return r

if TYPE_CHECKING:
    from game_data import GameData


class StarshipSystem:
    """This handles a starship system, such as warp drives or shields.
    
    """

    def __init__(self, name:str):
        """This handles a starship system, such as warp drives or shields.

        Args:
            name (str): The name of the system.
        """
        self._integrety = 1.0
        self.name = '{: <15}'.format(name)

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
    def is_opperational(self):
        return self._integrety >= 0.15

    @property
    def get_effective_value(self):
        """
        Starship systems can take quite a bit of beating before they begin to show signs of reduced performance. Generaly, when the systems integrety dips below 80% is when you will see performance degrade. Should integrety fall below 15%, then the system is useless and inoperative.
        """
        return min(1.0, self._integrety * 1.25) if self.is_opperational else 0.0

    @property
    def is_comprimised(self):
        return self._integrety * 1.25 < 1.0

    @property
    def affect_cost_multiplier(self):
        return 1 / self.get_effective_value if self.is_opperational else inf

    #def __add__(self, value):

    def get_info(self, precision:float, effective_value:bool):
        
        i = min(1.0, self._integrety * 1.25) if effective_value else self._integrety
        
        if precision <= 1.0:
            return i
        
        try :
            r = round(i * 100 / precision) * precision * 0.01
        except ZeroDivisionError:
            r = 0.0
        
        assert isinstance(r, float)
        return r

    def printInfo(self, precision):
        return f"{self.name}: {self.get_info(precision, False)}" if self.is_opperational else f"{self.name} OFFLINE"

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
        "Warp Core:",
        "Sensors:",
        "Shield Gen.:",
        "Impulse Eng.:", 
        "Warp Drive:",      
    ]

    keys = [
        "sys_warp_core",
        "sys_sensors",
        "sys_shield",
        "sys_impulse",
        "sys_warp_drive",
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
        keys.append("sys_torpedos")
    
    return tuple(names), tuple(keys)

class ShipData:

    def __init__(self, *,
        ship_type:ShipTypes, symbol:str, max_shields:int, max_armor:int=0, max_hull:int, max_torps:int=0, 
        max_crew:int, max_energy:int, damage_control:float, torp_types:Optional[Iterable[TorpedoType]]=None, 
        torp_tubes:int=0,
        max_weap_energy:int, warp_breach_dist:int=2, weapon_name:str, 
        nameGenerator:Callable[[], str]
    ):
        self.ship_type = ship_type
        self.symbol = symbol

        self.max_shields = max_shields
        self.max_armor = max_armor
        self.max_hull = max_hull

        self.max_crew = max_crew
        self.max_energy = max_energy

        self.damage_control = damage_control
        """
        if len(torp_types) == 0:
            print('torp_types List has zero lenght')
        elif torp_types == None:
            printy('torp_types is None object')
        """
        if (torp_types is None or len(torp_types) == 0) != (torp_tubes < 1) != (max_torps < 1):
            raise IndexError(f'The length of the torp_types list is {len(torp_types)}, but the value of torp_tubes is {torp_tubes}, and the value of maxTorps is {max_torps}. All of these should be less then one, OR greater then or equal to one.')
#if (len(torp_types) == 0 and torp_tubes > 1) or (len(torp_types) > 0 and torp_tubes < 0):
        #torp_types.sort()

        if torp_types:
            torp_types.sort(key=lambda t: ALL_TORPEDO_TYPES[t])

        self.torp_types = tuple([TorpedoType.TORP_TYPE_NONE] if not torp_types else torp_types)

        self.max_torpedos = max_torps
        self.torp_tubes = torp_tubes
        self.max_weap_energy = max_weap_energy
        self.warp_breach_dist = warp_breach_dist
        self.weapon_name = weapon_name
        self.weapon_namePlural = self.weapon_name + 's'
        self.shipNameGenerator = nameGenerator

        self.system_names, self.system_keys = get_system_names(
            has_torpedo_launchers= max_torps > 0 and torp_tubes > 0,
            beam_weapon_name=self.weapon_namePlural
        )
    
    @property
    @lru_cache
    def ship_type_can_fire_torps(self):
        return len(self.torp_types) > 0 and self.torp_types[0] != TorpedoType.TORP_TYPE_NONE and self.max_torpedos > 0 and self.torp_tubes > 0

    @property
    @lru_cache
    def get_most_powerful_torpedo_type(self):
        if not self.ship_type_can_fire_torps:
            return TorpedoType.TORP_TYPE_NONE

        if len(self.torp_types) == 1:
            return self.torp_types[0]

        return find_most_powerful_torpedo(self.torp_types)


DEFIANT_CLASS = ShipData(
    ship_type=ShipTypes.TYPE_ALLIED, 
    symbol=SYM_PLAYER, 
    max_shields=2700, 
    max_armor=400, 
    max_hull=1000, 
    max_torps=20, 
    max_crew=50, 
    max_energy=5000, 
    damage_control=0.45,
    torp_types=[TorpedoType.TORP_TYPE_QUANTUM, TorpedoType.TORP_TYPE_PHOTON], 
    torp_tubes=2, 
    max_weap_energy=800, 
    warp_breach_dist=2, 
    weapon_name='Phaser', 
    nameGenerator=genNameDefiant)

RESUPPLY = ShipData(
    ship_type=ShipTypes.TYPE_ALLIED, 
    symbol=SYM_RESUPPLY, 
    max_shields=1200, 
    max_hull=200, 
    max_crew=10, 
    max_energy=3000, 
    damage_control=0.2,
    max_weap_energy=200, 
    warp_breach_dist=5, 
    weapon_name='Phaser', 
    nameGenerator=genNameResupply)

K_VORT_CLASS = ShipData(
    ship_type=ShipTypes.TYPE_ALLIED, 
    symbol=SYM_PLAYER, 
    max_shields=1900, 
    max_hull=800, 
    max_torps=20, 
    max_crew=12, 
    max_energy=4000, 
    damage_control=0.35,
    torp_types=[TorpedoType.TORP_TYPE_PHOTON], 
    torp_tubes=1, 
    max_weap_energy=750, 
    warp_breach_dist=2, 
    weapon_name='Disruptor', 
    #cloak_strength=0.875,
    nameGenerator=genNameKVort)

ATTACK_FIGHTER = ShipData(
    ship_type=ShipTypes.TYPE_ENEMY_SMALL, 
    symbol=SYM_FIGHTER, 
    max_shields=900,
    max_hull=460, 
    max_crew=15, 
    max_energy=2500, 
    damage_control=0.15,
    max_weap_energy=600, 
    warp_breach_dist=2, 
    weapon_name='Poleron', 
    nameGenerator=genNameAttackFighter)

ADVANCED_FIGHTER = ShipData(
    ship_type=ShipTypes.TYPE_ENEMY_SMALL, 
    symbol=SYM_AD_FIGHTER, 
    max_shields=1000,
    max_hull=500, 
    max_torps=5, 
    max_crew=15, 
    max_energy=3000, 
    damage_control=0.15,
    torp_types=[TorpedoType.TORP_TYPE_POLARON], 
    torp_tubes=1, 
    max_weap_energy=650, 
    warp_breach_dist=2, 
    weapon_name='Poleron', 
    nameGenerator=genNameAdvancedFighter)

CRUISER = ShipData(
    ship_type=ShipTypes.TYPE_ENEMY_LARGE, 
    symbol=SYM_CRUISER, 
    max_shields=3000, 
    max_hull=1200, 
    max_torps=10, 
    max_crew=1200, 
    max_energy=5250, 
    damage_control=0.125,
    torp_types=[TorpedoType.TORP_TYPE_POLARON], 
    torp_tubes=2, 
    max_weap_energy=875, 
    warp_breach_dist=3, 
    weapon_name='Poleron', 
    nameGenerator=genNameCruiser)

BATTLESHIP = ShipData(
    ship_type=ShipTypes.TYPE_ENEMY_LARGE, 
    symbol=SYM_BATTLESHIP, 
    max_shields=5500, 
    max_hull=1500, 
    max_torps=20, 
    max_crew=1200, 
    max_energy=8000, 
    damage_control=0.075,
    torp_types=[TorpedoType.TORP_TYPE_POLARON], 
    torp_tubes=6, 
    max_weap_energy=950, 
    warp_breach_dist=5, 
    weapon_name='Poleron', 
    nameGenerator=genNameBattleship)

HIDEKI = ShipData(
    ship_type=ShipTypes.TYPE_ENEMY_SMALL,
    symbol=SYM_AD_FIGHTER,
    max_shields=1500,
    max_hull=430,
    max_crew=35,
    max_energy=800,
    damage_control=0.2,
    max_weap_energy=700,
    warp_breach_dist=2,
    weapon_name="Compresser",
    nameGenerator=gen_name_cardassian
)

#refrence - DEFIANT_CLASS ATTACK_FIGHTER ADVANCED_FIGHTER CRUISER BATTLESHIP

class ShipStatus(Enum):
    """Enum of the four ship statuses.

    ACTIVE: The ship is intact and crewed.
    DERLICT: The ship is intact but has no living crew.
    HULK: The ship is wrecked but mostly intact. Think battle of Wolf 359
    OBLITERATED: The ship has been reduced to space dust.
    """

    ACTIVE = auto()
    DERLICT = auto()
    HULK = auto()
    OBLITERATED = auto()
    
class Starship:
    """
    TODO - implement cloaking device,

    chance of enemy ship detecting you when you are cloaked:
    (1 / distance) * enemy ship sensors
    """

    game_data: GameData

    def __init__(self, 
    ship_data:ShipData, 
    ai_cls: Type[BaseAi],
    xCo, yCo, 
    secXCo, secYCo
    ):
        def set_torps(torpedo_types_:Iterable[TorpedoType], max_torps:int):
            tDict: Dict[TorpedoType, int] = {}
            if not torpedo_types_:
                return tDict

            for t in torpedo_types_:
                
                tDict[t] = max_torps if t == torpedo_types_[0] else 0
                
            return tDict

        self.local_coords:MutableCoords = MutableCoords(xCo, yCo)
        self.sector_coords:MutableCoords = MutableCoords(secXCo, secYCo)
        
        self.ship_data:ShipData = ship_data
        self._shields = ship_data.max_shields
        self.armor = ship_data.max_armor
        self._hull = ship_data.max_hull

        self.torps = set_torps(ship_data.torp_types, ship_data.max_torpedos)

        self.able_crew = ship_data.max_crew
        self.injured_crew = 0
        self._energy = ship_data.max_energy

        self.sys_warp_drive = StarshipSystem('Warp Dri:')
        self.sys_torpedos = StarshipSystem('Tubes:')
        self.sys_impulse = StarshipSystem('Impulse:')
        self.sys_energy_weapon = StarshipSystem(self.ship_data.weapon_namePlural + ':')
        self.sys_shield_generator = StarshipSystem('Shield:')
        self.sys_sensors = StarshipSystem('Sensors:')
        self.sys_warp_core = StarshipSystem('Warp Core:')

        self.name = self.ship_data.shipNameGenerator()

        self.docked = False

        self.turn_taken = False

        self.turn_repairing = 0

        try:
            self.torpedo_loaded = TorpedoType.TORP_TYPE_NONE if not self.ship_type_can_fire_torps else self.ship_data.torp_types[0]
        except IndexError:
            self.torpedo_loaded = TorpedoType.TORP_TYPE_NONE

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
        elif self._shields > self.get_max_effective_shields:
            self._shields = self.get_max_effective_shields
    
    @property
    def hull(self):
        return self._hull

    @hull.setter
    def hull(self, value):
        self._hull = round(value)
        if self._hull > self.ship_data.max_hull:
            self._hull = self.ship_data.max_hull

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, value):
        self._energy = round(value)
        if self._energy < 0:
            self._energy = 0
        elif self._energy > self.ship_data.max_energy:
            self._energy = self.ship_data.max_energy

    @property
    def shields_percentage(self):
        try:
            return self._shields / self.ship_data.max_shields
        except ZeroDivisionError:
            return 0.0

    @property
    def hull_percentage(self):
        try:
            return self._hull / self.ship_data.max_hull
        except ZeroDivisionError:
            return 0.0

    @property
    def get_sub_sector(self) -> SubSector:
        return self.game_data.grid[self.sector_coords.y][self.sector_coords.x]

    @property
    def ship_type_can_fire_torps(self):
        return self.ship_data.ship_type_can_fire_torps

    @property
    def ship_can_fire_torps(self):
        return self.ship_data.ship_type_can_fire_torps and self.sys_torpedos.is_opperational and sum(self.torps.values()) > 0

    @property
    def crew_readyness(self):
        return (self.able_crew / self.ship_data.max_crew) + (self.injured_crew / self.ship_data.max_crew) * 0.25

    @property
    def able_crew_percent(self):
        return self.ableCrew / self.shipData.maxCrew
    
    @property
    def injured_crew_percent(self):
        return self.injuredCrew / self.shipData.maxCrew

    @property
    def get_total_torpedos(self):
        return 0 if not self.ship_type_can_fire_torps else tuple(accumulate(self.torps.values()))[-1]

    @property
    def get_max_shields(self):
        return self.ship_data.max_shields

    @property
    def get_max_effective_shields(self):
        return ceil(self.ship_data.max_shields * self.sys_shield_generator.get_effective_value)

    @property
    def get_max_firepower(self):
        return self.ship_data.max_weap_energy

    @property
    def get_max_effective_firepower(self):
        return ceil(self.ship_data.max_weap_energy * self.sys_energy_weapon.get_effective_value)

    def get_number_of_torpedos(self, precision = 1):
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

        if self.ship_type_can_fire_torps:
            if precision == 1:
                for t in self.ship_data.torp_types:
                    yield (t, self.torps[t])
            else:
                for t in self.ship_data.torp_types:
                    yield (t, scan_assistant(self.torps[t], precision))
        else:
            yield (TorpedoType.TORP_TYPE_NONE, 0)

    @property
    def combat_effectivness(self):
        divisor = 7
        total = (
            self.sys_warp_core.get_effective_value + self.sys_energy_weapon.get_effective_value + self.sys_shield_generator.get_effective_value + self.sys_sensors.get_effective_value + (self.shields / self.ship_data.max_shields) + self.crew_readyness + (self.hull / self.ship_data.max_hull)
        )
        
        if self.ship_type_can_fire_torps:
            total += self.sys_torpedos.get_effective_value
            divisor += 1
        
        return total / divisor

    @property
    def determin_precision(self):
        """
        Takes the effective value of the ships sensor system and returns an intiger value based on it. This
        intiger is passed into the scanAssistant function that is used for calculating the precision when 
        scanning another ship. If the 
        sensors are heavly damaged, their effective 'resoultion' drops. Say their effective value is 0.65.
        This means that this function will return 25. 
        

        Returns:
            int: The effective value that is used for 
        """
        getEffectiveValue = self.sys_sensors.get_effective_value

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

    #shields, hull, energy, torps, sys_warp_drive, sysImpuls, sysPhaser, sys_shield_generator, sys_sensors, sys_torpedos
    
    def scan_this_ship(self, precision: int=1, *, scan_for_crew:bool=True, scan_for_systems:bool=True)->Dict[str,Union[int,Tuple]]:
        """
        @ precision - this must be an intiger between 1 and 100
        Returns a dictionary containing 
        """

        if isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be an intiger between 1 amd 100")
        if precision not in {1,2,5,10,15,20,25,50,100,200,500}:
            raise ValueError(f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. It's actually value is {precision}.")

        d= {
            "shields" : scan_assistant(self.shields, precision),
            "hull" : scan_assistant(self.hull, precision),
            "energy" : scan_assistant(self.energy, precision),
            
            "number_of_torps" : tuple(self.get_number_of_torpedos(precision)),
            #"torp_tubes" : s
            
        }
        
        if scan_for_crew:
            d["able_crew"] = scan_assistant(self.able_crew, precision)
            d["injured_crew"] = scan_assistant(self.injured_crew, precision)

        if scan_for_systems:
            d["sys_warp_drive"] = self.sys_warp_drive.get_info(precision, False)# * 0.01,
            d["sys_impulse"] = self.sys_impulse.get_info(precision, False)# * 0.01,
            d["sys_energy_weapon"] = self.sys_energy_weapon.get_info(precision, False)# * 0.01,
            d["sys_shield"] = self.sys_shield_generator.get_info(precision, False)# * 0.01,
            d["sys_sensors"] = self.sys_sensors.get_info(precision, False)# * 0.01,
            d["sys_torpedos"] = self.sys_torpedos.get_info(precision, False)# * 0.01
            d["sys_warp_core"] = self.sys_warp_core.get_info(precision, False)

        if self.ship_data.ship_type_can_fire_torps:

            torps = tuple(self.get_number_of_torpedos(precision))
            for k, v in torps:
                d[k] = v

        return d

    """
    def printShipInfo(self, precision):
        textList = []
        blank = ' ' * 18
        scan = self.scanThisShip(precision, True)
        textList.append('{0:^18}'.format(self.name))
        textList.append('Shields: {0: =4}/{1: =4}'.format(scan[0], self.shipData.max_shields))
        textList.append('Hull:    {0: =4}/{1: =4}'.format(scan[1], self.shipData.max_hull))
        textList.append('Energy:  {0: =4}/{1: =4}'.format(scan[2], self.shipData.max_energy))
        textList.append('Crew:    {0: =4}/{1: =4}'.format(scan[3], self.shipData.max_crew))
        textList.append('Injured: {0: =4}/{1: =4}'.format(scan[4], self.shipData.max_crew))
        if self.ship_type_can_fire_torps:
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
    def get_ship_value(self):
        return (self.hull + self.ship_data.max_hull) * 0.5 if self.ship_status == ShipStatus.ACTIVE else 0.0

    def destroy(self, cause, warp_core_breach=False):
        gd = self.game_data
        #gd.grid[self.sector_coords.y][self.sector_coords.x].removeShipFromSec(self)
        is_controllable = self.is_controllable
        wc_value = self.sys_warp_drive.get_effective_value

        if is_controllable:
            gd.engine.message_log.print_messages = False

        if warp_core_breach:
        
            self.warp_core_breach()
                
        if self is self.game_data.selected_ship_planet_or_star:
            self.game_data.selected_ship_planet_or_star = None

        self.hull = -self.ship_data.max_hull

    def warp_core_breach(self, selfDestruct=False):

        shipList = self.game_data.grab_ships_in_same_sub_sector(self)

        damage = self.ship_data.max_hull * ((2 if selfDestruct else 1) / 3)

        for s in shipList:

            distance = self.local_coords.distance(coords=s.local_coords)

            damPercent = 1 - (distance / self.ship_data.warp_breach_dist)

            if damPercent > 0.0 and s.hull < 0:

                s.take_damage(round(damPercent * damage), f'Caught in the {"auto destruct radius" if selfDestruct else "warp core breach"} of the {self.name}', damage_type=DAMAGE_EXPLOSION)

    def calc_self_destruct_damage(self, target:Starship, *, scan:Optional[Dict]=None, number_of_simulations:int=1):
        #TODO - write an proper method to look at factors such as current and max hull strength to see if using a self destruct is worthwhile
        
        precision = self.determin_precision
        
        scan = scan if scan else target.scan_this_ship(precision)
                
        distance = self.local_coords.distance(coords=target.local_coords)
        
        damPercent = 1 - (distance / self.ship_data.warp_breach_dist)
        
        damage = self.ship_data.max_hull * (2 / 3)
        
        amount = round(damPercent * damage)
        
        averaged_shield = 0
        averaged_hull = 0
        averaged_shield_damage = 0
        averaged_hull_damage = 0
        
        for i in range(number_of_simulations):
        
            new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, torpedo_sys_damage = self.calculate_damage(amount, scan_dict=scan, precision=precision, calculate_crew=False, calculate_systems=False, damage_type=DAMAGE_EXPLOSION)
            
            averaged_shield += new_shields
            averaged_hull += new_hull
            averaged_shield_damage += shields_dam
            averaged_hull_damage += hull_dam
                
        averaged_shield /= number_of_simulations
        averaged_hull /= number_of_simulations
        averaged_shield_damage /= number_of_simulations
        averaged_hull_damage /= number_of_simulations
                
        return averaged_shield , averaged_hull, averaged_shield_damage, averaged_hull_damage, averaged_hull <= 0

    @property
    def ship_status(self):
        """Checks if the ship is relitivly intact. If a ship is destroyed but intact ship, then is a a runined hulk, like we saw in aftermath of the battle of Wolf 389. 

        Checks is the ship has no living crew, and returns True if it does not, False if it does.

        Returns:
            bool: Returns True if the hull is greater then or equal to half the negitive max hit points, and less then or equal to zero.
        """
        if self._hull < self.ship_data.max_hull * -0.5:
            return ShipStatus.OBLITERATED
        if self._hull <= 0:
            return ShipStatus.HULK
        return ShipStatus.DERLICT if self.able_crew + self.injured_crew < 1 else ShipStatus.ACTIVE

    def ram(self, otherShip:Starship):
        """Prepare for RAMMING speed!

        The ship will attempt to ram another

        Args:
            otherShip (Starship): [description]
        """
        self_hp = self.shields + self.hull
        other_hp = otherShip.shields + otherShip.hull

        if self.sys_impulse.get_effective_value <= otherShip.sys_impulse.get_effective_value:
            return False

        if self_hp > other_hp:
            self.take_damage(other_hp, 'Rammed the {0}'.format(self.name), damage_type=DAMAGE_EXPLOSION)
            otherShip.destroy('Rammed by the {0}'.format(self.name))
        elif self_hp < other_hp:
            otherShip.take_damage(self_hp, 'Rammed by the {0}'.format(self.name), damage_type=DAMAGE_EXPLOSION)
            self.destroy('Rammed the {0}'.format(self.name))
        else:
            otherShip.destroy('Rammed by the {0}'.format(self.name))
            self.destroy('Rammed the {0}'.format(self.name))

    def calculate_damage(self, amount:int, *, scan_dict:Optional[Dict]=None, precision:int=1, calculate_crew:bool=True, calculate_systems:bool=True,  damage_type:DamageType):
        
        #assume damage is 64, current shields are 80, max shields are 200
        #armor is 75, max armor is 100
        #80 * 2 / 200 = 160 / 200 = 0.8
        #0.8 * 64 = 51.2 = the amount of damage that hits the shields
        #64 - 51.2 = 12.8 = the amount of damage that hits the armor and hull
        #1 - (75 / 100) = 1 - 0.25 = 0.75
        #12.8 * 0.75 = 9.6 = the amount of damage that hits the armor
        #12.8 - 9.6 = 3.2 = the amount of damage that hits the hull
        
        random_varation = damage_type.damage_variation
        
        if random_varation > 0.0:
            amount = round(amount * uniform(0.0, 1.0 - random_varation))
        
        old_scan = scan_dict if scan_dict else self.scan_this_ship(precision)
        
        current_shields:int = old_scan["shields"]
        current_hull:int = old_scan["hull"]
        
        shield_effectiveness = 0 if old_scan["sys_shield"] < 0.15 else min(old_scan["sys_shield"] * 1.25, 1.0)
        
        shields_are_already_down = shield_effectiveness <= 0 or current_shields <= 0
        
        shields_dam = 0
        armorDam = 1.0 * amount
        hull_dam = 1.0 * amount
        
        shieldDamMulti = damage_type.damage_vs_shields_multiplier

        armorHullDamMulti = (damage_type.damage_vs_no_shield_multiplier if shields_are_already_down else damage_type.damage_vs_hull_multiplier) 
        
        shields_percentage = current_shields / self.ship_data.max_shields
        
        #shieldPercent = self.shields_percentage * 0.5 + 0.5
        
        bleedthru_factor = min(shields_percentage + 0.5, 1.0)
        
        if shields_are_already_down:
            
            hull_dam = amount * armorHullDamMulti
        else:
            
            shields_dam = amount * bleedthru_factor * shieldDamMulti
            if shields_dam > current_shields:
                shields_dam = current_shields
            hull_dam = amount * (1 - bleedthru_factor) * armorHullDamMulti
        
        new_shields = scan_assistant(current_shields - shields_dam, precision) if shields_dam > 0 else current_shields
        new_hull = scan_assistant(current_hull - hull_dam, precision) if hull_dam > 0 else current_hull
        
        hull_damage_as_a_percent = hull_dam / self.ship_data.max_hull
        new_shields_as_a_percent = new_shields / self.ship_data.max_shields
        new_hull_as_a_percent = new_hull / self.ship_data.max_hull
        
        killed_outright = 0
        killed_in_sickbay = 0
        wounded = 0
        
        if calculate_crew:
            
            crew_killed = hull_dam > 0 and new_hull_as_a_percent < random()
            
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
                
                killed_outright = round(self.able_crew * percentage_of_able_crew_killed)
                killed_in_sickbay = round(0.5 * self.able_crew * percentage_of_injured_crew_killed)
                wounded = round(self.able_crew * percentage_of_able_crew_wounded)
        
        shield_sys_damage = 0
        energy_weapons_sys_damage = 0
        impulse_sys_damage = 0
        warp_drive_sys_damage = 0
        sensors_sys_damage = 0
        torpedo_sys_damage = 0
        warp_core_sys_damage = 0
        
        if calculate_systems:
            chance_to_damage_system = damage_type.chance_to_damage_system
            
            systems_damaged = hull_dam > 0 and new_hull_as_a_percent < uniform(hull_damage_as_a_percent, 1.25 + hull_damage_as_a_percent)
            
            if systems_damaged:
                system_damage_chance = damage_type.damage_chance_vs_systems_multiplier
                
                def chance_of_system_damage():
                    return uniform(hull_damage_as_a_percent, chance_to_damage_system + hull_damage_as_a_percent) > new_hull_as_a_percent
                
                def random_system_damage():
                    return uniform(0.0, system_damage_chance * hull_damage_as_a_percent)
                
                if chance_of_system_damage():
                    shield_sys_damage = random_system_damage()
                if chance_of_system_damage():
                    energy_weapons_sys_damage = random_system_damage()
                if chance_of_system_damage():
                    impulse_sys_damage = random_system_damage()
                if chance_of_system_damage():
                    warp_drive_sys_damage = random_system_damage()
                if chance_of_system_damage():
                    sensors_sys_damage = random_system_damage()
                if self.ship_type_can_fire_torps and chance_of_system_damage():
                    torpedo_sys_damage = random_system_damage()
                if chance_of_system_damage():
                    warp_core_sys_damage = random_system_damage()
            
        return new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, torpedo_sys_damage

    def take_damage(self, amount, text, *, isTorp=False, is_beam=False, random_varation:float=0.0, damage_type:DamageType):
        #is_controllable = self.isControllable
        gd = self.game_data
        message_log = gd.engine.message_log
        
        new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, torpedo_sys_damage = self.calculate_damage(amount, damage_type=damage_type)
        
        ship_destroyed = new_hull < 0
        
        ship_is_player = self is self.game_data.player

        pre = 1 if ship_is_player else self.determin_precision
        
        old_scan = self.scan_this_ship(pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player)
        
        self.shields = new_shields
        self.hull = new_hull
        
        self.able_crew -= wounded
        self.injured_crew += wounded
        self.able_crew -= killed_outright
        self.injured_crew -= killed_in_sickbay
        
        self.sys_shield_generator.integrety -= shield_sys_damage
        self.sys_energy_weapon.integrety -= energy_weapons_sys_damage
        self.sys_impulse.integrety -= impulse_sys_damage
        self.sys_sensors.integrety -= sensors_sys_damage
        self.sys_warp_drive.integrety -= warp_drive_sys_damage
        self.sys_torpedos.integrety -= torpedo_sys_damage
        
        new_scan = self.scan_this_ship(pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player)
        
        #name = "our" if ship_is_player else f"the {self.name}'s"
        
        #name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
        #name_second_occ = "our" if ship_is_player else f"the {self.name}'s"
        
        if not ship_destroyed:
            
            old_shields = old_scan["shields"]
            
            newer_shields = new_scan['shields'] 
            
            old_hull = old_scan["hull"]
            
            newer_hull = new_scan["hull"]
            
            scaned_shields_percentage = newer_shields / self.ship_data.max_shields
            
            shield_status = "holding" if scaned_shields_percentage > 0.9 else (f"at {scaned_shields_percentage:.0%}" if self.shields > 0 else "down")
            
            shields_are_down = newer_shields == 0
            
            #shields_just_got_knocked_down = old_shields > 0 and shields_are_down
            
            shields_are_already_down = old_shields == 0 and shields_are_down
            
            old_hull_percent = old_hull / self.ship_data.max_hull
            newer_hull_hull_percent = newer_hull / self.ship_data.max_hull
            
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
                
                if killed_outright > 0:
                    message_log.add_message(f'{killed_outright} active duty crewmembers were killed.')
                    
                if killed_in_sickbay > 0:
                    message_log.add_message(f'{killed_in_sickbay} crewmembers in sickbay were killed.')
                    
                if wounded > 0:
                    message_log.add_message(f'{wounded} crewmembers were injured.')
                
                if impulse_sys_damage > 0:
                    message_log.add_message('Impulse engines damaged.')
                    
                if warp_drive_sys_damage > 0:
                    message_log.add_message('Warp drive damaged.')
                    
                if energy_weapons_sys_damage > 0:
                    message_log.add_message(f'{self.ship_data.weapon_name} emitters damaged.')
                    
                if sensors_sys_damage > 0:
                    message_log.add_message('Sensors damaged.')
                            
                if shield_sys_damage > 0:
                    message_log.add_message('Shield generator damaged.')
                
                if warp_core_sys_damage > 0:
                    message_log.add_message('Warp core damaged.')
                            
                if self.ship_type_can_fire_torps and torpedo_sys_damage > 0:
                    message_log.add_message('Torpedo launcher damaged.')
                
        else:
            wc_breach = random() > 0.85 and random() > self.sys_warp_drive.get_effective_value and random() > self.sys_warp_drive.integrety
            
            if ship_is_player:
                
                if wc_breach:
                    message_log.add_message("Warp core breach iminate!", colors.orange)
                
                message_log.add_message("Abandon ship, abandon ship, all hands abandon ship...", colors.red)
                
                
            else:
                message_log.add_message(f"The {self.name} {'suffers a warp core breach' if wc_breach else 'is destroyed'}!")
                
            self.destroy(text, warp_core_breach=wc_breach)
        
    def repair(self):
        """This method handles repairing the ship after each turn. Here's how it works:
        
        If the ship is not being fired on, manuivering, or firing topredos, then some rudimentory repairs are going to be done. Also, the ships batteries will be slowly be refilled by the warp core.
        
        However, if the ship focuses its crews attention soley on fixing the ship (by using the RepairOrder order), then the repairs are going to be much more effective. For each consuctive turn the ship's crew spends on fixing things up, a small but clumitive bonus is applied. The ships batteries will also recharge much more quickly.
        
        If the ship is docked/landed at a friendly planet, then the ship will benifit even more from the expertise of the local eneriners.
        """        
        #self.crew_readyness
        repair_factor:RepairStatus = REPAIR_DOCKED if self.docked else (REPAIR_DEDICATED if self.turn_repairing else REPAIR_PER_TURN)
        timeBonus = 1.0 + (self.turn_repairing / 25.0)

        hull_repair_factor = self.ship_data.damage_control * repair_factor.hull_repair * self.crew_readyness * timeBonus
        system_repair_factor = self.ship_data.damage_control * repair_factor.system_repair * self.crew_readyness * timeBonus

        self.energy+= repair_factor.energy_regeration * self.sys_warp_core.get_effective_value

        healCrew = min(self.injured_crew, ceil(self.injured_crew * 0.2) + randint(2, 5))
        self.able_crew+= healCrew
        self.injured_crew-= healCrew
        
        repair_amount = hull_repair_factor * uniform(0.5, 1.25) * self.ship_data.max_hull

        self.hull += repair_amount
        self.sys_warp_drive.integrety += system_repair_factor * (0.5 + random() * 0.5)
        self.sys_sensors.integrety += system_repair_factor * (0.5 + random() * 0.5)
        self.sys_impulse.integrety += system_repair_factor * (0.5 + random() * 0.5)
        self.sys_energy_weapon.integrety += system_repair_factor * (0.5 + random() * 0.5)
        self.sys_shield_generator.integrety += system_repair_factor * (0.5 + random() * 0.5)
        self.sys_warp_core.integrety += system_repair_factor * (0.5 + random() * 0.5)
        if self.ship_type_can_fire_torps:
            self.sys_torpedos.integrety += system_repair_factor * (0.5 + random() * 0.5)

    """
    def rollToHitBeam(self, enemy:Starship, estimated_enemy_impulse=-1):
        return self.roll_to_hit_energy(enemy=enemy, estimated_enemy_impulse=estimated_enemy_impulse, cannon=False)

    def rollToHitCannon(self, enemy:Starship, estimated_enemy_impulse=-1):
        return self.roll_to_hit_energy(enemy=enemy, estimated_enemy_impulse=estimated_enemy_impulse, cannon=False)
    """
    
    def roll_to_hit(self, enemy:Starship, *, estimated_enemy_impulse:float=-1.0, damage_type:DamageType):
        
        assert damage_type is not DAMAGE_EXPLOSION
        
        if estimated_enemy_impulse == -1.0:
            estimated_enemy_impulse = enemy.sys_impulse.get_effective_value
                
        distance_penalty = damage_type.accuracy_loss_per_distance_unit * self.local_coords.distance(coords=enemy.local_coords) if damage_type.accuracy_loss_per_distance_unit else damage_type.flat_accuracy_loss
        
        attack_value = self.sys_sensors.get_effective_value * (1 - distance_penalty)
        
        return attack_value + random() > estimated_enemy_impulse

    def roll_to_hit_energy(self, enemy:Starship, estimated_enemy_impulse:float=-1.0, cannon:bool=False):
        if estimated_enemy_impulse == -1.0:
            estimated_enemy_impulse = enemy.sys_impulse.get_effective_value
        """
        assume that the distance is 5, the sensors are at 70% and enemy impulse is at 80%
        so (1 / 5) * (0.7 * 1.25 / 0.8)
        0.2 * (0.875 / 0.8)
        0.2 * 1.09375
        2.1875"""
        divisor = 300 if cannon else 100

        distance = self.local_coords.distance(coords=enemy.local_coords)

        distance_roll = 200 / (distance * divisor)

        sensor_roll = self.sys_sensors.get_effective_value * 1.25 / estimated_enemy_impulse

        roll =  distance_roll * sensor_roll

        return roll > random()

    def attack_energy_weapon(self, enemy:Starship, amount:float, energy_cost:float,  damage_type:DamageType):
        gd = self.game_data
        if self.sys_energy_weapon.is_opperational:
            
            attacker_is_player = self is self.game_data.player
            target_is_player = not attacker_is_player and enemy is self.game_data.player

            self.energy-=energy_cost
                            
            gd.engine.message_log.add_message(
                f"Firing on the {enemy.name}!" if attacker_is_player else f"The {self.name} has fired on {'us' if target_is_player else f'the {enemy.name}'}!"
            )

            hit = self.roll_to_hit(enemy, estimated_enemy_impulse=-1.0, damage_type=damage_type)
            

            if hit:
                
                target_name = "We're" if target_is_player else f'The {enemy.name} is'

                gd.engine.message_log.add_message(
                    f"Direct hit on {enemy.name}!" if attacker_is_player else
                    f"{target_name} hit!", fg=colors.orange
                )

                enemy.take_damage(amount * self.sys_energy_weapon.get_effective_value, f'Destroyed by a {self.ship_data.weapon_name} hit from the {self.name}.', damage_type=damage_type)
                return True
            else:
                gd.engine.message_log.add_message(
                    "We missed!" if attacker_is_player else "A miss!"
                    )
                #f"{self.name} misses {enemy.name}!"

        return False

    def attack_torpedo(self, gd:GameData, enemy:Starship, torp:Torpedo):
        gd = self.game_data
        if self.roll_to_hit(enemy, damage_type=DAMAGE_TORPEDO):
            #chance to hit:
            #(4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)
            gd.engine.message_log.add_message(f'{enemy.name} was hit by a {torp.name} torpedo from {self.name}.')

            enemy.take_damage(torp.damage, f'Destroyed by a {torp.name} torpedo hit from the {self.name}', isTorp=True, damage_type=DAMAGE_TORPEDO)

            return True
        gd.engine.message_log.add_message(f'A {torp.name} torpedo from {self.name} missed {enemy.name}.')
        return False
    
    def get_no_of_avalible_torp_tubes(self, number=0):
        if not self.sys_torpedos.is_opperational:
            return 0

        if number == 0:
            number = self.ship_data.torp_tubes
        else:
            number = min(number, self.ship_data.torp_tubes)

        return max(1, round(number * self.sys_torpedos.get_effective_value))
    
    @property
    def is_controllable(self):
        return self is self.game_data.player

    """
    @property
    def hasValidTarget(self):
        return self.order and self.order.target and self.order.target.sector_coords == self.sector_coords
    """
    
    @property
    def get_most_powerful_torp_avaliable(self):
        rt = self.ship_data.get_most_powerful_torpedo_type

        if rt is TorpedoType.TORP_TYPE_NONE:
            return rt
        
        if self.get_total_torpedos > 0:
            if self.torps[rt] > 0:
                return rt

            avaliable_torps = [t for t, tyt in self.torps.items() if tyt]
            
            most_powerful = find_most_powerful_torpedo(avaliable_torps)

            return most_powerful

        return TorpedoType.TORP_TYPE_NONE
    
    def restock_torps(self, infrastructure:float):
        if self.ship_data.max_torpedos != self.get_total_torpedos:
            torpSpace = self.ship_data.max_torpedos - self.get_total_torpedos
            for t in self.ship_data.torp_types:
                if ALL_TORPEDO_TYPES[t].infrastructure <= infrastructure:
                    self.torps[t]+= torpSpace
                    break
    
    def simulate_torpedo_hit(self, target:Starship, number_of_simulations:int, *, simulate_systems:bool=False, simulate_crew:bool=False):
        precision = self.determin_precision
        target_scan = target.scan_this_ship(precision, scan_for_crew=simulate_crew)
        #shields, hull, energy, torps, sys_warp_drive, sysImpuls, sysPhaser, sys_shield_generator, sys_sensors, sys_torpedos
        targ_shield = target_scan["shields"]
        targ_hull = target_scan["hull"]
        torp = self.get_most_powerful_torp_avaliable
        if torp == None:
            return targ_shield, targ_hull
        torpedos = self.torps[torp]
        
        damage = ALL_TORPEDO_TYPES[torp].damage

        times_to_fire = min(self.get_no_of_avalible_torp_tubes(), torpedos)

        shield_damage = 0
        hull_damage = 0
        
        averaged_hull = 0
        averaged_shields = 0

        for s in range(number_of_simulations):
            
            for attack in range(times_to_fire):
                hull_dam  = 0
                shield_dam = 0
                if self.roll_to_hit(target, estimated_enemy_impulse=target_scan["sys_impulse"], damage_type=DAMAGE_TORPEDO):
                    
                    new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, torpedo_sys_damage =self.calculate_damage(damage, precision=precision, calculate_crew=simulate_crew, calculate_systems=simulate_systems, scan_dict=target_scan, damage_type=DAMAGE_TORPEDO)
                
                    target_scan["shields"] = new_shields
                    target_scan["hull"] = new_hull
                    
                    shield_dam += shields_dam
                    hull_dam += hull_dam
                    
                    if simulate_systems:
                        target_scan["sys_impulse"] = impulse_sys_damage
                        target_scan["sys_shield"] = shield_sys_damage
                        target_scan["sys_warp_drive"] = warp_drive_sys_damage
                    if simulate_crew:
                        target_scan[""]
            
            shield_damage += shield_dam
            hull_damage += hull_dam
            
            averaged_hull += target_scan["hull"]
            averaged_shields += target_scan["shields"]
            
            target_scan = target.scan_this_ship(precision)
        
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        shield_damage /= number_of_simulations
        hull_damage /= number_of_simulations
        
        return averaged_shields, averaged_hull, shield_damage, hull_damage, averaged_hull <= 0

    def simulate_phaser_hit(self, target:Starship, number_of_simulations:int, energy:float, cannon:bool=False, *, simulate_systems:bool=False):
                
        precision = self.determin_precision

        targScan = target.scan_this_ship(precision)
        
        targ_shield = targScan["shields"]
        targ_hull = targScan["hull"]

        total_shield_dam = 0
        total_hull_dam = 0
        
        averaged_shields = 0
        averaged_hull = 0
        
        damage_type = DAMAGE_CANNON if cannon else DAMAGE_BEAM

        amount = min(self.energy, self.get_max_effective_firepower, energy)

        for i in range(number_of_simulations):
            if self.roll_to_hit(target, estimated_enemy_impulse=targScan["sys_impulse"], damage_type=DAMAGE_CANNON if cannon else DAMAGE_BEAM):
                            
                new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, energy_weapons_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, torpedo_sys_damage =self.calculate_damage(amount, precision=precision, calculate_crew=False, calculate_systems=simulate_systems, scan_dict=targScan, damage_type=damage_type)
                
                averaged_shields += new_shields
                averaged_hull += new_hull
                total_shield_dam += shields_dam
                total_hull_dam += hull_dam
            else:
                averaged_shields += targ_shield
                averaged_hull += targ_hull

                #if targ_shield > 0:
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        total_shield_dam /= number_of_simulations
        total_hull_dam /= number_of_simulations
        
        return averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_hull <= 0

    def check_torpedo_los(self, target:Starship):

        gd = self.game_data

        dirX, dirY = Coords(target.local_coords.x - self.local_coords.x, target.local_coords.y - self.local_coords.y).normalize()

        g:SubSector = gd.grid[self.sector_coords.y][self.sector_coords.x]

        #posX, posY = self.local_coords.x, self.local_coords.y

        #torp_positions = gd.engine.get_lookup_table(direction_x=dirX, direction_y=dirY, normalise_direction=False)
        torp_positions = [co for co in gd.engine.get_lookup_table(direction_x=dirX, direction_y=dirY, normalise_direction=False)]
        #ships_in_same_subsector = gd.grab_ships_in_same_sub_sector(self)

        ship_positions = {
            ship.local_coords.create_coords() : ship for ship in gd.grab_ships_in_same_sub_sector(self)
        }

        for pos in torp_positions:
            ajusted_pos = Coords(x=pos.x+self.local_coords.x, y=pos.y+self.local_coords.y)

            if ajusted_pos.x not in gd.subsec_size_range_x or ajusted_pos.y not in gd.subsec_size_range_y:
                return False

            if ajusted_pos in g.stars_dict or pos in g.planets_dict:
                return False

            try:
                hit_ship = ship_positions[ajusted_pos]
                return not (hit_ship.is_controllable == self.is_controllable)

            except KeyError:
                pass

        return False
