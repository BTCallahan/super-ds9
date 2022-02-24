from __future__ import annotations
from collections import Counter
from random import choices
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Tuple, Union
from global_functions import average
from data_globals import LOCAL_ENERGY_COST, PLANET_FRIENDLY, SECTOR_ENERGY_COST, STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK, WARP_FACTOR, CloakStatus, ShipStatus

from order import CloakOrder, MoveOrder, Order, EnergyWeaponOrder, OrderWarning, RechargeOrder, RepairOrder, SelfDestructOrder, TorpedoOrder, TransportOrder, WarpOrder, WarpTravelOrder

if TYPE_CHECKING:
    from starship import Starship
    from space_objects import SubSector
    from game_data import GameData
    from ship_class import ShipClass

class BaseAi(Order):
    
    order:Optional[Order]
    
    def __init__(self, entity: Starship):
        
        self.entity = entity
        
        self.order_dict = Counter([])
        
        self.order_dict_size = 0
        
        self.precision = self.entity.sensors.determin_precision
    
    def check_for_at_warp(self):
        """Returns True if the entity is at warp, False if not

        Returns:
            bool: True if the entity is at warp, False if not
        """
        try:
            if self.entity.warp_drive.is_at_warp:
                wto = WarpTravelOrder(self.entity)
                wto.perform()
                return True
            return False
        except AttributeError:
            return False
    
    def determin_order(self):
        
        if self.order_dict_size == 0:
        
            self.order = RepairOrder(self.entity, 1)
            
        elif self.order_dict_size == 1:
            
            self.order = tuple(self.order_dict.keys())[0]
        else:
            highest_order_value = max(self.order_dict.values())
            
            half_highest_order_value = round(highest_order_value * 0.5)
            
            # we only want orders that 
            order_counter = {
                k:v for k,v in self.order_dict.items() if v >= half_highest_order_value
            }
            try:
                if len(order_counter) == 1:
                    self.order = tuple(self.order_dict.keys())[0]
                else:
                    keys = tuple(order_counter.keys())
                    weights = tuple(order_counter.values())
                    self.order = choices(population=keys, weights=weights, k=1)[0]
                    
            except IndexError:
                pass
    
    def get_player_enemies_in_same_system(self):
        return [ship for ship in  self.entity.game_data.grab_ships_in_same_sub_sector(
            self.entity, accptable_ship_statuses={STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED}
        ) if ship.nation in self.game_data.scenerio.get_set_of_enemy_nations]
    
    def get_player_allies_in_same_system(self):
        return [ship for ship in  self.entity.game_data.grab_ships_in_same_sub_sector(
            self.entity, accptable_ship_statuses={STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED}
        ) if ship.nation in self.game_data.scenerio.get_set_of_allied_nations]
    
def find_unopressed_planets(game_data:GameData, ship:Starship):

    for y in game_data.grid:
        for x in y:
            
            sector:SubSector = x

            if sector.coords != ship.sector_coords:

                for planet in sector.planets_dict.values():

                    if planet.planet_habbitation is PLANET_FRIENDLY:
                        yield planet.sector_coords

def calc_torpedos_easy(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):
    for ship, scan in zip(enemies_in_same_system, enemy_scans):
        
        chance_of_hit = self.entity.check_torpedo_los(ship)
    
        if chance_of_hit > 0:
            
            torpedos_to_fire = min(
                self.entity.torpedo_launcher.get_most_powerful_torp_avaliable, self.entity.ship_class.torp_tubes
            )

            torpedo = TorpedoOrder.from_coords(
                self.entity, torpedos_to_fire, ship.local_coords.x, ship.local_coords.y
            )
            self.order_dict[torpedo] = 1000
            self.order_dict_size+=1

