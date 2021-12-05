from __future__ import annotations
from enum import Enum, auto
from math import atan2, ceil, floor
from random import choice
from coords import Coords, IntOrFloat
from typing import TYPE_CHECKING, Iterable, Optional
from global_functions import to_rads, headingToCoords, headingToDirection
from data_globals import DAMAGE_BEAM, DAMAGE_RAMMING, LOCAL_ENERGY_COST, SECTOR_ENERGY_COST, STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK, PlanetHabitation
from space_objects import Planet, SubSector
from get_config import config_object

if TYPE_CHECKING:
    from starship import Starship

class OrderWarning(Enum):

    SAFE = auto()
    ZERO_VALUE_ENTERED = auto()
    NO_CHANGE_IN_POSITION = auto()
    NO_CHANGE_IN_SHIELD_ENERGY = auto()
    ENEMY_SHIPS_NEARBY = auto()
    ENEMY_SHIPS_NEARBY_WARN = auto()
    NO_ENEMY_SHIPS_NEARBY = auto()
    TORPEDO_WILL_HIT_PLANET = auto()
    TORPEDO_COULD_HIT_PLANET = auto()
    TORPEDO_WILL_NOT_HIT_ANYTHING = auto()
    NO_TORPEDOS_LEFT = auto()
    SHIP_WILL_COLLIDE_WITH_PLANET = auto()
    SHIP_WILL_COLLIDE_WITH_STAR = auto()
    SHIP_COULD_COLLIDE_WITH_SHIP = auto()
    NOT_ENOUGHT_ENERGY = auto()
    NOT_ENOUGHT_CREW = auto()
    OUT_OF_RANGE = auto()
    NO_TARGET = auto()
    NO_TARGETS = auto()
    SYSTEM_INOPERATIVE = auto()
    PLANET_TOO_DISTANT = auto()
    PLANET_TOO_PRIMITIVE = auto()
    PLANET_UNFRIENDLY = auto()
    PLANET_AFRAID = auto()
    NO_REPAIRS_NEEDED = auto()
    
blocks_action = {
    OrderWarning.NOT_ENOUGHT_ENERGY : "Error: We possess insufficent energy reserves",
    OrderWarning.OUT_OF_RANGE : "Error: Our destination is out of range",
    OrderWarning.SYSTEM_INOPERATIVE : "Error: That ship system is off line",
    OrderWarning.PLANET_AFRAID : "Error: The planet is too afarid of the nearby hostile forces",
    OrderWarning.PLANET_TOO_DISTANT : "Error: The planet is too far from our ship",
    OrderWarning.PLANET_TOO_PRIMITIVE : "Error: The planet lacks the infurstucture to repaire and repsuply our ship",
    OrderWarning.PLANET_UNFRIENDLY : "Error: The planet is hostile to us",
    OrderWarning.NO_TARGET : "Error: Our sensors have not targeted an enemy ship",
    OrderWarning.NO_TARGETS : "Error: There are no enemy ships in the area",
    OrderWarning.NO_TORPEDOS_LEFT : "Error: We have no remaining torpedos.",
    OrderWarning.ZERO_VALUE_ENTERED : "Error: You have entered a value of zero.",
    OrderWarning.NO_CHANGE_IN_POSITION : "Error: There is no change in position", # reword this later
    OrderWarning.NO_CHANGE_IN_SHIELD_ENERGY : "Error: There is no change in shield energy."
}

torpedo_warnings = {
    OrderWarning.TORPEDO_WILL_HIT_PLANET : "Warning: If we fire, the torpedo will hit a planet.",
    OrderWarning.TORPEDO_COULD_HIT_PLANET : "Warning: If the torpedo misses, it could hit a planet.",
    OrderWarning.TORPEDO_WILL_NOT_HIT_ANYTHING : "Warning: The torpedo will not hit anything."
}

