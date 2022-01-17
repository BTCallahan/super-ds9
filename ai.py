from __future__ import annotations
from collections import Counter
from random import choices
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Union
from coords import IntOrFloat
from data_globals import DAMAGE_TORPEDO, LOCAL_ENERGY_COST, PLANET_FRIENDLY, SECTOR_ENERGY_COST, STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK, CloakStatus

from order import CloakOrder, MoveOrder, Order, EnergyWeaponOrder, OrderWarning, RechargeOrder, RepairOrder, SelfDestructOrder, TorpedoOrder, WarpOrder

if TYPE_CHECKING:
    from starship import Starship
    from space_objects import SubSector
    from game_data import GameData

class BaseAi(Order):
    
    order:Optional[Order]
    
    def __init__(self, entity: Starship):
        
        self.entity = entity
        self.target:Optional[Starship] = None
        
        self.order_dict = Counter([])
        
        self.order_dict_size = 0
        
        self.precision = self.entity.determin_precision
    
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
    
    def calc_beam_weapon(self):
        raise NotImplementedError

    def calc_cannon_waepon(self):
        raise NotImplementedError

    def calc_torpedos(self):
        raise NotADirectoryError
    
    def calc_shields(self):
        raise NotImplementedError
    
    def calc_ram(self):
        raise NotImplementedError
    
    def calc_cloak(self):
        raise NotImplementedError
    
    def calc_auto_destruct(self, scan:Dict[str, Union[str, int]], nearbye_ships:Iterable[Starship]):
        raise NotImplementedError

    def calc_oppress(self):
        raise NotImplementedError
    
def find_unopressed_planets(game_data:GameData, ship:Starship):

    for y in game_data.grid:
        for x in y:
            
            sector:SubSector = x

            if sector.coords != ship.sector_coords:

                for planet in sector.planets_dict.values():

                    if planet.planet_habbitation is PLANET_FRIENDLY:
                        yield planet.sector_coords

class EasyEnemy(BaseAi):
        
    def perform(self) -> None:
        if not self.target:
            self.target = self.game_data.player
        
        player_status = self.target.ship_status
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return
        self.order:Optional[Order] = None

        if self.entity.energy <= 0:
            
            self.order =  RepairOrder(self.entity, 1)
        else:
            self.calc_beam_weapon()
            
            if self.entity.ship_can_fire_torps:
                    
                self.calc_torpedos()
                
        self.determin_order()
        self.order.perform()         
            
    def calc_torpedos(self):
        
        chance_of_hit = self.entity.check_torpedo_los(self.entity.game_data.player)
        if chance_of_hit > 0:
                
            torpedos_to_fire = min(
                self.entity.torps[self.entity.get_most_powerful_torp_avaliable], self.entity.ship_class.torp_tubes
            )

            torpedo = TorpedoOrder.from_coords(
                self.entity, torpedos_to_fire, self.target.local_coords.x, self.target.local_coords.y
            )
            self.order_dict[torpedo] = 1000
            self.order_dict_size+=1
            
    def calc_beam_weapon(self):
        
        energy_weapon=EnergyWeaponOrder.single_target_beam(
                entity=self.entity,
                target=self.target,
                amount=min(self.entity.get_max_effective_beam_firepower, self.entity.energy)
            )
            
        self.order_dict[energy_weapon] = 1000
        self.order_dict_size+=1
    
    def calc_cannon_waepon(self):
        
        cannon_weapon = EnergyWeaponOrder.cannon(
            entity=self.entity,
            target=self.target,
            amount=min(self.entity.get_max_effective_cannon_firepower, self.entity.energy)
        )
        
        self.order_dict[cannon_weapon] = 1000
        self.order_dict_size+=1
        
