from __future__ import annotations
from enum import Enum, auto
from math import atan2, ceil, floor
from random import choice

from frozendict import frozendict
from coords import Coords, IntOrFloat
from typing import TYPE_CHECKING, Final, Iterable, List, Optional, Tuple, Union
from global_functions import TO_RADIANS, heading_to_coords, heading_to_direction
from data_globals import DAMAGE_BEAM, DAMAGE_CANNON, DAMAGE_RAMMING, PLANET_NEUTRAL, PLANET_BARREN, PLANET_BOMBED_OUT, PLANET_HOSTILE, PLANET_PREWARP, STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK, WARP_FACTOR, CloakStatus
from nation import ALL_NATIONS
from space_objects import Planet, SubSector
from get_config import CONFIG_OBJECT
import colors
from torpedo import Torpedo
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
    TORPEDO_COULD_HIT_PLANET = auto() # the torp could hit the planet, or it could hit the enemy ship
    TORPEDO_COULD_FRIENDLY_SHIP = auto()
    TORPEDO_COULD_HIT_PLANET_OR_FRIENDLY_SHIP = auto()
    TORPEDO_WILL_HIT_PLANET_OR_FRIENDLY_SHIP = auto()
    TORPEDO_WILL_MISS = auto()
    TORPEDO_WILL_HIT_FRIENDLY_SHIP_OR_MISS = auto()
    NO_TORPEDOS_LEFT = auto()
    SHIP_WILL_COLLIDE_WITH_PLANET = auto()
    SHIP_WILL_COLLIDE_WITH_STAR = auto()
    SHIP_COULD_COLLIDE_WITH_SHIP = auto()
    NOT_ENOUGHT_ENERGY = auto()
    OUT_OF_RANGE = auto()
    NO_TARGET = auto()
    NO_TARGETS = auto()
    SYSTEM_INOPERATIVE = auto()
    SYSTEM_MISSING = auto()
    PLANET_TOO_DISTANT = auto()
    PLANET_TOO_PRIMITIVE = auto()
    PLANET_UNFRIENDLY = auto()
    PLANET_AFRAID = auto()
    NO_REPAIRS_NEEDED = auto()
    CLOAK_COOLDOWN = auto()
    DECLOAK_FIRST = auto()
    UNDOCK_FIRST = auto()
    TRANSPORT_NO_CREW_SELECTED = auto()
    TRANSPORT_NOT_ENOUGHT_CREW = auto()
    TRANSPORT_TOO_MANY_FOR_SYSTEMS = auto()
    TRANSPORT_DESTINATION_OUT_OF_RANGE = auto()
    TRANSPORT_SHIELDS_ARE_UP = auto()
    TRANSPORT_CREW_NOT_ABOARD = auto()
    TRANSPORT_CANNOT_RECREW = auto()
    TRANSPORT_NOT_ENOUGH_SPACE = auto()
    
BLOCKS_ACTION:Final = frozendict({
    OrderWarning.NOT_ENOUGHT_ENERGY : "Error: We possess insufficent energy reserves.",
    OrderWarning.OUT_OF_RANGE : "Error: Our destination is out of range.",
    OrderWarning.SYSTEM_INOPERATIVE : "Error: That ship system is off line.",
    OrderWarning.SYSTEM_MISSING : "Error: The required system is not present on this ship.",
    OrderWarning.PLANET_AFRAID : "Error: The planet is too afaid of the nearby hostile forces.",
    OrderWarning.PLANET_TOO_DISTANT : "Error: The planet is too far from our ship.",
    OrderWarning.PLANET_TOO_PRIMITIVE : "Error: The planet lacks the infurstucture to repaire and repsuply our ship.",
    OrderWarning.PLANET_UNFRIENDLY : "Error: The planet is hostile to us.",
    OrderWarning.NO_TARGET : "Error: Our sensors have not targeted an enemy ship.",
    OrderWarning.NO_TARGETS : "Error: There are no enemy ships in the area.",
    OrderWarning.NO_TORPEDOS_LEFT : "Error: We have no remaining torpedos.",
    OrderWarning.ZERO_VALUE_ENTERED : "Error: You have entered a value of zero.",
    OrderWarning.NO_CHANGE_IN_POSITION : "Error: There is no change in our position.", # reword this later
    OrderWarning.NO_CHANGE_IN_SHIELD_ENERGY : "Error: There is no change in shield energy or status.",
    OrderWarning.DECLOAK_FIRST : "Error: We must decloak first.",
    OrderWarning.CLOAK_COOLDOWN : "Error: Our cloaking system is still cooling down.",
    OrderWarning.UNDOCK_FIRST : "Error: We must undock first.",
    OrderWarning.TRANSPORT_NO_CREW_SELECTED : "Error: We have not selected any crew to transport over.",
    OrderWarning.TRANSPORT_CANNOT_RECREW : "Error: That spacecraft cannot be boarded",
    OrderWarning.TRANSPORT_TOO_MANY_FOR_SYSTEMS : "Error: Our systems are unable to handle that many passengers.",
    OrderWarning.TRANSPORT_SHIELDS_ARE_UP : "Error: Our target's shields are up.",
    OrderWarning.TRANSPORT_DESTINATION_OUT_OF_RANGE : "Error: Our destination is out of range.",
    OrderWarning.TRANSPORT_CREW_NOT_ABOARD : "Error: We have no crew aboard that ship.",
    OrderWarning.TRANSPORT_NOT_ENOUGH_SPACE : "Error: There is not enough space for our boarding team.",
    OrderWarning.TRANSPORT_NOT_ENOUGHT_CREW : "Error: If we sent over that amount of crew, it would criticly impare our ability to opperate our own ship."
})

TORPEDO_WARNINGS:Final = frozendict({
    OrderWarning.TORPEDO_WILL_HIT_PLANET : "Warning: If we fire, the torpedo will hit a planet.",
    OrderWarning.TORPEDO_COULD_HIT_PLANET : "Warning: If the torpedo misses, it could hit a planet.",
    OrderWarning.TORPEDO_WILL_MISS : "Warning: The torpedo will not hit anything."
})