def calc_torpedos_medium(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    try:
        c_value = 300 if self.entity.cloak.cloak_status != CloakStatus.INACTIVE else 100
    except AttributeError:
        c_value = 100
    
    for ship, scan in zip(enemies_in_same_system, enemy_scans):
        
        chance_of_hit = self.entity.check_torpedo_los(self.entity.game_data.player)
        
        if chance_of_hit > 0.0:
            
            averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_torpedo_hit(
                ship, 5,
                target_scan=scan
            )
            torpedos_to_fire = min(
                self.entity.torpedo_launcher.get_most_powerful_torp_avaliable, self.entity.ship_class.torp_tubes
            )
            torpedo = TorpedoOrder.from_coords(
                self.entity, torpedos_to_fire, ship.local_coords.x, ship.local_coords.y
            )
            warning = torpedo.raise_warning()
            
            if warning not in {
                OrderWarning.NO_TORPEDOS_LEFT, 
                OrderWarning.TORPEDO_WILL_HIT_FRIENDLY_SHIP_OR_MISS,
                OrderWarning.TORPEDO_WILL_HIT_PLANET, 
                OrderWarning.TORPEDO_WILL_HIT_PLANET_OR_FRIENDLY_SHIP,
                OrderWarning.TORPEDO_WILL_MISS
                }:
            
                self.order_dict[torpedo] = (
                        c_value
                    ) * (total_shield_dam + total_hull_dam + (1000 if ship_kills else 0))
                
                self.order_dict_size+=1

def calc_torpedos_hard(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    torpedos_to_fire = min(
        self.entity.torpedo_launcher.torps[self.entity.torpedo_launcher. get_most_powerful_torp_avaliable], 
        self.entity.ship_class.torp_tubes
    )
    for ship, scan in zip(enemies_in_same_system, enemy_scans):
    
        chance_of_hit = self.entity.check_torpedo_los(ship)
            
        if chance_of_hit > 0.0:
            
            averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_torpedo_hit(
                ship, 10,
                simulate_systems=True, simulate_crew=True, target_scan=scan
            )
            torpedo = TorpedoOrder.from_coords(
                self.entity, torpedos_to_fire, ship.local_coords.x, ship.local_coords.y
            )
            warning = torpedo.raise_warning()
            
            if warning not in {
                OrderWarning.NO_TORPEDOS_LEFT, 
                OrderWarning.TORPEDO_WILL_HIT_FRIENDLY_SHIP_OR_MISS,
                OrderWarning.TORPEDO_WILL_HIT_PLANET, 
                OrderWarning.TORPEDO_WILL_HIT_PLANET_OR_FRIENDLY_SHIP,
                OrderWarning.TORPEDO_WILL_MISS
            }:
                self.order_dict[torpedo] = (
                    300 if self.entity.cloak.cloak_status != CloakStatus.INACTIVE else 100
                ) * (total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills))
                
                self.order_dict_size+=1
                
def calc_beam_weapon_easy(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    for ship, scan in zip(enemies_in_same_system, enemy_scans):
    
        energy_weapon=EnergyWeaponOrder.single_target_beam(
            entity=self.entity,
            target=ship,
            amount=min(self.entity.get_max_effective_beam_firepower, self.entity.power_generator.energy)
        )
        self.order_dict[energy_weapon] = 1000
        self.order_dict_size+=1

def calc_beam_weapon_medium(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    energy_to_use = min(self.entity.get_max_effective_beam_firepower, self.entity.power_generator.energy)
    
    try:
        c_value = 300 if self.entity.cloak.cloak_status != CloakStatus.INACTIVE else 100
    except AttributeError:
        c_value = 100
    
    for ship, scan in zip(enemies_in_same_system, enemy_scans):
    
        averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_energy_hit(
            ship, 5, energy_to_use,
            target_scan=scan
        )
        if total_shield_dam + total_hull_dam > 0:
            
            energy_weapon = EnergyWeaponOrder.single_target_beam(self.entity, energy_to_use, target=ship)
            
            self.order_dict[energy_weapon] = (
                c_value
            ) * (total_shield_dam + total_hull_dam + (1000 * ship_kills))
            
            self.order_dict_size+=1

def calc_beam_weapon_hard(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    user = self.entity
            
    max_energy = min(user.power_generator.energy, user.get_max_effective_beam_firepower)
    
    try:
        c_value = 300 if self.entity.cloak.cloak_status != CloakStatus.INACTIVE else 100
    except AttributeError:
        c_value = 100
    
    if enemies_in_same_system:
        
        number_of_enemies = len(enemies_in_same_system)
        
        if number_of_enemies > 1:
            
            per_enemy_energy = max_energy / number_of_enemies

            collected_values = [
                user.simulate_energy_hit(
                    ship, 5, per_enemy_energy, 
                    simulate_systems=True, simulate_crew=True,
                    target_scan=scan
                ) for ship, scan in zip(enemies_in_same_system, enemy_scans)
            ]
            #averaged_shields = max([value[0] for value in collected_values])
            #averaged_hull = max([value[1] for value in collected_values])
            total_shield_dam = max([value[2] for value in collected_values])
            total_hull_dam = max([value[3] for value in collected_values])
            ship_kills = max([value[4] for value in collected_values])
            crew_kills = max([value[5] for value in collected_values])
            #averaged_crew_readyness = max([value[6] for value in collected_values])
                
            if total_shield_dam + total_hull_dam > 0:
                
                multi_order = EnergyWeaponOrder.multiple_targets(
                    entity=user, amount=max_energy, targets=enemies_in_same_system
                )
                self.order_dict[multi_order] = (
                    c_value
                ) * (
                    total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)
                )
                self.order_dict_size+=1
        
        for enemy in enemies_in_same_system:
            
            averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, averaged_number_of_ship_kills, averaged_number_of_crew_kills, averaged_crew_readyness = user.simulate_energy_hit(
                enemy, 5, max_energy, 
                simulate_systems=True, simulate_crew=True,
            )
            if total_shield_dam + total_hull_dam > 0:
            
                simgle_order = EnergyWeaponOrder.single_target_beam(
                    entity=user, amount=max_energy, target=enemy
                )
                self.order_dict[simgle_order] = (
                    c_value
                ) * (
                    total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)
                )
                self.order_dict_size+=1

def calc_cannon_weapon_easy(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):
    for ship, scan in zip(enemies_in_same_system, enemy_scans):
        
        cannon_weapon = EnergyWeaponOrder.cannon(
            entity=self.entity,
            target=ship,
            amount=min(self.entity.get_max_effective_cannon_firepower, self.entity.power_generator.energy)
        )
        self.order_dict[cannon_weapon] = 1000
        self.order_dict_size+=1
    
def calc_cannon_weapon_medium(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):
    energy_to_use = min(self.entity.get_max_effective_cannon_firepower, self.entity.power_generator.energy)
    
    for ship, scan in zip(enemies_in_same_system, enemy_scans):
        
        averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_energy_hit(
            ship, 5, energy_to_use, 
            cannon=True, target_scan=scan
        )
        if total_shield_dam + total_hull_dam > 0:
            
            energy_weapon = EnergyWeaponOrder.cannon(self.entity, energy_to_use, target=ship)
            
            self.order_dict[energy_weapon] = (
                300 if self.entity.cloak.cloak_status != CloakStatus.INACTIVE else 100
            ) * (total_shield_dam + total_hull_dam + (1000 * ship_kills))
            
            self.order_dict_size+=1
    
def calc_cannon_weapon_hard(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):
    user = self.entity
    
    max_energy = min(user.power_generator.energy, user.get_max_effective_beam_firepower)
    
    try:
        c_value = 300 if self.entity.cloak.cloak_status != CloakStatus.INACTIVE else 100
    except AttributeError:
        c_value = 100
    
    if enemies_in_same_system:
        
        for enemy in enemies_in_same_system:
            
            averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = user.simulate_energy_hit(
                enemy, 5, max_energy, True,
                simulate_systems=True, simulate_crew=True,
            )
            if total_shield_dam + total_hull_dam > 0:
            
                simgle_order = EnergyWeaponOrder.cannon(
                    entity=user, amount=max_energy, target=enemy
                )
                self.order_dict[simgle_order] = (
                    c_value
                ) * (
                    total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)
                )
                self.order_dict_size+=1

def calc_polarize_easy(
    self:BaseAi, hostile_ships_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    polarize_hull = len(hostile_ships_in_same_system)
    
    polarize_amount = self.entity.polarized_hull.get_effective_value * self.entity.ship_class.polarized_hull
            
    recharge= RechargeOrder(self.entity, polarize_amount, bool(polarize_hull))
                    
    self.order_dict[recharge] = polarize_amount * 10 * (1 + polarize_hull)
    
    self.order_dict_size += 1

def calc_shields_easy(
    self:BaseAi, hostile_ships_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    raise_shields = len(hostile_ships_in_same_system)
    
    recharge_amount = min(
        self.entity.get_max_effective_shields, self.entity.power_generator.energy + self.entity.shield_generator.shields
    )
            
    recharge= RechargeOrder(self.entity, recharge_amount, raise_shields)
                    
    self.order_dict[recharge] = recharge_amount * 10 * (1 + raise_shields)
    
    self.order_dict_size+=1

def calc_shields_medium(
    self:BaseAi, hostile_ships_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):    
    raise_shields = len(hostile_ships_in_same_system)
    
    recharge_amount = min(
        self.entity.get_max_effective_shields, self.entity.power_generator.energy + self.entity.shield_generator.shields
    )
            
    recharge= RechargeOrder(self.entity, recharge_amount, raise_shields)
                    
    self.order_dict[recharge] = recharge_amount * 10 * (1 + raise_shields)
    
    self.order_dict_size+=1

def calc_shields_hard(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):
    raise_shields = len(enemies_in_same_system)
    
    def evaluate_scan(scan: Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]):
        try:
            max_beam_energy = min(scan["class"].max_beam_energy, scan["energy"]) * scan["sys_beam_array"]
        except KeyError:
            max_beam_energy = 0
        try:
            max_cannon_energy = min(scan["class"].max_cannon_energy, scan["energy"]) * scan["sys_cannon"]
        except KeyError:
            max_cannon_energy = 0
        
        max_torpedo_damage = scan["class"].get_most_powerful_torpedo_type.damage
        
        return max(max_beam_energy, max_cannon_energy, max_torpedo_damage)
    
    attacks = [
        evaluate_scan(a) for a in enemy_scans
    ]
    
    recharge_amount = min(
        self.entity.get_max_effective_shields, self.entity.power_generator.energy + self.entity.shield_generator.shields
    )
            
    recharge= RechargeOrder(self.entity, recharge_amount, raise_shields)
                    
    self.order_dict[recharge] = recharge_amount * 10 * max(attacks + [1])
    
    self.order_dict_size+=1
    
def calc_cloak_medium(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):
    detect_strs = [
        scan["sys_sensors"] * ship.ship_class.detection_strength for ship, scan in zip(
            enemies_in_same_system, enemy_scans
        )
    ]
    
    detect_str = sum(detect_strs) / len(detect_strs)

    cloak_str = self.entity.ship_class.cloak_strength * self.entity.cloak.get_effective_value
    
    diff = cloak_str - detect_str
    
    cloak = CloakOrder(self.entity, deloak=False)
    
    self.order_dict[cloak] = (
        500 * diff
    )
    self.order_dict_size+=1

def calc_cloak_hard(
    self:BaseAi, enemies_in_same_system:Iterable[Starship], 
    enemy_scans:Iterable[Dict[str, Union[int, Tuple, ShipStatus, ShipClass]]]
):      
    cloaking_ability = self.entity.get_cloak_power
    
    cloak_strengths = [
        cloaking_ability - scan["sys_sensors"] * ship.ship_class.detection_strength for ship, scan in zip(
            enemies_in_same_system, enemy_scans
        )
    ]
    lowest_cloak_strength = min(cloak_strengths)
    
    if lowest_cloak_strength > 0:
        
        cloak = CloakOrder(self.entity, deloak=False)
    
        self.order_dict[cloak] = (
            500 * lowest_cloak_strength
        )
        self.order_dict_size+=1
        
def calc_oppress_hard(self:BaseAi):
    
    try:
        affect_cost_multiplier = self.entity.warp_drive.affect_cost_multiplier
    except AttributeError:
        return
        
    unopressed_planets = tuple(
        planet for planet in find_unopressed_planets(
            self.entity.game_data, self.entity
        ) if self.entity.sector_coords.distance(
            coords=planet
        ) * SECTOR_ENERGY_COST * affect_cost_multiplier <= self.entity.power_generator.energy
    )

    number_of_unoppressed_planets = len(unopressed_planets)
    
    if number_of_unoppressed_planets == 1:
        
        planet = unopressed_planets[0]
        
        energy_cost = self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.warp_drive.affect_cost_multiplier
            
        warp_to = WarpOrder.from_coords(self.entity, planet.x, planet.y)
        
        self.order_dict[warp_to] = self.entity.power_generator.energy - round(energy_cost)
        
        self.order_dict_size+=1
        
    elif number_of_unoppressed_planets > 1:

        planet_counter = Counter(unopressed_planets)
        
        highest = max(planet_counter.values())
        
        most_common = [
            k for k,v in planet_counter.items() if v == highest
        ]
        most_common.sort(key=lambda coords: coords.distance(coords=self.entity.sector_coords), reverse=True)

        planet = most_common[0]
        
        warp_to = WarpOrder.from_coords(
            self.entity, planet.x, planet.y, speed=WARP_FACTOR[1], 
            start_x=self.entity.sector_coords.x, start_y=self.entity.sector_coords.y
        )
        energy_cost = self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.warp_drive.affect_cost_multiplier
        
        self.order_dict[warp_to] = self.entity.power_generator.energy - round(energy_cost)
        
        self.order_dict_size+=1
    
def calc_auto_destruct_medium(
    self:BaseAi,
    all_nearbye_ships:Iterable[Starship],
    nearbye_enemy_ships:Iterable[Starship],
    nearbye_allied_ships:Iterable[Starship]
):
    user = self.entity
    
    precision = user.sensors.determin_precision
    
    enemy_collected_values = [
        user.calc_self_destruct_damage(
            enemy, 
            scan=enemy.scan_this_ship(
                precision, scan_for_crew=True, scan_for_systems=True, use_effective_values=True
            )
        ) for enemy in nearbye_enemy_ships
    ]
    #averaged_shields = max([value[0] for value in collected_values])
    #averaged_hull = max([value[1] for value in collected_values])
    total_shield_dam = average([value[2] for value in enemy_collected_values])
    total_hull_dam = average([value[3] for value in enemy_collected_values])
    ship_kills = average([value[4] for value in enemy_collected_values])
    crew_kills = average([value[5] for value in enemy_collected_values])
    #averaged_crew_readyness = max([value[6] for value in collected_values])
    
    enemy_power = (total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)) * 100
    friendly_power = 0
    
    if total_hull_dam + total_shield_dam > 0:
        
        self_destruct = SelfDestructOrder(self.entity, tuple(all_nearbye_ships))
        
        self.order_dict[self_destruct] = enemy_power - friendly_power
        
        self.order_dict_size+=1

def calc_auto_destruct_hard(
    self:BaseAi,
    all_nearbye_ships:Iterable[Starship],
    nearbye_enemy_ships:Iterable[Starship],
    nearbye_allied_ships:Iterable[Starship]
):
    user = self.entity
    
    precision = user.sensors.determin_precision
    
    enemy_collected_values = [
        user.calc_self_destruct_damage(
            enemy, 
            scan=enemy.scan_this_ship(
                precision, scan_for_crew=True, scan_for_systems=True, use_effective_values=True
            ),
            number_of_simulations=3, 
            simulate_systems=True, simulate_crew=True,
        ) for enemy in nearbye_enemy_ships
    ]
    #averaged_shields = max([value[0] for value in collected_values])
    #averaged_hull = max([value[1] for value in collected_values])
    total_shield_dam = max([value[2] for value in enemy_collected_values])
    total_hull_dam = max([value[3] for value in enemy_collected_values])
    ship_kills = max([value[4] for value in enemy_collected_values])
    crew_kills = max([value[5] for value in enemy_collected_values])
    #averaged_crew_readyness = max([value[6] for value in collected_values])
    
    enemy_power = (total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)) * 100
    friendly_power = 0
    
    if total_hull_dam + total_shield_dam > 0:
        
        power = (
            total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)
        )
        allied_collected_values = [
            
            user.calc_self_destruct_damage(
                enemy, 
                scan=enemy.scan_this_ship(
                    precision, scan_for_crew=True, scan_for_systems=True, use_effective_values=True
                ),
                number_of_simulations=3, 
                simulate_systems=True, simulate_crew=True,
            ) for enemy in nearbye_allied_ships
        ]
        ff_total_shield_dam = max([value[2] for value in allied_collected_values])
        ff_total_hull_dam = max([value[3] for value in allied_collected_values])
        ff_ship_kills = max([value[4] for value in allied_collected_values])
        ff_crew_kills = max([value[5] for value in allied_collected_values])
        
        friendly_power = (
            ff_total_shield_dam + ff_total_hull_dam + (1000 * ff_ship_kills) + (1000 * ff_crew_kills)
        ) * 1000
        
    if enemy_power > friendly_power:
        
        self_destruct = SelfDestructOrder(self.entity, tuple(all_nearbye_ships))
        
        self.order_dict[self_destruct] = enemy_power - friendly_power
        
        self.order_dict_size+=1
    