class MediumEnemy(BaseAi):
    
    def perform(self) -> None:
        if not self.target:
            self.target = self.game_data.player
        
        player_status = self.target.ship_status
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return
        self.order:Optional[Order] = None

        if self.entity.energy <= 0:
            
            self.order =  RepairOrder(self.entity, 1)
        else:
            if self.entity.ship_can_fire_beam_arrays:
                
                self.calc_beam_weapon()
            
            if self.entity.ship_can_fire_cannons:
                
                self.calc_cannon_waepon()
            
            if self.entity.ship_can_fire_torps:
                    
                self.calc_torpedos()
            
            if self.entity.ship_can_cloak:
                
                self.calc_cloak()
                
            if self.entity.get_max_effective_shields > 0:
                
                self.calc_shields()
                
        self.determin_order()
        self.order.perform()
    pass

    def calc_shields(self):
        recharge_amount = self.entity.get_max_effective_shields - self.entity.shields
                
        recharge= RechargeOrder(self.entity, recharge_amount)
                        
        self.order_dict[recharge] = recharge_amount * 10
        
        self.order_dict_size+=1
    
    def calc_torpedos(self):
        chance_of_hit = self.entity.check_torpedo_los(self.entity.game_data.player)
            
        if chance_of_hit > 0.0:
            
            averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_torpedo_hit(
                self.target, 5
            )
            
            torpedos_to_fire = min(
                self.entity.torps[self.entity.get_most_powerful_torp_avaliable], self.entity.ship_class.torp_tubes
            )

            torpedo = TorpedoOrder.from_coords(
                self.entity, torpedos_to_fire, self.target.local_coords.x, self.target.local_coords.y
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
                        300 if self.entity.cloak_status != CloakStatus.INACTIVE else 100
                    ) * (total_shield_dam + total_hull_dam + (1000 if ship_kills else 0))
                
                self.order_dict_size+=1

    def calc_beam_weapon(self):
        
        energy_to_use = min(self.entity.get_max_effective_beam_firepower, self.entity.energy)
        
        averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_energy_hit(
            self.target, 5, energy_to_use
        )
        if total_shield_dam + total_hull_dam > 0:
            
            energy_weapon = EnergyWeaponOrder.single_target_beam(self.entity, energy_to_use, target=self.target)
            
            self.order_dict[energy_weapon] = (
                300 if self.entity.cloak_status != CloakStatus.INACTIVE else 100
            ) * (total_shield_dam + total_hull_dam + (1000 * ship_kills))
            
            self.order_dict_size+=1

    def calc_cannon_waepon(self):
        energy_to_use = min(self.entity.get_max_effective_cannon_firepower, self.entity.energy)
        
        averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_energy_hit(
            self.target, 5, energy_to_use,
            cannon=True
        )
        if total_shield_dam + total_hull_dam > 0:
            
            energy_weapon = EnergyWeaponOrder.cannon(self.entity, energy_to_use, target=self.target)
            
            self.order_dict[energy_weapon] = (
                300 if self.entity.cloak_status != CloakStatus.INACTIVE else 100
            ) * (total_shield_dam + total_hull_dam + (1000 * ship_kills))
            
            self.order_dict_size+=1

    def calc_cloak(self):
        
        cloak = CloakOrder(self.entity, deloak=False)
                    
        cloak_str = self.entity.ship_class.cloak_strength
        
        detect_str = self.target.ship_class.detection_strength
        
        self.order_dict[cloak] = (
            500 * (cloak_str - detect_str)
        )
        self.order_dict_size+=1

