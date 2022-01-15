from __future__ import annotations
from collections import OrderedDict
from decimal import Decimal
import os
from random import choice
from textwrap import wrap
from data_globals import LOCAL_ENERGY_COST, SECTOR_ENERGY_COST, STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK, CloakStatus
from engine import CONFIG_OBJECT
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Union
from nation import ALL_NATIONS
from order import CloakOrder, SelfDestructOrder, blocks_action, torpedo_warnings, collision_warnings, misc_warnings, \
    Order, DockOrder, OrderWarning, EnergyWeaponOrder, RepairOrder, TorpedoOrder, WarpOrder, MoveOrder, RechargeOrder
from global_functions import stardate
from space_objects import Planet, Star
from starship import Starship
from torpedo import ALL_TORPEDO_TYPES
from ui_related import BooleanBox, ButtonBox, NumberHandeler, ScrollingTextBox, Selector, SimpleElement, TextHandeler, confirm
import tcod
import tcod.event
import tcod.constants
import colors, exceptions
from render_functions import print_mega_sector, print_message_log, print_system, render_other_ship_info, render_own_ship_info, render_command_box, render_position, select_ship_planet_star, select_sub_sector_space, select_sector_space

numeric = {
    tcod.event.K_0 : 0,
    tcod.event.K_KP_0 : 0,
    tcod.event.K_1 : 1,
    tcod.event.K_KP_1 : 1,
    tcod.event.K_2 : 2,
    tcod.event.K_KP_2 : 2,
    tcod.event.K_3 : 3,
    tcod.event.K_KP_3 : 3,
    tcod.event.K_4 : 4,
    tcod.event.K_KP_4 : 4,
    tcod.event.K_5 : 5,
    tcod.event.K_KP_5 : 5,
    tcod.event.K_6 : 6,
    tcod.event.K_KP_6 : 6,
    tcod.event.K_7 : 7,
    tcod.event.K_KP_7 : 7,
    tcod.event.K_8 : 8,
    tcod.event.K_KP_8 : 8,
    tcod.event.K_9 : 9,
    tcod.event.K_KP_9 : 9
}

negiative_signs = {tcod.event.K_MINUS, tcod.event.K_KP_MINUS}

if TYPE_CHECKING:
    from engine import Engine

OrderOrHandler = Union["Order", "BaseEventHandler"]

class BaseEventHandler(tcod.event.EventDispatch[OrderOrHandler]):
    engine: Engine
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Order), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[OrderOrHandler]:
        raise SystemExit()

class EventHandler(BaseEventHandler):

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def handle_action(self, action: Optional[OrderOrHandler]) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False
        try:
            action.perform()
            
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], colors.impossible)
            return False  # Skip enemy turn on exceptions.
        
        self.engine.player.repair()

        game_data = self.engine.game_data
        game_data.ships_in_same_sub_sector_as_player = game_data.grab_ships_in_same_sub_sector(
            game_data.player, accptable_ship_statuses={
                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
            }
        )
        game_data.date_time = game_data.date_time + game_data.fifteen_seconds
        game_data.stardate = stardate(game_data.date_time)
        #game_data.stardate_text = f"{game_data.stardate:5.2}"

        self.engine.handle_enemy_turns()
        
        
        
        return True

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:

        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            if self.engine.game_data.scenerio.scenario_type.is_game_over(self.engine.game_data):
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
        if not self.engine.player.ship_status.is_active:
            pass
        return self

class MainGameEventHandler(EventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.warned_once = False
    
    def on_render(self, console: tcod.Console) -> None:
        
        print_system(console, self.engine.game_data)
        print_mega_sector(console, self.engine.game_data)
        render_own_ship_info(console, self.engine.game_data)

        render_other_ship_info(console, self.engine.game_data, self.engine.game_data.selected_ship_planet_or_star)

        print_message_log(console, self.engine.game_data)
        render_position(console, self.engine.game_data)

class CancelConfirmHandler(MainGameEventHandler):
    
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        self.confirm_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=16+CONFIG_OBJECT.command_display_y,
            width=9,
            height=3,
            text="Confirm",
            active_fg=colors.white,
            bg=colors.black,
        )

        self.cancel_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=20+CONFIG_OBJECT.command_display_y,
            width=9,
            height=3,
            text="Cancel",
            active_fg=colors.white,
            bg=colors.black,
        )
    
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        self.cancel_button.render(console)
        self.confirm_button.render(console)