collision_warnings = {
    OrderWarning.SHIP_COULD_COLLIDE_WITH_SHIP : "Warning: That course could result in a ship to ship collision!",
    OrderWarning.SHIP_WILL_COLLIDE_WITH_PLANET : "Warning: That course will result in our ship crashing into a planet!",
    OrderWarning.SHIP_WILL_COLLIDE_WITH_STAR : "Warning: That course will result in our ship crashing into a star!"
}

misc_warnings = {
    OrderWarning.NO_ENEMY_SHIPS_NEARBY : "Warning: There are no enemy ships nearbye.",
    OrderWarning.ENEMY_SHIPS_NEARBY_WARN : "Warning: There are no enemy ships nearbye.",
    OrderWarning.NO_REPAIRS_NEEDED : "Warning: No repairs are needed right now."
}

class Order:

    def __init__(self, entity:Starship) -> None:
        self.entity = entity
        
    def perform(self) -> None:

        raise NotImplementedError()
    
    def __hash__(self) -> int:
        return hash((self.entity))
    
    @property
    def game_data(self):
        return self.entity.game_data
    
    def can_be_carried_out(self) -> bool:

        return self.raise_warning() not in blocks_action
    
    def raise_warning(self):
        return OrderWarning.SAFE
    
class WarpOrder(Order):

    def __init__(self, entity:Starship, heading:int, distance:int, x:int, y:int) -> None:
        super().__init__(entity)
        self.heading = heading
        self.distance = distance
        self.cost = ceil(self.distance * SECTOR_ENERGY_COST * self.entity.sys_warp_drive.affect_cost_multiplier)
        self.x, self.y = x,y
        # TODO: Implement warp speed
    
    def __hash__(self):
        return hash((self.entity, self.heading, self.distance, self.cost, self.x, self.y))
    
    @classmethod
    def from_coords(cls, entity:Starship, x:int, y:int):

        distance = entity.sector_coords.distance(coords=Coords(x,y))

        rel_x = x - entity.sector_coords.x
        rel_y = y - entity.sector_coords.y

        c:Coords = Coords(rel_x, rel_y)
        x_, y_ = c.normalize()

        heading = atan2(y_, x_)
        return cls(entity, heading, distance, x, y)
    
    @classmethod
    def from_heading(cls, entity:Starship, heading:int, distance:int):

        x, y = headingToCoords(heading, distance, entity.sector_coords.x, entity.sector_coords.y, config_object.sector_width, config_object.sector_height)

        return cls(entity, heading, distance, x, y)

    def perform(self) -> None:

        #self.entity.warp(self.x, self.y)
        
        old_x, old_y = self.entity.sector_coords.x, self.entity.sector_coords.y
        
        self.entity.sector_coords.x = self.x
        self.entity.sector_coords.y = self.y

        ships = self.entity.game_data.grab_ships_in_same_sub_sector(self.entity)

        subsector: SubSector = self.entity.game_data.grid[self.y][self.x]

        safe_spots = subsector.safeSpots.copy()

        for ship in ships:

            safe_spots.remove(ship.local_coords.create_coords())

        spot = choice(safe_spots)
        
        self.entity.local_coords.x = spot.x
        self.entity.local_coords.y = spot.y
        
        energy_cost = self.cost

        self.entity.energy -= energy_cost

        if self.entity.is_controllable:
            
            self.game_data.player_record["energy_used"] += energy_cost
            self.game_data.player_record["times_gone_to_warp"] += 1

            self.game_data.engine.message_log.add_message(
                "Engage!"
            )
            self.game_data.engine.message_log.add_message(
                f"The {self.entity.name} hase come out of warp in {self.entity.sector_coords.x} {self.entity.sector_coords.y}."
            )
                
        self.entity.turn_repairing = 0
    
    def raise_warning(self):
        if not self.entity.sys_warp_drive.is_opperational:
            return OrderWarning.SYSTEM_INOPERATIVE
        
        if self.x == self.entity.sector_coords.x and self.y == self.entity.sector_coords.y:
            return OrderWarning.NO_CHANGE_IN_POSITION
        
        if not (0 <= self.x < config_object.sector_width and 0 <= self.y < config_object.subsector_height):
            return OrderWarning.OUT_OF_RANGE
        
        #distance_to_destination = self.entity.sector_coords.distance(x=self.x, y=self.y)
        
        return OrderWarning.NOT_ENOUGHT_ENERGY if self.cost > self.entity.energy else OrderWarning.SAFE