COLLISION_WARNINGS:Final = frozendict({
    OrderWarning.SHIP_COULD_COLLIDE_WITH_SHIP : "Warning: That course could result in a ship to ship collision!",
    OrderWarning.SHIP_WILL_COLLIDE_WITH_PLANET : "Warning: That course will result in our ship crashing into a planet!",
    OrderWarning.SHIP_WILL_COLLIDE_WITH_STAR : "Warning: That course will result in our ship crashing into a star!"
})

MISC_WARNINGS:Final = frozendict({
    OrderWarning.NO_ENEMY_SHIPS_NEARBY : "Warning: There are no enemy ships nearbye.",
    OrderWarning.ENEMY_SHIPS_NEARBY_WARN : "Warning: There are enemy ships nearbye.",
    OrderWarning.NO_REPAIRS_NEEDED : "Warning: No repairs are needed right now."
})

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

        return self.raise_warning() not in BLOCKS_ACTION
    
    def raise_warning(self):
        return OrderWarning.SAFE
    
class WarpOrder(Order):

    def __init__(
        self, entity:Starship, *, heading:int, distance:int, x:int, y:int, speed:int, start_x:int, start_y:int
    ) -> None:
        super().__init__(entity)
        self.heading = heading
        self.distance = distance
        self.start_x = start_x
        self.start_y = start_y
        assert speed > 0
        self.speed = speed
        self.warp_speed, cost = WARP_FACTOR[speed]
        self.cost = ceil(self.distance * CONFIG_OBJECT.sector_energy_cost * cost)
        self.x, self.y = x,y
    
    def __hash__(self):
        return hash((
            self.entity, self.heading, self.distance, self.speed, self.warp_speed, self.cost, 
            self.x, self.y, self.start_x, self.start_y
        ))
    
    @classmethod
    def from_coords(
        cls, 
        *,
        entity:Starship,  
        x:int, y:int, speed:int, start_x:int, start_y:int
    ):
        distance = entity.sector_coords.distance(coords=Coords(x,y))
        
        x_, y_ = Coords.normalize_other(x=x - entity.sector_coords.x, y=y - entity.sector_coords.y)

        heading = atan2(y_, x_)
        return cls(entity=entity, heading=heading, distance=distance, x=x, y=y, speed=speed, start_x=start_x, start_y=start_y)
    
    @classmethod
    def from_heading(cls, entity:Starship, *, heading:int, distance:int, speed:int, start_x:int, start_y:int):

        x, y = heading_to_coords(
            heading, distance, 
            entity.sector_coords.x, entity.sector_coords.y, 
            CONFIG_OBJECT.sector_width, CONFIG_OBJECT.sector_height
        )
        return cls(
            entity=entity, heading=heading, distance=distance, x=x, y=y, speed=speed, start_x=start_x, start_y=start_y
        )

    def perform(self) -> None:
        
        x_aim = self.x - self.start_x
        y_aim = self.y - self.start_y
        co_tuple = tuple(
            Coords(x=self.start_x+co.x, y=self.start_y+co.y) for co in self.game_data.engine.get_lookup_table(
                direction_x=x_aim, direction_y=y_aim, normalise_direction=True
            )
        )
        end = Coords(x=self.x, y=self.y)
        
        end_index = co_tuple.index(end)
        
        co_tuples = co_tuple[:end_index+1]
        
        self.entity.warp_drive.current_warp_factor = self.speed
        self.entity.warp_drive.warp_destinations = co_tuples
        
        old_x, old_y = self.entity.sector_coords.x, self.entity.sector_coords.y
        
        energy_cost = self.cost

        self.entity.power_generator.energy -= energy_cost
        
        is_controllable = self.entity.is_controllable
        
        player_sector_coords = self.game_data.player.sector_coords
        
        player_in_departure_system = player_sector_coords.x == old_x and player_sector_coords.y == old_y

        if is_controllable:
            
            self.game_data.player_record["energy_used"] += energy_cost
            self.game_data.player_record["times_gone_to_warp"] += 1

            self.game_data.engine.message_log.add_message(
                "Engage!", colors.cyan
            )
        elif player_in_departure_system:
            
            self.game_data.engine.message_log.add_message(
                f"The {self.entity.name} has gone to warp.", colors.cyan
            )
        self.entity.turn_repairing = 0
        
        wto = WarpTravelOrder(self.entity)
        
        wto.perform()
    
    def raise_warning(self):
        if not self.entity.warp_drive.is_opperational:
            return OrderWarning.SYSTEM_INOPERATIVE
        
        if self.x == self.entity.sector_coords.x and self.y == self.entity.sector_coords.y:
            return OrderWarning.NO_CHANGE_IN_POSITION
        
        if not (0 <= self.x < CONFIG_OBJECT.sector_width and 0 <= self.y < CONFIG_OBJECT.subsector_height):
            return OrderWarning.OUT_OF_RANGE
        
        return OrderWarning.NOT_ENOUGHT_ENERGY if self.cost > self.entity.power_generator.energy else OrderWarning.SAFE

class WarpTravelOrder(Order):
    """This is used to handle warp travel"""
    
    def perform(self) -> None:
        self.entity.warp_drive.increment_warp_progress()
        
        co = self.entity.warp_drive.get_warp_current_warp_sector()
        
        self.entity.sector_coords.x = co.x
        self.entity.sector_coords.y = co.y
        
        if co != self.entity.warp_drive.warp_destinations[-1]:
            return
        
        self.entity.warp_drive.current_warp_factor = 0
        
        subsector: SubSector = self.entity.game_data.grid[self.entity.sector_coords.y][self.entity.sector_coords.x]

        safe_spots = subsector.safe_spots.copy()

        ships = self.entity.game_data.grab_ships_in_same_sub_sector(
            self.entity, accptable_ship_statuses={
                STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED,
            }
        )
        for ship in ships:
            try:
                safe_spots.remove(ship.local_coords.create_coords())
            except ValueError:
                pass

        spot = choice(safe_spots)
        
        self.entity.local_coords.x = spot.x
        self.entity.local_coords.y = spot.y
        
        player_sector_coords = self.game_data.player.sector_coords
        
        is_controllable = self.entity.is_controllable
        
        player_in_destination_system = player_sector_coords == self.entity.sector_coords
        
        if player_in_destination_system or is_controllable:
            
            self.game_data.engine.message_log.add_message(
f"The {self.entity.name} has come out of warp in {self.entity.sector_coords.x} {self.entity.sector_coords.y}.", 
                colors.cyan
            )

