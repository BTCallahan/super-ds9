from __future__ import annotations
import os
from coords import Coords
from data_globals import LOCAL_ENERGY_COST, SECTOR_ENERGY_COST
from engine import config_object
from typing import TYPE_CHECKING, List, Optional, Union
from global_functions import headingToCoords
from order import SelfDestructOrder, blocks_action, torpedo_warnings, collision_warnings, \
    Order, DockOrder, OrderWarning, PhaserOrder, RepairOrder, TorpedoOrder, WarpOrder, MoveOrder, RechargeOrder
from space_objects import Planet
from ui_related import ButtonBox, NumberHandeler, TextHandeler, confirm
import tcod
import tcod.event
import tcod.constants
import colors, exceptions
from render_functions import print_mega_sector, print_message_log, print_subsector, render_other_ship_info, render_own_ship_info, render_command_box, render_position, select_ship_planet_star, select_sub_sector_space, is_click_within_bounds, select_sector_space

ActionOrHandler = Union["Order", "BaseEventHandler"]

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

class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
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

    def ev_quit(self, event: tcod.event.Quit) -> Optional[ActionOrHandler]:
        raise SystemExit()

class EventHandler(BaseEventHandler):

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def handle_action(self, action: Optional[ActionOrHandler]) -> bool:
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

        self.engine.handle_enemy_turns()
        game_data = self.engine.game_data
        game_data.ships_in_same_sub_sector_as_player = game_data.grapShipsInSameSubSector(game_data.player)
        return True

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:

        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            if not self.engine.player.isAlive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
        if not self.engine.player.isAlive:
            pass
        return self