def calc_ram_hard(
    self:BaseAi, 
    enemy_ships:Iterable[Starship], 
    enemy_ship_scans:Iterable[Dict[str,Union[int,Tuple,ShipStatus]]]
):
    for ship, scan in zip(enemy_ships, enemy_ship_scans):
        
        energy_cost = round(
            self.entity.local_coords.distance(
                x=ship.local_coords.x, y=ship.local_coords.y
            ) * LOCAL_ENERGY_COST * 
            self.entity.impulse_engine.affect_cost_multiplier
        )
        if energy_cost > self.entity.power_generator.energy:
            
            continue
        
        averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_ram_attack(
            ship, number_of_simulations=3, 
            simulate_systems=True, simulate_crew=True,
            target_scan=scan
        )
        shields_score = min(ship.ship_class.max_shields - averaged_shields, total_shield_dam)
        hull_score = min(ship.ship_class.max_hull - averaged_hull, total_hull_dam)
        
        if shields_score + hull_score > 0:
            
            score = (
                shields_score + hull_score + (1000 * ship_kills) + (1000 * crew_kills)
            ) * 500
            
            ram_order = MoveOrder.from_coords(self.entity, ship.local_coords.x, ship.local_coords.y)
        
            self.order_dict[ram_order] = score
            
            self.order_dict_size+=1
    