class MinMaxInitator(CancelConfirmHandler):
    
    def __init__(
        self, 
        engine: Engine, 
        *,
        max_value:int, starting_value:int
        ) -> None:
        super().__init__(engine)
        
        self.max_button = SimpleElement(
            x=3+12+CONFIG_OBJECT.command_display_x,
            y=16+CONFIG_OBJECT.command_display_y,
            width=7,
            height=3,
            text="Max",
            active_fg=colors.white,
            bg=colors.black
        )
        
        self.min_button = SimpleElement(
            x=3+12+CONFIG_OBJECT.command_display_x,
            y=20+CONFIG_OBJECT.command_display_y,
            width=7,
            height=3,
            text="Min",
            active_fg=colors.white,
            bg=colors.black
        )
        
        self.amount_button = NumberHandeler(
            limit=4, max_value=max_value, 
            min_value=0, starting_value=starting_value,
            x=3+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=12,
            height=3,
            title="Amount:",
            alignment=tcod.constants.RIGHT,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        super().on_render(console)
        
        self.min_button.render(console)
        self.max_button.render(console)
        self.amount_button.render(console)
        
class HeadingBasedHandler(CancelConfirmHandler):
        
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        self.heading_button = NumberHandeler(
            limit=3, 
            max_value=360, min_value=0, wrap_around=True, starting_value=0,
            x=3+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=12,
            height=3,
            title="Heading:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.selected_handeler = self.heading_button
        
        self.three_fifteen_button = SimpleElement(
            x=16+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="315",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.two_seventy_button = SimpleElement(
            x=16+CONFIG_OBJECT.command_display_x,
            y=6+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="270",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.zero_button = SimpleElement(
            x=22+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="0",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.fourty_five_button = SimpleElement(
            x=28+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="45",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.two_twenty_five_button = SimpleElement(
            x=16+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="225",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.ninty_button = SimpleElement(
            x=28+CONFIG_OBJECT.command_display_x,
            y=6+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="90",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )
        
        self.one_thirty_five_button = SimpleElement(
            x=28+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="135",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.one_eighty_button = SimpleElement(
            x=22+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=5,
            height=3,
            text="180",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
            
        if self.fourty_five_button.cursor_overlap(event):
            self.heading_button.set_text(45)
            #self.heading_button.text = self.fourty_five_button.text
            
        elif self.ninty_button.cursor_overlap(event):
            self.heading_button.set_text(90)
            #self.heading_button.text = self.ninty_button.text
        
        elif self.one_thirty_five_button.cursor_overlap(event):
            self.heading_button.set_text(135)
            #self.heading_button.text = self.one_thirty_five_button.text
        
        elif self.one_eighty_button.cursor_overlap(event):
            self.heading_button.set_text(180)
            #self.heading_button.text = self.one_eighty_button.text
            
        elif self.two_twenty_five_button.cursor_overlap(event):
            self.heading_button.set_text(225)
            #self.heading_button.text = self.two_twenty_five_button.text
        
        elif self.two_seventy_button.cursor_overlap(event):
            self.heading_button.set_text(270)
            #self.heading_button.text = self.two_seventy_button.text
        
        elif self.three_fifteen_button.cursor_overlap(event):
            self.heading_button.set_text(315)
            #self.heading_button.text = self.three_fifteen_button.text
        
        elif self.zero_button.cursor_overlap(event):
            self.heading_button.set_text(0)
            #self.heading_button.text = self.zero_button.text
        
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        self.heading_button.render(console)
        self.fourty_five_button.render(console)
        self.ninty_button.render(console)
        self.one_thirty_five_button.render(console)
        self.one_eighty_button.render(console)
        self.two_twenty_five_button.render(console)
        self.two_seventy_button.render(console)
        self.three_fifteen_button.render(console)
        self.zero_button.render(console)

class CoordBasedHandler(CancelConfirmHandler):
    
    def __init__(
        self, engine: Engine, 
        *,
        max_x:int,
        max_y:int,
        starting_x:int,
        starting_y:int,
        ) -> None:
        
        super().__init__(engine)
                
        self.x_button = NumberHandeler(
            limit=2, 
            max_value=max_x, min_value=0, 
            wrap_around=True, 
            starting_value=starting_x,
            x=3+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=6,
            height=3,
            title="X:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.y_button = NumberHandeler(
            limit=2, 
            max_value=max_y, min_value=0, 
            wrap_around=True, 
            starting_value=starting_y,
            x=10+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=6,
            height=3,
            title="Y:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT,
            initally_active=False
        )

        self.selected_handeler = self.x_button
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.x_button.cursor_overlap(event):
            self.selected_handeler = self.x_button
            self.x_button.is_active = True
            self.y_button.is_active = False
        elif self.y_button.cursor_overlap(event):
            self.selected_handeler = self.y_button
            self.x_button.is_active = False
            self.y_button.is_active = True
        
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        self.y_button.render(console)
        self.x_button.render(console)

class CommandEventHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        #print("CommandEventHandler")
        super().__init__(engine)
        
        self.ship_type_can_fire_beam_arrays = self.engine.player.ship_type_can_fire_beam_arrays
        self.ship_type_can_fire_cannons = self.engine.player.ship_type_can_fire_cannons
        self.ship_type_can_cloak = self.engine.player.ship_type_can_cloak
        self.ship_type_can_fire_torps = self.engine.player.ship_type_can_fire_torps
        
        self.warp_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x, 
            y=2+CONFIG_OBJECT.command_display_y,
            width=11,
            height=3,
            text="(W)arp",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )

        self.move_button = SimpleElement(
            x=2+13+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=11,
            height=3,
            text="(M)ove",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )

        self.shields_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=5+CONFIG_OBJECT.command_display_y,
            width=11,
            height=3,
            text="(S)hields",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )

        self.repair_button = SimpleElement(
            x=2+13+CONFIG_OBJECT.command_display_x,
            y=5+CONFIG_OBJECT.command_display_y,
            width=11,
            height=3,
            text="(R)epair",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )
        
        self.cloak_button = BooleanBox(
            x=2+CONFIG_OBJECT.command_display_x,
            y=8+CONFIG_OBJECT.command_display_y,
            width=11,
            height=3,
            active_text="(C)loak",
            inactive_text="De(C)loak",
            active_fg=colors.white,
            inactive_fg=colors.white,
            initally_active=self.engine.player.cloak_status == CloakStatus.INACTIVE
        )
        
        self.dock_button = BooleanBox(
            x=2+13+CONFIG_OBJECT.command_display_x,
            y=8+CONFIG_OBJECT.command_display_y,
            width=11,
            height=3,
            active_text="(D)ock",
            inactive_text="Un(D)ock",
            active_fg=colors.white,
            inactive_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER,
            initally_active= not self.engine.player.docked
        )
        beam_name_cap = self.engine.player.ship_class.get_energy_weapon.beam_name_cap

        self.phasers_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=11+CONFIG_OBJECT.command_display_y,
            width=24,
            height=3,
            text=f"(F)ire {beam_name_cap}s",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )
        cannon_name_cap = self.engine.player.ship_class.get_energy_weapon.cannon_name_cap
        
        self.cannons_buttons = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=14+CONFIG_OBJECT.command_display_y,
            width=24,
            height=3,
            text=f"F(i)re {cannon_name_cap}s",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )

        self.torpedos_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=17+CONFIG_OBJECT.command_display_y,
            width=24,
            height=3,
            text="Fire (T)orpedos",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )
        
        self.auto_destruct_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=20+CONFIG_OBJECT.command_display_y,
            width=24,
            height=3,
            text="(A)uto-Destruct",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )        

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        captain = self.engine.player.ship_class.nation.captain_rank_name
        
        if self.warp_button.cursor_overlap(event):
            
            self.warned_once = False
            
            if not self.engine.player.sys_warp_drive.is_opperational:
                
                self.engine.message_log.add_message(f"Error: Warp engines are inoperative, {captain}.", fg=colors.red)

            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
                
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return WarpHandlerEasy(self.engine) if self.engine.easy_warp else WarpHandler(self.engine)
        
        elif self.move_button.cursor_overlap(event):
            
            self.warned_once = False
            
            if not self.engine.player.sys_impulse.is_opperational:
                
                self.engine.message_log.add_message(
                    f"Error: Impulse systems are inoperative, {captain}.", fg=colors.red
                )

            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
                
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return MoveHandlerEasy(self.engine) if self.engine.easy_navigation else MoveHandler(self.engine)
        
        elif self.shields_button.cursor_overlap(event):
            
            self.warned_once = False
            
            if not self.engine.player.sys_shield_generator.is_opperational:
                
                self.engine.message_log.add_message(f"Error: Shield systems are inoperative, {captain}.", fg=colors.red)

            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
            #elif self.engine.player.docked:
            #    self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return ShieldsHandler(self.engine)
            
        elif self.phasers_button.cursor_overlap(event) and self.engine.player.ship_type_can_fire_beam_arrays:
            
            self.warned_once = False
            
            if not self.engine.player.sys_beam_array.is_opperational:
                
                p = self.engine.player.ship_class.get_energy_weapon.beam_name_cap
                
                self.engine.message_log.add_message(
                    f"Error: {p} systems are inoperative, {captain}.", fg=colors.red
                )
            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
                
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return BeamArrayHandler(self.engine)

        elif self.cannons_buttons.cursor_overlap(event) and self.engine.player.ship_can_fire_cannons:
            
            self.warned_once = False
            
            if not self.engine.player.sys_cannon_weapon.is_opperational:
                
                p = self.engine.player.ship_class.get_energy_weapon.cannon_name_cap
                
                self.engine.message_log.add_message(
                    f"Error: {p} systems are inoperative, {captain}.", fg=colors.red
                )
            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
                
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return CannonHandler(self.engine)

        elif self.dock_button.cursor_overlap(event):
            planet = self.engine.game_data.selected_ship_planet_or_star

            if not planet and not isinstance(planet, Planet):
                player = self.engine.player
                
                nearby_planets = [
                    planet_ for planet_ in player.get_sub_sector.planets_dict.values() if 
                    planet_.local_coords.is_adjacent(
                        other=player.local_coords
                    ) and planet_.planet_habbitation.can_ressuply
                ]
                
                nearby_planets.sort(reverse=True)
                
                try:
                    planet = nearby_planets[0]
                    
                except IndexError:
                    planet = None

            
            self.warned_once = False
            dock_order = DockOrder(self.engine.player, planet)

            warning = dock_order.raise_warning()

            if warning == OrderWarning.SAFE:
                self.dock_button.is_active = not self.dock_button.is_active
                #self.dock_button.text = "(D)ock" if self.engine.player.docked else "Un(D)ock"
                return dock_order
            if warning == OrderWarning.ENEMY_SHIPS_NEARBY:
                if self.warned_once:
                    return dock_order
                self.engine.message_log.add_message("Warning: There are hostile ships nearby.", fg=colors.orange)
                
            else:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)

        elif self.repair_button.cursor_overlap(event):
            
            repair = RepairOrder(self.engine.player, 1)
            warning = repair.raise_warning()
            
            if self.warned_once:
                return repair
            try:
                self.engine.message_log.add_message(misc_warnings[warning], fg=colors.orange)
                self.warned_once = True
            except KeyError:
                
                return repair
            
        elif self.cloak_button.cursor_overlap(event) and self.engine.player.ship_type_can_cloak:
                player = self.engine.player
                cloak_order = CloakOrder(player, player.cloak_status != CloakStatus.INACTIVE)
                warning = cloak_order.raise_warning()

                if warning == OrderWarning.SAFE:
                    self.cloak_button.is_active = not self.cloak_button.is_active
                    return cloak_order
                
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)

        elif self.torpedos_button.cursor_overlap(event) and self.engine.player.ship_type_can_fire_torps:
            
            self.warned_once = False
            
            if not self.engine.player.ship_can_fire_torps:
                self.engine.message_log.add_message(
                    text=f"Error: Torpedo systems are inoperative, {captain}." 
                    if not self.engine.player.sys_torpedos.is_opperational else 
                    f"Error: This ship has no remaining torpedos, {captain}.", fg=colors.red
                )
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return TorpedoHandlerEasy(self.engine) if self.engine.easy_aim else TorpedoHandler(self.engine)
            
        elif self.auto_destruct_button.cursor_overlap(event):
            
            return SelfDestructHandler(self.engine)
        else:
            game_data = self.engine.game_data
            ship_planet_or_star = select_ship_planet_star(game_data, event)
            
            if ship_planet_or_star:
                
                if isinstance(ship_planet_or_star, (Planet, Star)):
                    
                    game_data.selected_ship_planet_or_star = ship_planet_or_star
                    
                elif isinstance(ship_planet_or_star, Starship):
                    if (
                        ship_planet_or_star is not self.engine.player and 
                        ship_planet_or_star is not game_data.selected_ship_planet_or_star
                    ):    
                        game_data.ship_scan = ship_planet_or_star.scan_this_ship(
                            game_data.player.determin_precision, use_effective_values=False
                        )
                        game_data.selected_ship_planet_or_star = ship_planet_or_star
                else:
                    game_data.selected_ship_planet_or_star = None

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:
        
        captain = self.engine.player.ship_class.nation.captain_rank_name
        
        if event.sym == tcod.event.K_w:
            
            self.warned_once = False
            
            if not self.engine.player.sys_warp_drive.is_opperational:
                
                self.engine.message_log.add_message(f"Error: Warp engines are inoperative, {captain}.", fg=colors.red)

            elif self.engine.player.energy <= 0:
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
            elif self.engine.player.docked:
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return WarpHandlerEasy(self.engine) if self.engine.easy_warp else WarpHandler(self.engine)
        elif event.sym == tcod.event.K_m:
            self.warned_once = False
            if not self.engine.player.sys_impulse.is_opperational:
                self.engine.message_log.add_message(
                    f"Error: Impulse systems are inoperative, {captain}.", fg=colors.red
                )

            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
                
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return MoveHandlerEasy(self.engine) if self.engine.easy_navigation else MoveHandler(self.engine)
            
        elif event.sym == tcod.event.K_s:
            
            self.warned_once = False
            
            if not self.engine.player.sys_shield_generator.is_opperational:
                self.engine.message_log.add_message(f"Error: Shield systems are inoperative, {captain}.", fg=colors.red)

            elif self.engine.player.energy <= 0:
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
            
            else:
                return ShieldsHandler(self.engine)
            
        elif event.sym == tcod.event.K_r:
            
            repair = RepairOrder(self.engine.player, 1)
            
            warning = repair.raise_warning()
            
            if self.warned_once:
                return repair
            try:
                
                self.engine.message_log.add_message(misc_warnings[warning], fg=colors.orange)
                self.warned_once = True
                
            except KeyError:
                
                return repair
            
        elif event.sym == tcod.event.K_c and self.engine.player.ship_type_can_cloak:

            player = self.engine.player
            cloak_order = CloakOrder(player, player.cloak_status != CloakStatus.INACTIVE)
            warning = cloak_order.raise_warning()

            if warning == OrderWarning.SAFE:
                self.cloak_button.is_active = not self.cloak_button.is_active
                return cloak_order
            
            self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            
        elif event.sym == tcod.event.K_f and self.engine.player.ship_type_can_fire_beam_arrays:
            
            self.warned_once = False
            
            if not self.engine.player.sys_beam_array.is_opperational:
                
                p = self.engine.player.ship_class.get_energy_weapon.beam_name
                self.engine.message_log.add_message(f"Error: {p} systems are inoperative, {captain}.", fg=colors.red)

            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
                
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return BeamArrayHandler(self.engine)
            
        elif event.sym == tcod.event.K_i and self.engine.player.ship_type_can_fire_cannons:
            
            self.warned_once = False
            
            if not self.engine.player.sys_cannon_weapon.is_opperational:
                
                p = self.engine.player.ship_class.get_energy_weapon.cannon_name_cap
                
                self.engine.message_log.add_message(
                    f"Error: {p} systems are inoperative, {captain}.", fg=colors.red
                )
            elif self.engine.player.energy <= 0:
                
                self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
                
            elif self.engine.player.docked:
                
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return CannonHandler(self.engine)
            
        elif event.sym == tcod.event.K_d:

            planet = self.engine.game_data.selected_ship_planet_or_star

            if not planet and not isinstance(planet, Planet):
                
                player = self.engine.player
                
                nearby_planets = [
                    planet_ for planet_ in player.get_sub_sector.planets_dict.values() if 
                    planet_.local_coords.is_adjacent(
                        other=player.local_coords
                    ) and planet_.planet_habbitation.can_ressuply
                ]
                
                nearby_planets.sort(reverse=True)
                
                try:
                    planet = nearby_planets[0]
                    
                except IndexError:
                    planet = None
                
            if planet and isinstance(planet, Planet):
                dock_order = DockOrder(self.engine.player, planet)
                self.warned_once = False
                warning = dock_order.raise_warning()

                if warning == OrderWarning.SAFE:
                    self.dock_button.is_active = not self.dock_button.is_active
                    #self.dock_button.text = "(D)ock" if self.engine.player.docked else "Un(D)ock"
                    return dock_order
                if warning == OrderWarning.ENEMY_SHIPS_NEARBY:
                    #if self.warned_once:
                    #    return dock_order
                    self.engine.message_log.add_message("Warning: There are hostile ships nearby", fg=colors.orange)
                    
                else:
                    self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            else:
                self.engine.message_log.add_message(f"Error: No suitable planet nearbye, {captain}.", fg=colors.red)
                
        elif event.sym == tcod.event.K_t and self.engine.player.ship_type_can_fire_torps:
            self.warned_once = False
            if not self.engine.player.ship_can_fire_torps:
                self.engine.message_log.add_message(
                    text=f"Error: Torpedo systems are inoperative, {captain}." 
                    if not self.engine.player.sys_torpedos.is_opperational else 
                    f"Error: This ship has not remaining torpedos, {captain}.", fg=colors.red
                )
            elif self.engine.player.docked:
                self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
            else:
                return TorpedoHandlerEasy(self.engine) if self.engine.easy_aim else TorpedoHandler(self.engine)
        elif event.sym == tcod.event.K_a:
            return SelfDestructHandler(self.engine)

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        captain = self.engine.player.ship_class.nation.captain_rank_name

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title=f"Your orders, {captain}?"
            )
        
        self.warp_button.render(console)
        self.move_button.render(console)
        self.dock_button.render(console)
        self.shields_button.render(console)
        
        if self.ship_type_can_fire_beam_arrays:
            self.phasers_button.render(console)
            
        if self.ship_type_can_fire_cannons:
            self.cannons_buttons.render(console)
            
        self.repair_button.render(console)
        
        if self.ship_type_can_fire_torps:
            self.torpedos_button.render(console)
            
        self.auto_destruct_button.render(console)
        
        if self.ship_type_can_cloak:
            self.cloak_button.render(console)
        
