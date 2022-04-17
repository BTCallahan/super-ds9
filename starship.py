from __future__ import annotations
from copy import copy
from decimal import DivisionByZero
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Tuple, Type, Union
from random import choice, uniform, random, randint
from math import ceil
from components.beam_array import BeamArray
from components.cannon import Cannon
from components.cloak import Cloak
from components.life_support import LifeSupport
from components.impulse_ingine import ImpulseEngine
from components.polarized_hull import PolarizedHull
from components.power_generator import PowerGenerator
from components.sensors import Sensors
from components.shields import Shields
from components.torpedo_launcher import TorpedoLauncher
from components.transporter import Transporter
from components.warp_drive import WarpDrive

from global_functions import ajust_system_integrity, calculate_polarization, inverse_square_law, scan_assistant
from nation import ALL_NATIONS
from ship_class import ShipClass
from space_objects import SubSector, CanDockWith
from torpedo import Torpedo
from coords import Coords, MutableCoords
import colors
from data_globals import DAMAGE_BEAM, DAMAGE_CANNON, DAMAGE_EXPLOSION, DAMAGE_RAMMING, DAMAGE_TORPEDO, PRECISION_SCANNING_VALUES, REPAIR_DEDICATED, REPAIR_DOCKED, REPAIR_PER_TURN, STATUS_AT_WARP, DamageType, RepairStatus, ShipStatus, STATUS_ACTIVE, STATUS_DERLICT, STATUS_CLOAKED, STATUS_CLOAK_COMPRIMISED,STATUS_HULK, STATUS_OBLITERATED, CloakStatus

if TYPE_CHECKING:
    from game_data import GameData
    from ai import BaseAi
    from nation import Nation

def randomNeumeral(n:int) -> str:
    for i in range(n):
        yield choice(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])