def reactivate_derelict_hard(self:BaseAi):
    
    if self.game_data.player.sector_coords == self.entity.sector_coords or self.entity.ship_class.is_automated:
        return
    try:
        able_crew = self.entity.crew.able_crew
    except AttributeError:
        return
    try:
        transport_power = self.entity.transporter.get_effective_value
    except AttributeError:
        transport_power = -1
    
    all_derelicts = [ship for ship in self.game_data.total_starships if ship.ship_status.is_recrewable]
    
    if all_derelicts:
        
        derelicts_in_system = [ship for ship in all_derelicts if ship.sector_coords == self.entity.sector_coords]
        
        if derelicts_in_system:
            
            if transport_power > 0:
                
                for derelict in derelicts_in_system:
                    
                    crew_to_send = min(derelict.ship_class.max_crew, able_crew)
                
                    order = TransportOrder(
                        self.entity,
                        derelict,
                        crew_to_send
                    )
                    stragic_value = derelict.calculate_ship_stragic_value(value_multiplier_for_derlict=1)
                    
                    self.order_dict[order] = average(stragic_value) / crew_to_send
            """
            derelicts_in_system.sort(key=lambda ship: ship.local_coords.distance(self.entity.local_coords), reverse=True)
            
            adjacent = [ship for ship in derelicts_in_system if ship.local_coords.is_adjacent(self.entity.local_coords)]

            if adjacent:
                
                adjacent.sort(
                    key=lambda ship: ship.ship_class.max_crew, reverse=True
                )
                able_crew -= adjacent[0].ship_class.max_crew
            else:
                able_crew -= self.entity.local_coords.distance(derelicts_in_system[0].local_coords)
            """
        else:
            
            for derelict in all_derelicts:
                
                order = WarpOrder.from_coords(
                    self.entity, 
                    x=derelict.sector_coords.x,
                    y=derelict.sector_coords.y,
                    start_x=self.entity.sector_coords.x,
                    start_y=self.entity.sector_coords.y,
                    speed=1
                )
                dist = derelict.sector_coords.distance(self.entity.sector_coords)
                
                self.order_dict[order] = derelict.get_ship_value / dist

