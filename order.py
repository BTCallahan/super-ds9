from __future__ import annotations
from enum import Enum, auto
from math import atan2, ceil, floor
from random import choice
from coords import Coords, IntOrFloat
from typing import TYPE_CHECKING, Iterable, Optional
from global_functions import to_rads, headingToCoords, headingToDirection
from data_globals import LOCAL_ENERGY_COST, SECTOR_ENERGY_COST, PlanetHabitation
from space_objects import Planet, SubSector
from torpedo import torpedo_types
from get_config import config_object

if TYPE_CHECKING:
    from starship import Starship

class OrderWarning(Enum):

    SAFE = auto()
    ZERO_VALUE_ENTERED = auto()
    ENEMY_SHIPS_NEARBY = auto()
    TORPEDO_WILL_HIT_PLANET = auto()
    TORPEDO_COULD_HIT_PLANET = auto()
    TORPEDO_WILL_NOT_HIT_ANYTHING = auto()
    NO_TORPEDOS_LEFT = auto()
    SHIP_WILL_COLLIDE_WITH_PLANET = auto()
    SHIP_WILL_COLLIDE_WITH_STAR = auto()
    SHIP_COULD_COLLIDE_WITH_SHIP = auto()
    NOT_ENOUGHT_ENERGY = auto()
    OUT_OF_RANGE = auto()
    NO_TARGET = auto()
    NO_TARGETS = auto()
    SYSTEM_INOPERATIVE = auto()
    PLANET_TOO_DISTANT = auto()
    PLANET_TOO_PRIMITIVE = auto()
    PLANET_UNFRIENDLY = auto()
    PLANET_AFRAID = auto()
    
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
    OrderWarning.NO_TORPEDOS_LEFT : "Error. We have no remaining torpedos.",
    OrderWarning.ZERO_VALUE_ENTERED : "Error. You have entered a value of zero."
}

torpedo_warnings = {
    OrderWarning.TORPEDO_WILL_HIT_PLANET : "Warning: If we fire, the torpedo will hit a planet",
    OrderWarning.TORPEDO_COULD_HIT_PLANET : "Warning: If the torpedo misses, it could hit a planet",
    OrderWarning.TORPEDO_WILL_NOT_HIT_ANYTHING : "Warning: The torpedo will not hit anything"
}

collision_warnings = {
    OrderWarning.SHIP_COULD_COLLIDE_WITH_SHIP : "Warning: That course could result in a ship to ship collision!",
    OrderWarning.SHIP_WILL_COLLIDE_WITH_PLANET : "Warning: That course will result in our ship crashing into a planet!",
    OrderWarning.SHIP_WILL_COLLIDE_WITH_STAR : "Warning: That course will result in our ship crashing into a star!"
}

class Order:

    def __init__(self, entity:Starship) -> None:
        self.entity = entity
        
    def perform(self) -> None:

        raise NotImplementedError()
    
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

        self.x, self.y = x,y
        # TODO: Implement warp speed
    
    @classmethod
    def from_coords(cls, entity:Starship, x:int, y:int):

        distance = entity.sectorCoords.distance(coords=Coords(x,y))

        rel_x = x - entity.sectorCoords.x
        rel_y = y - entity.sectorCoords.y

        c:Coords = Coords(rel_x, rel_y)
        x_, y_ = c.normalize()

        heading = atan2(y_, x_)
        return cls(entity, heading, distance, x, y)
    
    @classmethod
    def from_heading(cls, entity:Starship, heading:int, distance:int):

        x, y = headingToCoords(heading, distance, entity.sectorCoords.x, entity.sectorCoords.y, config_object.sector_width, config_object.sector_height)

        return cls(entity, heading, distance, x, y)

    def perform(self) -> None:

        #self.entity.warp(self.x, self.y)
        
        self.entity.sectorCoords.x = self.x
        self.entity.sectorCoords.y = self.y

        ships = self.entity.game_data.grapShipsInSameSubSector(self.entity)

        subsector: SubSector = self.entity.game_data.grid[self.y][self.x]

        safe_spots = subsector.safeSpots.copy()

        for ship in ships:

            safe_spots.remove(ship.localCoords.create_coords())

        spot = choice(safe_spots)
        
        self.entity.localCoords.x = spot.x
        self.entity.localCoords.y = spot.y

        self.entity.energy -= self.distance * SECTOR_ENERGY_COST * self.entity.sysWarp.affect_cost_multiplier

        if self.entity.isControllable:

            self.game_data.engine.message_log.add_message(
                "Engage!"
            )
            self.game_data.engine.message_log.add_message(
                f"The {self.entity.name} hase come out of warp in {self.entity.sectorCoords.x} {self.entity.sectorCoords.y}."
            )
        self.entity.game_data.set_condition()
        self.entity.turnRepairing = 0
    
    def raise_warning(self):
        if not self.entity.sysWarp.isOpperational:
            return OrderWarning.SYSTEM_INOPERATIVE
        
        if not (0 <= self.x < config_object.sector_width and 0 <= self.y < config_object.subsector_height):
            return OrderWarning.OUT_OF_RANGE
        
        distance_to_destination = self.entity.sectorCoords.distance(x=self.x, y=self.y)
        
        return OrderWarning.NOT_ENOUGHT_ENERGY if distance_to_destination * SECTOR_ENERGY_COST * self.entity.sysWarp.affect_cost_multiplier > self.entity.energy else OrderWarning.SAFE