class MoveOrder(Order):

    def __init__(
        self, 
        *,
        entity:Starship,
        heading:IntOrFloat, distance:int, x:int, y:int, x_aim:float, y_aim:float, cost:int
    ) -> None:
        super().__init__(entity)
        self.heading = heading
        self.distance = distance
        self.cost = cost#ceil(distance * self.entity.impulse_engine.affect_cost_multiplier * LOCAL_ENERGY_COST)
        self.x, self.y = x,y
        self.x_aim, self.y_aim = x_aim, y_aim
        
        self.coord_list = tuple(
            Coords(
                co.x + self.entity.local_coords.x, co.y + self.entity.local_coords.y
            ) for co in self.game_data.engine.get_lookup_table(
                direction_x=x_aim, direction_y=y_aim, normalise_direction=False
            )
        )[:ceil(distance)]

        self.ships = {
            ship.local_coords.create_coords() : ship for ship in 
            self.entity.game_data.grab_ships_in_same_sub_sector(
                self.entity, accptable_ship_statuses={STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK}
            ) if ship.local_coords in self.coord_list
        }
    
    def __hash__(self):
        return hash((self.entity, self.heading, self.distance, self.cost, self.x, self.y, self.x_aim, self.y_aim))
    
    @classmethod
    def from_coords(
        cls, 
        *,
        entity:Starship, x:int, y:int, cost:int
    ):
        distance = entity.local_coords.distance(x=x,y=y)

        rel_x = x - entity.local_coords.x
        rel_y = y - entity.local_coords.y

        x_, y_ = Coords.normalize_other(x=rel_x, y=rel_y)

        heading = atan2(y_, x_) / TO_RADIANS

        return cls(entity=entity, distance=distance, heading=heading, x=x, y=y, x_aim=x_, y_aim=y_, cost=cost)
    
    @classmethod
    def from_heading(
        cls, 
        *,
        entity:Starship, heading:int, distance:int, cost:int
    ):
        x_aim, y_aim = heading_to_direction(heading)
        x, y = heading_to_coords(
            heading, distance, 
            entity.local_coords.x, entity.local_coords.y,
            CONFIG_OBJECT.subsector_width, CONFIG_OBJECT.subsector_height
        )
        return cls(entity=entity, distance=distance, heading=heading, x=x, y=y, x_aim=x_aim, y_aim=y_aim, cost=cost)

    def perform(self) -> None:
        
        sub_sector:SubSector = self.entity.get_sub_sector
        
        energy_cost = self.cost

        self.entity.power_generator.energy -= energy_cost

        if self.entity.is_controllable:
            
            self.game_data.player_record["energy_used"] += energy_cost

        if self.game_data.three_d_movment:
            
            co = Coords(x=self.x, y=self.y)
            try:
                planet = sub_sector.planets_dict[co]
            except KeyError:
                try:
                    star = sub_sector.stars_dict[co]
                except KeyError:
                    try:
                        ship = self.ships[co]
                        try:
                            crew_readyness = self.entity.crew.crew_readyness
                        except AttributeError:
                            crew_readyness = 1
                        try:
                            target_crew_readyness = ship.crew.crew_readyness
                        except AttributeError:
                            target_crew_readyness = 1
                        
                        hit = self.entity.roll_to_hit(
                            ship, 
                            systems_used_for_accuray=(
                                self.entity.impulse_engine.get_effective_value,
                                self.entity.sensors.get_effective_value
                            ),
                            damage_type=DAMAGE_RAMMING,
                            crew_readyness=crew_readyness,
                            target_crew_readyness=target_crew_readyness
                        )
                        self.entity.ram(ship, False)

                    except KeyError:
                        pass
        else:
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
                            try:
                                crew_readyness = self.entity.crew.crew_readyness
                            except AttributeError:
                                crew_readyness = 1
                            try:
                                target_crew_readyness = ship.crew.crew_readyness
                            except AttributeError:
                                target_crew_readyness = 1
                            hit = self.entity.roll_to_hit(
                                ship, 
                                systems_used_for_accuray=(
                                    self.entity.impulse_engine.get_effective_value,
                                    self.entity.sensors.get_effective_value
                                ),
                                damage_type=DAMAGE_RAMMING,
                                crew_readyness=crew_readyness,
                                target_crew_readyness=target_crew_readyness
                            )
                            self.entity.ram(ship, True)

                        except KeyError:
                            pass
                    
        self.entity.local_coords.x = self.x
        self.entity.local_coords.y = self.y
        
        self.entity.turn_repairing = 0

    def raise_warning(self):
        
        if self.x == self.entity.local_coords.x and self.y == self.entity.local_coords.y:
            return OrderWarning.NO_CHANGE_IN_POSITION

        if not self.entity.impulse_engine.is_opperational:
            return OrderWarning.SYSTEM_INOPERATIVE

        last_coord = self.coord_list[-1]

        if last_coord.x not in range(
            CONFIG_OBJECT.subsector_width
        ) and last_coord.y not in range(CONFIG_OBJECT.subsector_height):
            return OrderWarning.OUT_OF_RANGE
        
        if self.entity.power_generator.energy < self.cost:
            return OrderWarning.NOT_ENOUGHT_ENERGY

        sub_sector:SubSector = self.entity.game_data.grid[self.entity.sector_coords.y][self.entity.sector_coords.x]

        could_collide_with_ship = False
        
        if self.game_data.three_d_movment:
            
            co = Coords(x=self.x,y=self.y)
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
        else:
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

    def __init__(
        self, entity:Starship, amount:int, *, 
        target:Optional[Starship]=None, targets:Optional[Tuple[Starship]]=None, use_cannons:bool
    ) -> None:
        super().__init__(entity)
        self.amount = min(entity.power_generator.energy, amount, entity.ship_class.max_beam_energy)
        self.target = target
        self.targets = targets
        self.use_cannons = use_cannons
        if self.targets:
            if use_cannons:
                raise ValueError(
                    "Cannons can only be used to target a single ship. If the parameter 'use_cannons' is True, then the parameter 'targets' must be None"
                )
            self.targets
    
    def __hash__(self):
        return hash((self.entity, self.amount, self.target, self.targets, self.use_cannons))
    
    @classmethod
    def cannon(cls, entity:Starship, amount:int, target:Starship):
        return cls(entity, amount, target=target, use_cannons=True)
    
    @classmethod
    def single_target_beam(cls, entity:Starship, amount:int, target:Starship):
        return cls(entity, amount, target=target, use_cannons=False)

    @classmethod
    def multiple_targets(cls, entity:Starship, amount:int, targets:List[Starship]):
        targets.sort(key=lambda a: entity.local_coords.distance(coords=a.local_coords))
        
        max_targets = min(
            entity.ship_class.max_beam_targets, len(targets)
        )
        return cls(
            entity, amount, 
            targets=tuple(targets[:max_targets]), 
            use_cannons=False
        )

    @property
    def multi_targets(self):
        return self.targets is not None
    
    def perform(self) -> None:

        actual_amount = floor(self.entity.beam_array.get_effective_value * self.amount)
        try:
            cloak_status = self.entity.cloak.force_fire_decloak()
            
            player = self.game_data.player
            if (
                cloak_status and 
                self.entity is not player and self.entity.sector_coords == player.sector_coords
            ):
                self.game_data.engine.message_log.add_message(
                    "Enemy ship decloaking!", colors.alert_red
                )
        except AttributeError:
            pass

        if self.multi_targets:
            
            number_of_targers = len(self.targets)

            amount = actual_amount / number_of_targers
            
            cost = self.amount / number_of_targers

            for ship in self.targets:

                self.entity.attack_energy_weapon(ship, amount, cost, DAMAGE_BEAM)
        else:
            dam_type = DAMAGE_CANNON if self.use_cannons else DAMAGE_BEAM
            
            self.entity.attack_energy_weapon(self.target, actual_amount, self.amount, dam_type)
            
        if self.entity.is_controllable:
            self.game_data.player_record["energy_used"] += self.amount
        
        self.entity.turn_repairing = 0

    def raise_warning(self):
        if (
            not self.use_cannons and not self.entity.beam_array.is_opperational
        ) or (
            self.use_cannons and not self.entity.cannons.is_opperational
        ):
            return OrderWarning.SYSTEM_INOPERATIVE
        
        if self.multi_targets and not self.targets:
            return OrderWarning.NO_TARGETS
        
        if not self.multi_targets and not self.target:
            return OrderWarning.NO_TARGET
        
        if self.amount == 0:
            return OrderWarning.ZERO_VALUE_ENTERED
        
        return (
            OrderWarning.NOT_ENOUGHT_ENERGY if self.amount > self.entity.power_generator.energy else OrderWarning.SAFE
        )
      