class EasyEnemy(BaseAi):
        
    def perform(self) -> None:
        
        if self.check_for_at_warp():
            return
        
        player_status = self.game_data.player.ship_status
        
        assert player_status.is_active
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return
        self.order:Optional[Order] = None

        if self.entity.power_generator.energy <= 0:
            
            self.order =  RepairOrder(self.entity, 1)
        else:
            enemy_ships = self.get_player_allies_in_same_system()
                        
            enemy_scans = [
                ship.scan_this_ship(
                    precision=self.precision, scan_for_crew=False, scan_for_systems=False
                ) for ship in enemy_ships
            ]
            if self.entity.ship_can_fire_beam_arrays:
            
                calc_beam_weapon_easy(self, enemy_ships, enemy_scans)
                
            if self.entity.ship_can_fire_cannons:
                
                calc_cannon_weapon_easy(self, enemy_ships, enemy_scans)
            
            if self.entity.ship_can_fire_torps:
                    
                calc_torpedos_easy(self, enemy_ships, enemy_scans)
                
        self.determin_order()
        self.order.perform()         
                 
class MediumEnemy(BaseAi):
    
    def perform(self) -> None:
        
        if self.check_for_at_warp():
            return
        
        player_status = self.game_data.player.ship_status
        
        assert player_status.is_active
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return
        self.order:Optional[Order] = None

        if self.entity.power_generator.energy <= 0:
            
            self.order =  RepairOrder(self.entity, 1)
        else:
            enemy_ships = self.get_player_allies_in_same_system()
            
            precision = self.entity.sensors.determin_precision
            
            enemy_scans = [
                ship.scan_this_ship(
                    precision=precision, scan_for_crew=False, scan_for_systems=False
                ) for ship in enemy_ships
            ]
            enemy_is_present = bool(enemy_ships)
            
            if enemy_is_present:
                
                if self.entity.hull / self.entity.ship_class.max_hull < 0.25:
                    
                    calc_auto_destruct_medium(
                        self,
                        all_nearbye_ships=self.game_data.grab_ships_in_same_sub_sector(
                            self.entity,
                            accptable_ship_statuses={
                                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED,STATUS_CLOAKED,STATUS_DERLICT,STATUS_HULK
                            }
                        ),
                        nearbye_allied_ships=[], 
                        nearbye_enemy_ships=enemy_ships,
                    )
            has_energy = self.entity.power_generator.energy > 0
            
            if has_energy:
            
                if self.entity.ship_can_fire_beam_arrays:
                    
                    calc_beam_weapon_medium(self, enemy_ships, enemy_scans)
                
                if self.entity.ship_can_fire_cannons:
                    
                    calc_cannon_weapon_medium(self, enemy_ships, enemy_scans)
            
            if self.entity.ship_can_fire_torps:
                    
                calc_torpedos_medium(self, enemy_ships, enemy_scans)
            
            if self.entity.ship_can_cloak:
                
                calc_cloak_medium(self, enemy_ships, enemy_scans)
                
            if self.entity.get_max_effective_shields > 0:
                
                calc_shields_medium(self, enemy_ships)
                
        self.determin_order()
        self.order.perform()