class MoveOrder(Order):

    def __init__(self, entity:Starship, *, heading:IntOrFloat, distance:int, x:int, y:int, x_aim:float, y_aim:float) -> None:
        super().__init__(entity)
        self.heading = heading
        self.distance = distance

        self.x, self.y = x,y
        self.x_aim, self.y_aim = x_aim, y_aim

        #x, y = headingToDirection(self.heading)

        c:Coords = Coords(x=x - entity.localCoords.x, y=y - entity.localCoords.y)

        x_, y_ = c.normalize()

        self.coord_list = tuple([Coords(co.x, co.y) for co in self.game_data.engine.get_lookup_table(x_, y_)][:ceil(distance)])

        self.ships = {ship.localCoords.create_coords() : ship for ship in self.entity.game_data.grapShipsInSameSubSector(self.entity) if ship.localCoords in self.coord_list}
    
    @classmethod
    def from_coords(cls, entity:Starship, x:int, y:int):

        distance = entity.sectorCoords.distance(x=x,y=y)

        rel_x = x - entity.sectorCoords.x
        rel_y = y - entity.sectorCoords.y

        c:Coords = Coords(rel_x, rel_y)
        x_, y_ = c.normalize()

        heading = atan2(y_, x_) / to_rads

        return cls(entity, ceil(distance), heading=heading, x=x, y=y, x_aim=x_, y_aim=y_)
    
    @classmethod
    def from_heading(cls, entity:Starship, heading:int, distance:int):
        
        x_aim, y_aim = headingToDirection(heading)
        x, y = headingToCoords(
            heading, config_object.max_move_distance, 
            entity.sectorCoords.x, entity.sectorCoords.y,
            config_object.subsector_width, config_object.subsector_height
        )

        return cls(entity, distance, heading=heading, x=x, y=y, x_aim=x_aim, y_aim=y_aim)

    """
    def can_be_carried_out(self):

        if self.entity.energy < self.distance * self.entity.sysImpulse.affect_cost_multiplier * LOCAL_ENERGY_COST:
            return False

        last_coord = self.coord_list[-1]

        return (
            self.entity.sysImpulse.isOpperational and
            self.entity.energy >= self.distance * (1 / self.entity.sysImpulse.getEffectiveValue) and
            last_coord.x in self.game_data.subsecSizeRangeX and
            last_coord.y in self.game_data.subsecSizeRangeY
            )
    """

    def perform(self) -> None:

        sub_sector:SubSector = self.entity.game_data.grid[self.entity.sectorCoords.y][self.entity.sectorCoords.x]

        #ships = [ship for ship in self.entity.game_data.grapShipsInSameSubSector(self.entity) if ship.localCoords in self.coord_list]

        #self.entity.move()

        self.entity.energy -= self.distance * self.entity.sysImpulse.affect_cost_multiplier * LOCAL_ENERGY_COST

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
                        self.entity.ram(ship)

                    except KeyError:
                        pass
                    
        self.entity.localCoords.x = self.x
        self.entity.localCoords.y = self.y
        
        self.entity.turnRepairing = 0

    def raise_warning(self):

        if not self.entity.sysImpulse.isOpperational:
            return OrderWarning.SYSTEM_INOPERATIVE

        last_coord = self.coord_list[-1]

        if last_coord.x not in range(config_object.subsector_width) and last_coord.y not in range(config_object.subsector_height):
            return OrderWarning.OUT_OF_RANGE
        
        if self.entity.energy < self.distance * self.entity.sysImpulse.affect_cost_multiplier * LOCAL_ENERGY_COST:
            return OrderWarning.NOT_ENOUGHT_ENERGY

        sub_sector:SubSector = self.entity.game_data.grid[self.entity.sectorCoords.y][self.entity.sectorCoords.x]

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

class PhaserOrder(Order):

    def __init__(self, entity:Starship, amount:int, *, target:Optional[Starship]=None, targets:Optional[Iterable[Starship]]=None) -> None:
        super().__init__(entity)
        self.amount = min(entity.energy, amount, entity.shipData.maxWeapEnergy)
        self.target = target
        self.targets = targets
    
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

        actual_amount = floor(self.entity.sysEnergyWep.getEffectiveValue * self.amount)

        if self.multi_targets:

            amount = actual_amount / len(self.targets)

            for ship in self.targets:

                self.entity.attackEnergyWeapon(ship, floor(actual_amount), amount)
        else:
            self.entity.attackEnergyWeapon(self.target, actual_amount, actual_amount)

    def raise_warning(self):

        if not self.entity.sysEnergyWep.isOpperational:
            return OrderWarning.SYSTEM_INOPERATIVE
        
        if self.multi_targets and not self.targets:
            return OrderWarning.NO_TARGETS
        
        if not self.multi_targets and not self.target:
            return OrderWarning.NO_TARGET
        
        return OrderWarning.NOT_ENOUGHT_ENERGY if self.amount > self.entity.energy else OrderWarning.SAFE
        