class WarpHandler(HeadingBasedHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        self.distance = NumberHandeler(
            limit=3, 
            max_value=CONFIG_OBJECT.max_warp_distance, 
            min_value=1,
            x=3+CONFIG_OBJECT.command_display_x,
            y=7+CONFIG_OBJECT.command_display_y,
            width=12,
            height=3,
            title="Distance:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT,
            initally_active=False
        )
        
        self.energy_cost = round(
            self.distance.add_up() * 
            self.engine.player.sys_warp_drive.affect_cost_multiplier * SECTOR_ENERGY_COST
        )
        
        self.cost_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            width=10,
            height=3,
            title="Energy Cost:",
            text=f"{self.energy_cost}",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input warp heading and distance"
            )
        super().on_render(console)
        
        self.distance.render(console)
        
        self.cost_button.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
        
        elif self.confirm_button.cursor_overlap(event):
            warp_order = WarpOrder.from_heading(
                self.engine.player, self.heading_button.add_up(), self.distance.add_up()
            )
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)

        elif self.heading_button.cursor_overlap(event):
            self.selected_handeler = self.heading_button
            self.heading_button.is_active = True
            self.distance.is_active = False
        elif self.distance.cursor_overlap(event):
            self.selected_handeler = self.distance
            self.heading_button.is_active = False
            self.distance.is_active = True
        else:
            super().ev_mousebuttondown(event)
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            warp_order = WarpOrder.from_heading(
                self.engine.player, self.heading_button.add_up(), self.distance.add_up()
            )
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)

        else:
            self.selected_handeler.handle_key(event)
            
            if self.selected_handeler is self.distance:
                
                self.energy_cost = round(
                    self.distance.add_up() * 
                    self.engine.player.sys_warp_drive.affect_cost_multiplier * SECTOR_ENERGY_COST
                )
                