class MoveOrder(Order):

    def __init__(self, entity:Starship, *, heading:IntOrFloat, distance:int, x:int, y:int, x_aim:float, y_aim:float) -> None:
        super().__init__(entity)
        self.heading = heading
        self.distance = distance
        self.cost = ceil(distance * self.entity.sys_impulse.affect_cost_multiplier * LOCAL_ENERGY_COST)
        self.x, self.y = x,y
        self.x_aim, self.y_aim = x_aim, y_aim

        #x, y = headingToDirection(self.heading)

        c:Coords = Coords(x=x - entity.local_coords.x, y=y - entity.local_coords.y)

        x_, y_ = c.normalize()

        self.coord_list = tuple([Coords(co.x + self.entity.local_coords.x, co.y + self.entity.local_coords.y) for co in self.game_data.engine.get_lookup_table(direction_x=x_, direction_y=y_, normalise_direction=False)][:ceil(distance)])

        self.ships = {ship.local_coords.create_coords() : ship for ship in self.entity.game_data.grab_ships_in_same_sub_sector(self.entity) if ship.local_coords in self.coord_list}
    
    def __hash__(self):
        return hash((self.entity, self.heading, self.distance, self.cost, self.x, self.y, self.x_aim, self.y_aim))
    
    @classmethod
    def from_coords(cls, entity:Starship, x:int, y:int):

        distance = entity.local_coords.distance(x=x,y=y)

        rel_x = x - entity.local_coords.x
        rel_y = y - entity.local_coords.y

        c:Coords = Coords(rel_x, rel_y)
        x_, y_ = c.normalize()

        heading = atan2(y_, x_) / to_rads

        return cls(entity, distance=distance, heading=heading, x=x, y=y, x_aim=x_, y_aim=y_)
    
    @classmethod
    def from_heading(cls, entity:Starship, heading:int, distance:int):
        
        x_aim, y_aim = headingToDirection(heading)
        x, y = headingToCoords(
            heading, config_object.max_move_distance, 
            entity.local_coords.x, entity.local_coords.y,
            config_object.subsector_width, config_object.subsector_height
        )

        return cls(entity, distance=distance, heading=heading, x=x, y=y, x_aim=x_aim, y_aim=y_aim)

    """
    def can_be_carried_out(self):

        if self.entity.energy < self.distance * self.entity.sys_impulse.affect_cost_multiplier * LOCAL_ENERGY_COST:
            return False

        last_coord = self.coord_list[-1]

        return (
            self.entity.sys_impulse.isOpperational and
            self.entity.energy >= self.distance * (1 / self.entity.sys_impulse.getEffectiveValue) and
            last_coord.x in self.game_data.subsec_size_range_x and
            last_coord.y in self.game_data.subsec_size_range_y
            )
    """

    def perform(self) -> None:

        sub_sector:SubSector = self.entity.game_data.grid[self.entity.sector_coords.y][self.entity.sector_coords.x]

        #ships = [ship for ship in self.entity.game_data.grab_ships_in_same_sub_sector(self.entity) if ship.local_coords in self.coord_list]

        #self.entity.move()
        
        energy_cost = self.cost

        self.entity.energy -= energy_cost

        if self.entity.is_controllable:
            
            self.game_data.player_record["energy_used"] += energy_cost

        for co in self.coord_list:
            try:
                planet = sub_sector.planets_dict[co]
                break

            except KeyError:
                try:
                    star = sub_sector.stars_dict[co]
                    break

                except KeyError:

                    try:
                        ship = self.ships[co]
                        hit = self.entity.roll_to_hit(
                            ship, 
                            systems_used_for_accuray=(
                                self.entity.sys_impulse.get_effective_value,
                                self.entity.sys_sensors.get_effective_value
                            ),
                            damage_type=DAMAGE_RAMMING
                        )
                        self.entity.ram(ship)

                    except KeyError:
                        pass
                    
        self.entity.local_coords.x = self.x
        self.entity.local_coords.y = self.y
        
        self.entity.turn_repairing = 0

    def raise_warning(self):
        
        if self.x == self.entity.local_coords.x and self.y == self.entity.local_coords.y:
            return OrderWarning.NO_CHANGE_IN_POSITION

        if not self.entity.sys_impulse.is_opperational:
            return OrderWarning.SYSTEM_INOPERATIVE

        last_coord = self.coord_list[-1]

        if last_coord.x not in range(config_object.subsector_width) and last_coord.y not in range(config_object.subsector_height):
            return OrderWarning.OUT_OF_RANGE
        
        if self.entity.energy < self.cost:
            return OrderWarning.NOT_ENOUGHT_ENERGY

        sub_sector:SubSector = self.entity.game_data.grid[self.entity.sector_coords.y][self.entity.sector_coords.x]

        could_collide_with_ship = False

        for co in self.coord_list:
            try:
                planet = sub_sector.planets_dict[co]
                return OrderWarning.SHIP_WILL_COLLIDE_WITH_PLANET

            except KeyError:
                try:
                    star = sub_sector.stars_dict[co]
                    return OrderWarning.SHIP_WILL_COLLIDE_WITH_STAR

                except KeyError:
                    try:
                        ship = self.ships[co]
                        could_collide_with_ship = True

                    except KeyError:
                        pass
        return OrderWarning.SHIP_COULD_COLLIDE_WITH_SHIP if could_collide_with_ship else OrderWarning.SAFE