class TorpedoOrder(Order):

    def __init__(self, entity:Starship, amount:int, *, heading:IntOrFloat, x:int, y:int, x_aim:float, y_aim:float) -> None:
        super().__init__(entity)
        self.heading = heading
        self.amount = amount
        self.x, self.y = x,y
        self.x_aim, self.y_aim = x_aim, y_aim
        
        self.coord_list = tuple([Coords(co.x+entity.localCoords.x, co.y+entity.localCoords.y) for co in self.game_data.engine.get_lookup_table(direction_x=x_aim, direction_y=y_aim, normalise_direction=False)])

        self.ships = {ship.localCoords.create_coords() : ship for ship in self.entity.game_data.grapShipsInSameSubSector(self.entity) if ship.localCoords in self.coord_list and ship.isAlive}
    
    @classmethod
    def from_coords(cls, entity:Starship, amount:int, x:int, y:int):

        rel_x = x - entity.sectorCoords.x
        rel_y = y - entity.sectorCoords.y

        c:Coords = Coords(rel_x, rel_y)
        x_, y_ = c.normalize()

        heading = atan2(y_, x_) / to_rads
        return cls(entity, amount, heading=heading, x=x, y=y, x_aim=x_, y_aim=y_)
    
    @classmethod
    def from_heading(cls, entity:Starship, heading:int, amount:int):
        #m=max(config_object.max_move_distance, config_object.max_warp_distance)

        x_aim, y_aim = headingToDirection(heading)
        x, y = headingToCoords(heading, config_object.max_move_distance, 
        entity.sectorCoords.x, entity.sectorCoords.y,
        config_object.subsector_width, config_object.subsector_height
        )

        return cls(entity, amount, heading=heading, x=x, y=y, x_aim=x_aim, y_aim=y_aim)

    def perform(self) -> None:

        #torpedo = torpedo_types[self.entity.torpedoLoaded]

        self.entity.game_data.handleTorpedo(self.entity, self.amount, self.coord_list, self.entity.torpedoLoaded, self.ships)
        
        self.entity.turnRepairing = 0

    def raise_warning(self):

        if not self.entity.sysTorp.isOpperational:
            return OrderWarning.SYSTEM_INOPERATIVE

        sub_sector:SubSector = self.game_data.grid[self.entity.sectorCoords.y][self.entity.sectorCoords.x]

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
        self.ships = self.entity.game_data.grapShipsInSameSubSector(self.entity)
    
    def can_be_carried_out(self) -> bool:
        if self.undock:
            return True

        return self.planet.canSupplyPlayer(self.entity)
    
    def raise_warning(self):

        if self.undock and self.ships:
            return OrderWarning.ENEMY_SHIPS_NEARBY

        if not self.planet.localCoords.is_adjacent(self.entity.localCoords):
            return OrderWarning.PLANET_TOO_DISTANT
        
        planet_habbitation = self.planet.planet_habbitation

        if planet_habbitation in {PlanetHabitation.PLANET_BARREN, PlanetHabitation.PLANET_BOMBED_OUT, PlanetHabitation.PLANET_PREWARP}:
            return OrderWarning.PLANET_TOO_PRIMITIVE
        
        return OrderWarning.PLANET_UNFRIENDLY if planet_habbitation in {PlanetHabitation.PLANET_ANGERED, PlanetHabitation.PLANET_HOSTILE} else OrderWarning.SAFE

class RechargeOrder(Order):

    def __init__(self, entity:Starship, amount:int) -> None:
        super().__init__(entity)
        self.amount = amount
    
    def perform(self) -> None:

        amount = self.amount

        if amount >= 0:

            if amount > self.amount:
                amount = self.amount

            self.amount-= amount
            amount*= self.entity.sysShield.getEffectiveValue

            self.entity.shields = min(self.entity.shields + amount, self.entity.shipData.maxShields)
        else:

            if -amount > self.entity.shields:
                amount = -self.entity.shields

            self.entity.shields+=amount
            amount*= -self.entity.sysShield.getEffectiveValue
            self.amount = min(self.amount + amount, self.entity.shipData.maxEnergy)
    
    def raise_warning(self):
        return OrderWarning.NOT_ENOUGHT_ENERGY if self.amount > self.entity.energy else OrderWarning.SAFE

class RepairOrder(Order):

    def __init__(self, entity:Starship, amount:int) -> None:
        super().__init__(entity)
        self.amount = amount
    
    def perform(self) -> None:
        self.entity.repair(self.amount)
        
        self.entity.turnRepairing += 1





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