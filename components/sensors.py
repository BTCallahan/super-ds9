from __future__ import annotations
from random import uniform
from typing import TYPE_CHECKING, Dict, Tuple, Union
from data_globals import STATUS_ACTIVE, STATUS_CLOAKED, STATUS_OBLITERATED, STATUS_HULK, STATUS_DERLICT, CloakStatus, ShipStatus
from get_config import CONFIG_OBJECT

if TYPE_CHECKING:
    from starship import Starship

from global_functions import scan_assistant
from components.starship_system import StarshipSystem
import colors

class Sensors(StarshipSystem):
    
    def __init__(self):
        super().__init__("Sensors:")
    
    @property
    def determin_precision(self):
        """Takes the effective value of the ships sensor system and returns an intiger value based on it. This
        intiger is passed into the scanAssistant function that is used for calculating the precision when 
        scanning another ship. If the sensors are heavly damaged, their effective 'resoultion' drops. Say their 
        effective value is 0.65. This means that this function will return 25. 
        
        Returns:
            int: The effective value that is used for 
        """
        getEffectiveValue = self.get_effective_value

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
    
    @property
    def get_targeting_power(self):
        return self.starship.ship_class.targeting * self.get_effective_value
    
    def detect_all_enemy_cloaked_ships_in_system(self):
        
        if not self.is_opperational:
            return
        
        # can't detect while at warp!
        try:
            if self.starship.warp_drive.is_at_warp:
                return
        except AttributeError:
            pass
        
        allied_nations = self.starship.game_data.scenerio.get_set_of_allied_nations
        
        is_on_players_side = self.starship.nation in allied_nations
        
        nations = allied_nations if is_on_players_side else self.starship.game_data.scenerio.get_set_of_enemy_nations
        
        ships_in_same_system = self.starship.game_data.grab_ships_in_same_sub_sector(
            self.starship, accptable_ship_statuses={STATUS_CLOAKED}
        )
        cloaked_enemy_ships = [
            ship for ship in ships_in_same_system if ship.nation in nations
        ]
        player = self.starship.game_data.player
        
        for ship in cloaked_enemy_ships:
            
            detected = True
            
            detection_strength = self.starship.ship_class.detection_strength * self.get_effective_value
            
            cloak_strength = ship.get_cloak_power

            for i in range(CONFIG_OBJECT.chances_to_detect_cloak):

                if uniform(
                    0.0, detection_strength
                ) < uniform(
                    0.0, cloak_strength
                ):
                    detected = False
                    break
                
            if detected:
                
                ship.cloak.cloak_status = CloakStatus.COMPRIMISED
                
                if player.sector_coords == self.starship.sector_coords:
                    
                    cr = player.nation.captain_rank_name
                    
                    self.starship.game_data.engine.message_log.add_message(
f'{f"{cr}, we have" if self is player else f"The {self.name} has"} detected {"us" if ship is player else ship.name}!'
                    )
    
    def detect_cloaked_ship(self, ship:Starship):
        if ship.cloak.cloak_status != CloakStatus.ACTIVE:
            raise AssertionError(f"The ship {self.starship.name} is atempting to detect the ship {ship.name}, even though {ship.name} is not cloaked.")

        if not self.is_opperational:
            return False
        
        detected = True
        
        detection_strength = self.starship.ship_class.detection_strength * self.get_effective_value
        
        cloak_strength = ship.get_cloak_power

        for i in range(CONFIG_OBJECT.chances_to_detect_cloak):

            if uniform(
                0.0, detection_strength
            ) < uniform(
                0.0, cloak_strength
            ):
                detected = False
                break
            
        player = self.starship.game_data.player
        
        if detected and player.sector_coords == self.starship.sector_coords:
            
            cr = player.nation.captain_rank_name
            
            self.starship.game_data.engine.message_log.add_message(
f'{f"{cr}, we have" if self is player else f"The {self.name} has"} detected {"us" if ship is player else ship.name}!'
            )
        return detected
    
    def scan_for_print(self, precision: int=1):
        
        ship = self.starship
        
        if isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be an intiger between 1 amd 100")
        if precision not in {1, 2, 5, 10, 15, 20, 25, 50, 100, 200, 500}:
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

        shields = scan_assistant(self.shield_generator.shields, precision)
        hull = scan_assistant(self.hull, precision)
        energy = scan_assistant(self.energy, precision)
        
        ship_class = self.ship_class
        
        ship_type_can_fire_torps = self.ship_type_can_fire_torps
        
        hull_damage = scan_assistant(self.hull_damage, precision)
        
        d= {
            "shields" : (shields, print_color(shields, ship_class.max_shields)),
            "hull" : (hull, print_color(hull, ship_class.max_hull)),
            "energy" : (energy, print_color(energy, ship_class.max_energy))
        }
        if hull_damage:
            d["hull_damage"] = hull_damage, print_color(hull_damage, ship_class.max_hull)
        
        if ship_type_can_fire_torps:
            d["number_of_torps"] = tuple(self.get_number_of_torpedos(precision))
        
        if not ship.ship_class.is_automated:
            able_crew = scan_assistant(self.able_crew, precision)
            injured_crew = scan_assistant(self.injured_crew, precision)
            d["able_crew"] = (able_crew, print_color(able_crew, ship_class.max_crew))
            d["injured_crew"] = (injured_crew, print_color(injured_crew, ship_class.max_crew, True))
        
        ship_type_can_cloak = ship.ship_type_can_cloak

        if ship_type_can_cloak:
            d["cloak_cooldown"] = (
                self.cloak_cooldown, print_color(self.cloak_cooldown, ship_class.cloak_cooldown, True)
            )

        if ship.is_mobile:
            d["sys_warp_drive"] = self.sys_warp_drive.print_info(precision), self.sys_warp_drive.get_color(), self.sys_warp_drive.name
            d["sys_impulse"] = self.sys_impulse.print_info(precision), self.sys_impulse.get_color(), self.sys_impulse.name
        if ship.ship_type_can_fire_beam_arrays:
            d["sys_beam_array"] = self.sys_beam_array.print_info(precision), self.sys_beam_array.get_color(), self.sys_beam_array.name
        if self.ship_type_can_fire_cannons:
            d["sys_cannon_weapon"] = self.sys_cannon_weapon.print_info(precision), self.sys_cannon_weapon.get_color(), self.sys_cannon_weapon.name
        d["sys_shield"] = self.sys_shield_generator.print_info(precision), self.sys_shield_generator.get_color(), self.sys_shield_generator.name
        d["sys_sensors"] = self.sys_sensors.print_info(precision), self.sys_sensors.get_color(), self.sys_sensors.name
        if ship_type_can_fire_torps:
            d["sys_torpedos"] = self.sys_torpedos.print_info(precision), self.sys_torpedos.get_color(), self.sys_torpedos.name
        if ship_type_can_cloak:
            d["sys_cloak"] = self.sys_cloak.print_info(precision), self.sys_cloak.get_color(), self.sys_cloak.name
        if not self.is_automated:
            d["sys_transporter"] = self.sys_transporter.print_info(precision), self.sys_transporter.get_color(), self.sys_transporter.name
        d["sys_warp_core"] = self.sys_warp_core.print_info(precision), self.sys_warp_core.get_color(), self.sys_warp_core.name
            
        if ship_type_can_fire_torps:

            torps = tuple(self.get_number_of_torpedos(precision))
            for k, v in torps:
                d[k] = v

        return d
    
    def scan_this_ship(
        self, precision: int=1, *, scan_for_crew:bool=True, scan_for_systems:bool=True, use_effective_values=False
    )->Dict[str,Union[int,Tuple,ShipStatus]]:
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
        if precision not in {1, 2, 5, 10, 15, 20, 25, 50, 100, 200, 500}:
            raise ValueError(
                f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. It's actually value is {precision}."
            )

        hull = scan_assistant(self.hull, precision)
        
        status = STATUS_ACTIVE if hull > 0 else (
            STATUS_OBLITERATED if hull < self.ship_class.max_hull * -0.5 else STATUS_HULK
        )

        d= {
            "shields" : scan_assistant(self.shield_generator.shields, precision),
            "hull" : hull,
            "energy" : scan_assistant(self.energy, precision),
            
            "number_of_torps" : tuple(self.get_number_of_torpedos(precision)),
            #"torp_tubes" : s
        }
        
        if scan_for_crew and not self.ship_class.is_automated:
            able_crew = scan_assistant(self.able_crew, precision)
            injured_crew = scan_assistant(self.injured_crew, precision)
            d["able_crew"] = able_crew
            d["injured_crew"] = injured_crew
            
            if status is STATUS_ACTIVE and not self.ship_class.is_automated and able_crew + injured_crew <= 0:
                status = STATUS_DERLICT

        ship_type_can_cloak = self.ship_type_can_cloak

        if ship_type_can_cloak:
            d["cloak_cooldown"] = self.cloak_cooldown

        ship_type_can_fire_torps = self.ship_type_can_fire_torps

        if scan_for_systems:
            
            if self.is_mobile:
                d["sys_warp_drive"] = self.sys_warp_drive.get_info(precision, use_effective_values)# * 0.01,
                d["sys_impulse"] = self.sys_impulse.get_info(precision, use_effective_values)# * 0.01,
            if self.ship_type_can_fire_beam_arrays:
                d["sys_beam_array"] = self.sys_beam_array.get_info(precision, use_effective_values)# * 0.01,
            if self.ship_type_can_fire_cannons:
                d["sys_cannon_weapon"] = self.sys_cannon_weapon.get_info(precision, use_effective_values)
            d["sys_shield"] = self.sys_shield_generator.get_info(precision, use_effective_values)# * 0.01,
            d["sys_sensors"] = self.sys_sensors.get_info(precision, use_effective_values)# * 0.01,
            if ship_type_can_fire_torps:
                d["sys_torpedos"] = self.sys_torpedos.get_info(precision, use_effective_values)# * 0.01
            if ship_type_can_cloak:
                d["sys_cloak"] = self.sys_cloak.get_info(precision, use_effective_values)
            if not self.is_automated:
                d["sys_transporter"] = self.sys_transporter.get_info(precision, use_effective_values)
            d["sys_warp_core"] = self.sys_warp_core.get_info(precision, use_effective_values)
            
        d["status"] = status

        if ship_type_can_fire_torps:

            torps = tuple(self.get_number_of_torpedos(precision))
            for k, v in torps:
                d[k] = v

        return d