class MainGameEventHandler(EventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.warned_once = False
    
    def on_render(self, console: tcod.Console) -> None:
        
        print_subsector(console, self.engine.game_data)
        print_mega_sector(console, self.engine.game_data)
        render_own_ship_info(console, self.engine.game_data)

        render_other_ship_info(console, self.engine.game_data, self.engine.game_data.selected_ship_or_planet)

        print_message_log(console, self.engine.game_data)
        render_position(console, self.engine.game_data)

class CommandEventHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        print("CommandEventHandler")
        super().__init__(engine)
        self.warp_button = ButtonBox(
            x=2+config_object.command_display_x, 
            y=2+config_object.command_display_y,
            width=10,
            height=3,
            text="(W)arp",
        )

        self.move_button = ButtonBox(
            x=2+13+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=10,
            height=3,
            text="(M)ove",
        )

        self.shields_button = ButtonBox(
            x=2+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=10,
            height=3,
            text="(S)hields",
        )

        self.repair_button = ButtonBox(
            x=2+13+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=10,
            height=3,
            text="(R)epair",
        )

        self.phasers_button = ButtonBox(
            x=2+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=10,
            height=3,
            text="(P)hasers",
        )

        self.dock_button = ButtonBox(
            x=2+13+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=10,
            height=3,
            text="(D)ock",
        )

        self.torpedos_button = ButtonBox(
            x=2+config_object.command_display_x,
            y=14+config_object.command_display_y,
            width=10,
            height=3,
            text="(T)orpedos",
        )
        
        self.auto_destruct_button = ButtonBox(
            x=2+13+config_object.command_display_x,
            y=14+config_object.command_display_y,
            width=10,
            height=4,
            text="(A)uto-Destruct"
        )

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:
        
        if not select_ship_planet_star(self.engine.game_data, event):
            if self.warp_button.cursor_overlap(event):
                
                if not self.engine.player.sysWarp.isOpperational:
                    self.engine.message_log.add_message("Error: Warp engines are inoperative, Captain", fg=colors.red)

                elif self.engine.player.energy <= 0:
                    self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
                elif self.engine.player.docked:
                    self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
                else:
                    return WarpHandlerEasy(self.engine) if self.engine.easy_warp else WarpHandler(self.engine)
            
            elif self.move_button.cursor_overlap(event):
                if not self.engine.player.sysImpulse.isOpperational:
                    self.engine.message_log.add_message("Error: Impulse systems are inoperative, Captain", fg=colors.red)

                elif self.engine.player.energy <= 0:
                    self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
                elif self.engine.player.docked:
                    self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
                else:
                    return MoveHandlerEasy(self.engine) if self.engine.easy_navigation else MoveHandler(self.engine)
            
            elif self.shields_button.cursor_overlap(event):
                if not self.engine.player.sysShield.isOpperational:
                    self.engine.message_log.add_message("Error: Shield systems are inoperative, Captain", fg=colors.red)

                elif self.engine.player.energy <= 0:
                    self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
                elif self.engine.player.docked:
                    self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
                else:
                    return ShieldsHandler(self.engine)
                
            elif self.phasers_button.cursor_overlap(event):
                if not self.engine.player.sysEnergyWep.isOpperational:
                    self.engine.message_log.add_message("Error: Phaser systems are inoperative, Captain", fg=colors.red)

                elif self.engine.player.energy <= 0:
                    self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
                elif self.engine.player.docked:
                    self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
                else:
                    return EnergyWeaponHandler(self.engine)

            elif self.dock_button.cursor_overlap(event):
                planet = self.engine.game_data.selected_ship_or_planet

                if not planet and not isinstance(planet, Planet):
                    self.engine.message_log.add_message("Error: No planet selected, Captain", fg=colors.red)
                elif self.engine.player.docked:
                    self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)

                else:

                    dock_order = DockOrder(self.engine.player, planet)

                    warning = dock_order.raise_warning()

                    if warning == OrderWarning.SAFE:
                        return dock_order
                    if warning == OrderWarning.ENEMY_SHIPS_NEARBY:
                        #if self.warned_once:
                        #return dock_order
                        self.engine.message_log.add_message("Warning: There are hostile ships nearby", fg=colors.orange)
                        self.warned_once = True
                    else:
                        self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)

            elif self.repair_button.cursor_overlap(event):
                return RepairOrder(self.engine.player, 1)

            elif self.torpedos_button.cursor_overlap(event) and self.engine.player.shipTypeCanFireTorps:

                if not self.engine.player.ship_can_fire_torps:
                    self.engine.message_log.add_message(
                        text="Error: Torpedo systems are inoperative, Captain" if not self.engine.player.sysTorp.isOpperational else "Error: This ship has no remaining torpedos, Captain", fg=colors.red
                    )
                elif self.engine.player.docked:
                    self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
                else:
                    return TorpedoHandlerEasy(self.engine) if self.engine.easy_aim else TorpedoHandler(self.engine)
            elif self.auto_destruct_button.cursor_overlap(event):
                return SelfDestructHandler(self.engine)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_w:
            if not self.engine.player.sysWarp.isOpperational:
                self.engine.message_log.add_message("Error: Warp engines are inoperative, Captain", fg=colors.red)

            elif self.engine.player.energy <= 0:
                self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
            elif self.engine.player.docked:
                self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
            else:
                return WarpHandlerEasy(self.engine) if self.engine.easy_warp else WarpHandler(self.engine)
        elif event.sym == tcod.event.K_m:
            if not self.engine.player.sysImpulse.isOpperational:
                self.engine.message_log.add_message("Error: Impulse systems are inoperative, Captain", fg=colors.red)

            elif self.engine.player.energy <= 0:
                self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
            elif self.engine.player.docked:
                self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
            else:
                return MoveHandlerEasy(self.engine) if self.engine.easy_navigation else MoveHandler(self.engine)
        elif event.sym == tcod.event.K_s:
            if not self.engine.player.sysShield.isOpperational:
                self.engine.message_log.add_message("Error: Shield systems are inoperative, Captain", fg=colors.red)

            elif self.engine.player.energy <= 0:
                self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
            elif self.engine.player.docked:
                self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
            else:
                return ShieldsHandler(self.engine)
            
        elif event.sym == tcod.event.K_r:
            pass
        elif event.sym == tcod.event.K_p:
            if not self.engine.player.sysEnergyWep.isOpperational:
                self.engine.message_log.add_message("Error: Phaser systems are inoperative, Captain", fg=colors.red)

            elif self.engine.player.energy <= 0:
                self.engine.message_log.add_message("Error: Insufficent energy reserves, Captain", fg=colors.red)
            elif self.engine.player.docked:
                self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
            else:
                return EnergyWeaponHandler(self.engine)
        if event.sym == tcod.event.K_d:

            planet = self.engine.game_data.selected_ship_or_planet

            if not planet and not isinstance(planet, Planet):
                self.engine.message_log.add_message("Error: No planet selected, Captain.", fg=colors.red)
            else:
                dock_order = DockOrder(self.engine.player, planet)

                warning = dock_order.raise_warning()

                if warning == OrderWarning.SAFE:
                    return dock_order
                if warning == OrderWarning.ENEMY_SHIPS_NEARBY:
                    if self.warned_once:
                        return dock_order
                    self.engine.message_log.add_message("Warning: There are hostile ships nearby", fg=colors.orange)
                    self.warned_once = True
                else:
                    self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            
        if event.sym == tcod.event.K_t and self.engine.player.shipTypeCanFireTorps:
            if not self.engine.player.ship_can_fire_torps:
                self.engine.message_log.add_message(
                    text="Error: Torpedo systems are inoperative, Captain" if not self.engine.player.sysTorp.isOpperational else "Error: This ship has not remaining torpedos, Captain", fg=colors.red
                )
            elif self.engine.player.docked:
                self.engine.message_log.add_message("Error: We undock first, Captain", fg=colors.red)
            else:
                return TorpedoHandlerEasy(self.engine) if self.engine.easy_aim else TorpedoHandler(self.engine)
        elif event.sym == tcod.event.K_a:
            return SelfDestructHandler(self.engine)

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Your orders, captain?"
            )
        
        self.warp_button.render(console)
        self.move_button.render(console)
        self.dock_button.render(console)
        self.shields_button.render(console)
        self.phasers_button.render(console)
        self.repair_button.render(console)
        if self.engine.player.shipTypeCanFireTorps:
            self.torpedos_button.render(console)
        self.auto_destruct_button.render(console)
        
class WarpHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        self.heading = NumberHandeler(limit=3, max_value=360, min_value=0, wrap_around=True, starting_value=0)
        self.distance = NumberHandeler(limit=3, max_value=config_object.max_warp_distance, min_value=1)

        self.selected_handeler = self.heading

        self.heading_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=12,
            height=3,
            title="Heading:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.distance_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=7+config_object.command_display_y,
            width=12,
            height=3,
            title="Distance:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.three_fifteen_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="315",
            alignment=tcod.constants.RIGHT
        )

        self.two_seventy_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=5,
            height=3,
            text="270",
            alignment=tcod.constants.RIGHT
        )

        self.zero_button = ButtonBox(
            x=22+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="0",
            alignment=tcod.constants.RIGHT
        )

        self.fourty_five_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="45",
            alignment=tcod.constants.RIGHT
        )

        self.two_twenty_five_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="225",
            alignment=tcod.constants.RIGHT
        )

        self.ninty_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=5,
            height=3,
            text="90",
            alignment=tcod.constants.RIGHT
        )
        
        self.one_thirty_five_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="135",
            alignment=tcod.constants.RIGHT
        )

        self.one_eighty_button = ButtonBox(
            x=22+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="180",
            alignment=tcod.constants.RIGHT
        )
        
        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Confirm"
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input heading and distance"
            )

        self.heading_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.heading else colors.grey,
            bg=colors.black,
            text=self.heading.text_to_print,
            cursor_position=self.heading.cursor
        )

        self.distance_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.distance else colors.grey,
            bg=colors.black,
            text=self.distance.text_to_print,
            cursor_position=self.distance.cursor
        )

        self.confirm_button.render(console)

        self.cancel_button.render(console)

        self.zero_button.render(console)

        self.fourty_five_button.render(console)

        self.ninty_button.render(console)

        self.one_thirty_five_button.render(console)

        self.one_eighty_button.render(console)

        self.two_twenty_five_button.render(console)

        self.two_seventy_button.render(console)
        
        self.three_fifteen_button.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)

        if self.zero_button.cursor_overlap(event):
            self.heading.set_text(0)
        elif self.fourty_five_button.cursor_overlap(event):
            self.heading.set_text(45)
        elif self.ninty_button.cursor_overlap(event):
            self.heading.set_text(90)
        elif self.one_thirty_five_button.cursor_overlap(event):
            self.heading.set_text(135)
        elif self.one_eighty_button.cursor_overlap(event):
            self.heading.set_text(180)
        elif self.two_twenty_five_button.cursor_overlap(event):
            self.heading.set_text(235)
        elif self.two_seventy_button.cursor_overlap(event):
            self.heading.set_text(270)
        elif self.three_fifteen_button.cursor_overlap(event):
            self.heading.set_text(315)

        elif self.heading_button.cursor_overlap(event):
            self.selected_handeler = self.heading
        elif self.distance_button.cursor_overlap(event):
            self.selected_handeler = self.distance
        elif self.confirm_button.cursor_overlap(event):
            warp_order = WarpOrder.from_heading(self.engine.player, self.heading.add_up(), self.distance.add_up())
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning])
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            warp_order = WarpOrder.from_heading(self.engine.player, self.heading.add_up(), self.distance.add_up())
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning])

        else:
            self.selected_handeler.handle_key(event)
        """
        elif event.sym == tcod.event.K_BACKSPACE:
            self.selected_handeler.delete()
        elif event.sym == tcod.event.K_DELETE:
            self.selected_handeler.delete(True)
        else:
            a = self.selected_handeler.translate_key(event)
            if a is not None:
                self.selected_handeler.insert(character=a)
        """

class WarpHandlerEasy(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)

        sector_coords = self.engine.game_data.player.sectorCoords

        self.x = NumberHandeler(limit=2, max_value=config_object.sector_width, min_value=0, wrap_around=True, starting_value=sector_coords.x)

        self.y = NumberHandeler(limit=2, max_value=config_object.sector_height, min_value=0, wrap_around=True, starting_value=sector_coords.y)

        self.selected_handeler = self.x

        self.energy_cost = round(self.engine.player.sectorCoords.distance(x=self.x.add_up(),y=self.y.add_up()) * self.engine.player.sysWarp.affect_cost_multiplier * SECTOR_ENERGY_COST)

        self.x_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=6,
            height=3,
            title="X:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.y_button = ButtonBox(
            x=10+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=6,
            height=3,
            title="Y:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.cost_button = ButtonBox(
            x=10+config_object.command_display_x,
            y=8+config_object.command_display_y,
            width=10,
            height=3,
            title="Energy Cost:",
            text="",
            alignment=tcod.constants.RIGHT
        )
        
        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Confirm"
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input coordants"
            )

        self.x_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.x else colors.grey,
            bg=colors.black,
            text=self.x.text_to_print,
            cursor_position=self.x.cursor
        )

        self.y_button.render(
            console,
            fg=colors.white if self.selected_handeler is self.y else colors.grey,
            bg=colors.black,
            text=self.y.text_to_print,
            cursor_position=self.y.cursor
        )

        self.cost_button.render(
            console,
            text=f"{self.energy_cost}"
        )

        self.confirm_button.render(console)

        self.cancel_button.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)

        if self.x_button.cursor_overlap(event):
            self.selected_handeler = self.x
        elif self.y_button.cursor_overlap(event):
            self.selected_handeler = self.y
        elif self.confirm_button.cursor_overlap(event):
            warp_order = WarpOrder.from_coords(self.engine.player, self.x.add_up(), self.y.add_up())
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
        
        else:
            x, y = select_sector_space(event)

            if x is not False and y is not False:
                print(f"{x} {y}")
                self.x.set_text(x)
                self.y.set_text(y)

                self.energy_cost = round(self.engine.player.sectorCoords.distance(x=self.x.add_up(),y=self.y.add_up()) * self.engine.player.sysWarp.affect_cost_multiplier * SECTOR_ENERGY_COST)
                
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            
            warp_order = WarpOrder.from_coords(self.engine.player, self.x.add_up(), self.y.add_up())
            warning = warp_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return warp_order
            
            self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
        else:
            self.selected_handeler.handle_key(event)
            self.energy_cost = round(self.engine.player.sectorCoords.distance(x=self.x.add_up(),y=self.y.add_up()) * self.engine.player.sysWarp.affect_cost_multiplier * SECTOR_ENERGY_COST)
        """
        elif event.sym == tcod.event.K_BACKSPACE:
            self.selected_handeler.delete()
        elif event.sym == tcod.event.K_DELETE:
            self.selected_handeler.delete(True)
        else:
            a = self.selected_handeler.translate_key(event)
            if a is not None:
                self.selected_handeler.insert(character=a)
        """

class MoveHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.heading = NumberHandeler(limit=3, max_value=360, min_value=0, wrap_around=True)
        self.distance = NumberHandeler(limit=3, max_value=config_object.max_move_distance, min_value=1)

        self.energy_cost = round(self.distance.add_up() * LOCAL_ENERGY_COST * self.engine.player.sysImpulse.affect_cost_multiplier)

        self.heading_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=12,
            height=3,
            title="Heading:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.distance_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=7+config_object.command_display_y,
            width=12,
            height=3,
            title="Distance:",
            text="",
            alignment=tcod.constants.RIGHT
        )


        self.three_fifteen_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="315",
            alignment=tcod.constants.RIGHT
        )

        self.two_seventy_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=5,
            height=3,
            text="270",
            alignment=tcod.constants.RIGHT
        )

        self.zero_button = ButtonBox(
            x=22+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="0",
            alignment=tcod.constants.RIGHT
        )

        self.fourty_five_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="45",
            alignment=tcod.constants.RIGHT
        )

        self.two_twenty_five_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="225",
            alignment=tcod.constants.RIGHT
        )

        self.ninty_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=5,
            height=3,
            text="90",
            alignment=tcod.constants.RIGHT
        )
        
        self.one_thirty_five_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="135",
            alignment=tcod.constants.RIGHT
        )

        self.one_eighty_button = ButtonBox(
            x=22+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="180",
            alignment=tcod.constants.RIGHT
        )

        self.cost_button = ButtonBox(
            x=10+config_object.command_display_x,
            y=8+config_object.command_display_y,
            width=10,
            height=3,
            title="Energy Cost:",
            text=f"{self.energy_cost}",
            alignment=tcod.constants.RIGHT
        )

        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Confirm"
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

        self.selected_handeler = self.heading

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input heading and distance"
            )

        self.heading_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.heading else colors.grey,
            bg=colors.black,
            text=self.heading.text_to_print,
            cursor_position=self.heading.cursor
        )

        self.distance_button.render(
            console,
            fg=colors.white if self.selected_handeler is self.distance else colors.grey,
            bg=colors.black,
            text=self.distance.text_to_print,
            cursor_position=self.distance.cursor
        )

        self.zero_button.render(console)

        self.fourty_five_button.render(console)

        self.ninty_button.render(console)

        self.one_thirty_five_button.render(console)

        self.one_eighty_button.render(console)

        self.two_twenty_five_button.render(console)

        self.two_seventy_button.render(console)
        
        self.three_fifteen_button.render(console)


        self.cost_button.render(
            console,
            text=f"{self.energy_cost}"
        )

        self.confirm_button.render(
            console
        )

        self.cancel_button.render(
            console
        )

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:

        if self.zero_button.cursor_overlap(event):
            self.heading.set_text(0)
        elif self.fourty_five_button.cursor_overlap(event):
            self.heading.set_text(45)
        elif self.ninty_button.cursor_overlap(event):
            self.heading.set_text(90)
        elif self.one_thirty_five_button.cursor_overlap(event):
            self.heading.set_text(135)
        elif self.one_eighty_button.cursor_overlap(event):
            self.heading.set_text(180)
        elif self.two_twenty_five_button.cursor_overlap(event):
            self.heading.set_text(235)
        elif self.two_seventy_button.cursor_overlap(event):
            self.heading.set_text(270)
        elif self.three_fifteen_button.cursor_overlap(event):
            self.heading.set_text(315)

        elif self.heading_button.cursor_overlap(event):
            self.selected_handeler = self.heading
        elif self.distance_button.cursor_overlap(event):
            self.selected_handeler = self.distance
        elif self.confirm_button.cursor_overlap(event):
            move_order = MoveOrder(self.engine.player, self.heading.add_up(), self.distance.add_up())
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

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm and not self.heading.is_empty and not self.distance.is_empty:
            move_order = MoveOrder(self.engine.player, self.heading.add_up(), self.distance.add_up())
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
            self.energy_cost = round(self.distance.add_up() * LOCAL_ENERGY_COST * self.engine.player.sysImpulse.affect_cost_multiplier)
        
class MoveHandlerEasy(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)

        local_coords = self.engine.game_data.player.localCoords

        self.x = NumberHandeler(limit=1, max_value=config_object.sector_width, min_value=0, wrap_around=True, starting_value=local_coords.x)
        self.y = NumberHandeler(limit=1, max_value=config_object.sector_height, min_value=0, wrap_around=True, starting_value=local_coords.y)

        self.selected_handeler = self.x

        self.energy_cost = round(self.engine.player.localCoords.distance(x=self.x.add_up(), y=self.y.add_up())  * LOCAL_ENERGY_COST * self.engine.player.sysImpulse.affect_cost_multiplier)

        self.x_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=6,
            height=3,
            title="X:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.y_button = ButtonBox(
            x=10+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=6,
            height=3,
            title="Y:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Confirm"
        )

        self.cost_button = ButtonBox(
            x=10+config_object.command_display_x,
            y=8+config_object.command_display_y,
            width=10,
            height=3,
            title="Energy Cost:",
            text=f"{self.energy_cost}",
            alignment=tcod.constants.RIGHT
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input coordants"
            )

        self.x_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.x else colors.grey,
            bg=colors.black,
            text=self.x.text_to_print,
            cursor_position=self.x.cursor
        )

        self.y_button.render(
            console,
            fg=colors.white if self.selected_handeler is self.y else colors.grey,
            bg=colors.black,
            text=self.y.text_to_print,
            cursor_position=self.y.cursor
        )

        self.cost_button.render(
            console,
            text=f"{self.energy_cost}"
        )

        self.confirm_button.render(
            console
        )

        self.cancel_button.render(
            console
        )
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
        
        if self.x_button.cursor_overlap(event):
            self.selected_handeler = self.x
        elif self.y_button.cursor_overlap(event):
            self.selected_handeler = self.y
        elif self.confirm_button.cursor_overlap(event):
            warp_order = MoveOrder.from_coords(self.engine.player, self.x.add_up(), self.y.add_up())
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
                
                self.x.set_text(x)
                self.y.set_text(y)
                self.warned_once = False
                self.energy_cost = round(self.engine.player.localCoords.distance(x=self.x.add_up(), y=self.y.add_up())  * LOCAL_ENERGY_COST * self.engine.player.sysImpulse.affect_cost_multiplier)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            
            warp_order = MoveOrder.from_coords(self.engine.player, self.x.add_up(), self.y.add_up())
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
            self.energy_cost = round(self.engine.player.localCoords.distance(x=self.x.add_up(), y=self.y.add_up())  * LOCAL_ENERGY_COST)
            self.warned_once = False
            
class ShieldsHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        player = self.engine.player
        self.amount = NumberHandeler(limit=4, max_value=player.get_max_shields - player.shields, min_value=player.shields)

        self.amount_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=12,
            height=3,
            title="Amount:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Confirm"
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input energy to transfer to shields"
            )

        self.amount_button.render(
            console,
            text=self.amount.text_to_print,
            fg=colors.white,
            bg =colors.black,
            cursor_position=self.amount.cursor
        )

        self.confirm_button.render(console)
        self.cancel_button.render(console)

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:

        if self.confirm_button.cursor_overlap(event):
            recharge_order = RechargeOrder(self.engine.player, self.amount.add_up())

            warning = recharge_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return recharge_order
            
            self.engine.message_log.add_message(blocks_action[warning], colors.red)
        elif self.cancel_button.cursor_overlap(event):

            return CommandEventHandler(self.engine)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            recharge_order = RechargeOrder(self.engine.player, self.amount.add_up())

            warning = recharge_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return recharge_order
            
            self.engine.message_log.add_message(blocks_action[warning], colors.red)
        else:
            self.amount.handle_key(event)

class EnergyWeaponHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        player = self.engine.player
        self.amount = NumberHandeler(limit=4, max_value=player.get_max_firepower, min_value=0)

        self.amount_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=12,
            height=3,
            title="Amount:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Fire"
        )

        self.fire_all_button = ButtonBox(
            x=3+12+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=12,
            height=4,
            text="Fire all"
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input energy to use:"
            )
        
        self.amount_button.render(
            console,
            text=self.amount.text_to_print,
            fg=colors.white,
            bg=colors.black,
            cursor_position=self.amount.cursor
        )

        self.confirm_button.render(console)

        self.fire_all_button.render(console)

        self.cancel_button.render(console)

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:
        
        if self.confirm_button.cursor_overlap(event):

            fire_order = PhaserOrder.single_target(
                self.engine.player,
                self.amount.add_up(),
                self.engine.game_data.selected_ship_or_planet
            )

            warning = fire_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return fire_order
            
            self.engine.message_log.add_message(
                blocks_action[warning]
            )
        elif self.fire_all_button.cursor_overlap(event):

            fire_order = PhaserOrder.multiple_targets(
                self.engine.player,
                self.amount.add_up(),
                self.engine.game_data.grapShipsInSameSubSector(self.engine.player)
            )

            warning = fire_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return fire_order
            
            self.engine.message_log.add_message(
                blocks_action[warning]
            )
        elif self.cancel_button.cursor_overlap(event):

            return CommandEventHandler(self.engine)
        
        select_ship_planet_star(self.engine.game_data, event)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            fire_order = PhaserOrder(
                self.engine.player,
                self.amount.add_up(),
                target=self.engine.game_data.selected_ship_or_planet
            )

            warning = fire_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return fire_order
            
            self.engine.message_log.add_message(
                blocks_action[warning]
            )
        else:
            self.amount.handle_key(event)

class TorpedoHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        self.heading = NumberHandeler(limit=3, max_value=360, min_value=0, wrap_around=True)
        self.number = NumberHandeler(limit=1, max_value=self.engine.player.shipData.torpTubes, min_value=1)

        self.selected_handeler = self.heading

        self.heading_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=12,
            height=3,
            title="Heading:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.number_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=7+config_object.command_display_y,
            width=12,
            height=3,
            title="Number:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.three_fifteen_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="315",
            alignment=tcod.constants.RIGHT
        )

        self.two_seventy_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=5,
            height=3,
            text="270",
            alignment=tcod.constants.RIGHT
        )

        self.zero_button = ButtonBox(
            x=22+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="0",
            alignment=tcod.constants.RIGHT
        )

        self.fourty_five_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=10+config_object.command_display_y,
            width=5,
            height=3,
            text="45",
            alignment=tcod.constants.RIGHT
        )

        self.two_twenty_five_button = ButtonBox(
            x=16+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="225",
            alignment=tcod.constants.RIGHT
        )

        self.ninty_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=6+config_object.command_display_y,
            width=5,
            height=3,
            text="90",
            alignment=tcod.constants.RIGHT
        )
        
        self.one_thirty_five_button = ButtonBox(
            x=28+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="135",
            alignment=tcod.constants.RIGHT
        )

        self.one_eighty_button = ButtonBox(
            x=22+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=5,
            height=3,
            text="180",
            alignment=tcod.constants.RIGHT
        )


        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Confirm"
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input heading and distance"
            )

        self.heading_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.heading else colors.grey,
            bg=colors.black,
            text=self.heading.text_to_print,
            cursor_position=self.heading.cursor
        )

        self.number_button.render(
            console,
            fg=colors.white if self.selected_handeler is self.number else colors.grey,
            bg=colors.black,
            text=self.number.text_to_print,
            cursor_position=self.number.cursor
        )

        self.confirm_button.render(console)

        self.cancel_button.render(console)

        self.zero_button.render(console)

        self.fourty_five_button.render(console)

        self.ninty_button.render(console)

        self.one_thirty_five_button.render(console)

        self.one_eighty_button.render(console)

        self.two_twenty_five_button.render(console)

        self.two_seventy_button.render(console)
        
        self.three_fifteen_button.render(console)

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)

        if self.zero_button.cursor_overlap(event):
            self.heading.set_text(0)
        elif self.fourty_five_button.cursor_overlap(event):
            self.heading.set_text(45)
        elif self.ninty_button.cursor_overlap(event):
            self.heading.set_text(90)
        elif self.one_thirty_five_button.cursor_overlap(event):
            self.heading.set_text(135)
        elif self.one_eighty_button.cursor_overlap(event):
            self.heading.set_text(180)
        elif self.two_twenty_five_button.cursor_overlap(event):
            self.heading.set_text(235)
        elif self.two_seventy_button.cursor_overlap(event):
            self.heading.set_text(270)
        elif self.three_fifteen_button.cursor_overlap(event):
            self.heading.set_text(315)

        elif self.heading_button.cursor_overlap(event):
            self.selected_handeler = self.heading
        elif self.number_button.cursor_overlap(event):
            self.selected_handeler = self.number
        elif self.confirm_button.cursor_overlap(event):
            torpedo_order = TorpedoOrder.from_heading(self.engine.player, self.heading.add_up(), self.number.add_up())
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
            select_ship_planet_star(self.engine.game_data, event)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            torpedo_order = TorpedoOrder.from_heading(self.engine.player, self.heading.add_up(), self.number.add_up())
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
        