class EnergyWeaponOrder(Order):

    def __init__(self, entity:Starship, amount:int, *, target:Optional[Starship]=None, targets:Optional[Iterable[Starship]]=None) -> None:
        super().__init__(entity)
        self.amount = min(entity.energy, amount, entity.ship_data.max_weap_energy)
        self.target = target
        self.targets = targets
    
    def __hash__(self):
        return hash((self.entity, self.amount, self.target, self.targets))
    
    @classmethod
    def single_target(cls, entity:Starship, amount:int, target:Starship):
        return cls(entity, amount, target=target)

    @classmethod
    def multiple_targets(cls, entity:Starship, amount:int, targets:Iterable[Starship]):
        return cls(entity, amount, targets=targets)

    @property
    def multi_targets(self):
        return self.targets is not None
    
    def perform(self) -> None:

        actual_amount = floor(self.entity.sys_energy_weapon.get_effective_value * self.amount)

        if self.multi_targets:
            
            number_of_targers = len(self.targets)

            amount = actual_amount / number_of_targers
            
            cost = self.amount / number_of_targers

            for ship in self.targets:

                self.entity.attack_energy_weapon(ship, actual_amount, cost)
        else:
            self.entity.attack_energy_weapon(self.target, actual_amount, self.amount, DAMAGE_BEAM)
            
        if self.entity.is_controllable:
            self.game_data.player_record["energy_used"] += self.amount
        
        self.entity.turn_repairing = 0

    def raise_warning(self):

        if not self.entity.sys_energy_weapon.is_opperational:
            return OrderWarning.SYSTEM_INOPERATIVE
        
        if self.multi_targets and not self.targets:
            return OrderWarning.NO_TARGETS
        
        if not self.multi_targets and not self.target:
            return OrderWarning.NO_TARGET
        
        if self.amount == 0:
            return OrderWarning.ZERO_VALUE_ENTERED
        
        return OrderWarning.NOT_ENOUGHT_ENERGY if self.amount > self.entity.energy else OrderWarning.SAFE
        
