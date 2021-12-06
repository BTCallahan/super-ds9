from __future__ import annotations
from collections import Counter
from random import choices
from typing import TYPE_CHECKING, Optional
from data_globals import DAMAGE_TORPEDO, SECTOR_ENERGY_COST, STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK, PlanetHabitation

from order import MoveOrder, Order, EnergyWeaponOrder, RechargeOrder, RepairOrder, SelfDestructOrder, TorpedoOrder, WarpOrder

if TYPE_CHECKING:
    from starship import Starship
    from space_objects import SubSector
    from game_data import GameData

class BaseAi(Order):
    pass

def find_unopressed_planets(game_data:GameData, ship:Starship):

    for y in game_data.grid:
        for x in y:
            
            sector:SubSector = x

            if sector.coords != ship.sector_coords:

                for planet in sector.planets_dict.values():

                    if planet.planet_habbitation == PlanetHabitation.PLANET_FRIENDLY:
                        yield planet.sector_coords

class HostileEnemy(BaseAi):

    def __init__(self, entity: Starship):
        self.entity = entity
        self.target:Optional[Starship] = None
        #self.path: List[Tuple[int, int]] = []
    
    def perform(self) -> None:
        if not self.target:
            self.target = self.game_data.player
        
        order_dict = Counter([])
        
        order_dict_size = 0
        
        if not self.target.ship_status.is_active:
            # player is not alive = do nothing
            return
        order:Optional[Order] = None

        if self.entity.energy <= 0:
            order =  RepairOrder(self.entity, 1)
        else:
            #scan = self.target.scanThisShip(self.entity.determinPrecision)
            scan = self.target.scan_this_ship(self.entity.determin_precision)
            
            precision = self.entity.determin_precision
            
            ajusted_impulse = self.target.sys_impulse.get_info(precision, True)
            
            player_is_present = self.target.sector_coords == self.entity.sector_coords
            
            has_energy = self.entity.energy > 0
            
            if player_is_present:
                
                nearbye_ships = [ship for ship in self.game_data.grab_ships_in_same_sub_sector(self.target, accptable_ship_statuses={STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK}) if self.target.local_coords.distance(coords=ship.local_coords) <= self.target.ship_class.warp_breach_dist]
            
                if len(nearbye_ships) > 0:
                    
                    averaged_shield, averaged_hull, averaged_shield_damage, averaged_hull_damage, kill = self.entity.calc_self_destruct_damage(self.target, scan=scan)
                
                    self_destruct_damage = (averaged_hull_damage + (1000 if kill else 0)) * (1 - self.entity.hull_percentage)
                
                    self_destruct = SelfDestructOrder(self.entity, tuple(nearbye_ships))
                    
                    order_dict[self_destruct] = round(self_destruct_damage)
                    
                    order_dict_size+=1
            
                if self.entity.ship_can_fire_torps:
                    
                    chance_of_hit = self.entity.check_torpedo_los(self.entity.game_data.player)
                    
                    if chance_of_hit > 0.0:
                        
                        hits = 0
                        for i in range(10):
                            
                            if self.entity.roll_to_hit(
                                self.target, 
                                systems_used_for_accuray=(
                                    self.entity.sys_energy_weapon.get_effective_value,
                                    self.entity.sys_sensors.get_effective_value
                                ),
                                estimated_enemy_impulse=ajusted_impulse, 
                                damage_type=DAMAGE_TORPEDO
                            ):
                                hits += 1
                            
                        averaged_shields, averaged_hull, shield_damage, hull_damage, kill = self.entity.simulate_torpedo_hit(self.target, 10)
                        
                        torpedos_to_fire = min(self.entity.torps[self.entity.get_most_powerful_torp_avaliable], self.entity.ship_class.torp_tubes)

                        torpedo = TorpedoOrder.from_coords(
                            self.entity, torpedos_to_fire, self.target.local_coords.x, self.target.local_coords.y
                        )
                        
                        order_dict[torpedo] = round(100 * round(shield_damage + hull_damage + (1000 if kill else 0)) * (hits / 10))
                        
                        order_dict_size+=1
                    
                if has_energy:
                    if self.entity.sys_energy_weapon.is_opperational:
                        energy_to_use = min(self.entity.ship_class.max_weap_energy, self.entity.energy)
                        averaged_shields, averaged_hull, shield_damage, hull_damage, kill = self.entity.simulate_energy_hit(self.target, 10, energy_to_use)
                        
                        if shield_damage + hull_damage > 0:
                            
                            energy_weapon = EnergyWeaponOrder(self.entity, energy_to_use, target=self.target)
                            
                            order_dict[energy_weapon] = 100 * round(shield_damage + hull_damage + (1000 if kill else 0))
                            
                            order_dict_size+=1
                        
                    if self.entity.sys_impulse.is_opperational and self.entity.local_coords.distance(coords=self.target.local_coords) * 100 * self.entity.sys_impulse.affect_cost_multiplier <= self.entity.energy:
                        hull_percentage = scan["hull"] / self.target.ship_class.max_hull
                        shields_percentage = scan["shields"] / self.target.hull_percentage
                        
                        ram_damage = round(self.entity.sys_impulse.get_effective_value / (self.entity.hull_percentage + self.entity.shields_percentage) - (min(scan["sys_impulse"] * 1.25, 1.0) / (hull_percentage + shields_percentage)))
                        
                        if ram_damage > 0:
                        
                            ram = MoveOrder.from_coords(self.entity, self.target.local_coords.x, self.target.local_coords.y)
                            order_dict[ram] = ram_damage
                            
                            order_dict_size+=1
            else:
                
                ships_in_same_system = self.game_data.grab_ships_in_same_sub_sector(
                    self.entity, accptable_ship_statuses={STATUS_ACTIVE}
                )
                allied_ships_in_same_system = [ship for ship in ships_in_same_system if ship is not self.game_data.player]
                
                system = self.entity.get_sub_sector
                
                if allied_ships_in_same_system or system.friendly_planets == 0:
                
                    unopressed_planets = tuple(planet for planet in find_unopressed_planets(self.entity.game_data, self.entity) if self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier <= self.entity.energy)

                    number_of_unoppressed_planets = len(unopressed_planets)
                    
                    if number_of_unoppressed_planets == 1:
                        
                        planet = unopressed_planets[0]
                        
                        energy_cost = self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier
                            
                        warp_to = WarpOrder.from_coords(self.entity, planet.x, planet.y)
                        
                        order_dict[warp_to] = self.entity.energy - round(energy_cost)
                        
                        order_dict_size+=1
                        
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
                        
                        order_dict[warp_to] = self.entity.energy - round(energy_cost)
                        
                        order_dict_size+=1
                    
            if self.entity.sys_shield_generator.is_opperational:
                
                recharge_amount = self.entity.get_max_effective_shields - self.entity.shields
                
                recharge= RechargeOrder(self.entity, recharge_amount)
                                
                order_dict[recharge] = recharge_amount * 10
                
                order_dict_size+=1
                
            #total = fireTorp + firePhaser + recharge + repair

            #if self.entity.game_data.player.sector_coords != self.entity.sector_coords:
            if order_dict_size == 0:
            
                order = RepairOrder(self.entity, 1)
                
            elif order_dict_size == 1:
                
                order = tuple(order_dict.keys())[0]
                
            else:
                
                highest_order_value = max(order_dict.values())
                
                half_highest_order_value = round(highest_order_value * 0.5)
                
                # we only want orders that 
                order_counter = {
                    k:v for k,v in order_dict.items() if v >= half_highest_order_value
                }
                
                try:
                    if len(order_counter) == 1:
                        order = tuple(order_dict.keys())[0]
                    else:
                        keys = tuple(order_counter.keys())
                        weights = tuple(order_counter.values())
                        order = choices(population=keys, weights=weights, k=1)[0]
                        
                    #order = tuple(order_dict.keys())[0] if len(order_counter) == 1 else choices(tuple(order_counter.keys()), weights=tuple(order_counter.values()))[0]
                except IndexError:
                    
                    pass
            
        order.perform()

    def reactivateDerelict(self):
        player_present = self.game_data.player.sector_coords == self.entity.sector_coords
        
        weight = 0
        
        if not player_present:
            
            all_derelicts = [ship for ship in self.game_data.all_enemy_ships if ship.ship_status.is_recrewable]
            
            if all_derelicts:
                
                weight = self.entity.able_crew
                
                derelicts = [ship for ship in all_derelicts if ship.sector_coords == self.entity.sector_coords]
                
                if derelicts:
                    
                    derelicts.sort(key=lambda ship: ship.local_coords.distance(self.entity.local_coords), reverse=True)
                    
                    adjacent = [ship for ship in derelicts if ship.local_coords.is_adjacent(self.entity.local_coords)]
                
                    if adjacent:
                        
                        adjacent.sor(
                            key=lambda ship: ship.ship_class.max_crew, reverse=True
                        )
                        
                        weight -= adjacent[0].ship_class.max_crew
                        
                    else:
                
                        weight -= self.entity.local_coords.distance(derelicts[0].local_coords)
                
                else:
                    
                    all_derelicts.sort(key=lambda ship: ship.sector_coords.distance(self.entity.sector_coords), reverse=True)
                    
                    weight -= self.entity.sector_coords.distance(derelicts[0].sector_coords) * 10