class TorpedoHandlerEasy(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)

        local_coords = self.engine.game_data.player.localCoords

        self.x = NumberHandeler(limit=2, max_value=config_object.subsector_width, min_value=0, wrap_around=True, starting_value=local_coords.x)
        self.y = NumberHandeler(limit=2, max_value=config_object.subsector_height, min_value=0, wrap_around=True, starting_value=local_coords.y)

        self.number = NumberHandeler(limit=1, max_value=self.engine.player.shipData.torpTubes, min_value=1)

        self.selected_handeler = self.x

        self.x_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=6,
            height=3,
            title="X:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.y_button = ButtonBox(
            x=3+8+config_object.command_display_x,
            y=2+config_object.command_display_y,
            width=6,
            height=3,
            title="Y:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.number_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=7+config_object.command_display_y,
            width=12,
            height=3,
            title="Number:",
            text="",
            alignment=tcod.constants.RIGHT
        )

        self.confirm_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=12+config_object.command_display_y,
            width=9,
            height=3,
            text="Confirm"
        )

        self.cancel_button = ButtonBox(
            x=3+config_object.command_display_x,
            y=18+config_object.command_display_y,
            width=9,
            height=3,
            text="Cancel"
        )

    def on_render(self, console: tcod.Console) -> None:

        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input heading and distance"
            )

        self.x_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.x else colors.grey,
            bg=colors.black,
            text=self.x.text_to_print,
            cursor_position=self.x.cursor
        )

        self.y_button.render(
            console, 
            fg=colors.white if self.selected_handeler is self.y else colors.grey,
            bg=colors.black,
            text=self.y.text_to_print,
            cursor_position=self.y.cursor
        )

        self.number_button.render(
            console,
            fg=colors.white if self.selected_handeler is self.number else colors.grey,
            bg=colors.black,
            text=self.number.text_to_print,
            cursor_position=self.number.cursor
        )

        self.confirm_button.render(console)

        self.cancel_button.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)

        if self.x_button.cursor_overlap(event):
            self.selected_handeler = self.x
        elif self.y_button.cursor_overlap(event):
            self.selected_handeler = self.y
        elif self.number_button.cursor_overlap(event):
            self.selected_handeler = self.number
        elif self.confirm_button.cursor_overlap(event):
            torpedo_order = TorpedoOrder.from_coords(self.engine.player, self.number.add_up(), self.x.add_up(), self.y.add_up())
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
            x,y = select_sub_sector_space(event)

            if x is not False and y is not False:
                self.x.set_text(x)
                self.y.set_text(y)
                self.warned_once == False

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

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