class TransportOrder(Order):
    
    def __init__(self, entity: Starship, target: Starship, amount: int, board:bool=False, send:bool=True) -> None:
        super().__init__(entity)
        self.target = target
        self.amount = amount
        self.board = board
        self.send = send
    
    def __hash__(self) -> int:
        return hash((self.entity, self.target, self.amount, self.board, self.send))
    
    def raise_warning(self):
        
        try:
            if self.entity.cloak.cloak_is_turned_on:
                return OrderWarning.DECLOAK_FIRST
        except AttributeError:
            pass
        try:
            total_crew = self.target.crew.able_crew + self.target.crew.injured_crew
        except AttributeError:
            
            return OrderWarning.TRANSPORT_CANNOT_RECREW
        
        if self.target.is_automated:
            return OrderWarning.TRANSPORT_CANNOT_RECREW
        
        if self.amount >= self.entity.crew.able_crew:
            return OrderWarning.TRANSPORT_NOT_ENOUGHT_CREW
        
        if self.amount > self.entity.transporter.get_max_number:
            return OrderWarning.TRANSPORT_TOO_MANY_FOR_SYSTEMS
        
        if self.amount <= 0:
            return OrderWarning.TRANSPORT_NO_CREW_SELECTED
        try:
            target_shields_are_up = (
                self.target.shield_generator.is_opperational and 
                self.target.shield_generator.shields_up and 
                self.target.shield_generator.shields > 0
            )
        except AttributeError:
            target_shields_are_up = False
        
        if target_shields_are_up:
        
            return OrderWarning.TRANSPORT_SHIELDS_ARE_UP

        if self.board and not self.entity.local_coords.is_adjacent(self.target.local_coords):
            return OrderWarning.TRANSPORT_DESTINATION_OUT_OF_RANGE
        elif (
            not self.board and 
            not self.entity.local_coords.distance(coords=self.target.local_coords) <= 
            self.entity.transporter.get_effective_value * CONFIG_OBJECT.max_move_distance
        ):
            return OrderWarning.TRANSPORT_DESTINATION_OUT_OF_RANGE
        
        set_of_allied_nations = self.target.game_data.scenerio.get_set_of_allied_nations
        
        if not self.send:
            
            return (
                OrderWarning.TRANSPORT_CREW_NOT_ABOARD if 
                self.entity.nation not in self.target.crew.hostiles_on_board else 
                OrderWarning.SAFE
            )
        else:
            if self.target.ship_status.is_recrewable or (
                (self.entity.nation in set_of_allied_nations) == (self.target.nation in set_of_allied_nations)
            ):
                free = self.target.crew.get_total_crew - self.target.ship_class.max_crew
            
                return OrderWarning.TRANSPORT_NOT_ENOUGH_SPACE if free <= self.amount else OrderWarning.SAFE
        
        return OrderWarning.SAFE
        
    def perform(self) -> None:
        
        describe_actions = self.entity.sector_coords == self.target.sector_coords
        
        if describe_actions:
            describe_player_actions = self.entity.is_controllable
            describe_other_actions = self.target.is_controllable
        else:
            describe_player_actions = False
            describe_other_actions = False
        
        message_log = self.entity.game_data.engine.message_log
        
        if describe_player_actions:
            message_log.add_message("Energizing...", colors.alert_blue)
        
        if not self.send:
            
            nation = self.entity.nation
            
            crew = self.target.crew.hostiles_on_board[nation]
            
            able_crew, injured_crew = crew[0], crew[1]
            
            total_crew = able_crew + injured_crew
            
            crew_left_behind = total_crew - self.amount
            
            able_crew_left_behind, injured_crew_left_behind = 0, 0
            able_crew_returned, injured_crew_returned = 0, 0
            
            # if not everybody was evacuated:
            if crew_left_behind > 0:
                
                #if all able crew and some injured crew were left behind:
                if crew_left_behind > able_crew:
                    
                    able_crew_left_behind = able_crew
                    
                    injured_crew_returned = total_crew - crew_left_behind
                    
                    injured_crew_left_behind = total_crew - injured_crew_returned
                    
                    # if some able crew and no injured crew were left behind
                elif crew_left_behind < able_crew:
                    
                    injured_crew_returned = injured_crew
                    
                    able_crew_returned = total_crew - crew_left_behind
                    
                    able_crew_left_behind = able_crew - able_crew_returned
                else:
                    able_crew_left_behind = able_crew
                    
                    injured_crew_returned = injured_crew
            else:
                able_crew_returned = able_crew
                
                injured_crew_returned = injured_crew
            
            total_crew_returned = self.amount
            
            self.entity.crew.able_crew += able_crew_returned
            self.entity.crew.injured_crew += injured_crew_returned
            
            if crew_left_behind == 0:
                del self.target.crew.hostiles_on_board[nation]
            else:
                self.target.crew.hostiles_on_board[nation][0] = able_crew_left_behind
                self.target.crew.hostiles_on_board[nation][1] = injured_crew_left_behind
            
            if describe_actions and (
                describe_player_actions or describe_other_actions
            ):
                message:List[str] = []
                
                if describe_player_actions:
                    
                    message.append(
                        f"We have retrived {self.amount} crew"
                    )
                    if injured_crew_returned > 0:
                        
                        message.append(
                            f"members, {'all' if injured_crew_returned == self.amount else f'{injured_crew}'} of whom were transported to sickbay."
                        )
                    else:
                        message.append("members.")
                    
                    if crew_left_behind > 0:
                        
                        if able_crew_left_behind > 0:
                            
                            message.append(
                                f"{able_crew_left_behind} uninjured crew"
                            )
                            if injured_crew_left_behind > 0:
                                message.append("and")
                            
                        if injured_crew_left_behind > 0:
                            
                            message.append(
                                    f"{injured_crew_left_behind} injured crew"
                                )
                        message.append("remain behind.")
                    
                else:
                    message.append(
                        f"The {self.entity.name} has transported"
                    )
                    if crew_left_behind == 0:
                        
                        message.append("all")
                        
                    if able_crew_returned > 0:
                        
                        message.append(f"{able_crew_returned} uninjured attackers")
                        
                        if injured_crew_returned > 0:
                            
                            message.append("and")
                            
                    if injured_crew_returned > 0:
                        
                        message.append(f"{injured_crew_returned} injured attackers")   
                    
                    if crew_left_behind == 0:
                        
                        message.append("back to the ship.")
                    else:
                        message.append(f"back to the ship, leaving behind")
                        
                        if able_crew_left_behind > 0:
                            
                            message.append(f"{able_crew_left_behind} uninjured attackers")
                            
                            if injured_crew_left_behind > 0:
                                
                                message.append("and")
                        
                        if injured_crew_left_behind > 0:
                            
                            message.append(f"{injured_crew_left_behind} injured attackers")
                            
                        message.append("who continue to fight on.")
                
                message_log.add_message(" ".join(message), colors.orange)
            return
        
        is_derlict = self.target.ship_status.is_recrewable
        
        set_of_allied_nations = self.target.game_data.scenerio.get_set_of_allied_nations
        
        entity_in_allied_nation = self.entity.nation in set_of_allied_nations
        
        target_in_allied_nation = self.target.nation in set_of_allied_nations
        
        hostile_takeover = entity_in_allied_nation != target_in_allied_nation
        
        if hostile_takeover:
            
            if is_derlict:
                
                self.target.override_nation_code = self.entity.ship_class.nation_code
            
                difficulty = self.game_data.allied_ai if target_in_allied_nation else self.game_data.difficulty
                
                self.target.ai = difficulty
                
                self.target.crew.able_crew += self.amount
                
                if describe_player_actions:
                    message_log.add_message(
                        "Our forces have transported over taken control of the ship without meeting any restance."
                    )
                #if the acting ship is renforcing an existing boarding party
            elif self.entity.nation in self.target.crew.hostiles_on_board:
                
                if describe_player_actions or describe_other_actions:
                        
                    attackers = self.target.crew.hostiles_on_board[self.entity.nation]
                    
                    able_attackers = attackers[0]
                    injured_attackers = attackers[1]
                    
                    if able_attackers + injured_attackers <= 0:
                        raise ValueError(f"The total number of attackers is {able_attackers + injured_attackers}. However this should have resulted in a diffrent operation")
                    
                    message:List[str] = []
                    
                    if describe_player_actions:
                        
                        message.append(
                            f"Our force of {self.amount} have renforced our existing forces of"
                        )
                        if able_attackers > 0:
                            
                            message.append(f"{able_attackers} able")
                        
                            message.append("crew and" if injured_attackers > 0 else "crew.")
                        
                        if injured_attackers > 0:
                            
                            message.append(f"{injured_attackers} injured crew.")
                    else:
                        message.append(
                            f"The {self.entity.name} has transported {self.amount} to renforce their existing forces of"
                        )
                        if able_attackers > 0:
                            
                            message.append(f"{able_attackers} able")
                        
                            message.append("crew and" if injured_attackers > 0 else "crew.")
                        
                        if injured_attackers > 0:
                            
                            message.append(f"{injured_attackers} injured crew.")
                    
                    message_log.add_message(" ".join(message), colors.orange)
                    
                self.target.crew.hostiles_on_board[self.entity.nation][0] += self.amount
            else:
                self.target.crew.hostiles_on_board[self.entity.nation] = [self.amount, 0]
                
                if describe_player_actions or describe_other_actions:
                    
                    we_them, us_them, our_their = (
                        "We have", "us", "Our"
                    ) if describe_player_actions else (
                        f"The {self.entity.name} has", f"the {self.entity.name}", "Their"
                    )
                    
                    #us_them = "us" if describe_other_actions else f"the {self.entity.name}"
                    
                    #our_their = 'Our' if describe_player_actions else 'Their'
                    
                    message_log.add_message(
f"{we_them} transported {self.amount} of boarders to {us_them}! {our_their} forces are fighting for control of the ship.", 
                        colors.orange
                    )
        else:
            if describe_player_actions or describe_other_actions:
                
                we_them = "We have" if describe_player_actions else f"The {self.entity.name} has"
                                    
                us_them = "us" if describe_other_actions else f"the {self.entity.name}"
                
                message_log.add_message(
                    f"{we_them} renforced {us_them} with {self.amount} fresh crew members."
                )
            
            self.target.crew.able_crew += self.amount
        
        self.entity.crew.able_crew -= self.amount
    