class HardEnemy(BaseAi):
    
    def perform(self) -> None:
        
        if self.check_for_at_warp():
            return
        
        player_status = self.game_data.player.ship_status
        
        assert player_status.is_active
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return

        if self.entity.power_generator.energy <= 0:
            
            self.order =  RepairOrder(self.entity, 1)
        else:
            precision = self.entity.sensors.determin_precision
            
            enemy_ships = self.get_player_allies_in_same_system()
            
            friendly_ships = self.get_player_enemies_in_same_system()
            
            enemy_scans = [
                ship.scan_this_ship(
                    precision=precision, scan_for_crew=False, scan_for_systems=False
                ) for ship in enemy_ships
            ]
            enemy_is_present = bool(enemy_ships)
            
            has_energy = self.entity.power_generator.energy > 0
            
            if enemy_is_present:
                
                if self.entity.hull / self.entity.ship_class.max_hull < 0.25:
                    
                    calc_auto_destruct_hard(
                        self,
                        all_nearbye_ships=self.game_data.grab_ships_in_same_sub_sector(
                            self.entity,
                            accptable_ship_statuses={
                                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED,STATUS_CLOAKED,STATUS_DERLICT,STATUS_HULK
                            }
                        ),
                        nearbye_allied_ships=friendly_ships, 
                        nearbye_enemy_ships=enemy_is_present,
                    )
                if self.entity.ship_can_fire_torps:
                    
                    calc_torpedos_hard(self, enemy_ships, enemy_scans)
                    
                if has_energy:                    
                    if self.entity.ship_can_fire_beam_arrays:
                        
                        calc_beam_weapon_hard(self, enemy_ships, enemy_scans)
                    
                    if self.entity.ship_can_fire_cannons:
                        
                        calc_cannon_weapon_hard(self, enemy_ships, enemy_scans)
                        
                    calc_ram_hard(self, enemy_ships, enemy_scans)
                        
                if self.entity.ship_can_cloak and self.entity.cloak.cloak_status == CloakStatus.INACTIVE:
                    
                    calc_cloak_hard(self, enemy_ships, enemy_scans)
            else:
                # if the player is not present:
                
                system = self.entity.get_sub_sector
                
                if friendly_ships or system.friendly_planets == 0:
                
                    calc_oppress_hard(self)
                    
            max_effective_shields = self.entity.shield_generator.get_max_effective_shields
            
            if self.entity.shield_generator.is_opperational and self.entity.shield_generator.shields < max_effective_shields:
                
                calc_shields_hard(self, enemy_ships)
            
        self.determin_order()
            
        self.order.perform()
        