class WarpHandlerEasy(CoordBasedHandler):

    def __init__(self, engine: Engine) -> None:
        sector_coords = engine.game_data.player.sector_coords
        super().__init__(
            engine,
            max_x=CONFIG_OBJECT.sector_width,
            max_y=CONFIG_OBJECT.sector_height,
            starting_x=sector_coords.x,
            starting_y=sector_coords.y
        )
        
        self.energy_cost = round(
            self.engine.player.sector_coords.distance(x=self.x_button.add_up(),y=self.y_button.add_up()) * 
            self.engine.player.sys_warp_drive.affect_cost_multiplier * SECTOR_ENERGY_COST
        )
        
        self.cost_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            width=10,
            height=3,
            title="Energy Cost:",
            text=f"{self.energy_cost}",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input warp coordants"
            )
        
        super().on_render(console)
        
        self.cost_button.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)

        if self.x_button.cursor_overlap(event):
            self.selected_handeler = self.x_button
            self.x_button.is_active = True
            self.y_button.is_active = False
        elif self.y_button.cursor_overlap(event):
            self.selected_handeler = self.y_button
            self.x_button.is_active = False
            self.y_button.is_active = True
        elif self.confirm_button.cursor_overlap(event):
            
            warp_order = WarpOrder.from_coords(self.engine.player, self.x_button.add_up(), self.y_button.add_up())
            
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
        
        else:
            
            x, y = select_sector_space(event)

            if x is not False and y is not False:
                
                #print(f"{x} {y}")
                
                self.x_button.set_text(x)
                self.y_button.set_text(y)
                
                self.energy_cost = round(
                    self.engine.player.sector_coords.distance(x=self.x_button.add_up(),y=self.y_button.add_up()) * 
                    self.engine.player.sys_warp_drive.affect_cost_multiplier * SECTOR_ENERGY_COST
                )
                self.cost_button.text = f"{self.energy_cost}"
            else:
                super().ev_mousebuttondown(event)
                
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            
            return CommandEventHandler(self.engine)
        
        if event.sym in confirm:
            
            warp_order = WarpOrder.from_coords(self.engine.player, self.x_button.add_up(), self.y_button.add_up())
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
        else:
            self.selected_handeler.handle_key(event)
            
            self.energy_cost = round(
                
                self.engine.player.sector_coords.distance(x=self.x_button.add_up(),y=self.y_button.add_up()) * 
                self.engine.player.sys_warp_drive.affect_cost_multiplier * SECTOR_ENERGY_COST
            )
            
            self.cost_button.text = f"{self.energy_cost}"

class MoveHandler(HeadingBasedHandler):

    def __init__(self, engine: Engine) -> None:
        
        super().__init__(engine)
        
        self.distance_button = NumberHandeler(
            limit=3, max_value=CONFIG_OBJECT.max_move_distance, min_value=1,
            x=3+CONFIG_OBJECT.command_display_x,
            y=7+CONFIG_OBJECT.command_display_y,
            width=12,
            height=3,
            title="Distance:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT,
            initally_active=False
            )

        self.energy_cost = round(
            self.distance_button.add_up() * LOCAL_ENERGY_COST * self.engine.player.sys_impulse.affect_cost_multiplier)
        
        self.cost_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            width=10,
            height=3,
            title="Energy Cost:",
            text=f"{self.energy_cost}",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )

        self.selected_handeler = self.heading_button

    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input move heading and distance"
        )
        
        super().on_render(console)
        
        self.distance_button.render(console)
        
        self.cost_button.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.heading_button.cursor_overlap(event):
            
            self.selected_handeler = self.heading_button
            self.heading_button.is_active = True
            self.distance_button.is_active = False
            
        elif self.distance_button.cursor_overlap(event):
            
            self.selected_handeler = self.distance_button
            self.heading_button.is_active = False
            self.distance_button.is_active = True
            
        elif self.confirm_button.cursor_overlap(event):
            
            move_order = MoveOrder.from_heading(
                self.engine.player, self.heading_button.add_up(), self.distance_button.add_up(), self.energy_cost
            )
            warning = move_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return move_order
            try:
                self.engine.message_log.add_message(blocks_action[warning], colors.red)
            except KeyError:
                if not self.engine.crash_warning or self.warned_once:
                    return move_order
                self.engine.message_log.add_message(collision_warnings[warning], colors.orange)
                self.warned_once = True

        elif self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
        super().ev_mousebuttondown(event)


    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm and not self.heading_button.is_empty and not self.distance_button.is_empty:
            move_order = MoveOrder.from_heading(
                self.engine.player, self.heading_button.add_up(), self.distance_button.add_up(), self.energy_cost
            )
            warning = move_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return move_order

            try:
                self.engine.message_log.add_message(blocks_action[warning], colors.red)
            except KeyError:
                if not self.engine.crash_warning or self.warned_once:
                    return move_order
                self.engine.message_log.add_message(collision_warnings[warning], colors.orange)
                self.warned_once = True
        else:
            self.selected_handeler.handle_key(event)
            
            self.warned_once = False
            
            if self.selected_handeler is self.distance_button:
            
                self.energy_cost = round(
                    self.distance_button.add_up() * LOCAL_ENERGY_COST * 
                    self.engine.player.sys_impulse.affect_cost_multiplier
                )
                
                self.cost_button.text = f"{self.energy_cost}"
        