class TorpedoOrder(Order):

    def __init__(
        self, entity:Starship, amount:int, 
        *, 
        torpedo:Torpedo,
        heading:IntOrFloat, x:int, y:int, x_aim:float, y_aim:float, cost:int
    ) -> None:
        super().__init__(entity)
        self.heading = heading
        self.amount = amount
        self.x, self.y = x,y
        self.x_aim, self.y_aim = x_aim, y_aim
        self.torpedo = torpedo
        self.cost = cost
        
        torp_coords = self.game_data.engine.get_lookup_table(
            direction_x=x_aim, direction_y=y_aim, normalise_direction=False
        )
        self.coord_list = tuple(
            Coords(
                co.x+entity.local_coords.x, co.y+entity.local_coords.y
            ) for co in torp_coords if 0 <= 
            co.x+entity.local_coords.x < CONFIG_OBJECT.subsector_width and 
            co.y+entity.local_coords.y < CONFIG_OBJECT.subsector_height
        )
        self.ships = {
            ship.local_coords.create_coords() : ship for ship in self.entity.game_data.grab_ships_in_same_sub_sector(
                self.entity, accptable_ship_statuses={STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK}
            ) if ship.local_coords in self.coord_list and ship.ship_status.is_active
        }
    
    def __hash__(self):
        return hash((self.entity, self.heading, self.amount, self.x, self.y, self.x_aim, self.y_aim, self.coord_list, self.cost))
    
    @classmethod
    def from_coords(
        cls, 
        *,
        entity:Starship, 
        amount:int, 
        torpedo:Torpedo,
        x:int, y:int,
        cost:int
    ):
        x_aim, y_aim = Coords.normalize_other(x=x - entity.local_coords.x, y=y - entity.local_coords.y)

        heading = atan2(y_aim, x_aim) / TO_RADIANS
        return cls(
            entity, amount, 
            torpedo=torpedo,
            heading=heading, x=x, y=y, x_aim=x_aim, y_aim=y_aim, cost=cost
        )
    
    @classmethod
    def from_heading(
        cls, 
        *,
        entity:Starship, heading:int, amount:int, torpedo:Torpedo, cost:int
    ):
        x_aim, y_aim = heading_to_direction(heading)
        
        x_aim, y_aim = Coords.normalize_other(x=x_aim, y=y_aim)
        
        x, y = heading_to_coords(
            heading, CONFIG_OBJECT.max_move_distance, entity.local_coords.x, entity.local_coords.y, 
            CONFIG_OBJECT.subsector_width, CONFIG_OBJECT.subsector_height
        )
        return cls(
            entity, amount, torpedo=torpedo, heading=heading, x=x, y=y, x_aim=x_aim, y_aim=y_aim, cost=cost
        )

    def perform(self) -> None:
        try:
            cloak_status = self.entity.cloak.force_fire_decloak()
            
            player = self.game_data.player
            if (
                cloak_status and 
                self.entity is not player and self.entity.sector_coords == player.sector_coords
            ):
                self.game_data.engine.message_log.add_message(
                    "Enemy ship decloaking!", colors.alert_red
                )
        except AttributeError:
            pass
        
        self.entity.game_data.handle_torpedo(
            shipThatFired=self.entity,torpsFired=self.amount, 
            coords=self.coord_list, 
            torpedo_type=self.torpedo, 
            ships_in_area=self.ships, 
            heading=self.heading
        )
        self.entity.turn_repairing = 0
        
        if self.entity.is_controllable:
            self.game_data.player_record["torpedos_fired"] += self.amount
            self.game_data.player_record["energy_used"] += self.cost

    def raise_warning(self):

        if not self.entity.torpedo_launcher.is_opperational:
            return OrderWarning.SYSTEM_INOPERATIVE

        if self.amount == 0:
            return OrderWarning.ZERO_VALUE_ENTERED
        
        if self.cost > self.entity.power_generator.energy:
            return OrderWarning.NOT_ENOUGHT_ENERGY

        sub_sector:SubSector = self.game_data.grid[self.entity.sector_coords.y][self.entity.sector_coords.x]

        hit_enemy_ship = False
        hit_friendly_ship = False
        for co in self.coord_list:
            try:
                planet = sub_sector.planets_dict[co]
                if not hit_enemy_ship:
                    return (
                        OrderWarning.TORPEDO_WILL_HIT_PLANET_OR_FRIENDLY_SHIP 
                        if hit_friendly_ship else 
                        OrderWarning.TORPEDO_WILL_HIT_PLANET
                    )
                return (
                        OrderWarning.TORPEDO_COULD_HIT_PLANET if hit_friendly_ship else 
                        OrderWarning.TORPEDO_COULD_HIT_PLANET_OR_FRIENDLY_SHIP
                    )
            except KeyError:
                try:
                    star = sub_sector.stars_dict[co]
                    
                    return OrderWarning.SAFE if hit_enemy_ship else OrderWarning.TORPEDO_WILL_MISS

                except KeyError:
                    try:
                        ship = self.ships[co]
                        if ship:
                            if ship.ship_class.nation_code == self.entity.ship_class.nation_code:
                                hit_friendly_ship = True
                            else:
                                hit_enemy_ship = True
                    except KeyError:
                        pass
        return (
            OrderWarning.TORPEDO_COULD_FRIENDLY_SHIP if hit_friendly_ship else OrderWarning.SAFE
        ) if hit_enemy_ship else (
            OrderWarning.TORPEDO_WILL_HIT_FRIENDLY_SHIP_OR_MISS if hit_friendly_ship else OrderWarning.TORPEDO_WILL_MISS
        )
        