class TorpedoOrder(Order):

    def __init__(self, entity:Starship, amount:int, *, heading:IntOrFloat, x:int, y:int, x_aim:float, y_aim:float) -> None:
        super().__init__(entity)
        self.heading = heading
        self.amount = amount
        self.x, self.y = x,y
        self.x_aim, self.y_aim = x_aim, y_aim
        
        torp_coords = self.game_data.engine.get_lookup_table(direction_x=x_aim, direction_y=y_aim, normalise_direction=False)
        
        self.coord_list = tuple(Coords(co.x+entity.local_coords.x, co.y+entity.local_coords.y) for co in torp_coords)

        self.ships = {ship.local_coords.create_coords() : ship for ship in self.entity.game_data.grab_ships_in_same_sub_sector(self.entity, accptable_ship_statuses={STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK}) if ship.local_coords in self.coord_list and ship.ship_status.is_active}
    
    def __hash__(self):
        return hash((self.entity, self.heading, self.amount, self.x, self.y, self.x_aim, self.y_aim, self.coord_list))
    
    @classmethod
    def from_coords(cls, entity:Starship, amount:int, x:int, y:int):

        rel_x = x - entity.sector_coords.x
        rel_y = y - entity.sector_coords.y

        c:Coords = Coords(rel_x, rel_y)
        x_, y_ = c.normalize()

        heading = atan2(y_, x_) / to_rads
        return cls(entity, amount, heading=heading, x=x, y=y, x_aim=x_, y_aim=y_)
    
    @classmethod
    def from_heading(cls, entity:Starship, heading:int, amount:int):
        #m=max(config_object.max_move_distance, config_object.max_warp_distance)

        x_aim, y_aim = headingToDirection(heading)
        
        c:Coords = Coords(x_aim,y_aim)
        
        x_aim, y_aim = c.normalize()
        
        x, y = headingToCoords(heading, config_object.max_move_distance, 
        entity.sector_coords.x, entity.sector_coords.y,
        config_object.subsector_width, config_object.subsector_height
        )

        return cls(entity, amount, heading=heading, x=x, y=y, x_aim=x_aim, y_aim=y_aim)

    def perform(self) -> None:

        #torpedo = torpedo_types[self.entity.torpedo_loaded]

        self.entity.game_data.handle_torpedo(
            shipThatFired=self.entity,torpsFired=self.amount, coords=self.coord_list, torpedo_type=self.entity.torpedo_loaded, ships_in_area=self.ships, heading=self.heading
        )
        
        self.entity.turn_repairing = 0
        
        if self.entity.is_controllable:
            self.game_data.player_record["torpedos_fired"] += self.amount

    def raise_warning(self):

        if not self.entity.sys_torpedos.is_opperational:
            return OrderWarning.SYSTEM_INOPERATIVE

        if self.amount == 0:
            return OrderWarning.ZERO_VALUE_ENTERED

        sub_sector:SubSector = self.game_data.grid[self.entity.sector_coords.y][self.entity.sector_coords.x]

        hit_ship = False

        for co in self.coord_list:

            try:
                planet = sub_sector.planets_dict[co]
                return OrderWarning.TORPEDO_COULD_HIT_PLANET if hit_ship else OrderWarning.TORPEDO_WILL_HIT_PLANET

            except KeyError:

                try:
                    star = sub_sector.stars_dict[co]
                    return OrderWarning.SAFE if hit_ship else OrderWarning.TORPEDO_WILL_NOT_HIT_ANYTHING

                except KeyError:

                    try:
                        ship = self.ships[co]
                        if ship:
                            hit_ship = True

                    except KeyError:
                        pass
        return OrderWarning.SAFE if hit_ship else OrderWarning.TORPEDO_WILL_NOT_HIT_ANYTHING