class Starship(CanDockWith):
    """This class is the bread and butter of the game
    """

    game_data: GameData

    def __init__(self, 
        ship_class:ShipClass, 
        ai_cls: Type[BaseAi],
        xCo, yCo, 
        secXCo, secYCo,
        *,
        name:Optional[str]=None,
        override_nation:Optional[Nation]=None
    ):
        self.local_coords:MutableCoords = MutableCoords(xCo, yCo)
        self.sector_coords:MutableCoords = MutableCoords(secXCo, secYCo)
        
        self.ship_class:ShipClass = ship_class
        
        self.name = name if name else self.ship_class.create_name()
        
        self.proper_name = (
            f"{self.ship_class.nation.ship_prefix} {self.name}" if self.ship_class.nation.ship_prefix else self.name
        )
        self.armor = ship_class.max_armor
        self._hull = ship_class.max_hull
        
        self._hull_damage = 0
        
        self.power_generator = PowerGenerator(ship_class)
        self.power_generator.starship = self
        
        self.sensors = Sensors()
        self.sensors.starship = self
        
        if ship_class.polarized_hull:
            
            self.polarized_hull = PolarizedHull(ship_class)
            self.polarized_hull.starship = self
        
        if ship_class.max_shields:#if has shields
            
            self.shield_generator = Shields(ship_class)
            self.shield_generator.starship = self
        
        if ship_class.ship_type_can_fire_torps:#if has torpedos
            
            self.torpedo_launcher = TorpedoLauncher(ship_class)
            self.torpedo_launcher.starship = self

        if ship_class.max_crew:#if has crew
            
            self.life_support = LifeSupport(ship_class)
            self.life_support.starship = self
            
            self.transporter = Transporter()
            self.transporter.starship = self
        
        if ship_class.cloak_strength:#if can cloak
            
            self.cloak = Cloak()
            self.cloak.starship = self

        if ship_class.max_beam_energy:
            
            self.beam_array = BeamArray(ship_class)
            self.beam_array.starship = self
        
        if ship_class.max_cannon_energy:
            
            self.cannons = Cannon(ship_class)
            self.cannons.starship = self
        
        if ship_class.evasion:
            
            self.impulse_engine = ImpulseEngine()
            self.impulse_engine.starship = self
        
        if ship_class.max_warp:
            self.warp_drive = WarpDrive()
            self.warp_drive.starship = self

        self.override_nation = override_nation
        
        self.docked = False

        self.turn_taken = False

        self.turn_repairing = 0
        
        self.ai: Optional[BaseAi] = ai_cls(entity=self)
    
    @property
    def nation(self):
        return self.override_nation if self.override_nation else self.ship_class.nation
    
    @nation.setter
    def nation(self, value:Nation):
        
        if value != self.ship_class.nation:
            
            self.override_nation = value
        else:
            self.override_nation = None
    
    @property
    def ship_is_captured(self):
        return self.override_nation and self.override_nation is not self.ship_class.nation
    
    @property
    def hull_damage(self):
        return round(self._hull_damage)
    
    @hull_damage.setter
    def hull_damage(self, value:float):
        self._hull_damage = value
        if self._hull_damage < 0.0:
            self._hull_damage = 0.0
    
    @property
    def get_max_hull(self):
        return self.ship_class.max_hull - self._hull_damage
    
    @property
    def hull(self):
        return self._hull

    @hull.setter
    def hull(self, value):
        self._hull = round(value)
        if self._hull > self.get_max_hull:
            self._hull = self.get_max_hull

    @property
    def hull_percentage(self):
        try:
            return self.hull / self.ship_class.max_hull
        except ZeroDivisionError:
            return 0.0

    @property
    def get_sub_sector(self) -> SubSector:
        return self.game_data.grid[self.sector_coords.y][self.sector_coords.x]

    @property
    def is_automated(self):
        return self.ship_class.is_automated

    @property
    def can_be_docked_with(self):
        return not self.ship_class.is_mobile and not self.ship_class.is_automated

    def can_dock_with(self, starship: Starship, require_adjacent:bool=True):
        
        return (
            not self.ship_class.is_mobile and not self.ship_class.is_automated and starship.nation is self.nation and 
            starship.local_coords.is_adjacent(other=self.local_coords)
        ) if require_adjacent else (
            not self.ship_class.is_mobile and not self.ship_class.is_automated and starship.nation is self.nation
        )
    
    @property
    def get_dock_repair_factor(self):
        
        return self.ship_class.damage_control
    
    @property
    def ship_color(self):
        return self.nation.nation_color

    @property
    def is_enemy(self):
        return self.nation in self.game_data.scenerio.get_set_of_enemy_nations

    @property
    def is_mission_critical(self):
        return self.ship_class in self.game_data.scenerio.mission_critical_ships

    @property
    def get_combat_effectivness(self):
        
        total = (self.hull / self.ship_class.max_hull) * 2
        divisor = 1
        try:
            total += self.life_support.crew_readyness
            divisor += 1
        except AttributeError:
            pass
        try:
            total += self.beam_array.get_max_effective_beam_firepower
            divisor += 1
        except AttributeError:
            pass
        try:
            total += self.cannons.get_max_effective_cannon_firepower
            divisor += 1
        except AttributeError:
            pass
        try:
            total += self.shield_generator.get_max_effective_shields
            divisor += 1
        except AttributeError:
            pass
        try:
            total += self.torpedo_launcher.get_effective_value
            divisor += 1
        except AttributeError:
            pass
        
        return total / divisor

    @property
    def get_stragic_value(self):
        
        hull, shields, energy, crew, beam_energy, cannon_energy, torpedo_value, detection_strength, cloaking, evasion, targeting = self.ship_class.get_stragic_values

        hull_value = hull * self.hull_percentage
        
        try:
            shields_value = shields * self.shield_generator.get_effective_value
        except AttributeError:
            shields_value = 0
            
        energy_value = energy * self.power_generator.get_effective_value
        try:
            crew_value = self.life_support.crew_readyness
        except AttributeError:
            crew_value = 1
        try:
            beam_energy_value = beam_energy * self.beam_array.get_effective_value
        except AttributeError:
            beam_energy_value = 0
        try:
            cannon_energy_value = cannon_energy * self.cannons.get_effective_value
        except AttributeError:
            cannon_energy_value = 0
        try:
            torpedo_value_value = torpedo_value * self.torpedo_launcher.get_effective_value
        except AttributeError:
            torpedo_value_value = 0
        return (
            hull_value + shields_value + energy_value + crew_value + 
                beam_energy_value + cannon_energy_value + torpedo_value_value
        )

    @property
    def get_ship_value(self):
        return (self.hull + self.ship_class.max_hull) * 0.5 if self.ship_status.is_active else 0.0

    def calculate_ship_stragic_value(
        self, 
        *, 
        value_multiplier_for_destroyed:float=0.0, 
        value_multiplier_for_derlict:float=0.0, 
        value_multiplier_for_active:float=1.0
    ):
        """Calculates to point value of the ship and returns a tuple containing the maximum possible value, and the acutal value.

        Args:
            value_multiplier_for_destroyed (float, optional): How much the value of destroyed ships should be multiplied by. Defaults to 0.0.
            value_multiplier_for_derlict (float, optional): How much the value of derlict ships should be multiplied by. Defaults to 0.0.
            value_multiplier_for_active (float, optional): How much the value of active ships should be multiplied by. Defaults to 1.0.
        """
        
        def calculate_value(
            *,
            hull:float, shields:float, energy:float, crew:int, 
            beam_energy:int, cannon_energy:int, torpedo_value:int, multiplier_value:float
        ):
            
            if multiplier_value == 0.0:
                return 0.0
            
            hull_value = hull * self.hull_percentage
            shields_value = shields * self.shield_generator.get_effective_value
            energy_value = energy * self.power_generator.get_effective_value
            crew_value = crew * self.life_support.crew_readyness
            dodge_value = self.impulse_engine.get_effective_value * self.ship_class.evasion
            weapon_energy_value = beam_energy * self.beam_array.get_effective_value if beam_energy else 0
            cannon_energy_value = cannon_energy * self.cannons.get_effective_value if cannon_energy else 0
            torpedo_value_value = torpedo_value * self.torpedo_launcher.get_effective_value if torpedo_value else 0
            transporter_value = self.transporter.get_effective_value
            targeting = self.sensors.get_effective_value * self.ship_class.targeting if any(
                (weapon_energy_value, cannon_energy_value, torpedo_value_value)
            ) else 0
            
            return (
                hull_value + shields_value + energy_value + crew_value + weapon_energy_value + 
                cannon_energy_value + torpedo_value_value + dodge_value + targeting
            ) * multiplier_value
        
        hull, shields, energy, crew, beam_energy, cannon_energy, torpedo_value, detection_strength, cloaking, evasion, targeting = self.ship_class.get_stragic_values
        
        max_possible_value = sum(
            (hull, shields, energy, crew, beam_energy, cannon_energy, torpedo_value, 1), 
            start= 0.0
        )
        ship_status = self.ship_status
        
        value_used_in_calculation = (
            value_multiplier_for_destroyed if ship_status.is_destroyed else (
                value_multiplier_for_derlict if ship_status.is_recrewable else value_multiplier_for_active
            )
        )
        value_to_be_returned = calculate_value(
            hull=hull, shields=shields, energy=energy, crew=crew, beam_energy=beam_energy, 
            cannon_energy=cannon_energy, torpedo_value=torpedo_value, 
            multiplier_value=value_used_in_calculation
        )
        
        return max_possible_value, value_to_be_returned
    
    #shields, hull, energy, torps, sys_warp_drive, sysImpuls, sysPhaser, sys_shield_generator, sys_sensors, sys_torpedos
    
    def scan_for_print(self, precision: int=1):
        
        if isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be an intiger between 1 amd 100")
        if precision not in PRECISION_SCANNING_VALUES:
            raise ValueError(
                f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. It's actually value is {precision}."
            )

        def print_color(amount:float, base:float, inverse:bool=False):
            a = amount / base
            
            if inverse:
                if a <= 0.0:
                    return colors.alert_green
                if a <= 0.25:
                    return colors.lime
                if a <= 0.5:
                    return colors.alert_yellow
                if a <= 0.75:
                    return colors.orange
                return colors.alert_red
            
            if a >= 1.0:
                return colors.alert_green
            if a >= 0.75:
                return colors.lime
            if a >= 0.5:
                return colors.alert_yellow
            if a >= 0.25:
                return colors.orange
            return colors.alert_red

        hull = scan_assistant(self.hull, precision)
        energy = scan_assistant(self.power_generator.energy, precision)
        
        ship_class = self.ship_class
                
        hull_damage = scan_assistant(self.hull_damage, precision)
        
        d= {
            "hull" : (hull, print_color(hull, ship_class.max_hull)),
            "energy" : (energy, print_color(energy, ship_class.max_energy))
        }
        try:
            shields = scan_assistant(self.shield_generator.read_shields, precision)
            d["shields"] = (shields, print_color(shields, ship_class.max_shields))
        except AttributeError:
            pass
        try:
            hull_polarization = scan_assistant(self.polarized_hull.read_polarization, precision)
            d["polarization"] = (hull_polarization, colors.white)
        except AttributeError:
            pass
        if hull_damage:
            d["hull_damage"] = hull_damage, print_color(hull_damage, ship_class.max_hull)
        try:
            total_torps = tuple(self.torpedo_launcher.get_number_of_torpedos(precision))
            
            all_torps = sum([v for k,v in total_torps])
            
            d["number_of_torps"] = tuple(self.torpedo_launcher.get_number_of_torpedos(precision))
            d["torpedo_color"] = colors.white if all_torps == self.ship_class.max_torpedos else colors.planet_hostile
        except AttributeError:
            pass
        try:
            able_crew = scan_assistant(self.life_support.able_crew, precision)
            injured_crew = scan_assistant(self.life_support.injured_crew, precision)
            d["able_crew"] = (able_crew, print_color(able_crew, ship_class.max_crew))
            if injured_crew:
                d["injured_crew"] = (injured_crew, print_color(injured_crew, ship_class.max_crew, True))
        except AttributeError:
            pass
        try:
            d["cloak_cooldown"] = (
                self.cloak.cloak_cooldown, print_color(self.cloak.cloak_cooldown, ship_class.cloak_cooldown, True)
            )
        except AttributeError:
            pass
        try:
            if self.life_support.has_boarders:
                d["boarders"] = tuple(self.life_support.get_boarding_parties(self.nation, precision))
        except AttributeError:
            pass
        try:
            d["sys_impulse"] = self.impulse_engine.print_info(precision), self.impulse_engine.get_color(), self.impulse_engine.name
        except AttributeError:
            pass
        try:
            d["sys_warp_drive"] = self.warp_drive.print_info(precision), self.warp_drive.get_color(), self.warp_drive.name
        except AttributeError:
            pass
        try:
            d["sys_beam_array"] = self.beam_array.print_info(precision), self.beam_array.get_color(), self.beam_array.name
        except AttributeError:
            pass
        try:
            d["sys_cannon_weapon"] = self.cannons.print_info(precision), self.cannons.get_color(), self.cannons.name
        except AttributeError:
            pass
        try:
            d["sys_polarize"] = self.polarized_hull.print_info(precision), self.polarized_hull.get_color(), self.polarized_hull.name
        except AttributeError:
            pass
        try:
            d["sys_shield"] = self.shield_generator.print_info(precision), self.shield_generator.get_color(), self.shield_generator.name
        except AttributeError:
            pass
        d["sys_sensors"] = self.sensors.print_info(precision), self.sensors.get_color(), self.sensors.name
        try:
            d["sys_torpedos"] = self.torpedo_launcher.print_info(precision), self.torpedo_launcher.get_color(), self.torpedo_launcher.name
        except AttributeError:
            pass
        try:
            d["sys_cloak"] = self.cloak.print_info(precision), self.cloak.get_color(), self.cloak.name
        except AttributeError:
            pass
        try:
            d["sys_transporter"] = self.transporter.print_info(precision), self.transporter.get_color(), self.transporter.name
        except AttributeError:
            pass
        d["sys_warp_core"] = self.power_generator.print_info(precision), self.power_generator.get_color(), self.power_generator.name
        try:
            torps = tuple(self.torpedo_launcher.get_number_of_torpedos(precision))
            for k, v in torps:
                d[k] = v
        except AttributeError:
            pass
        return d
    
    def scan_this_ship(
        self, precision: int=1, *, scan_for_crew:bool=True, scan_for_systems:bool=True, use_effective_values=False
    )->Dict[str,Union[int,Tuple,ShipStatus,ShipClass]]:
        """Scans the ship based on the precision value.

        Args:
            precision (int, optional): Used to see how precise the scan wiil be. lower values are better. Defaults to 1.
            scan_for_crew (bool, optional): If true, dictionary enteries will be return for the able and infured crew. Defaults to True.
            scan_for_systems (bool, optional): If trun, dictionary enteries will be returbed for the systems. Defaults to True.

        Raises:
            TypeError: If precision is a float.
            ValueError: if precision is not in the following

        Returns:
            Dict[str,Union[int,Tuple,ShipStatus]]: A dictionary containing enteries for the ships hull, shield, energy, torpedos, 
        """

        if isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be an intiger between 1 amd 100")
        if precision not in PRECISION_SCANNING_VALUES:
            raise ValueError(
                f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. It's actually value is {precision}."
            )
        hull = scan_assistant(self.hull, precision)
        
        status = STATUS_ACTIVE if hull > 0 else (
            STATUS_OBLITERATED if hull < self.ship_class.max_hull * -0.5 else STATUS_HULK
        )
        d= {
            "hull" : hull,
            "energy" : scan_assistant(self.power_generator.energy, precision),
            "class" : self.ship_class
        }
        try:
            d["shields"] = scan_assistant(self.shield_generator.shields, precision)
        except AttributeError:
            pass
        try:
            d["polarization"] = scan_assistant(self.polarized_hull.polarization_amount, precision)
        except AttributeError:
            pass
        try:
            d["number_of_torps"] = tuple(self.torpedo_launcher.get_number_of_torpedos(precision))
        except AttributeError:
            pass
        if scan_for_crew:
            try:
                able_crew = scan_assistant(self.life_support.able_crew, precision)
                injured_crew = scan_assistant(self.life_support.injured_crew, precision)
                d["able_crew"] = able_crew
                d["injured_crew"] = injured_crew
                
                if status is STATUS_ACTIVE and not self.ship_class.is_automated and able_crew + injured_crew <= 0:
                    status = STATUS_DERLICT
            except AttributeError:
                pass

        try:
            d["cloak_cooldown"] = self.cloak.cloak_cooldown
        except AttributeError:
            pass

        if scan_for_systems:
            try:
                d["sys_warp_drive"] = self.warp_drive.get_info(precision)
            except AttributeError:
                pass
            try:
                d["sys_impulse"] = self.impulse_engine.get_info(precision)
            except AttributeError:
                pass
            try:
                d["sys_beam_array"] = self.beam_array.get_info(precision)
            except AttributeError:
                pass
            try:
                d["sys_cannon_weapon"] = self.cannons.get_info(precision)
            except AttributeError:
                pass
            try:
                d["sys_polarize"] = self.polarized_hull.get_info(precision)
            except AttributeError:
                pass
            try:
                d["sys_shield"] = self.shield_generator.get_info(precision)
            except AttributeError:
                pass
            d["sys_sensors"] = self.sensors.get_info(precision)
            try:
                d["sys_torpedos"] = self.torpedo_launcher.get_info(precision)
            except AttributeError:
                pass
            try:
                d["sys_cloak"] = self.cloak.get_info(precision)
            except AttributeError:
                pass
            try:
                d["sys_transporter"] = self.transporter.get_info(precision)
            except AttributeError:
                pass
            d["sys_warp_core"] = self.power_generator.get_info(precision)
            
        d["status"] = status
        try:
            torps = tuple(self.torpedo_launcher.get_number_of_torpedos(precision))
            for k, v in torps:
                d[k] = v
        except AttributeError:
            pass
        return d

    def get_random_ajacent_empty_coord(self):
        
        star_system = self.get_sub_sector
        
        ships = set(ship.local_coords.create_coords() for ship in self.game_data.grab_ships_in_same_sub_sector(self, include_self_in_ships_to_grab=True, accptable_ship_statuses={STATUS_ACTIVE,STATUS_DERLICT,STATUS_HULK}))
        
        a2 = [a_ for a_ in star_system.safe_spots if a_.is_ajacent(self.local_coords) and a_ not in ships]
        
        return choice(a2)

    def destroy(self, cause:str, *, warp_core_breach:bool=False, self_destruct:bool=False):
        """Destroys the ship. I hope this wasn't you!

        Args:
            cause (str): A description of the cause of destruction.
            warp_core_breach (bool, optional): If True, the ship will be totaly destroyed and will damage neabye craft. If False, it will leave behind wreckage. Defaults to False.
            self_destruct (bool, optional): Similar to the above, but more damaging. Defaults to False.
        """
        gd = self.game_data
        #gd.grid[self.sector_coords.y][self.sector_coords.x].removeShipFromSec(self)
        is_controllable = self.is_controllable
        #wc_value = self.sys_warp_core.get_effective_value

        if self.is_controllable:
            self.game_data.cause_of_damage = cause
        try:
            self.life_support.able_crew = 0
            self.life_support.injured_crew = 0
        except AttributeError:
            pass
        try:
            for k in self.torpedo_launcher.torps.keys():
                self.torpedo_launcher.torps[k] = 0
            self.torpedo_launcher.integrety = 0.0
        except AttributeError:
            pass
        try:
            self.shield_generator.shields = 0
            self.shield_generator.shields_up = False
            self.shield_generator.integrety = 0.0
        except AttributeError:
            pass
        try:
            self.polarized_hull.polarization_amount = 0
            self.polarized_hull.is_polarized = False
            self.polarized_hull.integrety = 0.0
        except AttributeError:
            pass
        self.power_generator.energy = 0
        self.power_generator.integrety = 0
        try:
            self.warp_drive.integrety = 0.0
        except AttributeError:
            pass
        try:
            self.beam_array.integrety = 0.0
        except AttributeError:
            pass
        try:
            self.cannons.integrety = 0.0
        except AttributeError:
            pass
        try:
            self.impulse_engine.integrety = 0.0
        except AttributeError:
            pass
        self.sensors.integrety = 0.0
        try:
            self.cloak.cloak_status = CloakStatus.INACTIVE
            self.cloak.integrety = 0.0
        except AttributeError:
            pass
        try:
            self.transporter.integrety = 0.0
        except AttributeError:
            pass

        if is_controllable:
            gd.engine.message_log.print_messages = False

        if warp_core_breach or self_destruct:
        
            self.warp_core_breach(self_destruct)
            self.hull = -self.ship_class.max_hull
                
        if self is self.game_data.selected_ship_planet_or_star:
            self.game_data.selected_ship_planet_or_star = None
        
        self.get_sub_sector.destroy_ship(self)
        
    def warp_core_breach(self, self_destruct=False):

        shipList = self.game_data.grab_ships_in_same_sub_sector(self)

        for s in shipList:
            
            if s is self:
                continue
            
            damage = self.warp_core_breach_damage_based_on_distance(s, self_destruct)

            if damage > 0:

                s.take_damage(
                    damage, 
f'Caught in the {"auto destruct radius" if self_destruct else "warp core breach"} of the {self.name}', 
                    damage_type=DAMAGE_EXPLOSION
                )

    def warp_core_breach_damage_based_on_distance(self, target:Starship, self_destruct:bool=False):
        
        distance = self.local_coords.distance(coords=target.local_coords)
        
        try:
            damage = inverse_square_law(
                base=self.ship_class.warp_breach_damage * ((4/3) if self_destruct else 1), 
                distance=distance
            )
        except ZeroDivisionError:
            damage = self.ship_class.warp_breach_damage
        
        return round(damage)

    def simulate_self_destruct(
        self, target:Starship, *, scan:Optional[Dict]=None, number_of_simulations:int=1, 
        simulate_systems:bool=False, simulate_crew:bool=False
        ):
        """Calculates the damage that this ship would inflict on the target if it were auto-destructed.

        Args:
            target (Starship): The ship that is going to be 'attacked'.
            scan (Optional[Dict], optional): A scan of the ship, if not present, one will be generated. Defaults to None.
            number_of_simulations (int, optional): How many times the simulation will be preformed. Defaults to 1.
            simulate_systems (bool, optional): If true, damage to the systems will be taken into account. Defaults to False.
            simulate_crew (bool, optional): If True, crew fatalities and injuries will be taken into account. Defaults to False.

        Returns:
            Tuple[float, float, float, float, float, float]: A tuple containing floats
        """
        
        precision = self.sensors.determin_precision
        
        scan = scan if scan else target.scan_this_ship(
            precision, scan_for_crew=simulate_crew, scan_for_systems=simulate_systems
        )
        amount = self.warp_core_breach_damage_based_on_distance(target)
        
        averaged_shield = 0
        averaged_hull = 0
        averaged_shield_damage = 0
        averaged_hull_damage = 0
        averaged_crew_readyness = 0
        
        scan_target_crew = not target.ship_class.is_automated and simulate_crew
                
        for i in range(number_of_simulations):
        
            new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage,             torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage, polarized_hull_damage = self.calculate_damage(
                amount, scan_dict=scan, precision=precision, calculate_crew=simulate_crew, 
                calculate_systems=simulate_systems, damage_type=DAMAGE_EXPLOSION
            )
            averaged_shield += new_shields
            averaged_hull += new_hull
            averaged_shield_damage += shields_dam
            averaged_hull_damage += hull_dam
            
            if scan_target_crew:
                
                averaged_crew_readyness += target.life_support.caluclate_crew_readyness(
                    scan["able_crew"], scan["injured_crew"]
                )
        averaged_shield /= number_of_simulations
        averaged_hull /= number_of_simulations
        averaged_shield_damage /= number_of_simulations
        averaged_hull_damage /= number_of_simulations
        
        if scan_target_crew:
            averaged_crew_readyness /= number_of_simulations
        else:
            averaged_crew_readyness = 1.0
                
        return averaged_shield, averaged_hull, averaged_shield_damage, averaged_hull_damage, averaged_hull <= 0, averaged_crew_readyness

    @property
    def ship_status(self):
        """Checks if the ship is relitivly intact. 
        
        If a ship is destroyed but intact ship, then it is a ruined hulk, like the ones we saw in aftermath of the battle of Wolf 389. 

        Checks is the ship has no living crew, and returns True if it does not, False if it does.

        Returns:
            bool: Returns True if the hull is greater then or equal to half the negitive max hit points, and less then or equal to zero.
        """
        try:
            if self.warp_drive.is_at_warp:
                return STATUS_AT_WARP
        except AttributeError:
            pass
        if self.hull < self.ship_class.max_hull * -0.5:
            return STATUS_OBLITERATED
        if self.hull <= 0:
            return STATUS_HULK
        try:            
            if self.life_support.is_derlict:
                return STATUS_DERLICT
        except AttributeError:
            pass
        try:
            if self.cloak.cloak_is_turned_on:
                return STATUS_CLOAKED if self.cloak.cloak_status == CloakStatus.ACTIVE else STATUS_CLOAK_COMPRIMISED
        except AttributeError:
            pass
        return STATUS_ACTIVE
            
    def ram(self, other_ship:Starship, intentional_ram_attempt:bool):
        """Prepare for RAMMING speed!

        The ship will attempt to ram another ship.

        Args:
            other_ship (Starship): The ship that the attacker will atempt to ram.
            intentional_ram_attempt (bool): If True,
        """
        self_status = self.ship_status
        other_status = other_ship.ship_status
        
        try:
            self_hp = (self.shield_generator.shields if self_status.do_shields_work else 0) + self.hull
        except AttributeError:
            self_hp = self.hull
        try:
            other_hp = (other_ship.shield_generator.shields if other_status.do_shields_work else 0) + other_ship.hull
        except AttributeError:
            other_hp = other_ship.hull
        
        self_damage = self_hp + self.ship_class.max_hull * 0.5
        #other_damage = other_hp + other_ship.ship_class.max_hull * 0.5
        try:
            crew_readyness = self.life_support.crew_readyness
        except AttributeError:
            crew_readyness = 1
        try:
            target_crew_readyness = other_ship.life_support.crew_readyness
        except AttributeError:
            target_crew_readyness = 1

        hit_roll = self.roll_to_hit(
            other_ship, 
            systems_used_for_accuray=[self.impulse_engine.get_effective_value, self.ship_class.evasion],
            damage_type=DAMAGE_RAMMING,
            crew_readyness=crew_readyness,
            target_crew_readyness=target_crew_readyness
        )
        if hit_roll:

            self.take_damage(
                other_hp, f'Rammed the {self.name}', damage_type=DAMAGE_EXPLOSION
            )
            other_ship.take_damage(
                self_damage, f'Rammed by the {self.name}', damage_type=DAMAGE_EXPLOSION
            )
        if intentional_ram_attempt and (
            not hit_roll or (
                self.ship_status is not STATUS_OBLITERATED and other_ship.ship_status is not STATUS_OBLITERATED
            )
        ):
            ships_in_same_sector = self.game_data.grab_ships_in_same_sub_sector(
                other_ship, accptable_ship_statuses={
                    STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
                }
            )
            bad_spots = [
                ship.local_coords.create_coords() for ship in ships_in_same_sector if 
                other_ship.local_coords.is_adjacent(other=ship.local_coords)
            ]
            safe_spots = [
                spot for spot in self.get_sub_sector.safe_spots if other_ship.local_coords.is_adjacent(other=spot) and
                spot not in bad_spots
            ]
            spot = choice(safe_spots)
            
            self.local_coords.x = spot.x
            self.local_coords.y = spot.y

        return hit_roll

    def calculate_damage(
        self, amount:int, *, 
        scan_dict:Optional[Dict]=None, 
        precision:int=1, 
        calculate_crew:bool=True, 
        calculate_systems:bool=True,  
        damage_type:DamageType,
        use_effective_values:bool=True
    ):
        """Calculates the result of damage inflicted on this ship

        Args:
            amount (int): The amount of damage
            damage_type (DamageType): The type of damage
            scan_dict (Optional[Dict], optional): A dictionary containing values. Defaults to None.
            precision (int, optional): This is only used if scan_dict is None. Defaults to 1.
            calculate_crew (bool, optional): If true, the calculation will take into account the result of killed/injured crewmembers. Defaults to True.
            calculate_systems (bool, optional): If true, the calculation will take into account the result of damaged. Defaults to True.
            use_effective_values (bool, optional): If scan_dict is None, this value will be passed in the scan_this_ship method call. Defaults to True.

        Returns:
            Tuple[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]: _description_
        """
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
            amount = round(amount * uniform(1.0 - random_varation, 1.0))
        
        old_scan = scan_dict if scan_dict else self.scan_this_ship(
            precision, scan_for_crew=calculate_crew, 
            scan_for_systems=calculate_systems, 
            use_effective_values=use_effective_values
        )
        try:
            current_shields:int = old_scan["shields"]
        except KeyError:
            current_shields = 0
        try:
            polarization:int = old_scan["polarization"]
            
            if calculate_systems:
                
                polarization = round(polarization * (
                    ajust_system_integrity(
                        old_scan["sys_polarize"]
                    ) if use_effective_values else old_scan["sys_polarize"]
                ))
        except KeyError:
            polarization = 0
        current_hull:int = old_scan["hull"]
                
        old_status = self.ship_status
        
        is_hulk = current_hull < 0
        
        try:
            is_derlict = old_scan["able_crew"] + old_scan["injured_crew"] <= 0
        except KeyError:
            is_derlict = False
        try:
            shield_effectiveness = ajust_system_integrity(old_scan["sys_shield"]) if use_effective_values else old_scan["sys_shield"]
        except KeyError:
            shield_effectiveness = 1
        
        shields_are_already_down = shield_effectiveness <= 0 or current_shields <= 0 or not old_status.do_shields_work or not self.shield_generator.shields_up
        
        shields_dam = 0
        armorDam = amount
        hull_dam = amount
        
        shield_dam_multi = damage_type.damage_vs_shields_multiplier

        armorHullDamMulti = (
            damage_type.damage_vs_no_shield_multiplier 
            if shields_are_already_down else damage_type.damage_vs_hull_multiplier
        ) 
        try:
            shields_percentage = current_shields / self.ship_class.max_shields
        except ZeroDivisionError:
            shields_percentage = 0
            shields_are_already_down = True
            
        bleedthru_factor = min(shields_percentage + 0.5, 1.0)
        
        if shields_are_already_down:
            
            hull_dam = amount * armorHullDamMulti
        else:
            to_add = 0
            shields_dam = amount * bleedthru_factor * shield_dam_multi
            if shields_dam > current_shields:
                to_add = shields_dam - current_shields
                
                shields_dam = current_shields
            amount *= (1 - bleedthru_factor)
            amount += to_add
            hull_dam = amount * armorHullDamMulti
        
        hull_dam = round(calculate_polarization(hull_dam, polarization))
        
        new_shields = scan_assistant(current_shields - shields_dam, precision) if shields_dam > 0 else current_shields
        new_hull = scan_assistant(current_hull - hull_dam, precision) if hull_dam > 0 else current_hull
        
        hull_damage_as_a_percent = hull_dam / self.ship_class.max_hull
        try:
            new_shields_as_a_percent = new_shields / self.ship_class.max_shields
        except ZeroDivisionError:
            new_shields_as_a_percent = 0
        new_hull_as_a_percent = new_hull / self.ship_class.max_hull
        
        killed_outright = 0
        killed_in_sickbay = 0
        wounded = 0
        
        if calculate_crew and not is_derlict and not is_hulk:
            
            crew_killed = hull_dam > 0 and new_hull_as_a_percent < random() and not self.ship_class.is_automated
            
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
                
                killed_outright = round(self.life_support.able_crew * percentage_of_able_crew_killed)
                killed_in_sickbay = round(0.5 * self.life_support.able_crew * percentage_of_injured_crew_killed)
                wounded = round(self.life_support.able_crew * percentage_of_able_crew_wounded)
        
        shield_sys_damage = 0
        energy_weapons_sys_damage = 0
        cannon_sys_damage = 0
        impulse_sys_damage = 0
        warp_drive_sys_damage = 0
        sensors_sys_damage = 0
        torpedo_sys_damage = 0
        warp_core_sys_damage = 0
        cloak_sys_damage = 0
        transporter_sys_damage = 0
        polarized_hull_damage = 0
        
        if calculate_systems and not is_hulk:
            chance_to_damage_system = damage_type.chance_to_damage_system
            
            systems_damaged = hull_dam > 0 and new_hull_as_a_percent < uniform(
                hull_damage_as_a_percent, 1.25 + hull_damage_as_a_percent)
            
            if systems_damaged:
                system_damage_chance = damage_type.damage_chance_vs_systems_multiplier
                
                def chance_of_system_damage():
                    # this is cumbersome. A better way may be random() * chance_to_damage_system > (old_hull_as_a_percent + new_hull_as_a_percent) * 0.5
                    return uniform(
                        hull_damage_as_a_percent, chance_to_damage_system + hull_damage_as_a_percent
                        ) > new_hull_as_a_percent
                
                def random_system_damage():
                    return uniform(0.0, system_damage_chance * hull_damage_as_a_percent)
                
                if self.ship_class.max_shields and chance_of_system_damage():
                    shield_sys_damage = random_system_damage()
                    
                if self.ship_class.max_beam_energy and chance_of_system_damage():
                    energy_weapons_sys_damage = random_system_damage()
                    
                if self.ship_class.max_cannon_energy and chance_of_system_damage():
                    cannon_sys_damage = random_system_damage()
                    
                if self.ship_class.evasion and chance_of_system_damage():
                    impulse_sys_damage = random_system_damage()
                    
                if self.ship_class.max_warp and chance_of_system_damage():
                    warp_drive_sys_damage = random_system_damage()
                    
                if chance_of_system_damage():
                    sensors_sys_damage = random_system_damage()
                    
                if self.ship_class.max_torpedos and chance_of_system_damage():
                    torpedo_sys_damage = random_system_damage()
                    
                if chance_of_system_damage():
                    warp_core_sys_damage = random_system_damage()
                    
                if self.ship_class.cloak_strength and chance_of_system_damage():
                    cloak_sys_damage = random_system_damage()
                
                if self.ship_class.max_crew and chance_of_system_damage():
                    transporter_sys_damage = random_system_damage()
                
                if self.ship_class.polarized_hull and chance_of_system_damage():
                    polarized_hull_damage = random_system_damage()
                
        return (
            new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, 
            new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, 
            impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, 
            warp_core_sys_damage, 
            energy_weapons_sys_damage, cannon_sys_damage, 
            torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage, polarized_hull_damage
        )

    def take_damage(self, amount, text, *, damage_type:DamageType):
        
        game_data = self.game_data
        message_log = game_data.engine.message_log
        
        old_ship_status = self.ship_status
        
        ship_originaly_destroyed = old_ship_status in {STATUS_HULK, STATUS_OBLITERATED}
        
        new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage, polarized_hull_damage = self.calculate_damage(amount, damage_type=damage_type)
        
        ship_destroyed = new_hull < 0
        
        ship_is_player = self.is_controllable

        pre = 1 if ship_is_player else self.game_data.player.sensors.determin_precision
        
        old_scan = self.scan_this_ship(
            pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player, use_effective_values=True
        )
        originally_derlict = old_ship_status == STATUS_DERLICT
        
        is_derlict = originally_derlict
        try:
            self.shield_generator.shields = new_shields
        except AttributeError:
            pass
        self.hull = new_hull
        
        self.hull_damage += hull_dam * 0.15
        try:
            self.life_support.injuries_and_deaths(wounded, killed_outright, killed_in_sickbay)
            
            if self.life_support.is_derlict:
                is_derlict = True
            
        except AttributeError:
            pass            
        try:
            self.shield_generator.integrety -= shield_sys_damage
        except AttributeError:
            pass
        try:
            self.polarized_hull.integrety -= polarized_hull_damage
        except AttributeError:
            pass
        try:
            self.beam_array.integrety -= energy_weapons_sys_damage
        except AttributeError:
            pass
        try:
            self.cannons.integrety -= cannon_sys_damage
        except AttributeError:
            pass
        try:
            self.impulse_engine.integrety -= impulse_sys_damage
        except AttributeError:
            pass
        try:
            self.shield_generator.integrety -= shield_sys_damage
        except AttributeError:
            pass
        self.sensors.integrety -= sensors_sys_damage
        try:
            self.warp_drive.integrety -= warp_drive_sys_damage
        except AttributeError:
            pass
        try:
            self.torpedo_launcher.integrety -= torpedo_sys_damage
        except AttributeError:
            pass
        try:
            self.transporter.integrety -= transporter_sys_damage
        except AttributeError:
            pass
        
        new_ship_status = self.ship_status
        
        new_scan = self.scan_this_ship(pre, scan_for_systems=ship_is_player, scan_for_crew=ship_is_player)
        
        #name = "our" if ship_is_player else f"the {self.name}'s"
        
        #name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
        #name_second_occ = "our" if ship_is_player else f"the {self.name}'s"
                
        if self.turn_repairing > 0:
            self.turn_repairing -= 1
        
        if not ship_destroyed:
            
            try:
                old_shields = old_scan["shields"] if old_ship_status.do_shields_work else 0
            
                newer_shields = new_scan['shields'] if new_ship_status.do_shields_work else 0
            except KeyError:
                old_shields = 0
                
                newer_shields = 0
            
            old_hull = old_scan["hull"]
            
            newer_hull = new_scan["hull"]
            
            try:
                scaned_shields_percentage = newer_shields / self.ship_class.max_shields
            except ZeroDivisionError:
                scaned_shields_percentage = 0
            
            shield_status = "holding" if scaned_shields_percentage > 0.9 else (
                f"at {scaned_shields_percentage:.0%}" if newer_shields > 0 else "down")
            
            shields_are_down = newer_shields == 0
            
            #shields_just_got_knocked_down = old_shields > 0 and shields_are_down
            
            shields_are_already_down = old_shields == 0 and shields_are_down
            
            old_hull_percent = old_hull / self.ship_class.max_hull
            newer_hull_hull_percent = newer_hull / self.ship_class.max_hull
            
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
                message_log.add_message(" ".join(message_to_print),fg)
                
            elif self.ship_class.max_shields:
                name_first_occ = "Our" if ship_is_player else f"The {self.name}'s"
                message_log.add_message(f"{name_first_occ} shields are {shield_status}." )
            
            if old_ship_status.is_active and new_ship_status.is_recrewable and not ship_is_player:
                
                message_log.add_message("Captain, I am not reading any life signs.")
            
            if ship_is_player:
                
                if not self.ship_class.is_automated:
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
                    message_log.add_message(f'{self.ship_class.energy_weapon.beam_name} emitters damaged.')
                    
                if cannon_sys_damage > 0:
                    message_log.add_message(f'{self.ship_class.energy_weapon.cannon_name} damaged.')
                    
                if sensors_sys_damage > 0:
                    message_log.add_message('Sensors damaged.')
                            
                if shield_sys_damage > 0:
                    message_log.add_message('Shield generator damaged.')
                
                if warp_core_sys_damage > 0:
                    message_log.add_message(
                        'Warp core damaged.' if self.ship_class.max_warp else 'Power generator damaged.'
                    )
                            
                if torpedo_sys_damage > 0:
                    message_log.add_message('Torpedo launcher damaged.')
                
                if cloak_sys_damage > 0:
                    message_log.add_message("Cloaking device damaged.")
                
        elif not ship_originaly_destroyed:
            wc_breach = ((not old_ship_status.is_destroyed and new_ship_status is STATUS_OBLITERATED) or (
                    random() > 0.85 and random() > self.power_generator.get_effective_value and 
                    random() > self.power_generator.integrety) or self.power_generator.integrety == 0.0)
            
            if ship_is_player:
                
                if wc_breach:
                    message_log.add_message("Warp core breach iminate!", colors.orange)
                
                message_log.add_message("Abandon ship, abandon ship, all hands abandon ship...", colors.red)
            else:
                message_log.add_message(
                    f"The {self.name} {'suffers a warp core breach' if wc_breach else 'is destroyed'}!"
                )
            self.destroy(text, warp_core_breach=wc_breach)
        elif old_ship_status == STATUS_HULK and not ship_is_player:
            
            message_log.add_message(
                f"The remains of the {self.proper_name} disintrate under the onslaght!" if 
                new_ship_status == STATUS_OBLITERATED else 
                f"Peices of the {self.proper_name} break off."
            )
        
    def handle_repair_and_energy_consumption(self):
        """This method handles repairing the ship after each turn, as well as energy consuption from have the shields up or the cloak turned on. Here's how it works:
        
        If the ship is not being fired on, manuivering, or firing topredos, then some rudimentory repairs are going to be done. Also, the ships batteries will be slowly be refilled by the warp core.
        
        However, if the ship focuses its crews attention soley on fixing the ship (by using the RepairOrder order), then the repairs are going to be much more effective. For each consuctive turn the ship's crew spends on fixing things up, a small but clumitive bonus is applied. The ships batteries will also recharge much more quickly. However, the cost in energy from having the shields up or the cloak turned on will be subtracted from the recharge amount.
        
        If the ship is docked/landed at a friendly planet, then the ship will benifit even more from the expertise of the local eneriners.
        """
        
        repair_factor:RepairStatus = REPAIR_DOCKED if self.docked else (
            REPAIR_DEDICATED if self.turn_repairing else REPAIR_PER_TURN
        )
        time_bonus = 1.0 + (self.turn_repairing / 25.0)
        energy_regeneration_bonus = 1.0 + (self.turn_repairing / 5.0)
        
        energy_cost = 0
        try:
            energy_cost += self.polarized_hull.get_energy_cost_per_turn
        except AttributeError:
            pass
        try:
            energy_cost += self.cloak.get_energy_cost_per_turn
        except AttributeError:
            pass
        try:
            energy_cost += self.shield_generator.get_energy_cost_per_turn
        except AttributeError:
            pass
        try:
            crew_readyness = self.life_support.crew_readyness
        except AttributeError:
            crew_readyness = 1

        repair_amount = self.ship_class.damage_control * crew_readyness * time_bonus

        hull_repair_factor = repair_amount * repair_factor.hull_repair
        
        system_repair_factor = repair_amount * repair_factor.system_repair
        
        energy_rengerated_this_turn = (
            repair_factor.energy_regeration * self.power_generator.get_effective_value * 
            energy_regeneration_bonus * self.ship_class.power_generated_per_turn
        ) - energy_cost
        
        self.power_generator.energy += energy_rengerated_this_turn

        if not self.ship_class.is_automated:
            self.life_support.heal_crew(0.2, randint(2, 5))
            
        repair_amount = hull_repair_factor * uniform(0.5, 1.25) * self.ship_class.max_hull
        
        perm_hull_repair = ceil(repair_amount * repair_factor.repair_permanent_hull_damage)

        self.hull_damage -= perm_hull_repair
        self.hull += repair_amount
        
        self.sensors.integrety += system_repair_factor * (0.5 + random() * 0.5)
        try:
            self.warp_drive.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
        try:
            self.impulse_engine.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
        try:
            self.beam_array.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
        try:
            self.cannons.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
        try:
            self.shield_generator.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
        try:
            self.polarized_hull.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except:
            pass
        try:
            self.power_generator.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
        try:
            self.transporter.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
        try:            
            self.torpedo_launcher.integrety += system_repair_factor * (0.5 + random() * 0.5)
        except AttributeError:
            pass
    
    def roll_to_hit(
        self, enemy:Starship, *, 
        systems_used_for_accuray:Iterable[float], precision:int=1, 
        estimated_enemy_impulse:Optional[float]=None, damage_type:DamageType, crew_readyness:float, target_crew_readyness:float
    ):
        """A method that preforms a number of calcuations to see if an attack roll succeded or not.

        Args:
            enemy (Starship): The target that the attacker will be rolling against.
            systems_used_for_accuray (Iterable[float]): An iterable of floats. Often, these will be the effective value of the sensors system, and another system such as cannons, torpedos, or beam arrays.
            damage_type (DamageType): The type of damage. This must be onw of the DamageType constants.
            crew_readyness (float): The readyness of the crew of the attacking ship.
            target_crew_readyness (float): The readyness of the crew of the defending ship.
            precision (int, optional): The precision that is used to determin the enemy impulse (see below). Defaults to 1.
            estimated_enemy_impulse (Optional[float], optional): This value is used to determin the defenders chance of evading the attack. If not present, then it will be estimated using the precision argument. Defaults to None.

        Returns:
            bool: Returns True if the attack hit the target ship, False if it missed.
        """
        assert damage_type is not DAMAGE_EXPLOSION
        
        enemy_ship_status = enemy.ship_status
        
        if not enemy_ship_status.is_active:
            
            estimated_enemy_impulse = 0.0
        
        elif estimated_enemy_impulse is None:
            
            estimated_enemy_impulse = enemy.impulse_engine.get_info(
                precision, True
            ) * enemy.ship_class.evasion * target_crew_readyness
        else:
            estimated_enemy_impulse *= enemy.ship_class.evasion * target_crew_readyness
        
        # ramming an imobile object always works!
        if damage_type.autohit_if_target_cant_move and estimated_enemy_impulse == 0.0:
            return True
        
        enemy_size = enemy.ship_class.size
        
        distance_penalty = (
            damage_type.accuracy_loss_per_distance_unit * self.local_coords.distance(coords=enemy.local_coords)
        ) if damage_type.accuracy_loss_per_distance_unit > 0 else 0.0
                
        distance_penalty += damage_type.flat_accuracy_loss
        
        distance_penalty /= enemy_size
        
        deffence_value = (estimated_enemy_impulse + distance_penalty) * (1 if enemy_ship_status.is_visible else 8)
        
        targeting = (sum(systems_used_for_accuray) / len(systems_used_for_accuray)) * self.ship_class.targeting
        
        attack_value = crew_readyness * targeting * (1 if enemy_ship_status.is_visible else 0.125)
        
        return attack_value + random() > deffence_value
    
    def attack_energy_weapon(self, enemy:Starship, amount:float, energy_cost:float,  damage_type:DamageType):
        
        assert damage_type in {DAMAGE_BEAM, DAMAGE_CANNON}
        
        assert self.beam_array.is_opperational
        
        gd = self.game_data
                
        attacker_is_player = self is self.game_data.player
        target_is_player = not attacker_is_player and enemy is self.game_data.player

        self.power_generator.energy-=energy_cost
                        
        gd.engine.message_log.add_message(
            f"Firing on the {enemy.name}!" 
            if attacker_is_player else 
            f"The {self.name} has fired on {'us' if target_is_player else f'the {enemy.name}'}!"
        )
        try:
            crew_readyness=self.life_support.crew_readyness
        except AttributeError:
            crew_readyness=1
        try:
            target_crew_readyness=enemy.life_support.crew_readyness
        except AttributeError:
            target_crew_readyness=1
        
        if self.roll_to_hit(
            enemy, 
            estimated_enemy_impulse=-1.0, 
            systems_used_for_accuray=(
                self.beam_array.get_effective_value,
                self.sensors.get_effective_value
            ),
            damage_type=damage_type,
            crew_readyness=crew_readyness,
            target_crew_readyness=target_crew_readyness
        ):
            target_name = "We're" if target_is_player else f'The {enemy.name} is'

            gd.engine.message_log.add_message(
                f"Direct hit on {enemy.name}!" if attacker_is_player else
                f"{target_name} hit!", fg=colors.orange
            )
            enemy.take_damage(
                amount * self.beam_array.get_effective_value, 
                f'Destroyed by a {self.ship_class.energy_weapon.beam_name} hit from the {self.name}.', 
                damage_type=damage_type
            )
            return True
        else:
            gd.engine.message_log.add_message("We missed!" if attacker_is_player else "A miss!")

        return False

    def attack_torpedo(self, gd:GameData, enemy:Starship, torp:Torpedo):
        
        assert self.torpedo_launcher.is_opperational
        
        gd = self.game_data
        
        try:
            crew_readyness = self.life_support.crew_readyness
        except AttributeError:
            crew_readyness = 1
        try:
            target_crew_readyness = enemy.life_support.crew_readyness
        except AttributeError:
            target_crew_readyness = 1
        
        if self.roll_to_hit(
            enemy, 
            systems_used_for_accuray=(
                self.sensors.get_effective_value,
                self.torpedo_launcher.get_effective_value
            ),
            damage_type=DAMAGE_TORPEDO,
            crew_readyness = crew_readyness,
            target_crew_readyness = target_crew_readyness
        ):
            gd.engine.message_log.add_message(f'{enemy.name} was hit by a {torp.name} torpedo from {self.name}.')

            enemy.take_damage(
                torp.damage, f'Destroyed by a {torp.name} torpedo hit from the {self.name}', 
                damage_type=DAMAGE_TORPEDO
            )
            return True
        gd.engine.message_log.add_message(f'A {torp.name} torpedo from {self.name} missed {enemy.name}.')
        return False
    
    @property
    def is_controllable(self):
        return self is self.game_data.player
    
    def simulate_torpedo_hit(
        self, target:Starship, 
        torpdeo:Torpedo,
        number_of_simulations:int, 
        *, 
        times_to_fire:int,
        simulate_systems:bool=False, 
        simulate_crew:bool=False,
        use_effective_values:bool=False,
        target_scan:Optional[Dict[str,Union[Tuple,int,ShipStatus,ShipClass]]]
    ):
        precision = self.sensors.determin_precision
        
        target_scan = target_scan if target_scan else target.scan_this_ship(
            precision, 
            scan_for_crew=simulate_crew, 
            scan_for_systems=simulate_systems, 
            use_effective_values=use_effective_values
        )
        ship_class = target_scan["class"]
        
        damage = torpdeo.damage

        total_shield_dam = 0
        total_hull_dam = 0
        
        averaged_hull = 0
        averaged_shields = 0
        averaged_crew_readyness = 0
        
        number_of_ship_kills = 0
        
        number_of_crew_kills = 0
        try:
            crew_readyness = self.life_support.crew_readyness
        except AttributeError:
            crew_readyness = 1
        
        scan_target_crew = not target.ship_class.is_automated and simulate_crew        

        for s in range(number_of_simulations):
            
            new_scan = copy(target_scan)
            
            new_hull = new_scan["hull"]
            new_shields = new_scan["shields"]
            
            hull_dam  = 0
            shield_dam = 0
            
            for attack in range(times_to_fire):
                try:
                    target_crew_readyness = target.life_support.caluclate_crew_readyness(
                        new_scan["able_crew"], new_scan["injured_crew"]
                    ) if scan_target_crew else 1.0
                except AttributeError:
                    target_crew_readyness = 1.0
                except KeyError:
                    target_crew_readyness = 1.0
                try:
                    estimated_enemy_impulse = (ajust_system_integrity(
                        new_scan["sys_impulse"]
                    ) if use_effective_values else new_scan["sys_impulse"])
                except KeyError:
                    estimated_enemy_impulse = 1.0 if ship_class.evasion else 0.0
                
                if self.roll_to_hit(
                    target, 
                    estimated_enemy_impulse=estimated_enemy_impulse, 
                    systems_used_for_accuray=(
                        self.sensors.get_effective_value,
                        self.torpedo_launcher.get_effective_value
                    ),
                    damage_type=DAMAGE_TORPEDO,
                    crew_readyness=crew_readyness,
                    target_crew_readyness=target_crew_readyness
                ):
                    new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage, polarized_hull_damage = target.calculate_damage(
                        damage, precision=precision, calculate_crew=simulate_crew, 
                        calculate_systems=simulate_systems, scan_dict=new_scan, damage_type=DAMAGE_TORPEDO
                    )
                    new_scan["shields"] = new_shields
                    new_scan["hull"] = new_hull
                    
                    shield_dam += shields_dam
                    hull_dam += hull_dam
                    
                    if simulate_systems:
                        
                        new_scan["sys_impulse"] -= impulse_sys_damage
                        new_scan["sys_shield"] -= shield_sys_damage
                        new_scan["sys_warp_drive"] -= warp_drive_sys_damage
                        new_scan["sys_warp_core"] -= warp_core_sys_damage
                        new_scan["sys_polarize"] -= polarized_hull_damage
                                                
                    if scan_target_crew:
                        
                        new_scan["able_crew"] -= wounded + killed_outright
                        new_scan["injured_crew"] += wounded - killed_in_sickbay
                        
                        target_crew_readyness = target.life_support.caluclate_crew_readyness(
                            new_scan["able_crew"], new_scan["injured_crew"]
                        )
            total_shield_dam += shield_dam
            total_hull_dam += hull_dam
            
            if new_hull <= 0:
                number_of_ship_kills +=1
            
            averaged_hull += new_scan["hull"]
            averaged_shields += new_scan["shields"]
            
            if scan_target_crew:
                _crew_readyness = target.life_support.caluclate_crew_readyness(
                    new_scan["able_crew"], new_scan["injured_crew"]
                )
                if _crew_readyness == 0.0:
                    number_of_crew_kills += 1
        
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        total_shield_dam /= number_of_simulations
        total_hull_dam /= number_of_simulations
        
        if scan_target_crew:
            averaged_crew_readyness /= number_of_simulations
        else:
            averaged_crew_readyness = 1.0
        
        return averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, number_of_ship_kills / number_of_simulations, number_of_crew_kills / number_of_simulations, averaged_crew_readyness

    def simulate_energy_hit(
        self, target:Starship, number_of_simulations:int, energy:float, cannon:bool=False, 
        *, 
        simulate_systems:bool=False, 
        simulate_crew:bool=False, 
        use_effective_values:bool=False,
        target_scan:Optional[Dict[str,Union[Tuple,int,ShipStatus,ShipClass]]]
    ):
        """Run a number of simulations of energy weapon hits against the target ship and returns the avaraged result.

        Args:
            target (Starship): The target ship.
            number_of_simulations (int): How many simulations will be run. High is mroe accurate.
            energy (float): The amound of energy used in the attack.
            cannon (bool, optional): If true, it will simulat a cannon attack. Defaults to False.
            simulate_systems (bool, optional): If true, systems damage will be taken into account. Defaults to False.
            simulate_crew (bool, optional): If true, crew deaths and injuries will be taken into account. Defaults to False.

        Returns:
            tuple[float, float, float, float, float, float, float]: A tuple containing float values for the following: averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_number_of_ship_kills, averaged_number_of_crew_kills, averaged_crew_readyness
        """
        precision = self.sensors.determin_precision

        target_scan = target_scan if target_scan else target.scan_this_ship(
            precision, 
            scan_for_systems=simulate_systems, 
            scan_for_crew=simulate_crew, 
            use_effective_values=use_effective_values
        )
        ship_class = target_scan["class"]
        try:
            targ_shield = target_scan["shields"]
        except KeyError:
            targ_shield = 0
            
        targ_hull = target_scan["hull"]

        total_shield_dam = 0
        total_hull_dam = 0
        
        averaged_shields = 0
        averaged_hull = 0
        
        averaged_crew_readyness = 0
        
        number_of_ship_kills = 0
        
        number_of_crew_kills = 0
        
        damage_type, _amount = (
            DAMAGE_CANNON, self.cannons.get_max_effective_cannon_firepower
        ) if cannon else (
            DAMAGE_BEAM, self.beam_array.get_max_effective_beam_firepower
        )
        amount = min(self.power_generator.energy, _amount, energy)
        try:
            crew_readyness = self.life_support.crew_readyness
        except AttributeError:
            crew_readyness = 1
        
        scan_target_crew = not target.ship_class.is_automated and simulate_crew
        try:
            target_crew_readyness = target.life_support.caluclate_crew_readyness(
                target_scan["able_crew"], target_scan["injured_crew"]
            ) if scan_target_crew else 1.0
        except AttributeError:
            target_crew_readyness = 1.0
        except KeyError:
            target_crew_readyness = 1.0
        try:
            estimated_enemy_impulse = (ajust_system_integrity(
                target_scan["sys_impulse"]
            ) if use_effective_values else target_scan["sys_impulse"])
        except KeyError:
            estimated_enemy_impulse = 1.0 if ship_class.evasion else 0.0
                
        for i in range(number_of_simulations):
            
            if self.roll_to_hit(
                target, 
                precision=precision, 
                systems_used_for_accuray=(
                    self.sensors.get_effective_value,
                    self.beam_array.get_effective_value
                ),
                damage_type=damage_type,
                crew_readyness=crew_readyness,
                target_crew_readyness=target_crew_readyness
            ):
                new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage,warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage, polarized_hull_damage = target.calculate_damage(
                    amount, precision=precision, calculate_crew=scan_target_crew, 
                    calculate_systems=simulate_systems, 
                    use_effective_values=use_effective_values,
                    scan_dict=target_scan, damage_type=damage_type
                )
                averaged_shields += new_shields
                averaged_hull += new_hull
                total_shield_dam += shields_dam
                total_hull_dam += hull_dam
                
                if new_hull <= 0:
                    number_of_ship_kills+=1
                
                if scan_target_crew:
                    able_crew = target_scan["able_crew"] - (wounded + killed_outright)
                    injured_crew = target_scan["injured_crew"] - killed_in_sickbay
                    try:
                        averaged_crew_readyness += target.life_support.caluclate_crew_readyness(able_crew, injured_crew)
                    except AttributeError:
                        averaged_crew_readyness += 1
                    
                    if able_crew + injured_crew == 0:
                        
                        number_of_crew_kills += 1
                else:
                    averaged_crew_readyness += 1
            else:
                averaged_shields += targ_shield
                averaged_hull += targ_hull
                
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        total_shield_dam /= number_of_simulations
        total_hull_dam /= number_of_simulations
        averaged_number_of_ship_kills = number_of_ship_kills / number_of_simulations
        averaged_number_of_crew_kills = number_of_crew_kills / number_of_simulations
        
        if scan_target_crew:
            averaged_crew_readyness /= number_of_simulations
        else:
            averaged_crew_readyness = 1.0
        
        return averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_number_of_ship_kills, averaged_number_of_crew_kills, averaged_crew_readyness

    def simulate_ram_attack(
        self, target:Starship, number_of_simulations:int, 
        *, 
        simulate_systems:bool=False, 
        simulate_crew:bool=False,
        use_effective_values:bool=False,
        target_scan:Optional[Dict[str,Union[Tuple,int,ShipStatus,ShipClass]]]
    ):
        precision = self.sensors.determin_precision

        target_scan = target_scan if target_scan else target.scan_this_ship(
            precision, scan_for_systems=simulate_systems, scan_for_crew=simulate_crew, 
            use_effective_values=use_effective_values
        )
        ship_class = target_scan["class"]
        
        targ_shield = target_scan["shields"]
        targ_hull = target_scan["hull"]

        total_shield_dam = 0
        total_hull_dam = 0
        
        averaged_shields = 0
        averaged_hull = 0
        
        averaged_crew_readyness = 0
        
        number_of_ship_kills = 0
        
        number_of_crew_kills = 0
        
        self_status = self.ship_status
        
        self_hp = (self.shield_generator.shields if self_status.do_shields_work else 0) + self.hull
        
        self_damage = self_hp + self.ship_class.max_hull * 0.5
        try:
            crew_readyness = self.life_support.crew_readyness
        except AttributeError:
            crew_readyness = 1
        try:
            target_crew_readyness = target.life_support.caluclate_crew_readyness(
                target_scan["able_crew"], target_scan["injured_crew"]
            ) if scan_target_crew else 1.0
        except AttributeError:
            target_crew_readyness = 1.0
        except KeyError:
            target_crew_readyness = 1.0
        try:
            estimated_enemy_impulse = (ajust_system_integrity(
                target_scan["sys_impulse"]
            ) if use_effective_values else target_scan["sys_impulse"])
        except KeyError:
            estimated_enemy_impulse = 1.0 if ship_class.evasion else 0.0
        
        scan_target_crew = not target.ship_class.is_automated and simulate_crew
                
        for i in range(number_of_simulations):
            
            to_hit = self.roll_to_hit(
                target, 
                damage_type=DAMAGE_RAMMING,
                crew_readyness=crew_readyness,
                target_crew_readyness=target_crew_readyness,
                systems_used_for_accuray=[self.impulse_engine.get_effective_value, self.ship_class.evasion],
                estimated_enemy_impulse=estimated_enemy_impulse
            )
            if to_hit:
                
                new_shields, new_hull, shields_dam, hull_dam, new_shields_as_a_percent, new_hull_as_a_percent, killed_outright, killed_in_sickbay, wounded, shield_sys_damage, impulse_sys_damage, warp_drive_sys_damage, sensors_sys_damage, warp_core_sys_damage, energy_weapons_sys_damage, cannon_sys_damage, torpedo_sys_damage, cloak_sys_damage, transporter_sys_damage, polarized_hull_damage = target.calculate_damage(
                    self_damage, 
                    scan_dict=target_scan, 
                    damage_type=DAMAGE_RAMMING
                )
                averaged_shields += new_shields
                averaged_hull += new_hull
                total_shield_dam += shields_dam
                total_hull_dam += hull_dam
                
                if new_hull <= 0:
                    number_of_ship_kills+=1
                
                if scan_target_crew:
                    able_crew = target_scan["able_crew"] - (wounded + killed_outright)
                    injured_crew = target_scan["injured_crew"] - killed_in_sickbay
                    
                    averaged_crew_readyness += target.life_support.caluclate_crew_readyness(able_crew, injured_crew)
                    
                    if able_crew + injured_crew == 0:
                        
                        number_of_crew_kills += 1
            else:
                averaged_shields += targ_shield
                averaged_hull += targ_hull
                
        averaged_shields /= number_of_simulations
        averaged_hull /= number_of_simulations
        total_shield_dam /= number_of_simulations
        total_hull_dam /= number_of_simulations
        averaged_number_of_ship_kills = number_of_ship_kills / number_of_simulations
        averaged_number_of_crew_kills = number_of_crew_kills / number_of_simulations
        
        if scan_target_crew:
            averaged_crew_readyness /= number_of_simulations
        else:
            averaged_crew_readyness = 1.0
        
        return averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_number_of_ship_kills, averaged_number_of_crew_kills, averaged_crew_readyness

    def check_torpedo_los(self, target:Starship):
        """Returns a float that examins the chance of a torpedo hitting an intended target.

        Args:
            target (Starship): The starship that the attacker is aiming at

        Returns:
            [float]: A float between 1 and 0 (inclusive)
        """
        game_data = self.game_data

        # Normalize the x and y direction
        c:Coords = Coords(
            target.local_coords.x - self.local_coords.x, target.local_coords.y - self.local_coords.y
        )
        dirX, dirY  = c.normalize()
        
        g:SubSector = self.get_sub_sector

        torp_positions = game_data.engine.get_lookup_table(
            direction_x=dirX, direction_y=dirY, normalise_direction=False
        )
        # Create dictionary of positions and ships for ships in the same system that are are not obliterated
        ship_positions = {
            ship.local_coords.create_coords() : ship for ship in 
            game_data.grab_ships_in_same_sub_sector(self, accptable_ship_statuses={STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK})
        }
        score = []

        for pos in torp_positions:
            x = pos.x + self.local_coords.x
            y = pos.y + self.local_coords.y
            
            if x not in game_data.subsec_size_range_x or y not in game_data.subsec_size_range_y:
                break

            ajusted_pos = Coords(x=pos.x+self.local_coords.x, y=pos.y+self.local_coords.y)

            if ajusted_pos in g.stars_dict or ajusted_pos in g.planets_dict:
                break
            try:
                hit_ship = ship_positions[ajusted_pos]
                score.append(
                    0 if hit_ship.is_controllable == self.is_controllable else 1
                )
            except KeyError:
                pass
        
        number_of_ship_hits = len(score)
                
        if number_of_ship_hits == 0:
            return 0.0

        if number_of_ship_hits == 1:
            return float(score[0])
        
        total = sum(score)
        
        return total / number_of_ship_hits
    