class DockOrder(Order):

    def __init__(self, entity: Starship, planet:Union[Planet, Starship]) -> None:
        super().__init__(entity)
        self.planet = planet
        self.undock = entity.docked
        self.ships = self.entity.game_data.grab_ships_in_same_sub_sector(
            self.entity, accptable_ship_statuses={STATUS_ACTIVE}
        )
    
    def __hash__(self) -> int:
        return hash((self.planet, self.undock, self.ships))
    
    def perform(self) -> None:
        self.entity.docked = not self.undock
        if self.entity.is_controllable:
            self.game_data.engine.message_log.add_message(
                "Docking procedures complete, captain." if self.entity.docked else "Undocking procedures complete, captain."
            )
        if self.entity.docked:
            
            torp, num = self.planet.can_supply_torpedos(self.entity)
            
            if torp is not None and num > 0:
                self.entity.torpedo_launcher.torps[torp] += num
    
    def raise_warning(self):
        
        if not self.undock:
            try:
                if self.entity.cloak.cloak_is_turned_on:
                    return OrderWarning.DECLOAK_FIRST
            except AttributeError:
                pass
        elif self.ships:
            return OrderWarning.ENEMY_SHIPS_NEARBY

        if not self.planet.local_coords.is_adjacent(other=self.entity.local_coords):
            return OrderWarning.PLANET_TOO_DISTANT
        
        planet_habbitation = self.planet.get_habbitation(self.entity)

        if planet_habbitation in {PLANET_BARREN, PLANET_BOMBED_OUT, PLANET_PREWARP}:
            return OrderWarning.PLANET_TOO_PRIMITIVE
        
        return (
            OrderWarning.PLANET_UNFRIENDLY if planet_habbitation == PLANET_HOSTILE else 
            OrderWarning.SAFE
        )