class AllyAI(BaseAi):
    
    def perform(self) -> None:
        
        if self.check_for_at_warp():
            return
        
        player_status = self.game_data.player.ship_status
        
        assert player_status.is_active
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return

        if self.entity.power_generator.energy <= 0:
            
            self.order =  RepairOrder(self.entity, 1)
        else:
            precision = self.entity.sensors.determin_precision
            
            enemy_ships = self.get_player_enemies_in_same_system()
            
            friendly_ships = self.get_player_allies_in_same_system()
            
            enemy_scans = [
                ship.scan_this_ship(
                    precision=precision, scan_for_crew=False, scan_for_systems=False
                ) for ship in enemy_ships
            ]
            enemy_is_present = bool(enemy_ships)
            
            has_energy = self.entity.power_generator.energy > 0
            
            if enemy_is_present:
                
                if self.entity.hull / self.entity.ship_class.max_hull < 0.25:
                    
                    calc_auto_destruct_hard(
                        self,
                        all_nearbye_ships=self.game_data.grab_ships_in_same_sub_sector(
                            self.entity,
                            accptable_ship_statuses={
                                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED,STATUS_CLOAKED,STATUS_DERLICT,STATUS_HULK
                            }
                        ),
                        nearbye_allied_ships=friendly_ships, 
                        nearbye_enemy_ships=enemy_is_present,
                    )
                if self.entity.ship_can_fire_torps:
                    
                    calc_torpedos_hard(self, enemy_ships, enemy_scans)
                    
                if has_energy:                    
                    if self.entity.ship_can_fire_beam_arrays:
                        
                        calc_beam_weapon_hard(self, enemy_ships, enemy_scans)
                    
                    if self.entity.ship_can_fire_cannons:
                        
                        calc_cannon_weapon_hard(self, enemy_ships, enemy_scans)
                        
                    calc_ram_hard(self, enemy_ships, enemy_scans)
                        
                if self.entity.ship_can_cloak and self.entity.cloak.cloak_status == CloakStatus.INACTIVE:
                    
                    calc_cloak_hard(self, enemy_ships, enemy_scans)
            else:
                # if the player is not present:
                
                system = self.entity.get_sub_sector
                
                if friendly_ships or system.friendly_planets == 0:
                
                    calc_oppress_hard(self)
                    
            max_effective_shields = self.entity.get_max_effective_shields
            
            if self.entity.shield_generator.is_opperational and self.entity.shield_generator.shields < max_effective_shields:
                
                calc_shields_hard(self, enemy_ships)
            
        self.order.perform()
        