class HardEnemy(BaseAi):
    
    def perform(self) -> None:
        if not self.target:
            self.target = self.game_data.player
        
        order_dict = Counter([])
        
        order_dict_size = 0
        
        player_status = self.target.ship_status
        
        if not player_status.is_active:
            # player is not alive = do nothing
            return
        order:Optional[Order] = None

        if self.entity.energy <= 0:
            order =  RepairOrder(self.entity, 1)
        else:
            #scan = self.target.scanThisShip(self.entity.determinPrecision)
            precision = self.entity.determin_precision
            
            scan = self.target.scan_this_ship(precision, use_effective_values=True)
            
            player_is_present = self.target.sector_coords == self.entity.sector_coords
            
            has_energy = self.entity.energy > 0
            
            player_is_not_cloaked = player_status.is_visible
            
            if player_is_present and player_is_not_cloaked:
                
                #ajusted_impulse = self.target.sys_impulse.get_info(precision, True)
                
                nearbye_ships = [
                    ship for ship in self.game_data.grab_ships_in_same_sub_sector(
                        self.target, accptable_ship_statuses={
                            STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED
                        }
                    )
                ]
                
                nearbye_enemy_ships = [ship for ship in nearbye_ships if ship.nation != self.entity.nation]
                
                #nearbye_friendly_ships = [ship for ship in nearbye_ships if ship.nation != self.entity.nation]
            
                if len(nearbye_enemy_ships) > 0:
                    
                    self.calc_auto_destruct()
                    
                if self.entity.ship_can_fire_torps:
                    
                    self.calc_torpedos()
                    
                if has_energy:                    
                    if self.entity.ship_can_fire_beam_arrays:
                        
                        self.calc_beam_weapon()
                    
                    if self.entity.ship_can_fire_cannons:
                        
                        self.calc_cannon_waepon()
                        
                    if self.entity.can_move_stl and self.entity.local_coords.distance(
                        coords=self.target.local_coords
                    ) * LOCAL_ENERGY_COST * self.entity.sys_impulse.affect_cost_multiplier <= self.entity.energy:
                        
                        self.calc_ram()
                        
                if self.entity.ship_can_cloak and self.entity.cloak_status == CloakStatus.INACTIVE:
                    
                    self.calc_cloak()
            else:
                # if the player is not present:
                
                ships_in_same_system = self.game_data.grab_ships_in_same_sub_sector(
                    self.entity, accptable_ship_statuses={STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED}
                )
                allied_ships_in_same_system = [
                    ship for ship in ships_in_same_system if ship is not self.game_data.player
                ]
                
                system = self.entity.get_sub_sector
                
                if allied_ships_in_same_system or system.friendly_planets == 0:
                
                    self.calc_oppress()
                    
            max_effective_shields = self.entity.get_max_effective_shields
            
            if self.entity.sys_shield_generator.is_opperational and self.entity.shields < max_effective_shields:
                
                self.calc_shields()
            
        order.perform()
        
    def calc_oppress(self):
        
        unopressed_planets = tuple(
            planet for planet in find_unopressed_planets(
                self.entity.game_data, self.entity
            ) if self.entity.sector_coords.distance(
                coords=planet
            ) * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier <= self.entity.energy
        )

        number_of_unoppressed_planets = len(unopressed_planets)
        
        if number_of_unoppressed_planets == 1:
            
            planet = unopressed_planets[0]
            
            energy_cost = self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier
                
            warp_to = WarpOrder.from_coords(self.entity, planet.x, planet.y)
            
            self.order_dict[warp_to] = self.entity.energy - round(energy_cost)
            
            self.order_dict_size+=1
            
        elif number_of_unoppressed_planets > 1:

            planet_counter = Counter(unopressed_planets)
            
            highest = max(planet_counter.values())
            
            most_common = [
                k for k,v in planet_counter.items() if v == highest
            ]
            
            most_common.sort(key=lambda coords: coords.distance(coords=self.entity.sector_coords), reverse=True)

            planet = most_common[0]
            
            warp_to = WarpOrder.from_coords(self.entity, planet.x, planet.y)
            
            energy_cost = self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier
            
            self.order_dict[warp_to] = self.entity.energy - round(energy_cost)
            
            self.order_dict_size+=1
        
    def calc_auto_destruct(self, scan:Dict[str, Union[str, int]], nearbye_ships:Iterable[Starship]):
        averaged_shield, averaged_hull, averaged_shield_damage, averaged_hull_damage, kill, crew_readyness = self.entity.calc_self_destruct_damage(self.target, scan=scan)
                
        self_destruct_damage = (averaged_hull_damage + (1000 if kill else 0)) * (1 - self.entity.hull_percentage)
    
        self_destruct = SelfDestructOrder(self.entity, tuple(nearbye_ships))
        
        self.order_dict[self_destruct] = self_destruct_damage
        
        self.order_dict_size+=1
        
    def calc_ram(self, scan:Dict[str, Union[str, int]]):
        hull_percentage = scan["hull"] / self.target.ship_class.max_hull
        shields_percentage = scan["shields"] / self.target.hull_percentage
        
        ram_damage = round(
            self.entity.sys_impulse.get_effective_value / (
                self.entity.hull_percentage + self.entity.shields_percentage
            ) - (min(scan["sys_impulse"] * 1.25, 1.0) / (hull_percentage + shields_percentage)))
        
        if ram_damage > 0:
            
            energy_cost = round(
                self.entity.local_coords.distance(
                    x=self.target.local_coords.x, y=self.target.local_coords.y
                ) * LOCAL_ENERGY_COST * 
                self.entity.sys_impulse.affect_cost_multiplier
            )
        
            ram = MoveOrder.from_coords(
                self.entity, self.target.local_coords.x, self.target.local_coords.y, energy_cost
            )
            self.order_dict[ram] = ram_damage
            
            self.order_dict_size+=1
        
    def calc_torpedos(self):
        chance_of_hit = self.entity.check_torpedo_los(self.entity.game_data.player)
            
        if chance_of_hit > 0.0:
            
            averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_torpedo_hit(self.target, 10)
            
            torpedos_to_fire = min(self.entity.torps[self.entity.get_most_powerful_torp_avaliable], self.entity.ship_class.torp_tubes)

            torpedo = TorpedoOrder.from_coords(
                self.entity, torpedos_to_fire, self.target.local_coords.x, self.target.local_coords.y
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
                        300 if self.entity.cloak_status != CloakStatus.INACTIVE else 100
                    ) * (total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills))
                
                self.order_dict_size+=1

    def calc_shields(self):
        recharge_amount = self.entity.get_max_effective_shields - self.entity.shields
                
        recharge= RechargeOrder(self.entity, recharge_amount)
                        
        self.order_dict[recharge] = recharge_amount * 10
        
        self.order_dict_size+=1
    
    def calc_beam_weapon(self):
        
        energy_to_use = min(self.entity.get_max_effective_beam_firepower, self.entity.energy)
        
        averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_energy_hit(
            self.target, 10, energy_to_use, simulate_systems=True
        )
        if total_shield_dam + total_hull_dam > 0:
            
            energy_weapon = EnergyWeaponOrder.single_target_beam(self.entity, energy_to_use, target=self.target)
            
            self.order_dict[energy_weapon] = (
                300 if self.entity.cloak_status != CloakStatus.INACTIVE else 100
            ) * (
                total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)
            )
            
            self.order_dict_size+=1
    
    def calc_cannon_waepon(self):
        
        energy_to_use = min(self.entity.get_max_effective_cannon_firepower, self.entity.energy)
        
        averaged_shields, averaged_hull, total_shield_dam, total_hull_dam, ship_kills, crew_kills, averaged_crew_readyness = self.entity.simulate_energy_hit(
            self.target, 10, energy_to_use, simulate_systems=True, cannon=True
        )
        if total_shield_dam + total_hull_dam > 0:
            
            energy_weapon = EnergyWeaponOrder.cannon(self.entity, energy_to_use, target=self.target)
            
            self.order_dict[energy_weapon] = (
                300 if self.entity.cloak_status != CloakStatus.INACTIVE else 100
            ) * (
                total_shield_dam + total_hull_dam + (1000 * ship_kills) + (1000 * crew_kills)
            )
            
            self.order_dict_size+=1
    
    def calc_cloak(self):
        cloak = CloakOrder(self.entity, deloak=False)
                    
        cloak_str = self.entity.sys_cloak.get_effective_value * self.entity.ship_class.cloak_strength
        
        detect_str = self.target.sys_cloak.get_info(
            precision=self.precision, effective_value=True
        ) * self.target.ship_class.detection_strength
        
        self.order_dict[cloak] = (
            500 * (cloak_str - detect_str)
        )
        self.order_dict_size+=1

    def reactivate_derelict(self):
        player_present = self.game_data.player.sector_coords == self.entity.sector_coords
        
        weight = 0
        
        if not player_present and not self.entity.ship_class.is_automated:
            
            all_derelicts = [ship for ship in self.game_data.all_enemy_ships if ship.ship_status.is_recrewable]
            
            if all_derelicts:
                
                weight = self.entity.able_crew
                
                derelicts = [ship for ship in all_derelicts if ship.sector_coords == self.entity.sector_coords]
                
                if derelicts:
                    
                    derelicts.sort(key=lambda ship: ship.local_coords.distance(self.entity.local_coords), reverse=True)
                    
                    adjacent = [ship for ship in derelicts if ship.local_coords.is_adjacent(self.entity.local_coords)]
                
                    if adjacent:
                        
                        adjacent.sort(
                            key=lambda ship: ship.ship_class.max_crew, reverse=True
                        )
                        
                        weight -= adjacent[0].ship_class.max_crew
                        
                    else:
                
                        weight -= self.entity.local_coords.distance(derelicts[0].local_coords)
                
                else:
                    
                    all_derelicts.sort(key=lambda ship: ship.sector_coords.distance(self.entity.sector_coords), reverse=True)
                    
                    weight -= self.entity.sector_coords.distance(derelicts[0].sector_coords) * 10

ALL_DIFFICULTIES = {
    EasyEnemy,
    MediumEnemy,
    HardEnemy
}

def aaaaa(t:type[BaseAi]):
    
    a = t()