class MoveHandlerEasy(CoordBasedHandler):

    def __init__(self, engine: Engine) -> None:
        
        local_coords = engine.game_data.player.local_coords
        
        super().__init__(
            engine, 
            starting_x=local_coords.x, starting_y=local_coords.y,
            max_x=CONFIG_OBJECT.sector_width,
            max_y=CONFIG_OBJECT.sector_height
        )
        
        self.energy_cost = round(
            self.engine.player.local_coords.distance(x=self.x_button.add_up(), y=self.y_button.add_up()) * LOCAL_ENERGY_COST * 
            self.engine.player.sys_impulse.affect_cost_multiplier
        )
        
        self.cost_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            width=10,
            height=3,
            title="Energy Cost:",
            text=f"{self.energy_cost}",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.constants.RIGHT
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input move coordants"
        )
        
        super().on_render(console)
        
        self.cost_button.render(
            console,
            text=f"{self.energy_cost}"
        )
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
            
        elif self.confirm_button.cursor_overlap(event):
            warp_order = MoveOrder.from_coords(
                self.engine.player, self.x_button.add_up(), self.y_button.add_up(), self.energy_cost
            )
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                if not self.engine.crash_warning or self.warned_once:
                    return warp_order
                self.engine.message_log.add_message(collision_warnings[warning], fg=colors.orange)
                self.warned_once = True
        else:
            x,y = select_sub_sector_space(event)

            if x is not False and y is not False:
                
                self.x_button.set_text(x)
                self.y_button.set_text(y)
                self.warned_once = False
                self.energy_cost = round(
                    self.engine.player.local_coords.distance(x=self.x_button.add_up(), y=self.y_button.add_up()) * 
                    LOCAL_ENERGY_COST * self.engine.player.sys_impulse.affect_cost_multiplier
                )
            else:
                super().ev_mousebuttondown(event)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            
            warp_order = MoveOrder.from_coords(
                self.engine.player, self.x_button.add_up(), self.y_button.add_up(), self.energy_cost
            )
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                if self.warned_once:
                    return warp_order
                self.engine.message_log.add_message(collision_warnings[warning], fg=colors.orange)
                self.warned_once =True
        else:
            self.selected_handeler.handle_key(event)
            self.energy_cost = round(
                self.engine.player.local_coords.distance(
                    x=self.x_button.add_up(), y=self.y_button.add_up()) * LOCAL_ENERGY_COST
            )
            
            self.warned_once = False
            
class ShieldsHandler(MinMaxInitator):

    def __init__(self, engine: Engine) -> None:
        
        player = engine.player
        
        super().__init__(
            engine, 
            starting_value=player.shields,
            max_value=min(player.shields + player.energy, player.get_max_effective_shields)
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input energy to transfer to shields"
        )
        
        super().on_render(console)

        self.amount_button.render(console)
        
        self.max_button.render(console)
        self.min_button.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.max_button.cursor_overlap(event):
            
            self.amount_button.set_text(self.amount_button.max_value)
            
        elif self.min_button.cursor_overlap(event):
            
            self.amount_button.set_text(0)

        elif self.confirm_button.cursor_overlap(event):
            
            recharge_order = RechargeOrder(self.engine.player, self.amount_button.add_up())

            warning = recharge_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return recharge_order
            
            try:
                self.engine.message_log.add_message(blocks_action[warning], colors.red)
            except KeyError:
                
                self.engine.message_log.add_message(misc_warnings[warning], colors.orange)
            
        elif self.cancel_button.cursor_overlap(event):

            return CommandEventHandler(self.engine)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            recharge_order = RechargeOrder(self.engine.player, self.amount_button.add_up())

            warning = recharge_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return recharge_order
            
            try:
                self.engine.message_log.add_message(blocks_action[warning], colors.red)
            except KeyError:
                
                self.engine.message_log.add_message(misc_warnings[warning], colors.orange)
        else:
            self.amount_button.handle_key(event)

class BeamArrayHandler(MinMaxInitator):

    def __init__(self, engine: Engine) -> None:
        player = engine.player
        super().__init__(
            engine, 
            max_value=player.get_max_effective_beam_firepower,
            starting_value=0
        )
        
        self.auto_target_button = SimpleElement(
            x=4+12+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=14,
            height=3,
            text="Auto-Target",
            active_fg=colors.white,
            bg=colors.black
        )
        
        self.fire_all_button = BooleanBox(
            x=4+12+CONFIG_OBJECT.command_display_x,
            y=7+CONFIG_OBJECT.command_display_y,
            width=14,
            height=3,
            active_text="Multi-Target",
            inactive_text="One Target",
            initally_active=False,
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input energy to use:"
        )
        
        super().on_render(console)
        
        self.amount_button.render(console)
        
        self.min_button.render(console)
        
        self.max_button.render(console)
        
        self.auto_target_button.render(console)

        self.confirm_button.render(console)

        self.fire_all_button.render(console)

        self.cancel_button.render(console)

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.max_button.cursor_overlap(event):
            
            self.amount_button.set_text(self.amount_button.max_value)
            
        elif self.min_button.cursor_overlap(event):
            
            self.amount_button.set_text(0)
            
        if self.auto_target_button.cursor_overlap(event):
            
            sel = self.engine.game_data.selected_ship_planet_or_star
            
            local_ships = self.engine.game_data.ships_in_same_sub_sector_as_player
            
            if (not isinstance(sel, Starship) or not sel.ship_status.is_active) and local_ships:
                
                okay_ships = [s for s in local_ships if s.ship_status.is_active]
                
                try:
                    ship = choice(okay_ships)
                    
                    self.engine.game_data.selected_ship_planet_or_star = ship
                    
                    self.engine.game_data.ship_scan = ship.scan_this_ship(
                        self.engine.player.determin_precision, use_effective_values=False
                    )
                    
                    self.engine.game_data.selected_ship_planet_or_star = ship
                    
                except IndexError:
                    captain_rank_name = self.engine.player.ship_class.nation.captain_rank_name
                    
                    self.engine.message_log.add_message(
                        f"There are no hostile ships in the system, {captain_rank_name}."
                    )
        elif self.confirm_button.cursor_overlap(event):

            if self.fire_all_button.is_active:
                
                ships_in_same_sub_sector = self.engine.game_data.grab_ships_in_same_sub_sector(
                    self.engine.player,
                    accptable_ship_statuses={STATUS_ACTIVE}
                )
                fire_order = EnergyWeaponOrder.multiple_targets(
                    self.engine.player,
                    self.amount_button.add_up(),
                    ships_in_same_sub_sector
                )
            else:
                fire_order = EnergyWeaponOrder.single_target_beam(
                    self.engine.player,
                    self.amount_button.add_up(),
                    self.engine.game_data.selected_ship_planet_or_star
                )
            warning = fire_order.raise_warning()

            if warning == OrderWarning.SAFE:
                self.amount_button.max_value = min(
                    self.engine.player.get_max_effective_beam_firepower, self.engine.player.energy
                )
                if self.amount_button.add_up() > self.amount_button.max_value:
                    self.amount_button.set_text(self.amount_button.max_value)
                return fire_order
            
            self.engine.message_log.add_message(
                blocks_action[warning], colors.red
            )
        elif self.fire_all_button.cursor_overlap(event):
            
            self.fire_all_button.is_active = not self.fire_all_button.is_active
            
        elif self.cancel_button.cursor_overlap(event):

            return CommandEventHandler(self.engine)
        
        ship_planet_or_star = select_ship_planet_star(self.engine.game_data, event)
        
        if (isinstance(
            
            ship_planet_or_star, Starship
            
        ) and ship_planet_or_star is not self.engine.player and 
            
            ship_planet_or_star is not self.engine.game_data.selected_ship_planet_or_star
        ):

            self.engine.game_data.ship_scan = ship_planet_or_star.scan_this_ship(self.engine.player.determin_precision)
            
            self.engine.game_data.selected_ship_planet_or_star = ship_planet_or_star
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym == tcod.event.K_a:
        
            sel = self.engine.game_data.selected_ship_planet_or_star
            
            local_ships = self.engine.game_data.ships_in_same_sub_sector_as_player
            
            if (not isinstance(sel, Starship) or sel.ship_status.is_active) and local_ships:
                
                okay_ships = [s for s in local_ships if s.ship_status.is_active]
                
                self.engine.game_data.selected_ship_planet_or_star = choice(okay_ships)
        
        if event.sym in confirm:
            if self.fire_all_button.is_active:
                
                ships_in_same_sub_sector = self.engine.game_data.grab_ships_in_same_sub_sector(
                    self.engine.player,
                    accptable_ship_statuses={STATUS_ACTIVE}
                )
                fire_order = EnergyWeaponOrder.multiple_targets(
                    self.engine.player,
                    self.amount_button.add_up(),
                    ships_in_same_sub_sector
                )
            else:
                fire_order = EnergyWeaponOrder.single_target_beam(
                    self.engine.player,
                    self.amount_button.add_up(),
                    self.engine.game_data.selected_ship_planet_or_star
                )
            warning = fire_order.raise_warning()

            if warning == OrderWarning.SAFE:
                self.amount_button.max_value = min(
                    self.engine.player.get_max_effective_beam_firepower, self.engine.player.energy
                )
                if self.amount_button.add_up() > self.amount_button.max_value:
                    self.amount_button.set_text(self.amount_button.max_value)
                return fire_order
            
            self.engine.message_log.add_message(
                blocks_action[warning], colors.red
            )
        else:
            self.amount_button.handle_key(event)