class DockOrder(Order):

    def __init__(self, entity: Starship, planet:Planet) -> None:
        super().__init__(entity)
        self.planet = planet
        self.undock = not entity.docked
        self.ships = self.entity.game_data.grab_ships_in_same_sub_sector(
            self.entity, accptable_ship_statuses={STATUS_ACTIVE}
        )
    
    def __hash__(self) -> int:
        return hash((self.planet, self.undock, self.ships))
    
    def perform(self) -> None:
        self.entity.docked = self.undock
        if self.entity.is_controllable:
            self.game_data.engine.message_log.add_message(
                "Docking procedures complete, captain." if self.entity.docked else "Undocking procedures complete, captain."
            )
    
    """
    def can_be_carried_out(self) -> bool:
        if self.undock:
            return True

        return self.planet.canSupplyPlayer(self.entity)
    """
    
    def raise_warning(self):

        if self.undock and self.ships:
            return OrderWarning.ENEMY_SHIPS_NEARBY

        if not self.planet.local_coords.is_adjacent(other=self.entity.local_coords):
            return OrderWarning.PLANET_TOO_DISTANT
        
        planet_habbitation = self.planet.planet_habbitation

        if planet_habbitation in {PlanetHabitation.PLANET_BARREN, PlanetHabitation.PLANET_BOMBED_OUT, PlanetHabitation.PLANET_PREWARP}:
            return OrderWarning.PLANET_TOO_PRIMITIVE
        
        return OrderWarning.PLANET_UNFRIENDLY if planet_habbitation in {PlanetHabitation.PLANET_ANGERED, PlanetHabitation.PLANET_HOSTILE} else OrderWarning.SAFE

class RechargeOrder(Order):

    def __init__(self, entity:Starship, amount:int) -> None:
        super().__init__(entity)
        
        self.cost = amount - self.entity.shields
        if amount >= self.entity.shields:
            
            amount = floor(amount * self.entity.sys_shield_generator.get_effective_value)

        else:
            self.cost =  ceil(self.cost * self.entity.sys_shield_generator.get_effective_value)
            
        self.amount = amount
        
    
    def __hash__(self) -> int:
        return hash((self.entity, self.cost, self.amount))
    
    def perform(self) -> None:

        amount = self.amount
        
        energy_cost = self.cost
        
        self.entity.energy -= energy_cost
                        
        self.entity.shields = amount
        
        if self.entity.is_controllable:
            self.game_data.player_record["energy_used"] += energy_cost
    
    def raise_warning(self):
        if self.amount == self.entity.shields:
            return OrderWarning.NO_CHANGE_IN_SHIELD_ENERGY
        return OrderWarning.NOT_ENOUGHT_ENERGY if self.cost > self.entity.energy else OrderWarning.SAFE

class RepairOrder(Order):

    def __init__(self, entity:Starship, amount:int) -> None:
        super().__init__(entity)
        self.amount = amount
        self.ships = tuple(self.entity.game_data.grab_ships_in_same_sub_sector(
            self.entity, accptable_ship_statuses={STATUS_ACTIVE}
        ))
        self.number = len(self.ships)
        
    def __hash__(self) -> int:
        return hash((self.entity, self.amount, self.ships, self.number))
    
    def perform(self) -> None:
        self.entity.repair()
        
        self.entity.turn_repairing += 1
        
    def raise_warning(self):
        
        if self.number:
            return OrderWarning.ENEMY_SHIPS_NEARBY_WARN
        
        if any(
            (
                self.entity.sys_energy_weapon.integrety == 1.0,
                self.entity.sys_impulse.integrety == 1.0,
                self.entity.sys_sensors.integrety == 1.0,
                self.entity.sys_shield_generator.integrety == 1.0,
                self.entity.sys_torpedos.integrety == 1.0,
                self.entity.sys_warp_core.integrety == 1.0,
                self.entity.sys_warp_drive.integrety == 1.0,
                self.entity.hull_percentage == 1.0,
                self.entity.shields_percentage == 1.0,
                self.entity.energy == self.entity.ship_data.max_energy
            )
        ):
            return OrderWarning.NO_REPAIRS_NEEDED
        
        return OrderWarning.SAFE