class PolarizeOrder(Order):
    
    def __init__(self, entity: Starship, amount:int, active:bool) -> None:
        super().__init__(entity)
        self.active = active
        self.amount = amount
    
    def __hash__(self) -> int:
        return hash((self.entity, self.active, self.amount))
    
    def perform(self) -> None:
        
        amount = self.amount
        
        old = self.entity.polarized_hull.is_polarized

        is_player = self.entity.is_controllable
        
        is_in_same_system = self.entity.sector_coords == self.game_data.player.sector_coords
        
        shields = self.entity.shield_generator.shields
        
        if old != self.active:
            
            if is_player:
            
                self.game_data.engine.message_log.add_message(
                    "Hull polarized." if self.active <= 0 else "Hull depolarized."
                )
            elif is_in_same_system:
                
                self.game_data.engine.message_log.add_message(
                    f"The {self.entity.name} has {'polarized' if self.active else 'depolarized'} it's hull."
                )
        if amount != shields:
            
            if is_player:
                
                self.game_data.engine.message_log.add_message(
                    "Increasing hull polarization." if amount > shields else "Decreasing hull polarization."
                )
            elif is_in_same_system:
                self.game_data.engine.message_log.add_message(
                    f"The {self.entity.name} has {'increased to' if amount > shields else 'decreased'} its hull polarization."
                )
        self.entity.polarized_hull.is_polarized = self.active
        
        self.entity.polarized_hull.polarization_amount = self.amount