class CannonHandler(MinMaxInitator):

    def __init__(self, engine: Engine) -> None:
        
        player = engine.player
        
        super().__init__(
            engine, 
            max_value=min(player.get_max_effective_cannon_firepower, player.energy),
            starting_value=0
        )
        self.auto_target_button = SimpleElement(
            x=4+12+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=14,
            height=3,
            text="Auto-Target",
            active_fg=colors.white,
            bg=colors.black
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input energy to use:"
        )
        super().on_render(console)
        
        self.amount_button.render(console)
        
        self.min_button.render(console)
        
        self.max_button.render(console)
        
        self.auto_target_button.render(console)

        self.confirm_button.render(console)

        self.cancel_button.render(console)

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.max_button.cursor_overlap(event):
            
            self.amount_button.set_text(self.amount_button.max_value)
            
        elif self.min_button.cursor_overlap(event):
            
            self.amount_button.set_text(0)
            
        if self.auto_target_button.cursor_overlap(event):
            
            sel = self.engine.game_data.selected_ship_planet_or_star
            
            local_ships = self.engine.game_data.ships_in_same_sub_sector_as_player
            
            if (not isinstance(sel, Starship) or not sel.ship_status.is_active) and local_ships:
                
                okay_ships = [s for s in local_ships if s.ship_status.is_active]
                
                try:
                    ship = choice(okay_ships)
                    
                    self.engine.game_data.selected_ship_planet_or_star = ship
                    
                    self.engine.game_data.ship_scan = ship.scan_this_ship(self.engine.player.determin_precision)
                    
                except IndexError:
                    captain_rank_name = self.engine.player.ship_class.nation.captain_rank_name
                    
                    self.engine.message_log.add_message(
                        f"There are no hostile ships in the system, {captain_rank_name}."
                    )
        elif self.confirm_button.cursor_overlap(event):

            fire_order = EnergyWeaponOrder.cannon(
                self.engine.player,
                self.amount_button.add_up(),
                self.engine.game_data.selected_ship_planet_or_star
            )
            warning = fire_order.raise_warning()

            if warning == OrderWarning.SAFE:
                self.amount_button.max_value = min(
                    self.engine.player.get_max_effective_cannon_firepower, self.engine.player.energy
                )
                if self.amount_button.add_up() > self.amount_button.max_value:
                    self.amount_button.set_text(self.amount_button.max_value)
                return fire_order
            
            self.engine.message_log.add_message(
                blocks_action[warning], colors.red
            )
        elif self.cancel_button.cursor_overlap(event):

            return CommandEventHandler(self.engine)
        
        ship_planet_or_star = select_ship_planet_star(self.engine.game_data, event)
        
        if (isinstance(
            
            ship_planet_or_star, Starship
            
        ) and ship_planet_or_star is not self.engine.player and 
            
            ship_planet_or_star is not self.engine.game_data.selected_ship_planet_or_star
        ):
            self.engine.game_data.ship_scan = ship_planet_or_star.scan_this_ship(self.engine.player.determin_precision)
            
            self.engine.game_data.selected_ship_planet_or_star = ship_planet_or_star
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym == tcod.event.K_a:
        
            sel = self.engine.game_data.selected_ship_planet_or_star
            
            local_ships = self.engine.game_data.ships_in_same_sub_sector_as_player
            
            if (not isinstance(sel, Starship) or sel.ship_status.is_active) and local_ships:
                
                okay_ships = [s for s in local_ships if s.ship_status.is_active]
                
                self.engine.game_data.selected_ship_planet_or_star = choice(okay_ships)
        
        if event.sym in confirm:
            
            fire_order = EnergyWeaponOrder.cannon(
                self.engine.player,
                self.amount_button.add_up(),
                target=self.engine.game_data.selected_ship_planet_or_star
            )
            warning = fire_order.raise_warning()

            if warning == OrderWarning.SAFE:
                self.amount_button.max_value = min(
                    self.engine.player.get_max_effective_cannon_firepower, self.engine.player.energy
                )
                if self.amount_button.add_up() > self.amount_button.max_value:
                    self.amount_button.set_text(self.amount_button.max_value)
                return fire_order
            
            self.engine.message_log.add_message(
                blocks_action[warning], colors.red
            )
        else:
            self.amount_button.handle_key(event)