class SelfDestructHandler(MainGameEventHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        player = engine.player
        
        nearbye_foes = [ship for ship in engine.game_data.grapShipsInSameSubSector(player) if player.localCoords.distance(coords=ship.localCoords) <= player.shipData.warpBreachDist]
        
        nearbye_foes.sort(key=lambda ship: ship.localCoords.distance(coords=player.localCoords), reverse=True)
        
        self.nearbye_foes = tuple(
            (player.calcSelfDestructDamage(ship)) for ship in nearbye_foes
        )
        
        self.any_ships_nearby = len(self.nearbye_foes) > 0

        self.code_handler = TextHandeler(
            12
        )

        self.code_status = 0

        self.confirm = ButtonBox(
            x=4+config_object.command_display_x,
            y=4+config_object.command_display_y,
            width=10,
            height=3,
            text="Confirm"
        )

        self.cancel = ButtonBox(
            x=16+config_object.command_display_x,
            y=4+config_object.command_display_y,
            width=10,
            height=3,
            text="Cancel"
        )

        self.code = ButtonBox(
            x=4+config_object.command_display_x,
            y=9+config_object.command_display_y,
            width=18,
            height=3,
            title="Input code:",
            text=self.code_handler.send()
        )
    
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input self destruct code"
            )
    
        self.confirm.render(console)

        self.cancel.render(console)

        self.code.render(
            console,
            text=self.code_handler.text_to_print,
            cursor_position=self.code_handler.cursor
        )
        
        console.print(
            x=4+config_object.command_display_x,
            y=12+config_object.command_display_y,
            string=f"Code: {config_object.auto_destruct_code}"
        )
        
        if self.any_ships_nearby:
            console.print(
                x=2+config_object.command_display_x,
                y=16+config_object.command_display_y,
                string="Ships in radius of a-destruct:"
            )
            
            console.print(
                x=2+config_object.command_display_x,
                y=17+config_object.command_display_y,
                string="Name    S. Dam.  H. Dam.  Kill"
            )
            for i, ship_info in enumerate(self.nearbye_foes):
                ship, shield_dam, hull_dam, kill = ship_info
                console.print(
                    x=2+config_object.command_display_x,
                    y=i+18+config_object.command_display_y,
                    string=f"{ship.name: <8}  {shield_dam: <7}  {hull_dam: <7} {'Yes' if kill else 'No'}"
                )
        else:
            console.print_box(
                x=2+config_object.command_display_x,
                y=16+config_object.command_display_y,
                width=(config_object.command_display_end_x - 2) - (2 + config_object.command_display_x),
                height=5,
                string="No ships in radius of auto destruct"
            )
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[ActionOrHandler]:

        if event.sym == tcod.event.K_CANCEL:
            return CommandEventHandler(self.engine)

        if event.sym in confirm:

            if self.code_handler.text_to_print == config_object.auto_destruct_code:

                return SelfDestructOrder(self.engine.player)
            else:
                self.engine.message_log.add_message("Error: The code for the self destruct is not correct.")
        else:
        
            self.code_handler.handle_key(event)

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[ActionOrHandler]:
        
        if self.cancel.cursor_overlap(event):
            
            return CommandEventHandler(self.engine)
        if self.confirm.cursor_overlap(event):
            if self.code_handler.text_to_print == config_object.auto_destruct_code:

                return SelfDestructOrder(self.engine.player)
            else:
                self.engine.message_log.add_message("Error: The code for the self destruct is not correct.")
                
