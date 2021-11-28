from __future__ import annotations
from collections import Counter
from random import choices
from typing import TYPE_CHECKING, Optional
from data_globals import SECTOR_ENERGY_COST, PlanetHabitation

from order import MoveOrder, Order, EnergyWeaponOrder, RechargeOrder, RepairOrder, SelfDestructOrder, TorpedoOrder, WarpOrder

from starship import ShipStatus

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
        
        if not self.target.is_alive:
            return
        order:Optional[Order] = None

        if self.entity.energy <= 0:
            order =  RepairOrder(self.entity, 1)
        else:
            #scan = self.target.scanThisShip(self.entity.determinPrecision)
            scan = self.target.scan_this_ship(self.entity.determin_precision)
                        
            player_is_present = self.target is self.game_data.player
            
            has_energy = self.entity.energy > 0
            
            if player_is_present:
            
                averaged_shield, averaged_hull, averaged_shield_damage, averaged_hull_damage, kill = self.entity.calc_self_destruct_damage(self.target, scan=scan)
                
                self_destruct_damage = (averaged_hull_damage + (1000 if kill else 0)) * (1 - self.entity.hull_percentage)
            
                self_destruct = SelfDestructOrder(self.entity)
                
                order_dict[self_destruct] = round(self_destruct_damage)
            
                if self.entity.ship_can_fire_torps and self.entity.check_torpedo_los(self.entity.game_data.player):

                    averaged_shields, averaged_hull, shield_damage, hull_damage, kill = self.entity.simulate_torpedo_hit(self.target, 10)

                    torpedo = TorpedoOrder.from_coords(
                        self.entity, min(self.entity.torps[self.entity.get_most_powerful_torp_avaliable], self.entity.ship_data.max_torpedos), self.target.local_coords.x, self.target.local_coords.y
                    )
                    
                    order_dict[torpedo] = 100 * round(shield_damage + hull_damage + (1000 if kill else 0))
                    
                if has_energy:
                    if self.entity.sys_energy_weapon.is_opperational:
                        energy_to_use = min(self.entity.ship_data.max_weap_energy, self.entity.energy)
                        averaged_shields, averaged_hull, shield_damage, hull_damage, kill = self.entity.simulate_phaser_hit(self.target, 10, energy_to_use)
                        
                        energy_weapon = EnergyWeaponOrder(self.entity, energy_to_use, target=self.target)
                        
                        order_dict[energy_weapon] = 100 * round(shield_damage + hull_damage + (1000 if kill else 0))
                        
                    if self.entity.sys_impulse.is_opperational and self.entity.local_coords.distance(coords=self.target.local_coords) * 100 * self.entity.sys_impulse.affect_cost_multiplier <= self.entity.energy:
                        hull_percentage = scan["hull"] / self.target.ship_data.max_hull
                        shields_percentage = scan["shields"] / self.target.hull_percentage
                        
                        ram_damage = round(self.entity.sys_impulse.get_effective_value / (self.entity.hull_percentage + self.entity.shields_percentage) - (min(scan["sys_impulse"] * 1.25, 1.0) / (hull_percentage + shields_percentage)))
                        
                        ram = MoveOrder.from_coords(self.entity, self.target.local_coords.x, self.target.local_coords.y)
                        order_dict[ram] = ram_damage
            else:
                
                ships_in_same_system = self.game_data.grab_ships_in_same_sub_sector(self.entity)
                allied_ships_in_same_system = [ship for ship in ships_in_same_system if ship is not self.game_data.player]
                
                system = self.entity.get_sub_sector
                
                if allied_ships_in_same_system or system.friendlyPlanets == 0:
                
                    unopressed_planets = tuple(planet for planet in find_unopressed_planets(self.entity.game_data, self.entity) if self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier <= self.entity.energy)

                    number_of_unoppressed_planets = len(unopressed_planets)
                    
                    if number_of_unoppressed_planets == 1:
                        
                        planet = unopressed_planets[0]
                        
                        energy_cost = self.entity.sector_coords.distance(coords=planet) * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier
                            
                        warp_to = WarpOrder.from_coords(self.entity, planet.x, planet.y)
                        
                        order_dict[warp_to] = self.entity.energy - round(energy_cost)
                        
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
                    
            if has_energy and self.entity.sys_shield_generator.is_opperational:
                
                recharge_amount = self.entity.get_max_effective_shields - self.entity.shields
                
                recharge= RechargeOrder(self.entity, recharge_amount)
                                
                order_dict[recharge] = recharge_amount * 10
                
            #total = fireTorp + firePhaser + recharge + repair

            #if self.entity.game_data.player.sector_coords != self.entity.sector_coords:
            
            """
            order_dict = {
                TorpedoOrder : round(fireTorp * 100),
                EnergyWeaponOrder : round(firePhaser * 100),
                RechargeOrder : round(recharge* 10),
                RepairOrder : repair * 10,
                WarpOrder : opress * 10,
                MoveOrder : round(ram),
                SelfDestructOrder : round(self_destruct)
            }
            """
            
            hightest = max(order_dict.values())
            
            order_counter = {
                k:v for k,v in order_dict.items() if v > hightest * 0.5
            }
            
            order = choices(tuple(order_counter.keys()), weights=tuple(order_counter.values()))[0]
            """
            if ch is TorpedoOrder:
                
                order = TorpedoOrder.from_coords(self.entity, amount=self.entity.shipData.torp_tubes, x=self.target.local_coords.x, y=self.target.local_coords.y)
                #finsih this later
            elif ch is EnergyWeaponOrder:
                keValue = scan["shields"] + scan["hull"]
                #en = max(0, min(keValue, self.entity.energy))
                order = EnergyWeaponOrder(self.entity, keValue, target=self.target)
            elif ch is RechargeOrder:
                reValue = min(self.entity.shipData.max_shields - self.entity.shields, self.entity.energy)
                order = RechargeOrder(self.entity, reValue)
            elif ch is RepairOrder:
                #unopressed_systems = 
                order = RepairOrder(self.entity, 1)
            else:
                co = planet_counter.most_common(1)[0][0]

                order = WarpOrder(self.entity, co.x, co.y)
            """
            
        order.perform()

    

    def reactivateDerelict(self):
        player_present = self.game_data.player.sectorCoords == self.entity.sectorCoords
        
        weight = 0
        
        if not player_present:
            
            all_derelicts = [ship for ship in self.game_data.all_enemy_ships if ship.ship_status == ShipStatus.DERLICT]
            
            if all_derelicts:
                
                weight = self.entity.ableCrew
                
                derelicts = [ship for ship in all_derelicts if ship.sectorCoords == self.entity.sectorCoords]
                
                if derelicts:
                    
                    derelicts.sort(key=lambda ship: ship.localCoords.distance(self.entity.localCoords), reverse=True)
                    
                    adjacent = [ship for ship in derelicts if ship.localCoords.is_adjacent(self.entity.localCoords)]
                
                    if adjacent:
                        
                        adjacent.sor(
                            key=lambda ship: ship.shipData.maxCrew, reverse=True
                        )
                        
                        weight -= adjacent[0].shipData.maxCrew
                        
                    else:
                
                        weight -= self.entity.localCoords.distance(derelicts[0].localCoords)
                
                else:
                    
                    all_derelicts.sort(key=lambda ship: ship.sectorCoords.distance(self.entity.sectorCoords), reverse=True)
                    
                    weight -= self.entity.sectorCoords.distance(derelicts[0].sectorCoords) * 10