class TorpedoHandler(HeadingBasedHandler):

    def __init__(self, engine: Engine) -> None:
        
        super().__init__(engine)
        
        self.number_button = NumberHandeler(
            limit=1, max_value=self.engine.player.ship_class.torp_tubes, min_value=1,
            x=3+CONFIG_OBJECT.command_display_x,
            y=6+CONFIG_OBJECT.command_display_y,
            width=12,
            height=3,
            title="Number:",
            alignment=tcod.constants.RIGHT,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=False
        )
        torpedos = self.engine.player.ship_class.torp_types
        
        self.torpedo_select = Selector(
            x=15+CONFIG_OBJECT.command_display_x,
            y=16+CONFIG_OBJECT.command_display_y,
            width=10,
            height=6,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            index_items=[
                ALL_TORPEDO_TYPES[name].cap_name for name in torpedos
            ],
            keys=torpedos
        )

    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input torpedo heading"
        )
        super().on_render(console)
        
        self.number_button.render(console)
        
        self.torpedo_select.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
        if self.torpedo_select.cursor_overlap(event):
            if self.torpedo_select.handle_click(event):
                key:str = self.torpedo_select.index_key
                
                self.engine.player.torpedo_loaded = key
                
                cap_name = ALL_TORPEDO_TYPES[key].cap_name
                
                captain_name = self.engine.player.ship_class.nation.captain_rank_name
                
                self.engine.message_log.add_message(
                    f"{cap_name} torpedos loaded, {captain_name}."
                )
        
        elif self.heading_button.cursor_overlap(event):
            
            self.selected_handeler = self.heading_button
            self.heading_button.is_active = True
            self.number_button.is_active = False
            
        elif self.number_button.cursor_overlap(event):
            
            self.selected_handeler = self.number_button
            self.heading_button.is_active = False
            self.number_button.is_active = True
            
        elif self.confirm_button.cursor_overlap(event):
            torpedo_order = TorpedoOrder.from_heading(self.engine.player, self.heading_button.add_up(), self.number_button.add_up())
            warning = torpedo_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return torpedo_order
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                if self.engine.torpedo_warning or self.warned_once:
                    return torpedo_order
                
                self.engine.message_log.add_message(torpedo_warnings[warning], fg=colors.orange)
                self.warned_once = True
        else:
            game_data = self.engine.game_data
            ship_planet_or_star = select_ship_planet_star(game_data, event)
            
            if ship_planet_or_star:
                if isinstance(ship_planet_or_star, (Planet, Star)):
                    game_data.selected_ship_planet_or_star = ship_planet_or_star
                elif isinstance(ship_planet_or_star, Starship):
                    
                    if (
                        ship_planet_or_star is not self.engine.player and 
                        ship_planet_or_star is not game_data.selected_ship_planet_or_star
                    ):
                        game_data.ship_scan = ship_planet_or_star.scan_this_ship(game_data.player.determin_precision)
                        game_data.selected_ship_planet_or_star = ship_planet_or_star
                else:
                    game_data.selected_ship_planet_or_star = None
            else:
                super().ev_mousebuttondown(event)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            torpedo_order = TorpedoOrder.from_heading(
                self.engine.player, self.heading_button.add_up(), self.number_button.add_up()
            )
            warning = torpedo_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return torpedo_order
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                if not self.engine.torpedo_warning or self.warned_once:
                    return torpedo_order
                
                self.engine.message_log.add_message(torpedo_warnings[warning], fg=colors.orange)
                self.warned_once = True
        else:
            self.selected_handeler.handle_key(event)
            
class TorpedoHandlerEasy(CoordBasedHandler):

    def __init__(self, engine: Engine) -> None:
        
        local_coords = engine.game_data.player.local_coords

        super().__init__(
            engine,
            max_x=CONFIG_OBJECT.subsector_width,
            max_y=CONFIG_OBJECT.subsector_height,
            starting_x=local_coords.x,
            starting_y=local_coords.y
        )
        self.number_button = NumberHandeler(
            limit=1, max_value=self.engine.player.ship_class.torp_tubes, min_value=1,
            x=3+CONFIG_OBJECT.command_display_x,
            y=7+CONFIG_OBJECT.command_display_y,
            width=12,
            height=3,
            title="Number:",
            alignment=tcod.constants.RIGHT,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black
        )
        torpedos = self.engine.player.ship_class.torp_types
        
        self.torpedo_select = Selector(
            x=15+CONFIG_OBJECT.command_display_x,
            y=16+CONFIG_OBJECT.command_display_y,
            width=10,
            height=6,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            index_items=[
                ALL_TORPEDO_TYPES[name].cap_name for name in torpedos
            ],
            keys=torpedos
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input torpedo coordants"
        )
        super().on_render(console)
        
        self.number_button.render(console)
        
        self.torpedo_select.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)

        if self.torpedo_select.cursor_overlap(event):
            
            self.torpedo_select.handle_click(event)

        if self.x_button.cursor_overlap(event):
            
            self.selected_handeler = self.x_button
            self.x_button.is_active = True
            self.y_button.is_active = False
            self.number_button.is_active = False
            
        elif self.y_button.cursor_overlap(event):
            
            self.selected_handeler = self.y_button
            self.x_button.is_active = False
            self.y_button.is_active = True
            self.number_button.is_active = False
            
        elif self.number_button.cursor_overlap(event):
            
            self.selected_handeler = self.number_button
            self.x_button.is_active = False
            self.y_button.is_active = False
            self.number_button.is_active = True
            
        elif self.confirm_button.cursor_overlap(event):
            
            torpedo_order = TorpedoOrder.from_coords(
                self.engine.player, self.number_button.add_up(), self.x_button.add_up(), self.y_button.add_up()
            )
            warning = torpedo_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return torpedo_order
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                if not self.engine.torpedo_warning or self.warned_once:
                    return torpedo_order
                
                self.engine.message_log.add_message(torpedo_warnings[warning], fg=colors.orange)
                self.warned_once = True
        else:
            game_data = self.engine.game_data
            ship_planet_or_star = select_ship_planet_star(game_data, event)
            
            if ship_planet_or_star:
                if isinstance(ship_planet_or_star, (Planet, Star)):
                    game_data.selected_ship_planet_or_star = ship_planet_or_star
                elif isinstance(ship_planet_or_star, Starship):
                    
                    if (
                        ship_planet_or_star is not self.engine.player and 
                        ship_planet_or_star is not game_data.selected_ship_planet_or_star
                    ):
                        game_data.ship_scan = ship_planet_or_star.scan_this_ship(game_data.player.determin_precision)
                        game_data.selected_ship_planet_or_star = ship_planet_or_star
                else:
                    game_data.selected_ship_planet_or_star = None
                    
                x,y = select_sub_sector_space(event)

                if x is not False and y is not False:
                    self.x_button.set_text(x)
                    self.y_button.set_text(y)
                    self.warned_once == False
                else:
                    super().ev_mousebuttondown(event)
                    
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            torpedo_order = TorpedoOrder(self, self.heading.add_up(), self.number.add_up())
            warning = torpedo_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return torpedo_order
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                if not self.engine.torpedo_warning or self.warned_once:
                    return torpedo_order
                
                self.engine.message_log.add_message(torpedo_warnings[warning], fg=colors.orange)
                self.warned_once = True
        else:
            self.selected_handeler.handle_key(event)
                