class SelfDestructOrder(Order):

    def __init__(self, entity: Starship, nearbye_ships:Iterable[Starship]) -> None:
        super().__init__(entity)
        self.ships = nearbye_ships

    def __hash__(self) -> int:
        return hash((self.entity, self.ships))

    def perform(self) -> None:
        if self.entity.is_controllable:
            self.game_data.engine.message_log.add_message("Captain, it has been an honor...")
        self.entity.hull = -self.entity.ship_data.max_hull
        self.entity.warp_core_breach(True)
        
    def raise_warning(self):

        sector_ships = self.ships

        if not sector_ships:
            return OrderWarning.NO_ENEMY_SHIPS_NEARBY
        
        ships_in_range = [
            ship for ship in sector_ships if self.entity.local_coords.distance(ship.local_coords) <= self.entity.ship_data.warp_breach_dist
        ]

        return OrderWarning.SAFE if ships_in_range else OrderWarning.NO_ENEMY_SHIPS_NEARBY

class ReactivateDerlict(Order):

    def __init__(self, entity: Starship, target:Starship, crew:int) -> None:
        super().__init__(entity)
        self.target = target
        self.crew = crew

        self.delrict_ships = [ship for ship in self.entity.game_data.enemyShipsInAction if ship.able_crew + ship.injuredCrew < 1]

        if self.delrict_ships:
            self.delrict_ships.sort(lambda ship: ship.sector_coords.distance(self.entity.sector_coords))
        
        self.ships_in_same_system = self.entity.game_data.grapShipsInSameSubSector(self.entity)

    def raise_warning(self):

        if self.crew >= self.entity.able_crew:
            return OrderWarning.NOT_ENOUGHT_CREW

        if self.target.sector_coords != self.entity.sector_coords:
            return OrderWarning.NO_TARGET
        
        if not self.entity.local_coords.is_adjacent(self.target.local_coords):
            return OrderWarning.OUT_OF_RANGE

        return OrderWarning.SAFE

    def perform(self) -> None:

        max_crew = self.target.ship_data.max_crew

        crew_to_send_over = min(max_crew, self.crew)

        self.entity.able_crew -= crew_to_send_over
        self.target.able_crew += crew_to_send_over

        


'''
class Or:

    def __init__(self, command, x, y, amount, target):

        self.command = command
        self.x = x
        self.y = y
        self.amount = amount
        self.target = target

    def Warp(self, x ,y):
        self.command = 'WARP'
        self.x = x
        self.y = y

    def Move(self, x, y):
        self.command = 'MOVE'
        self.x = x
        self.y = y

    def Phaser(self, amount, target):
        self.command = 'FIRE_PHASERS'
        self.amount = max(0, amount)
        self.target = target

    def Torpedo(self, x:int, y:int, amount):
        self.command = 'FIRE_TORPEDO'
        self.x = x
        self.y = y
        self.amount = max(1, amount)

    def Recharge(self, amount):
        self.command = 'RECHARGE'
        self.amount = amount

    def Repair(self, amount):
        self.comand = 'REPAIR'
        self.amount = amount

    @classmethod
    def OrderWarp(cls, x, y):
        return cls('WARP', x, y, 0, None)

    @classmethod
    def OrderMove(cls, x, y):
        return cls('MOVE', x, y, 0, None)

    @classmethod
    def OrderPhaser(cls, amount, target):
        return cls('FIRE_ENERGY', -1, -1, amount, target)

    @classmethod
    def OrderTorpedo(cls, x, y):
        return cls('FIRE_TORPEDO', x, y, 0, None)

    @classmethod
    def OrderRecharge(cls, amount):
        return cls('RECHARGE', -1, -1, amount, None)

    @classmethod
    def OrderRepair(cls):
        return cls('REPAIR', -1, -1, 0, None)
'''