class GameOverEventHandler(EventHandler):

    def generate_evaluation(self):
        gameDataGlobal = self.engine.game_data

        startingEnemyFleetValue = 0.0
        currentEnemyFleetValue = 0.0
        endingText = []
        total_ships = len(gameDataGlobal.totalStarships) - 1
        
        remaining_ships = len(gameDataGlobal.enemyShipsInAction)

        destroyed_ships = total_ships - remaining_ships

        derlict_ships = 0

        planets_angered = self.engine.game_data.player_record["planets_angered"]
        planets_depopulated = self.engine.game_data.player_record["planets_depopulated"]
        prewarp_planets_depopulated = self.engine.game_data.player_record["prewarp_planets_depopulated"]
        times_hit_planet = self.engine.game_data.player_record["times_hit_planet"]
        times_hit_poipulated_planet = self.engine.game_data.player_record["times_hit_poipulated_planet"]
        times_hit_prewarp_planet = self.engine.game_data.player_record["times_hit_prewarp_planet"]

        did_the_player_do_bad_stuff = times_hit_poipulated_planet > 0

        percentage_of_ships_destroyed = destroyed_ships / total_ships

        for s in gameDataGlobal.totalStarships:
            if not s.isControllable:
                startingEnemyFleetValue+= s.shipData.maxHull
                currentEnemyFleetValue+= s.getShipValue
                if s.isDerelict:
                    derlict_ships += 1

        destructionPercent = 1.0 - currentEnemyFleetValue / startingEnemyFleetValue
        timeLeftPercent = gameDataGlobal.turnsLeft / 100.0
        overallScore = destructionPercent * timeLeftPercent#TODO - implement a more complex algorithum for scoring
        noEnemyLosses = destroyed_ships == 0

        all_enemy_ships_destroyed = remaining_ships == 0

        if gameDataGlobal.player.isAlive:

            if all_enemy_ships_destroyed:

                if did_the_player_do_bad_stuff:

                    endingText.append("While the attacking Domminion force was wiped out, initial enthusamim over your victory \
has given way to horror. ")

                    endingText.extend(
                        self._the_player_did_bad_stuff(
                            planets_depopulated=planets_depopulated,
                            planets_angered=planets_angered,
                            prewarp_planets_depopulated=prewarp_planets_depopulated,
                            times_hit_poipulated_planet=times_hit_poipulated_planet,
                            times_hit_prewarp_planet=times_hit_prewarp_planet
                        )
                    )
                else:
                    endingText.append('Thanks to your heroic efforts, mastery of tactial skill, and shrewd manadgement of limited resources, \
you have completly destroyed the Domminion strike force. Well done!')

                    if timeLeftPercent < 0.25:

                        endingText.append('The enemy has been forced to relocate a large amount of their ships to \
this sector. In doing so, they have weakened their fleets in several key areas, including their holdings in the Alpha Quadrent.')

                    elif timeLeftPercent < 0.5:

                        endingText.append(f'Interecpted communications have revealed that because of the total destruction of the enemy task \
force, the {gameDataGlobal.player.name} has been designated as a priority target.')

                    elif timeLeftPercent < 0.75:

                        endingText.append('We are making prepations for an offensive to capture critical systems. Because of your abilities \
Starfleet Command is offering you a promotion to the rank of real admiral.')

                    else:

                        endingText.append('The enemy is in complete disarray thanks to the speed at which you annilated the opposing fleet! \
Allied forces have exploited the chaos, making bold strikes into Dominion controlled space in the Alpha Quadrent. Starfleet \
Intel has predicded mass defections among from the Cadrassian millitary. Because of abilities Starfleet Command has weighed \
the possibility of a promotion to the rank of real admiral, but ultimatly decided that your skills are more urgently needed \
in the war.')
            else:
                if noEnemyLosses:
                    endingText.append('The mission was a complete and utter failure. No ships of the Dominion strike force were destroyed, \
allowing enemy forces to fortify their positions within the Alpha Quadrent. You can expect a court marshal in your future.')
                elif percentage_of_ships_destroyed < 0.25:
                    endingText.append('The mission was a failure. Neglible losses were inflited on the enemy. Expect to be demoted')
                elif percentage_of_ships_destroyed < 0.5:
                    endingText.append('The mission was a failure. The casulties inflicted on the Domminion strike fore were insuficent \
to prevent them from taking key positions.')
                elif percentage_of_ships_destroyed < 0.75:
                    endingText.append('The mission was unsucessful. In spite of in')

        else:
            if all_enemy_ships_destroyed:
                endingText.append('Thanks to your sacrifice, mastery of tactial skill, and shrewd manadgement of limited resources, \
you have completly destroyed the Domminion strike force. Well done!')
                if timeLeftPercent < 0.25:
                    endingText.append('Your hard fought sacrifice will be long remembered in the reccords of Starfleet history. ')
                elif timeLeftPercent < 0.5:
                    endingText.append('')
                elif timeLeftPercent < 0.75:
                    endingText.append('')
                else:
                    endingText.append('Althoug you were completly victorous over the Domminion strike force, senior personel have \
questioned the reckless or your actions. Admeral Ross has stated that a more cautous aproch would resulted in the survival of your crew')
            elif noEnemyLosses:
                if timeLeftPercent < 0.25:
                    endingText.append('You are an embaressment to the Federation. ')
                else:
                    endingText.append('You are terrible at this. ')
            elif destructionPercent < 0.5:
                endingText.append('Pretty bad. ')
            else:
                endingText.append('Still bad. ')

        endingText.append(f'Overall score: {overallScore:%}')

        return ''.join(endingText)

    def _the_player_did_bad_stuff(self, *, planets_depopulated:int, planets_angered:int, times_hit_prewarp_planet:int, 
    prewarp_planets_depopulated:int, times_hit_poipulated_planet:int) -> List[str]:

        endingText = []

        if planets_depopulated > 0:

            if planets_depopulated == 1:

                how_many_planets_killed = "a"
            elif planets_depopulated == 2:

                how_many_planets_killed = "two"

            elif planets_depopulated == 3:

                how_many_planets_killed = "three"
            else:
                how_many_planets_killed = "four" if planets_depopulated == 4 else "multiple"

            endingText.append(f"Your ship records indcated that torpedos fired from your ship were the cause of the destruction \
of {how_many_planets_killed} ,")

            if planets_angered > 0:
                endingText.append("civilsations,")

                if planets_depopulated == planets_angered:

                    how_many_planets_angered = "all"
                elif planets_angered == 1:

                    how_many_planets_angered = "one"
                elif planets_angered == 2:
                    how_many_planets_angered = "two"
                elif planets_angered == 3:
                    how_many_planets_angered = "three"
                else:
                    how_many_planets_angered = "four" if planets_angered == 4 else "many"
                    
                endingText.append(f"{how_many_planets_angered} of which had good relations with the Federation until you fired on them.")
            else:
                endingText.append("civilsations.")

            if prewarp_planets_depopulated > 0:

                if prewarp_planets_depopulated == planets_depopulated:
                    how_many_prewarp_planets_killed = "all"
                elif prewarp_planets_depopulated == 1:
                    how_many_prewarp_planets_killed = "one"
                elif prewarp_planets_depopulated == 2:
                    how_many_prewarp_planets_killed = "two"
                elif prewarp_planets_depopulated == 3:
                    how_many_prewarp_planets_killed = "three"
                else:
                    how_many_prewarp_planets_killed = "four" if planets_depopulated == 4 else "numerous"

                endingText.append(f"Horriffingly, {how_many_prewarp_planets_killed} of thouse planets were prewarp civilastions.")

        return endingText

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.text_scroll = 0
        self.console_height = engine.screen_height
        self.ending_text = self.generate_evaluation()
        self.show_evaluation = False

    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("saves/" + self.engine.filename + ".sav"):
            self.engine.save_as("")
            #os.remove("savegame.sav")  # Deletes the active save file.
        else:
            print(self.engine.filename)
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        
        if self.show_evaluation:
            key = event.sym

            if key == tcod.event.K_ESCAPE:
                self.on_quit()
            elif key == tcod.event.K_UP and self.text_scroll > 0:
                self.text_scroll -= 1
            elif key == tcod.event.K_DOWN and self.text_scroll < len(self.text) - self.console_height:
                self.text_scroll += 1
        else:
            self.show_evaluation = True

    def on_render(self, console: tcod.Console) -> None:

        if self.show_evaluation:
            half_width = console.width//2

            console.print_frame(
                x=2, 
                y=2, 
                width=console.width-4, 
                height=self.console_height, 
                string="Y O U   H A V E   F A L L E N", 
            bg_blend=tcod.BKGND_MULTIPLY)

            console.print_rect(
                x=3, 
                y=3, 
                width=console.width-6,
                height=self.console_height-2,
                string=self.ending_text)

            #for i, e in enumerate(self.ending_text, self.text_scroll):
            
            console.print(x=10, y=40, string="Press ESC to quit")
        else:
            print_subsector(console, self.engine.game_data)
            print_mega_sector(console, self.engine.game_data)
            render_own_ship_info(console, self.engine.game_data)

            render_other_ship_info(console, self.engine.game_data, self.engine.game_data.selected_ship_or_planet)

            print_message_log(console, self.engine.game_data)
            render_position(console, self.engine.game_data)