class SelfDestructHandler(CancelConfirmHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        player = engine.player
        
        self.code = self.engine.game_data.auto_destruct_code
        
        nearbye_ships = [
            ship for ship in engine.game_data.grab_ships_in_same_sub_sector(
                player, accptable_ship_statuses={STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK}
                ) if player.local_coords.distance(coords=ship.local_coords) <= player.ship_class.warp_breach_damage
        ]
        
        nearbye_ships.sort(key=lambda ship: ship.local_coords.distance(coords=player.local_coords), reverse=True)
        
        self.all_nearbye_ships = tuple(nearbye_ships)
        
        nearbye_active_foes = [ship for ship in nearbye_ships if ship.ship_status.is_active]
        
        def scan_ship(ships:Iterable[Starship]):
            
            for ship in ships:
                
                scan = ship.scan_this_ship(player.determin_precision, use_effective_values=True)
                
                averaged_shield , averaged_hull, averaged_shield_damage, averaged_hull_damage, kill = player.calc_self_destruct_damage(
                    ship, scan=scan, number_of_simulations=10
                )
                #scan["shields"], scan["hull"], 
                yield ship.name, averaged_shield_damage, averaged_hull_damage, kill
        
        self.nearbye_active_foes = tuple(
            scan_ship(nearbye_active_foes)
        )
        
        nearbye_derlicts = [ship for ship in nearbye_ships if ship.ship_status.is_recrewable]
        
        self.nearbye_derlicts = tuple(
            scan_ship(nearbye_derlicts)
        )
        
        self.any_foes_nearby = len(self.nearbye_active_foes) > 0

        self.any_derlicts_nearbye = len(self.nearbye_derlicts) > 0

        self.code_handler = TextHandeler(
            limit=12,
            x=4+CONFIG_OBJECT.command_display_x,
            y=3+CONFIG_OBJECT.command_display_y,
            width=18,
            height=3,
            title="Input code:",
            active_fg=colors.white,
            inactive_fg=colors.white,
            bg=colors.black
        )

        self.code_status = 0
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input self destruct code"
            )
        
        super().on_render(console)
        
        self.code_handler.render(console)
        
        console.print(
            x=4+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            string=f"Code: {self.code}"
        )
        
        if self.any_foes_nearby:
            console.print(
                x=2+CONFIG_OBJECT.command_display_x,
                y=7+CONFIG_OBJECT.command_display_y,
                string="Ships in radius of a-destruct:"
            )
            
            console.print(
                x=2+CONFIG_OBJECT.command_display_x,
                y=8+CONFIG_OBJECT.command_display_y,
                string="Name    S. Dam.  H. Dam.  Kill"
            )
            for i, ship_info in enumerate(self.nearbye_active_foes):
                ship, shield_dam, hull_dam, kill = ship_info
                console.print(
                    x=2+CONFIG_OBJECT.command_display_x,
                    y=i+9+CONFIG_OBJECT.command_display_y,
                    string=f"{ship: <8}  {shield_dam: <7}  {hull_dam: <7} {'Yes' if kill else 'No'}"
                )
        else:
            console.print_box(
                x=2+CONFIG_OBJECT.command_display_x,
                y=7+CONFIG_OBJECT.command_display_y,
                width=(CONFIG_OBJECT.command_display_end_x - 2) - (2 + CONFIG_OBJECT.command_display_x),
                height=5,
                string="No ships in radius of auto destruct"
            )
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_CANCEL:
            return CommandEventHandler(self.engine)

        if event.sym in confirm:

            if self.code_handler.text_to_print == self.code:

                return SelfDestructOrder(self.engine.player)
            else:
                self.engine.message_log.add_message(
                    f"Error: The code for the self destruct is not correct.", colors.red
                )
        else:
        
            self.code_handler.handle_key(event)
            #self.code_handler.text = self.code_handler.text_to_print

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            
            return CommandEventHandler(self.engine)
        if self.confirm_button.cursor_overlap(event):
            if self.code_handler.text_to_print == self.code:

                return SelfDestructOrder(self.engine.player)
            else:
                self.engine.message_log.add_message(
                    f"Error: The code for the self destruct is not correct.", colors.red
                )
                
class GameOverEventHandler(EventHandler):

    def __init__(self, engine: Engine):
        super().__init__(engine)
        if engine.player.ship_status.is_active:
            engine.message_log.add_message(
                f"Incomming message from {engine.player.ship_class.nation.command_name}...", fg=colors.orange
            )
        self.message = "Incomming message"
        
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        return EvaluationHandler(self.engine)
        
    def on_render(self, console: tcod.Console) -> None:
        print_system(console, self.engine.game_data)
        print_mega_sector(console, self.engine.game_data)
        render_own_ship_info(console, self.engine.game_data)

        render_other_ship_info(console, self.engine.game_data, self.engine.game_data.selected_ship_planet_or_star)

        print_message_log(console, self.engine.game_data)
        render_position(console, self.engine.game_data)
        
        render_command_box(console, self.engine.game_data, self.message)
        
class EvaluationHandler(EventHandler):
    
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        text, self.evaluation, self.score = self.engine.game_data.scenerio.scenario_type.generate_evaluation(
            self.engine.game_data
        )
        
        width=CONFIG_OBJECT.screen_width - 4
        
        self.text_box = ScrollingTextBox(
            x=2, y=2,
            width=width,
            height=CONFIG_OBJECT.screen_height - 8,
            title="Evaluation:", total_text=wrap(text, width=width, replace_whitespace=False),
            lines_to_scroll=10
        )
        
        self.score_button = SimpleElement(
            x=2, y=self.text_box.height + self.text_box.y,
            width=15, height=3,
            text="See (S)core"
        )
        
    def on_render(self, console: tcod.Console) -> None:
        self.text_box.render(console)
        self.score_button.render(console)
    
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[BaseEventHandler]:
        if self.score_button.cursor_overlap(event):
            return ScoreHandler(self.engine, self.evaluation, self.score)
    
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[BaseEventHandler]:

        if event.sym in confirm or event.sym == tcod.event.K_s:
            return ScoreHandler(self.engine, self.evaluation, self.score)
        self.text_box.handle_key(event)

class ScoreHandler(EventHandler):
    
    def replace(self, s:str):
        
        if "_" in s:
            
            s_list = s.split("_")
            
            s_list2 = [s2.capitalize() for s2 in s_list]
            
            return " ".join(s_list2)
        else:
            return s.capitalize()
            
    def __init__(self, engine: Engine, evaluation: OrderedDict[str,Tuple[int,int]], score:Decimal) -> None:
        super().__init__(engine)
        
        max_evaluation_key_len = max(
            len(k) for k in evaluation.keys()
        )
        
        lines = [f"{self.replace(k):>{max_evaluation_key_len}}:{v[0]}/{v[1]}" for k,v in evaluation.items()]
        
        max_len = max(len(l) for l in lines)
        
        #self.info = self.engine.game_data.player_record
        
        self.evalu = SimpleElement(
            x=5, y=5,
            height=len(evaluation), width=max_len,
            title="Score Info:",
            text="\n".join(lines), alignment=tcod.LEFT
        )
        
        reccord = self.engine.game_data.player_record
        
        max_reccord_key_len = max(
            len(k) for k in reccord.keys()
        )
        
        reccord_lines = [f"{self.replace(k):>{max_reccord_key_len}}:{v}" for k,v in reccord.items()]
        
        max_reccord_len = max(len(l) for l in reccord_lines)
        
        self.player_record = SimpleElement(
            x=5, y=5 + self.evalu.y + self.evalu.height,
            height=len(reccord_lines), width=max_reccord_len+4,
            title="Player Record:", 
            text="\n".join(reccord_lines), alignment=tcod.LEFT
        )
        
        self.score_record = SimpleElement(
            x=5, y=5+self.player_record.y+self.player_record.height,
            height=3,
            width=40,
            title="Score:",
            text=f"{score:.6}"
        )
        
    def on_render(self, console: tcod.Console) -> None:
        self.evalu.render(console)
        self.player_record.render(console)
        self.score_record.render(console)
    
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[BaseEventHandler]:
        self.on_quit()
    
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[BaseEventHandler]:
        self.on_quit()
    
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        raise exceptions.QuitWithoutSaving()
        '''
        if os.path.exists("saves/" + self.engine.filename + ".sav"):
            self.engine.save_as("")
            #os.remove("savegame.sav")  # Deletes the active save file.
        else:
            print(self.engine.filename)
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.
        '''

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()