class MissionCriticalAllyAI(BaseAi):
    
    def perform(self) -> None:
        
        if self.check_for_at_warp():
            return
        
        player_status = self.game_data.player.ship_status
        
        assert player_status.is_active
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return

        if self.entity.power_generator.energy <= 0:
            
            self.order =  RepairOrder(self.entity, 1)
        else:
            precision = self.entity.sensors.determin_precision
            
            enemy_ships = self.get_player_enemies_in_same_system()
            
            #friendly_ships = self.get_player_allies_in_same_system()
            
            enemy_scans = [
                ship.scan_this_ship(
                    precision=precision, scan_for_crew=False, scan_for_systems=False
                ) for ship in enemy_ships
            ]
            enemy_is_present = bool(enemy_ships)
            
            has_energy = self.entity.power_generator.energy > 0
            
            if enemy_is_present:
                
                if self.entity.ship_can_fire_torps:
                    
                    calc_torpedos_hard(self, enemy_ships, enemy_scans)
                    
                if has_energy:                    
                    if self.entity.ship_can_fire_beam_arrays:
                        
                        calc_beam_weapon_hard(self, enemy_ships, enemy_scans)
                    
                    if self.entity.ship_can_fire_cannons:
                        
                        calc_cannon_weapon_hard(self, enemy_ships, enemy_scans)
                        
                if self.entity.ship_can_cloak and self.entity.cloak.cloak_status == CloakStatus.INACTIVE:
                    
                    calc_cloak_hard(self, enemy_ships, enemy_scans)
                    
            max_effective_shields = self.entity.get_max_effective_shields
            
            if self.entity.shield_generator.is_opperational and self.entity.shield_generator.shields < max_effective_shields:
                
                calc_shields_hard(self)
            
        self.determin_order()
            
        self.order.perform()

ALL_DIFFICULTIES = {
    EasyEnemy,
    MediumEnemy,
    HardEnemy
}

def aaaaa(t:type[BaseAi]):
    
    a = t()