class RechargeOrder(Order):

    def __init__(self, entity:Starship, amount:int, active:bool) -> None:
        super().__init__(entity)
        
        self.cost = amount - self.entity.shield_generator.shields
        if amount >= self.entity.shield_generator.shields:
            
            amount = floor(amount * self.entity.shield_generator.get_effective_value)
        else:
            self.cost =  ceil(self.cost * self.entity.shield_generator.get_effective_value)
            
        self.amount = amount
        self.active = active
    
    def __hash__(self) -> int:
        return hash((self.entity, self.cost, self.amount, self.active))
    
    def perform(self) -> None:

        amount = self.amount
        
        energy_cost = self.cost
        
        self.entity.power_generator.energy -= energy_cost
        
        old = self.entity.shield_generator.shields_up
        
        self.entity.shield_generator.shields_up = self.active
        
        is_player = self.entity.is_controllable
        
        is_in_same_system = self.entity.sector_coords == self.game_data.player.sector_coords
        
        shields = self.entity.shield_generator.shields
        
        if old != self.active:
            
            if is_player:
            
                self.game_data.engine.message_log.add_message(
                    "Shields up." if self.active <= 0 else "Shields down."
                )
            elif is_in_same_system:
                
                self.game_data.engine.message_log.add_message(
                    f"The {self.entity.name} has {'raised' if self.active else 'lowered'} it's shields."
                )
        
        if amount != shields:
            
            if is_player:
                
                self.game_data.engine.message_log.add_message(
                    "Transfering energy to shields." if amount > shields else "Diverting shield energy."
                )
            elif is_in_same_system:
                self.game_data.engine.message_log.add_message(
                    f"The {self.entity.name} has {'transfered energy to' if amount > shields else 'diverted energy from'} its shields."
                )
        if self.entity.is_controllable:
            shields = self.entity.shield_generator.shields
            
            if amount > shields:
                
                self.game_data.engine.message_log.add_message(
                    "Transfering energy to shields."
                )
            elif amount < shields:
                
                self.game_data.engine.message_log.add_message(
                    "Diverting shield energy"
                )
        self.entity.shield_generator.shields = amount
        
        if self.entity.is_controllable:
            self.game_data.player_record["energy_used"] += energy_cost
    
    def raise_warning(self):
        
        if self.amount == self.entity.shield_generator.shields and self.active == self.entity.shield_generator.shields_up:
            
            return OrderWarning.NO_CHANGE_IN_SHIELD_ENERGY
        
        if self.cost > self.entity.power_generator.energy:
            
            return OrderWarning.NOT_ENOUGHT_ENERGY
        
        if not self.active:
            nearbye_ships = [ship for ship in self.game_data.grab_ships_in_same_sub_sector(
                self.entity, accptable_ship_statuses={STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED}
            ) if ship.nation is ALL_NATIONS[self.game_data.scenerio.enemy_nation]]
            
            if nearbye_ships: 
                return OrderWarning.ENEMY_SHIPS_NEARBY_WARN 
        return OrderWarning.SAFE

class RepairOrder(Order):

    def __init__(self, entity:Starship, amount:int) -> None:
        super().__init__(entity)
        self.amount = amount
        self.ships = tuple(
            self.entity.game_data.grab_ships_in_same_sub_sector(
                self.entity, accptable_ship_statuses={STATUS_ACTIVE}
            )
        )
        self.number = len(self.ships)
        
    def __hash__(self) -> int:
        return hash((self.entity, self.amount, self.ships, self.number))
    
    def perform(self) -> None:
        
        self.entity.turn_repairing += 1
        
    def raise_warning(self):
        
        if self.number:
            return OrderWarning.ENEMY_SHIPS_NEARBY_WARN
        try:
            beam_i = self.entity.beam_array.integrety
        except AttributeError:
            beam_i = 1.0
        try:
            cannon_i = self.entity.cannons.integrety
        except AttributeError:
            cannon_i = 1.0
        try:
            impulse_i = self.entity.impulse_engine.integrety
        except AttributeError:
            impulse_i = 1.0
        try:
            shield_i = self.entity.shield_generator.integrety
            shield_e = self.entity.shield_generator.shields_percentage
        except AttributeError:
            shield_i = 1.0
            shield_e = 1.0
        try:
            torpedo_i = self.entity.torpedo_launcher.integrety
        except AttributeError:
            torpedo_i = 1.0
        try:
            warp_i = self.entity.warp_drive.integrety
        except AttributeError:
            warp_i = 1.0
        try:
            transport_i = self.entity.transporter.integrety
        except AttributeError:
            transport_i = 1.0
        try:
            cloak_i = self.entity.cloak.integrety
        except AttributeError:
            cloak_i = 1.0
        
        if all(
            (
                beam_i == 1.0,
                cannon_i == 1.0,
                impulse_i == 1.0,
                cloak_i == 1.0,
                self.entity.sensors.integrety == 1.0,
                shield_i == 1.0,
                torpedo_i == 1.0,
                self.entity.power_generator.integrety == 1.0,
                warp_i == 1.0,
                self.entity.hull_percentage == 1.0,
                shield_e == 1.0,
                transport_i == 1.0,
                self.entity.power_generator.energy_percentage == 1.0
            )
        ):
            return OrderWarning.NO_REPAIRS_NEEDED
        
        return OrderWarning.SAFE

class CloakOrder(Order):

    def __init__(self, entity: Starship, deloak:bool) -> None:
        super().__init__(entity)
        self.deloak = deloak
    
    def perform(self) -> None:
        
        clo = "decloaked" if self.deloak else "cloaked"
        
        player = self.game_data.player
        
        if self.entity.sector_coords == player.sector_coords:
            self.game_data.engine.message_log.add_message(
                f"We have sucessfully {clo}, {player.nation.captain_rank_name}." 
                if self.entity is player else 
                f"The {self.entity.name} has {clo}!", fg=colors.alert_blue
            )
        self.entity.cloak.cloak_status = CloakStatus.INACTIVE if self.deloak else CloakStatus.ACTIVE

    def raise_warning(self):
        
        if not self.deloak:
            if self.entity.docked:
                return OrderWarning.UNDOCK_FIRST
            
            if self.entity.cloak.cloak_cooldown > 0:
                return OrderWarning.CLOAK_COOLDOWN
            
            if not self.entity.ship_can_cloak:
                return OrderWarning.SYSTEM_INOPERATIVE
        
        return super().raise_warning()

class SelfDestructOrder(Order):

    def __init__(self, entity: Starship, nearbye_ships:Iterable[Starship]) -> None:
        super().__init__(entity)
        self.ships = nearbye_ships

    def __hash__(self) -> int:
        return hash((self.entity, self.ships))

    def perform(self) -> None:
        if self.entity.is_controllable:
            self.game_data.engine.message_log.add_message("Captain, it has been an honor...")
        self.entity.hull = -self.entity.ship_class.max_hull
        self.entity.destroy("self destruct", self_destruct=True)
        
    def raise_warning(self):

        sector_ships = self.ships

        if not sector_ships:
            return OrderWarning.NO_ENEMY_SHIPS_NEARBY
        
        ships_in_range = [
            ship for ship in sector_ships if self.entity.local_coords.distance(
                coords=ship.local_coords
            ) <= self.entity.ship_class.warp_breach_damage
        ]
        return OrderWarning.SAFE if ships_in_range else OrderWarning.NO_ENEMY_SHIPS_NEARBY
