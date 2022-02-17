from __future__ import annotations
from random import choice
from textwrap import wrap
from coords import Coords
from data_globals import LOCAL_ENERGY_COST, SECTOR_ENERGY_COST, STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK, STATUS_OBLITERATED, WARP_FACTOR, CloakStatus
from engine import CONFIG_OBJECT
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, Tuple, Union
from order import CloakOrder, SelfDestructOrder, TransportOrder, WarpTravelOrder, blocks_action, \
    torpedo_warnings, collision_warnings, misc_warnings, Order, DockOrder, OrderWarning, \
    EnergyWeaponOrder, RepairOrder, TorpedoOrder, WarpOrder, MoveOrder, RechargeOrder
from global_functions import stardate
from ship_class import ALL_SHIP_CLASSES, ShipClass
from space_objects import Planet, Star, SubSector
from starship import Starship
from torpedo import Torpedo
from ui_related import BooleanBox, InputHanderer, NumberHandeler, ScrollingTextBox, Selector, SimpleElement, \
    TextHandeler, confirm
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
        
        self.engine.player.handle_repair_and_energy_consumption()

        game_data = self.engine.game_data
        game_data.ships_in_same_sub_sector_as_player = game_data.grab_ships_in_same_sub_sector(
            game_data.player, accptable_ship_statuses={
                STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
            }
        )
        game_data.date_time = game_data.date_time + CONFIG_OBJECT.time_per_turn
        game_data.stardate = stardate(game_data.date_time)

        self.engine.handle_enemy_turns()
        try:
            game_data.player.cloak.handle_cooldown_and_status_recovery()
        except AttributeError:
            pass
        try:
            game_data.player.sensors.detect_all_enemy_cloaked_ships_in_system()
        except AttributeError:
            pass
        
        game_data.warp_factor = game_data.describe_warp_factor()
        game_data.shields_description = game_data.describe_shields()
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

def distance_button(*, limit:int, max_value:int, min_value:int=0) -> NumberHandeler:
    return NumberHandeler(
        limit=limit, max_value=max_value, min_value=min_value,
        x=3+CONFIG_OBJECT.command_display_x,
        y=6+CONFIG_OBJECT.command_display_y,
        width=12,
        height=3,
        title="Distance:",
        active_fg=colors.white,
        inactive_fg=colors.grey,
        bg=colors.black,
        alignment=tcod.constants.RIGHT,
        initally_active=False
    )

def torpedo_number_button(*, max_value:int):
    return NumberHandeler(
        limit=1, max_value=max_value, min_value=1,
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
    
def torpedo_select_button(index_items:Iterable[str], keys:Iterable[Any]):
    return Selector(
        x=15+CONFIG_OBJECT.command_display_x,
        y=16+CONFIG_OBJECT.command_display_y,
        width=10,
        height=6,
        active_fg=colors.white,
        inactive_fg=colors.grey,
        bg=colors.black,
        index_items=index_items,
        keys=keys
    )

def cost_button(cost:str) -> SimpleElement:
    return SimpleElement(
        x=3+CONFIG_OBJECT.command_display_x,
        y=10+CONFIG_OBJECT.command_display_y,
        width=12,
        height=3,
        title="Energy Cost:",
        text=cost,
        active_fg=colors.white,
        bg=colors.black,
        alignment=tcod.constants.RIGHT
    )
    
def speed_button(max_value:int) -> NumberHandeler:
    return NumberHandeler(
        x=3+CONFIG_OBJECT.command_display_x,
        y=14+CONFIG_OBJECT.command_display_y,
        width=8,
        height=3,
        title="Speed:",
        min_value=1,
        max_value=max_value,
        limit=1,
        active_fg=colors.white,
        inactive_fg=colors.grey,
        bg=colors.black,
        initally_active=False
    )
    
def auto_target_button():
    return SimpleElement(
            x=4+12+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=14,
            height=3,
            text="Auto-Target",
            active_fg=colors.white,
            bg=colors.black
        )

class CancelConfirmHandler(MainGameEventHandler):
    
    def __init__(self, engine: Engine, can_render_confirm_button:bool=True) -> None:
        super().__init__(engine)
        
        self.confirm_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=18+CONFIG_OBJECT.command_display_y,
            width=9,
            height=3,
            text="Confirm",
            active_fg=colors.white,
            bg=colors.black,
        )
        self.cancel_button = SimpleElement(
            x=3+CONFIG_OBJECT.command_display_x,
            y=22+CONFIG_OBJECT.command_display_y,
            width=9,
            height=3,
            text="Cancel",
            active_fg=colors.white,
            bg=colors.black,
        )
        self.can_render_confirm_button = can_render_confirm_button
    
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        self.cancel_button.render(console)
        if self.can_render_confirm_button:
            self.confirm_button.render(console)

class MinMaxInitator(CancelConfirmHandler):
    
    def __init__(
        self, 
        engine: Engine, can_render_confirm_button:bool=True,
        *,
        max_value:int, starting_value:int
    ) -> None:
        super().__init__(engine, can_render_confirm_button)
        
        self.max_button = SimpleElement(
            x=3+12+CONFIG_OBJECT.command_display_x,
            y=18+CONFIG_OBJECT.command_display_y,
            width=7,
            height=3,
            text="Max",
            active_fg=colors.white,
            bg=colors.black
        )
        self.min_button = SimpleElement(
            x=3+12+CONFIG_OBJECT.command_display_x,
            y=22+CONFIG_OBJECT.command_display_y,
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
        
    def __init__(self, engine: Engine, can_render_confirm_button:bool=True) -> None:
        super().__init__(engine, can_render_confirm_button)
        
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
        self, engine: Engine, can_render_confirm_button:bool=True,
        *,
        max_x:int,
        max_y:int,
        starting_x:int,
        starting_y:int,
        ) -> None:
        
        super().__init__(engine, can_render_confirm_button)
                
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
        self.is_mobile = self.engine.player.is_mobile
        self.ship_is_not_automated = not self.engine.player.is_automated
        
        self.warp_travel = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=(CONFIG_OBJECT.command_display_end_x - CONFIG_OBJECT.command_display_x) - 4,
            height=3,
            text="Continue to destination",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )
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
        try:
            cloak_status = self.engine.player.cloak.cloak_is_turned_on
        except AttributeError:
            cloak_status = False
        
        self.cloak_button = BooleanBox(
            x=2+CONFIG_OBJECT.command_display_x,
            y=8+CONFIG_OBJECT.command_display_y,
            width=11,
            height=3,
            active_text="(C)loak",
            inactive_text="De(C)loak",
            active_fg=colors.white,
            inactive_fg=colors.white,
            initally_active=cloak_status
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

        self.beam_button = SimpleElement(
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
            text="Fire T(o)rpedos",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )
        self.transporter_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=20+CONFIG_OBJECT.command_display_y,
            width=24,
            height=3,
            text="(T)ransporter",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )
        self.auto_destruct_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=23+CONFIG_OBJECT.command_display_y,
            width=24,
            height=3,
            text="(A)uto-Destruct",
            active_fg=colors.white,
            bg=colors.black,
            alignment=tcod.CENTER
        )        

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.engine.game_data.debug_warning == 1:
            self.engine.game_data.debug_warning = 0
                
        try:
            is_at_warp = self.engine.player.warp_drive.is_at_warp
            
        except AttributeError:
            
            is_at_warp = False
        
        if is_at_warp:
            if self.warp_travel.cursor_overlap(event):
            
                return WarpTravelOrder(self.engine.player)
        else:
            captain = self.engine.player.ship_class.nation.captain_rank_name
            
            if self.warp_button.cursor_overlap(event) and self.is_mobile:
                
                return self.warp(captain)
            
            elif self.move_button.cursor_overlap(event) and self.is_mobile:
                
                return self.move(captain)
                
            elif self.shields_button.cursor_overlap(event):
                
                return self.shields(captain)
                
            elif self.beam_button.cursor_overlap(event) and self.ship_type_can_fire_beam_arrays:
                
                return self.beam_arrays(captain)

            elif self.cannons_buttons.cursor_overlap(event) and self.ship_type_can_fire_cannons:
                
                return self.cannons(captain)
                
            elif self.dock_button.cursor_overlap(event) and self.is_mobile:
                
                return self.dock()
                    
            elif self.repair_button.cursor_overlap(event):
                
                return self.repair()
                
            elif self.cloak_button.cursor_overlap(event) and self.ship_type_can_cloak:
                    
                return self.cloak()

            elif self.torpedos_button.cursor_overlap(event) and self.ship_type_can_fire_torps:
                
                return self.torpedos(captain)
            
            elif self.transporter_button.cursor_overlap(event) and self.ship_is_not_automated:
                
                return self.transporters()
                
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
                            game_data.ship_scan = ship_planet_or_star.scan_for_print(game_data.player.sensors.determin_precision)
                            game_data.selected_ship_planet_or_star = ship_planet_or_star
                    else:
                        game_data.selected_ship_planet_or_star = None

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:
        
        if event.sym == tcod.event.K_u and event.mod & tcod.event.KMOD_SHIFT != 0:
                
            if self.engine.game_data.debug_warning == 0:
                
                self.engine.game_data.debug_warning = 1
                
                self.engine.message_log.add_message(
                    "You are about to enter debugging mode. Press Shift-U again to confirm."
                )
                return
            else:
                return DebugHandler(self.engine)
        else:
            if self.engine.game_data.debug_warning == 1:
                self.engine.game_data.debug_warning = 0
        
        try:
            is_at_warp = self.engine.player.warp_drive.is_at_warp
            
        except AttributeError:
            
            is_at_warp = False
            
        if is_at_warp:
            
            return WarpTravelOrder(self.engine.player)
        else:
            captain = self.engine.player.ship_class.nation.captain_rank_name
            
            if event.sym == tcod.event.K_w and self.is_mobile:
                
                return self.warp(captain)
                
            elif event.sym == tcod.event.K_m and self.is_mobile:
                
                return self.move(captain)
                
            elif event.sym == tcod.event.K_s:
                
                return self.shields(captain)
                
            elif event.sym == tcod.event.K_r:
                
                return self.repair(captain)
                
            elif event.sym == tcod.event.K_c and self.ship_type_can_cloak:

                return self.cloak()
                
            elif event.sym == tcod.event.K_f and self.ship_type_can_fire_beam_arrays:
                
                return self.beam_arrays(captain)
                
            elif event.sym == tcod.event.K_i and self.ship_type_can_fire_cannons:
                
                return self.cannons(captain)
                
            elif event.sym == tcod.event.K_d and self.is_mobile:

                return self.dock()
                    
            elif event.sym == tcod.event.K_o and self.ship_type_can_fire_torps:
                
                return self.torpedos()
            
            elif event.sym == tcod.event.K_t and self.ship_is_not_automated:
                
                return self.transporters()
                
            elif event.sym == tcod.event.K_a:
                
                return SelfDestructHandler(self.engine)

    def cloak(self):
        
        player = self.engine.player
        cloak_order = CloakOrder(player, player.cloak.cloak_is_turned_on)
        warning = cloak_order.raise_warning()

        if warning == OrderWarning.SAFE:
            self.cloak_button.is_active = not self.cloak_button.is_active
            return cloak_order
        
        self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)

    def dock(self):
        
        planet = self.engine.game_data.selected_ship_planet_or_star
        
        dock_with_this = None
        if (
            (
                isinstance(planet, Planet) and planet.planet_habbitation.can_ressuply
            ) or (
                isinstance(planet, Starship) and planet.can_be_docked_with
            )
        ) and self.engine.player.local_coords.is_adjacent(other=planet.local_coords):
            
            dock_with_this = planet
        
        if not dock_with_this:
            
            player = self.engine.player
            
            nearby_planets = [
                planet_ for planet_ in player.get_sub_sector.planets_dict.values() if 
                planet_.can_dock_with(player)
            ]
            nearby_planets.sort(reverse=True)
            
            try:
                dock_with_this = nearby_planets[0]
                
            except IndexError:
                
                nearby_stations = [
                    ship for ship in player.game_data.grab_ships_in_same_sub_sector(
                        player, 
                        accptable_ship_statuses={STATUS_ACTIVE}
                    ) if ship.can_dock_with(player)
                ]
                nearby_stations.sort(
                    key=lambda station: station.get_dock_repair_factor
                )
                try:
                    dock_with_this = nearby_stations[0]
                except IndexError:
                    pass
                
        if dock_with_this:
            
            self.warned_once = False
            
            dock_order = DockOrder(self.engine.player, dock_with_this)

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
        else:
            self.engine.message_log.add_message(
                f"Error: No suitable planet nearbye, {player.nation.captain_rank_name}.", fg=colors.red
            )
        
    def torpedos(self, captain:str):
        
        self.warned_once = False
        if not self.engine.player.ship_can_fire_torps:
            self.engine.message_log.add_message(
                text=f"Error: Torpedo systems are inoperative, {captain}." 
                if not self.engine.player.torpedo_launcher.is_opperational else 
                f"Error: This ship has not remaining torpedos, {captain}.", fg=colors.red
            )
        elif self.engine.player.docked:
            self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
        else:
            return TorpedoHandlerEasy(self.engine) if self.engine.easy_aim else TorpedoHandler(self.engine)
        
    def beam_arrays(self, captain:str):
        
        self.warned_once = False
            
        if not self.engine.player.beam_array.is_opperational:
            
            p = self.engine.player.ship_class.get_energy_weapon.beam_name
            self.engine.message_log.add_message(f"Error: {p} systems are inoperative, {captain}.", fg=colors.red)

        elif self.engine.player.power_generator.energy <= 0:
            
            self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
            
        elif self.engine.player.docked:
            
            self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
        else:
            return BeamArrayHandler(self.engine)
        
    def cannons(self, captain:str):
        
        self.warned_once = False
            
        if not self.engine.player.cannons.is_opperational:
            
            p = self.engine.player.ship_class.get_energy_weapon.cannon_name_cap
            
            self.engine.message_log.add_message(
                f"Error: {p} systems are inoperative, {captain}.", fg=colors.red
            )
        elif self.engine.player.power_generator.energy <= 0:
            
            self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
            
        elif self.engine.player.docked:
            
            self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
        else:
            return CannonHandler(self.engine)
        
    def warp(self, captain:str):
        
        self.warned_once = False
            
        if not self.engine.player.warp_drive.is_opperational:
            
            self.engine.message_log.add_message(f"Error: Warp engines are inoperative, {captain}.", fg=colors.red)

        elif self.engine.player.power_generator.energy <= 0:
            self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
        elif self.engine.player.docked:
            self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
        else:
            return WarpHandlerEasy(self.engine) if self.engine.easy_warp else WarpHandler(self.engine)
        
    def move(self, captain:str):
        
        self.warned_once = False
        
        if not self.engine.player.impulse_engine.is_opperational:
            
            self.engine.message_log.add_message(
                f"Error: Impulse systems are inoperative, {captain}.", fg=colors.red
            )
        elif self.engine.player.power_generator.energy <= 0:
            
            self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
            
        elif self.engine.player.docked:
            
            self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
        else:
            return MoveHandlerEasy(self.engine) if self.engine.easy_navigation else MoveHandler(self.engine)
            
    def shields(self, captain:str):
        
        self.warned_once = False
            
        if not self.engine.player.shield_generator.is_opperational:
            
            self.engine.message_log.add_message(f"Error: Shield systems are inoperative, {captain}.", fg=colors.red)

        elif self.engine.player.power_generator.energy <= 0:
            
            self.engine.message_log.add_message(f"Error: Insufficent energy reserves, {captain}.", fg=colors.red)
        #elif self.engine.player.docked:
        #    self.engine.message_log.add_message(f"Error: We undock first, {captain}.", fg=colors.red)
        else:
            return ShieldsHandler(self.engine)
            
    def repair(self):
        
        repair = RepairOrder(self.engine.player, 1)
        
        warning = repair.raise_warning()
        
        if self.warned_once:
            return repair
        try:
            self.engine.message_log.add_message(misc_warnings[warning], fg=colors.orange)
            self.warned_once = True
            
        except KeyError:
            
            return repair
            
    def transporters(self):
        
        if not self.engine.player.ship_can_transport:
                
            self.engine.message_log.add_message(
                f"Transporters are offline, {self.engine.player.nation.captain_rank_name}", fg=colors.red
            )
        else:
            return TransporterHandler(self.engine)
        
    def on_render(self, console: tcod.Console) -> None:
        captain = self.engine.player.ship_class.nation.captain_rank_name
        
        super().on_render(console)

        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title=f"Your orders, {captain}?"
        )
        try:
            is_at_warp = self.engine.player.warp_drive.is_at_warp
        except AttributeError:
            is_at_warp = False
        
        if is_at_warp:
            
            self.warp_travel.render(console)
        else:
            if self.engine.player.is_mobile:
                self.warp_button.render(console)
                self.move_button.render(console)
                self.dock_button.render(console)
                
            self.shields_button.render(console)
            
            if self.ship_type_can_fire_beam_arrays:
                self.beam_button.render(console)
                
            if self.ship_type_can_fire_cannons:
                self.cannons_buttons.render(console)
                
            self.repair_button.render(console)
            
            if self.ship_type_can_fire_torps:
                self.torpedos_button.render(console)
                
            self.auto_destruct_button.render(console)
            
            if self.ship_type_can_cloak:
                self.cloak_button.render(console)
            
            if self.ship_is_not_automated:
                self.transporter_button.render(console)
        
class WarpHandler(HeadingBasedHandler):

    def __init__(self, engine: Engine) -> None:
        super().__init__(engine, engine.player.warp_drive.is_opperational)
        
        self.distance = distance_button(
            limit=3,
            max_value=CONFIG_OBJECT.max_warp_distance,
            min_value=1
        )
        self.energy_cost = round(
            self.distance.add_up() * SECTOR_ENERGY_COST * WARP_FACTOR[1][1]
        )
        self.cost_button:SimpleElement = cost_button(cost=f"{self.energy_cost}")
        
        self.warp_speed = speed_button(round(9 * self.engine.player.warp_drive.get_effective_value))
        
        self.is_at_warp = self.engine.player.warp_drive.is_at_warp
        
    def on_render(self, console: tcod.Console) -> None:
                
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input warp heading and distance"
        )
        if self.is_at_warp:
            print_system(console, self.engine.game_data)
            print_mega_sector(console, self.engine.game_data)
            render_own_ship_info(console, self.engine.game_data)

            render_other_ship_info(console, self.engine.game_data, self.engine.game_data.selected_ship_planet_or_star)

            print_message_log(console, self.engine.game_data)
            render_position(console, self.engine.game_data)
            self.cancel_button.render(console)
        else:
            super().on_render(console)
            
            self.distance.render(console)
            
            self.cost_button.render(console)
            
            self.warp_speed.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
        if not self.is_at_warp:
            if self.confirm_button.cursor_overlap(event):
                if self.engine.player.warp_drive.is_at_warp:
                    return CommandEventHandler(self.engine)
                
                warp_order = WarpOrder.from_heading(
                    self.engine.player, heading=self.heading_button.add_up(), distance=self.distance.add_up(),
                    speed=self.warp_speed.add_up(), 
                    start_x=self.engine.player.sector_coords.x, start_y=self.engine.player.sector_coords.y
                )
                warning = warp_order.raise_warning()
                try:
                    self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
                except KeyError:
                
                    if warning == OrderWarning.SAFE:
                        self.is_at_warp = True
                        return warp_order
                finally:
                    self.can_render_confirm_button = self.engine.player.warp_drive.is_opperational
                
            elif self.heading_button.cursor_overlap(event):
                self.selected_handeler = self.heading_button
                self.heading_button.is_active = True
                self.distance.is_active = False
                self.warp_speed.is_active = False
            elif self.distance.cursor_overlap(event):
                self.selected_handeler = self.distance
                self.heading_button.is_active = False
                self.distance.is_active = True
                self.warp_speed.is_active = False
            elif self.warp_speed.cursor_overlap(event):
                self.selected_handeler = self.warp_speed
                self.heading_button.is_active = False
                self.distance.is_active = False
                self.warp_speed.is_active = True
            else:
                super().ev_mousebuttondown(event)
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if not self.is_at_warp:
            if event.sym in confirm:
                if self.engine.player.is_at_warp:
                    
                    return CommandEventHandler(self.engine)
                
                warp_order = WarpOrder.from_heading(
                    self.engine.player, self.heading_button.add_up(), self.distance.add_up(),
                    speed=self.warp_speed.add_up(), 
                    start_x=self.engine.player.sector_coords.x, start_y=self.engine.player.sector_coords.y
                )
                warning = warp_order.raise_warning()
                try:
                    self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
                except KeyError:
                
                    if warning == OrderWarning.SAFE:
                        self.is_at_warp = True
                        return warp_order
                finally:
                    self.can_render_confirm_button = self.engine.player.warp_drive.is_opperational
            else:
                self.selected_handeler.handle_key(event)
                
                if self.selected_handeler in {self.distance, self.warp_speed}:
                    
                    warp_speed, cost =  WARP_FACTOR[self.warp_speed.add_up()]
                    
                    self.energy_cost = round(
                        self.distance.add_up() * cost * SECTOR_ENERGY_COST
                    )
                    self.cost_button.text = f"{self.energy_cost}"
                
class WarpHandlerEasy(CoordBasedHandler):

    def __init__(self, engine: Engine) -> None:
        sector_coords = engine.game_data.player.sector_coords
        super().__init__(
            engine,
            can_render_confirm_button=engine.player.warp_drive.is_opperational,
            max_x=CONFIG_OBJECT.sector_width,
            max_y=CONFIG_OBJECT.sector_height,
            starting_x=sector_coords.x,
            starting_y=sector_coords.y
        )
        self.energy_cost = round(
            self.engine.player.sector_coords.distance(x=self.x_button.add_up(),y=self.y_button.add_up()) * 
            self.engine.player.warp_drive.affect_cost_multiplier * SECTOR_ENERGY_COST
        )
        self.cost_button:SimpleElement = cost_button(f"{self.energy_cost}")
        
        self.warp_speed = speed_button(
            round(9 * self.engine.player.warp_drive.get_effective_value)
        )
        self.is_at_warp = self.engine.player.warp_drive.is_at_warp
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input warp coordants"
        )
        if self.is_at_warp:
            print_system(console, self.engine.game_data)
            print_mega_sector(console, self.engine.game_data)
            render_own_ship_info(console, self.engine.game_data)

            render_other_ship_info(console, self.engine.game_data, self.engine.game_data.selected_ship_planet_or_star)

            print_message_log(console, self.engine.game_data)
            render_position(console, self.engine.game_data)
            self.cancel_button.render(console)
        else:
            super().on_render(console)
            
            self.cost_button.render(console)
            
            self.warp_speed.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
        if not self.is_at_warp:
            if self.x_button.cursor_overlap(event):
                self.selected_handeler = self.x_button
                self.x_button.is_active = True
                self.y_button.is_active = False
                self.warp_speed.is_active = False
            elif self.y_button.cursor_overlap(event):
                self.selected_handeler = self.y_button
                self.x_button.is_active = False
                self.y_button.is_active = True
                self.warp_speed.is_active = False
            elif self.warp_speed.cursor_overlap(event):
                self.selected_handeler = self.warp_speed
                self.x_button.is_active = False
                self.y_button.is_active = False
                self.warp_speed.is_active = True
            elif self.confirm_button.cursor_overlap(event):
                if self.is_at_warp:
                    return CommandEventHandler(self.engine)
                
                warp_order = WarpOrder.from_coords(
                    self.engine.player, x=self.x_button.add_up(), y=self.y_button.add_up(), 
                    speed=self.warp_speed.add_up(), 
                    start_x=self.engine.player.sector_coords.x, start_y=self.engine.player.sector_coords.y
                )
                warning = warp_order.raise_warning()
                try:
                    self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
                except KeyError:
                        
                    if warning == OrderWarning.SAFE:
                        self.is_at_warp = True
                        return warp_order
                finally:
                    self.can_render_confirm_button = self.engine.player.warp_drive.is_opperational
            else:
                x, y = select_sector_space(event)

                if x is not False and y is not False:
                    
                    self.x_button.set_text(x)
                    self.y_button.set_text(y)
                    
                    self.energy_cost = round(
                        self.engine.player.sector_coords.distance(x=self.x_button.add_up(),y=self.y_button.add_up()) * 
                        self.engine.player.warp_drive.affect_cost_multiplier * SECTOR_ENERGY_COST
                    )
                    self.cost_button.text = f"{self.energy_cost}"
                else:
                    super().ev_mousebuttondown(event)
                
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            
            return CommandEventHandler(self.engine)
        
        if not self.is_at_warp:
            if event.sym in confirm:
                if self.engine.player.is_at_warp:
                    return CommandEventHandler(self.engine)
                
                warp_order = WarpOrder.from_coords(
                    self.engine.player, x=self.x_button.add_up(), y=self.y_button.add_up(), speed=self.warp_speed.add_up(),
                    start_x=self.engine.player.sector_coords.x, start_y=self.engine.player.sector_coords.y
                )
                warning = warp_order.raise_warning()
                try:
                    self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
                except KeyError:
                        
                    if warning == OrderWarning.SAFE:
                        self.is_at_warp = True
                        return warp_order
                finally:
                    self.can_render_confirm_button = self.engine.player.warp_drive.is_opperational
            else:
                self.selected_handeler.handle_key(event)
                
                _distance = self.engine.player.sector_coords.distance(x=self.x_button.add_up(),y=self.y_button.add_up())
                warp_speed, cost =  WARP_FACTOR[self.warp_speed.add_up()]
                self.energy_cost = round(
                    cost * _distance * SECTOR_ENERGY_COST
                )
                self.cost_button.text = f"{self.energy_cost}"

class MoveHandler(HeadingBasedHandler):

    def __init__(self, engine: Engine) -> None:
        
        player = engine.player
        
        super().__init__(engine, can_render_confirm_button=player.impulse_engine.is_opperational)
        
        self.distance_button = distance_button(
            limit=3, max_value=CONFIG_OBJECT.max_move_distance, min_value=1,
        )
        self.energy_cost = round(
            self.distance_button.add_up() * LOCAL_ENERGY_COST * player.impulse_engine.affect_cost_multiplier
        )
        self.cost_button = cost_button(f"{self.energy_cost}")
        
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
            
        elif self.confirm_button.cursor_overlap(event) and self.can_render_confirm_button:
            
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
            finally:
                self.can_render_confirm_button = self.engine.player.impulse_engine.is_opperational

        elif self.cancel_button.cursor_overlap(event):
            return CommandEventHandler(self.engine)
        super().ev_mousebuttondown(event)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm and not self.heading_button.is_empty and not self.distance_button.is_empty and self.can_render_confirm_button:
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
            finally:
                self.can_render_confirm_button = self.engine.player.impulse_engine.is_opperational
        else:
            self.selected_handeler.handle_key(event)
            
            self.warned_once = False
            
            if self.selected_handeler is self.distance_button:
            
                self.energy_cost = round(
                    self.distance_button.add_up() * LOCAL_ENERGY_COST * 
                    self.engine.player.impulse_engine.affect_cost_multiplier
                )
                self.cost_button.text = f"{self.energy_cost}"
        
class MoveHandlerEasy(CoordBasedHandler):

    def __init__(self, engine: Engine) -> None:
        
        local_coords = engine.game_data.player.local_coords
        player = engine.player
        
        super().__init__(
            engine, can_render_confirm_button=engine.player.impulse_engine.is_opperational,
            starting_x=local_coords.x, starting_y=local_coords.y,
            max_x=CONFIG_OBJECT.sector_width,
            max_y=CONFIG_OBJECT.sector_height
        )
        self.energy_cost = round(
            player.local_coords.distance(x=self.x_button.add_up(), y=self.y_button.add_up()) * LOCAL_ENERGY_COST * 
            player.impulse_engine.affect_cost_multiplier
        )
        self.cost_button = cost_button(cost=f"{self.energy_cost}")
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Input move coordants"
        )
        super().on_render(console)
        
        self.cost_button.render(
            console
        )
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            
            return CommandEventHandler(self.engine)
            
        elif self.confirm_button.cursor_overlap(event) and self.engine.player.impulse_engine.is_opperational:
            
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
            finally:
                self.can_render_confirm_button = self.engine.player.impulse_engine.is_opperational
        else:
            x,y = select_sub_sector_space(event)

            if x is not False and y is not False:
                
                self.x_button.set_text(x)
                self.y_button.set_text(y)
                self.warned_once = False
                self.energy_cost = round(
                    self.engine.player.local_coords.distance(x=self.x_button.add_up(), y=self.y_button.add_up()) * 
                    LOCAL_ENERGY_COST * self.engine.player.impulse_engine.affect_cost_multiplier
                )
                self.cost_button.text = f"{self.energy_cost}"
            else:
                super().ev_mousebuttondown(event)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm and self.engine.player.impulse_engine.is_opperational:
            
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
            finally:
                self.can_render_confirm_button = self.engine.player.impulse_engine.is_opperational
        else:
            self.selected_handeler.handle_key(event)
            self.energy_cost = round(
                self.engine.player.local_coords.distance(
                    x=self.x_button.add_up(), y=self.y_button.add_up()) * LOCAL_ENERGY_COST
            )
            self.cost_button.text = f"{self.energy_cost}"
            
            self.warned_once = False
            
class ShieldsHandler(MinMaxInitator):

    def __init__(self, engine: Engine) -> None:
        
        player = engine.player
        
        super().__init__(
            engine, can_render_confirm_button=player.shield_generator.is_opperational,
            starting_value=player.shield_generator.shields,
            max_value=min(player.shield_generator.shields + player.power_generator.energy, player.shield_generator.get_max_effective_shields)
        )
        self.shield_status = BooleanBox(
            x=18+CONFIG_OBJECT.command_display_x,
            y=10+CONFIG_OBJECT.command_display_y,
            height=3,
            width=8,
            title="Shields",
            active_text="Up", inactive_text="Down",
            active_fg=colors.green, inactive_fg=colors.red,
            bg=colors.black,
            initally_active=True
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
        self.shield_status.render(console)
        
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:

        if self.max_button.cursor_overlap(event):
            
            self.amount_button.set_text(self.amount_button.max_value)
            
        elif self.min_button.cursor_overlap(event):
            
            self.amount_button.set_text(0)
            
        elif self.shield_status.cursor_overlap(event):
            
            self.shield_status.is_active = not self.shield_status.is_active
            self.warned_once = False

        elif self.confirm_button.cursor_overlap(event):
            
            recharge_order = RechargeOrder(
                self.engine.player, self.amount_button.add_up(), self.shield_status.is_active
            )

            warning = recharge_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return recharge_order
            try:
                self.engine.message_log.add_message(blocks_action[warning], colors.red)
                self.warned_once = False
                
            except KeyError:
                
                if self.warned_once:
                    return recharge_order
                
                self.engine.message_log.add_message(misc_warnings[warning], colors.orange)
                self.warned_once = True
            
        elif self.cancel_button.cursor_overlap(event):

            return CommandEventHandler(self.engine)

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return CommandEventHandler(self.engine)
        if event.sym in confirm:
            recharge_order = RechargeOrder(
                self.engine.player, self.amount_button.add_up(), self.shield_status.is_active
            )

            warning = recharge_order.raise_warning()

            if warning == OrderWarning.SAFE:
                return recharge_order
            try:
                self.engine.message_log.add_message(blocks_action[warning], colors.red)
                self.warned_once = False
            except KeyError:
                
                if self.warned_once:
                    return recharge_order
                
                self.engine.message_log.add_message(misc_warnings[warning], colors.orange)
                self.warned_once = True
        else:
            self.amount_button.handle_key(event)
            self.warned_once = False

class TransporterHandler(MinMaxInitator):
    
    def __init__(self, engine: Engine) -> None:
        max_value=engine.player.crew.able_crew
        super().__init__(
            engine, can_render_confirm_button=engine.player.transporter.is_opperational,
            max_value=max_value, 
            starting_value=0
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Transporter Controls:"
        )
        super().on_render(console)
    
    def ev_mousebuttondown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:
        
        if self.max_button.cursor_overlap(event):
            
            self.amount_button.set_text(self.amount_button.max_value)
            
        elif self.min_button.cursor_overlap(event):
            
            self.amount_button.set_text(self.amount_button.min_value)
            
        elif self.confirm_button.cursor_overlap(event):
            
            if not self.engine.player.transporter.is_opperational:
                self.engine.message_log.add_message(
                    f"The transporters are off line, {self.engine.player.nation.captain_rank_name}.", colors.red
                )
                return
            
            selected = self.engine.game_data.selected_ship_planet_or_star
            
            if isinstance(selected, Starship):
                
                order = TransportOrder(self.engine.player, selected, self.amount_button.add_up())
                
                warning = order.raise_warning()
                
                try:
                    self.engine.message_log.add_message(blocks_action[warning], colors.red)
                except KeyError:
                
                    if warning == OrderWarning.SAFE:
                        
                        return order
                finally:
                    self.can_render_confirm_button = self.engine.player.transporter.is_opperational
            else:
                self.engine.message_log.add_message(
                    f"No spacecraft is selected, {self.engine.player.nation.captain_rank_name}.", colors.red
                )
        elif self.cancel_button.cursor_overlap(event):
            
            return CommandEventHandler(self.engine)
        
        ship_planet_or_star = select_ship_planet_star(self.engine.game_data, event)
    
        if (isinstance(
            
            ship_planet_or_star, Starship
            
        ) and ship_planet_or_star is not self.engine.player and 
            
            ship_planet_or_star is not self.engine.game_data.selected_ship_planet_or_star
        ):
            self.engine.game_data.ship_scan = ship_planet_or_star.scan_for_print(self.engine.player.sensors.determin_precision)
            
            self.engine.game_data.selected_ship_planet_or_star = ship_planet_or_star
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:
        
        if event.sym in confirm:
            
            if not self.engine.player.transporter.is_opperational:
                self.engine.message_log.add_message(
                    f"The transporters are off line, {self.engine.player.nation.captain_rank_name}.", colors.red
                )
                return
            
            selected = self.engine.game_data.selected_ship_planet_or_star
            
            if isinstance(selected, Starship):
                
                order = TransportOrder(self.engine.player, selected, self.amount_button.add_up())
                
                warning = order.raise_warning()
                try:
                    self.engine.message_log.add_message(blocks_action[warning], colors.red)
                except KeyError:
                
                    if warning == OrderWarning.SAFE:
                        
                        return order
                finally:
                    self.can_render_confirm_button = self.engine.player.transporter.is_opperational
            else:
                self.engine.message_log.add_message(
                    f"No spacecraft is selected, {self.engine.player.nation.captain_rank_name}.", colors.red
                )
        elif event.sym == tcod.event.K_ESCAPE:
            
            return CommandEventHandler(self.engine)
        
        self.amount_button.handle_key(event)
            
class BeamArrayHandler(MinMaxInitator):

    def __init__(self, engine: Engine) -> None:
        player = engine.player
        super().__init__(
            engine, can_render_confirm_button=player.ship_can_fire_beam_arrays,
            max_value=player.get_max_effective_beam_firepower,
            starting_value=0
        )
        self.auto_target_button = auto_target_button()
        
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
        
        self.auto_target_button.render(console)

        self.fire_all_button.render(console)

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
                    
                    self.engine.game_data.ship_scan = ship.scan_for_print(self.engine.player.sensors.determin_precision)
                    
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
            try:
                self.engine.message_log.add_message(
                    blocks_action[warning], colors.red
                )
            except KeyError:
                if warning == OrderWarning.SAFE:
                    self.amount_button.max_value = min(
                        self.engine.player.get_max_effective_beam_firepower, self.engine.player.power_generator.energy
                    )
                    if self.amount_button.add_up() > self.amount_button.max_value:
                        self.amount_button.set_text(self.amount_button.max_value)
                    return fire_order
            finally:
                self.can_render_confirm_button = self.engine.player.ship_can_fire_beam_arrays
            
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
            self.engine.game_data.ship_scan = ship_planet_or_star.scan_for_print(self.engine.player.sensors.determin_precision)
            
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
            try:
                self.engine.message_log.add_message(
                    blocks_action[warning], colors.red
                )
            except KeyError:
                if warning == OrderWarning.SAFE:
                    self.amount_button.max_value = min(
                        self.engine.player.get_max_effective_beam_firepower, self.engine.player.power_generator.energy
                    )
                    if self.amount_button.add_up() > self.amount_button.max_value:
                        self.amount_button.set_text(self.amount_button.max_value)
                    return fire_order
            finally:
                self.can_render_confirm_button = self.engine.player.ship_can_fire_beam_arrays
        else:
            self.amount_button.handle_key(event)

class CannonHandler(MinMaxInitator):

    def __init__(self, engine: Engine) -> None:
        
        player = engine.player
        
        super().__init__(
            engine, can_render_confirm_button=player.ship_can_fire_cannons,
            max_value=min(player.get_max_effective_cannon_firepower, player.power_generator.energy),
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
        
        self.auto_target_button.render(console)

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
                    
                    self.engine.game_data.ship_scan = ship.scan_for_print(self.engine.player.sensors.determin_precision)
                    
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
            try:
                self.engine.message_log.add_message(
                    blocks_action[warning], colors.red
                )
            except:
                if warning == OrderWarning.SAFE:
                    self.amount_button.max_value = min(
                        self.engine.player.get_max_effective_cannon_firepower, self.engine.player.power_generator.energy
                    )
                    if self.amount_button.add_up() > self.amount_button.max_value:
                        self.amount_button.set_text(self.amount_button.max_value)
                    return fire_order
            finally:
                self.can_render_confirm_button = self.engine.player.ship_can_fire_cannons
            
        elif self.cancel_button.cursor_overlap(event):

            return CommandEventHandler(self.engine)
        
        ship_planet_or_star = select_ship_planet_star(self.engine.game_data, event)
        
        if (isinstance(
            
            ship_planet_or_star, Starship
            
        ) and ship_planet_or_star is not self.engine.player and 
            
            ship_planet_or_star is not self.engine.game_data.selected_ship_planet_or_star
        ):
            self.engine.game_data.ship_scan = ship_planet_or_star.scan_for_print(self.engine.player.sensors.determin_precision)
            
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
            try:
                self.engine.message_log.add_message(
                    blocks_action[warning], colors.red
                )
            except:
                if warning == OrderWarning.SAFE:
                    self.amount_button.max_value = min(
                        self.engine.player.get_max_effective_cannon_firepower, self.engine.player.power_generator.energy
                    )
                    if self.amount_button.add_up() > self.amount_button.max_value:
                        self.amount_button.set_text(self.amount_button.max_value)
                    return fire_order
            finally:
                self.can_render_confirm_button = self.engine.player.ship_can_fire_cannons
        else:
            self.amount_button.handle_key(event)

class TorpedoHandler(HeadingBasedHandler):

    def __init__(self, engine: Engine) -> None:
        
        player = engine.player
        
        super().__init__(engine, can_render_confirm_button=player.shield_generator.is_opperational)
        
        self.number_button = torpedo_number_button(
            max_value=player.ship_class.torp_tubes
        )
        torpedos = player.ship_class.allowed_torpedos_tuple
        
        self.torpedo_select = torpedo_select_button(
            index_items=[
                name.cap_name for name in torpedos
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
                key:Torpedo = self.torpedo_select.index_key
                                
                self.engine.player.torpedo_launcher.torpedo_loaded = key
                
                cap_name = key.cap_name
                
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
                        game_data.ship_scan = ship_planet_or_star.scan_for_print(game_data.player.sensors.determin_precision)
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
        player = engine.player

        super().__init__(
            engine, can_render_confirm_button=player.ship_can_fire_torps,
            max_x=CONFIG_OBJECT.subsector_width,
            max_y=CONFIG_OBJECT.subsector_height,
            starting_x=local_coords.x,
            starting_y=local_coords.y
        )
        self.number_button = torpedo_number_button(
            max_value=player.ship_class.torp_tubes
        )
        torpedos = player.torpedo_launcher.torps.keys()
        
        self.torpedo_select = torpedo_select_button(
            index_items=[
                t.cap_name for t in torpedos
            ],
            keys=tuple(torpedos)
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
            
        elif self.confirm_button.cursor_overlap(event) and self.engine.player.ship_can_fire_torps:
            
            torpedo_order = TorpedoOrder.from_coords(
                self.engine.player, self.number_button.add_up(), self.x_button.add_up(), self.y_button.add_up()
            )
            warning = torpedo_order.raise_warning()
            
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                
                if warning == OrderWarning.SAFE or not self.engine.torpedo_warning or self.warned_once:
                    return torpedo_order
                
                self.engine.message_log.add_message(torpedo_warnings[warning], fg=colors.orange)
                self.warned_once = True
            finally:
                self.can_render_confirm_button = self.engine.player.ship_can_fire_torps
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
                        game_data.ship_scan = ship_planet_or_star.scan_for_print(game_data.player.sensors.determin_precision)
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
            torpedo_order = TorpedoOrder.from_coords(self, self.x_button.add_up(), self.y_button.add_up())
            warning = torpedo_order.raise_warning()
            
            try:
                self.engine.message_log.add_message(blocks_action[warning], fg=colors.red)
            except KeyError:
                
                if warning == OrderWarning.SAFE or not self.engine.torpedo_warning or self.warned_once:
                    return torpedo_order
                
                self.engine.message_log.add_message(torpedo_warnings[warning], fg=colors.orange)
                self.warned_once = True
            finally:
                self.can_render_confirm_button = self.engine.player.ship_can_fire_torps
        else:
            self.selected_handeler.handle_key(event)
                
class SelfDestructHandler(CancelConfirmHandler):

    def __init__(self, engine: Engine) -> None:
        
        super().__init__(engine, can_render_confirm_button=True)
        
        player = engine.player
        
        self.code = self.engine.game_data.auto_destruct_code
        
        nearbye_ships = [
            ship for ship in engine.game_data.grab_ships_in_same_sub_sector(
                player, accptable_ship_statuses={
                    STATUS_ACTIVE, STATUS_DERLICT, STATUS_HULK, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED
                }
            )
        ]
        self.all_nearbye_ships = tuple(nearbye_ships)
        
        nearbye_detectable_ships_and_distances = [
            (
                ship, ship.local_coords.distance(coords=player.local_coords)
            ) for ship in nearbye_ships if ship.ship_status not in {STATUS_CLOAKED, STATUS_HULK}
        ]
        nearbye_detectable_ships_and_distances.sort(
            key=lambda distance: distance[1]
        )
        self.nearbye_active_foes = [
            (ship, distance) for ship, distance in nearbye_detectable_ships_and_distances if 
            ship.ship_status in {STATUS_CLOAK_COMPRIMISED, STATUS_ACTIVE} and 
            ship.nation is not self.engine.player.nation
        ]
        self.nearbye_active_friends = [
            (ship, distance) for ship, distance in nearbye_detectable_ships_and_distances if 
            ship.ship_status in {STATUS_CLOAK_COMPRIMISED, STATUS_ACTIVE, STATUS_CLOAKED} and 
            ship.nation is self.engine.player.nation
        ]
        self.nearbye_derlicts = [
            (ship, distance) for ship, distance in nearbye_detectable_ships_and_distances if 
            ship.ship_status is STATUS_DERLICT
        ]
        y_foes = len(self.nearbye_active_foes)
        
        self.any_foes_nearby = y_foes > 0
        
        self.y_foes_begin = 7
        
        y_friends = len(self.nearbye_active_friends)
        
        self.any_friends_nearby = y_friends > 0
        
        self.y_friends_begin = self.y_foes_begin + 2

        self.any_ship_nearbye = self.any_friends_nearby or self.any_foes_nearby

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
        if not self.any_foes_nearby:
            console.print(
                x=2+CONFIG_OBJECT.command_display_x,
                y=self.y_foes_begin+CONFIG_OBJECT.command_display_y,
                string="Warning: No enemy ships in system"
            )
        if self.any_ship_nearbye:
            if self.any_foes_nearby:
                console.print(
                    x=2+CONFIG_OBJECT.command_display_x,
                    y=self.y_foes_begin+CONFIG_OBJECT.command_display_y,
                    string="Enemy ships in system:"
                )
                for i, ship_info in enumerate(self.nearbye_active_foes):
                    ship, distance = ship_info
                    console.print(
                        x=2+CONFIG_OBJECT.command_display_x,
                        y=i+self.y_foes_begin+1+CONFIG_OBJECT.command_display_y,
                        string=f"{ship.name: <10}  {distance: <.2f}"
                    )
            if self.any_friends_nearby:
                
                console.print(
                    x=2+CONFIG_OBJECT.command_display_x,
                    y=self.y_friends_begin+CONFIG_OBJECT.command_display_y,
                    string="Allied ships in system:"
                )
                for i, ship_info in enumerate(self.nearbye_active_friends):
                    ship, distance = ship_info
                    console.print(
                        x=2+CONFIG_OBJECT.command_display_x,
                        y=i+self.y_friends_begin+1+CONFIG_OBJECT.command_display_y,
                        string=f"{ship.name: <10}  {distance: <.2f}"
                    )
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:

        if event.sym == tcod.event.K_CANCEL:
            
            return CommandEventHandler(self.engine)

        if event.sym in confirm:

            if self.code_handler.text_to_print == self.code:
                
                if self.warned_once:

                    return SelfDestructOrder(self.engine.player)
                
                self.warned_once = True
                if self.any_friends_nearby:
                    self.engine.message_log.add_message(
                        f"Warning: There are friendly ships nearbye that may be caught in the blast.", colors.orange
                    )
                elif not self.any_foes_nearby:
                    self.engine.message_log.add_message(
                        f"Warning: There are not hostile friendly ships nearbye.", colors.orange
                    )
                else:
                    self.engine.message_log.add_message(
                        f"Warning: Confirm self destruct?", colors.orange
                    )
            else:
                self.engine.message_log.add_message(
                    f"Error: The code for the self destruct is not correct.", colors.red
                )
        else:
        
            self.code_handler.handle_key(event)
            self.warned_once = False
            #self.code_handler.text = self.code_handler.text_to_print

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            
            return CommandEventHandler(self.engine)
        
        if self.confirm_button.cursor_overlap(event):
            
            if self.code_handler.text_to_print == self.code:

                if self.warned_once:

                    return SelfDestructOrder(self.engine.player)
                
                self.warned_once = True
                if self.any_friends_nearby:
                    self.engine.message_log.add_message(
                        f"Warning: There are friendly ships nearbye that may be caught in the blast.", colors.orange
                    )
                elif not self.any_foes_nearby:
                    self.engine.message_log.add_message(
                        f"Warning: There are not hostile friendly ships nearbye.", colors.orange
                    )
                else:
                    self.engine.message_log.add_message(
                        f"Warning: Confirm self destruct?", colors.orange
                    )
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
        
        text, self.evaluation = self.engine.game_data.scenerio.scenario_type.generate_evaluation(
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
            return ScoreHandler(self.engine, self.evaluation)
    
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[BaseEventHandler]:

        if event.sym in confirm or event.sym == tcod.event.K_s:
            return ScoreHandler(self.engine, self.evaluation)
        self.text_box.handle_key(event)

class ScoreHandler(EventHandler):
            
    def __init__(self, engine: Engine, evaluation: List[Tuple[str,str,Tuple[int,int,int]]]) -> None:
        super().__init__(engine)
        
        self.descriptions = [s[0] for s in evaluation]
        self.scores = [s[1] for s in evaluation]
        self.score_colors = [s[2] for s in evaluation]
        
        self.description_width = max(len(d) for d in self.descriptions)
        self.scores_width = max(len(s) for s in self.scores)
        
        self.evaluation_length = len(evaluation)
        
        self.evaluation_description_text = "\n".join([
            f"{a:>{self.description_width}}" for a in self.descriptions
        ])
        
    def on_render(self, console: tcod.Console) -> None:
        #self.evalu.render(console)
        
        console.draw_frame(
            x=5, y=5, 
            width=self.description_width + self.scores_width + 2,
            height=self.evaluation_length + 2
        )
        console.print_box(
            x=5+1,
            y=5+1,
            width=self.description_width,
            height=self.evaluation_length,
            string=self.evaluation_description_text
        )
        for s, sc, i in zip(self.scores, self.score_colors, range(self.evaluation_length)):
            
            console.print(
                x=5+1+self.description_width,
                y=5+1+i,
                string=s,
                fg=sc,
                bg=colors.black
            )
        
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

class DebugHandler(MainGameEventHandler):
    
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        self.place_ship = SimpleElement(
            x=CONFIG_OBJECT.command_display_x+2,
            y=CONFIG_OBJECT.command_display_y+3,
            height=3,
            width=12,
            text="(P)lace Ship"
        )
        self.edit_ship = BooleanBox(
            x=CONFIG_OBJECT.command_display_x+2,
            y=CONFIG_OBJECT.command_display_y+7,
            height=3,
            width=12,
            active_text="(E)dit Ship",
            inactive_text="(E)dit Ship",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=isinstance(self.engine.game_data.selected_ship_planet_or_star, Starship)
        )
        self.decloak_all = SimpleElement(
            x=CONFIG_OBJECT.command_display_x+2,
            y=CONFIG_OBJECT.command_display_y+11,
            height=3,
            text="(D)ecloak All",
            width=14,
        )
        self.cancel = SimpleElement(
            x=CONFIG_OBJECT.command_display_x+2,
            y=CONFIG_OBJECT.command_display_y+22,
            height=3,
            width=12,
            text="Cancel"
        )
    
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Debug mode activated"
        )
        self.place_ship.render(console)
        self.edit_ship.render(console)
        self.decloak_all.render(console)
        self.cancel.render(console)
        
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:
        
        if event.sym == tcod.event.K_ESCAPE:
            
            return CommandEventHandler(self.engine)
        
        if event.sym == tcod.event.K_p:
            
            return ShipPlacement(self.engine)
        
        if event.sym == tcod.event.K_e and isinstance(self.engine.game_data.selected_ship_planet_or_star, Starship):
            
            return ShipEditing(self.engine, self.engine.game_data.selected_ship_planet_or_star)
        
        if event.sym == tcod.event.K_d:
            
            ships = self.engine.game_data.ships_in_same_sub_sector_as_player
            
            for ship in ships:
                
                if ship.ship_status == STATUS_CLOAKED:
                    
                    ship.cloak.cloak_status = CloakStatus.COMPRIMISED
    
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.cancel.cursor_overlap(event):
            
            return CommandEventHandler(self.engine)
        
        if self.place_ship.cursor_overlap(event):
            
            return ShipPlacement(self.engine)
        
        if self.edit_ship.cursor_overlap(event) and isinstance(
            self.engine.game_data.selected_ship_planet_or_star, Starship
        ):
            return ShipEditing(self.engine, self.engine.game_data.selected_ship_planet_or_star)
        
        elif self.decloak_all.cursor_overlap(event):
            
            ships = self.engine.game_data.ships_in_same_sub_sector_as_player
            
            for ship in ships:
                
                if ship.ship_status == STATUS_CLOAKED:
                    
                    ship.cloak.cloak_status = CloakStatus.COMPRIMISED
        else:
            ship = select_ship_planet_star(self.engine.game_data, event)
            
            if isinstance(ship, Starship):
                
                self.engine.game_data.ship_scan = ship.scan_for_print(1)
                
                self.engine.game_data.selected_ship_planet_or_star = ship
            
            self.edit_ship.is_active = isinstance(ship, Starship)
                
class ShipPlacement(MainGameEventHandler):
    
    def __init__(self, engine: Engine) -> None:
        super().__init__(engine)
        
        all_ship_names = [n.name for n in ALL_SHIP_CLASSES.values()]
        
        self.all_ships = Selector(
            x=CONFIG_OBJECT.command_display_x+16,
            y=CONFIG_OBJECT.command_display_y+2,
            width=(CONFIG_OBJECT.command_display_end_x - 2) - (CONFIG_OBJECT.command_display_x + 16),
            height=CONFIG_OBJECT.command_display_end_y - (CONFIG_OBJECT.command_display_y + 4),
            wrap_item=True,
            index_items=all_ship_names,
            keys=tuple(ALL_SHIP_CLASSES.keys()),
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=True
        )
        selected_ship_is_friendly = self.all_ships.index_key in self.engine.game_data.scenerio.allied_nations
        self.system_x = NumberHandeler(
            limit=2, 
            max_value=CONFIG_OBJECT.sector_width, min_value=0, 
            wrap_around=True, 
            starting_value=0,
            x=2+CONFIG_OBJECT.command_display_x,
            y=2+CONFIG_OBJECT.command_display_y,
            width=6,
            height=3,
            title="X:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT,
            initally_active=False
        )
        self.system_y = NumberHandeler(
            limit=2, 
            max_value=CONFIG_OBJECT.sector_height, min_value=0, 
            wrap_around=True, 
            starting_value=0,
            x=2+CONFIG_OBJECT.command_display_x+6,
            y=2+CONFIG_OBJECT.command_display_y,
            width=6,
            height=3,
            title="X:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT,
            initally_active=False
        )
        self.local_x = NumberHandeler(
            limit=2, 
            max_value=CONFIG_OBJECT.sector_width, min_value=0, 
            wrap_around=True, 
            starting_value=0,
            x=2+CONFIG_OBJECT.command_display_x,
            y=5+CONFIG_OBJECT.command_display_y,
            width=6,
            height=3,
            title="LX:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT,
            initally_active=False
        )
        self.local_y = NumberHandeler(
            limit=2, 
            max_value=CONFIG_OBJECT.sector_height, min_value=0, 
            wrap_around=True, 
            starting_value=0,
            x=2+CONFIG_OBJECT.command_display_x+6,
            y=5+CONFIG_OBJECT.command_display_y,
            width=6,
            height=3,
            title="LY:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            alignment=tcod.constants.RIGHT,
            initally_active=False
        )
        self.friendy_hostile = BooleanBox(
            x=2+CONFIG_OBJECT.command_display_x,
            y=8+CONFIG_OBJECT.command_display_y,
            height=3,
            width=13,
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black,
            title="New ship:",
            active_text="Allied",
            inactive_text="Hostile",
            initally_active=selected_ship_is_friendly
        )
        self.hull_percent = NumberHandeler(
            x=2+CONFIG_OBJECT.command_display_x,
            y=11+CONFIG_OBJECT.command_display_y,
            height=3,
            width=9,
            limit=4,
            title="Hull %:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            min_value=-49,
            max_value=100,
            starting_value=100,
            initally_active=False
        )
        self.ship_name = TextHandeler(
            x=2+CONFIG_OBJECT.command_display_x,
            y=14+CONFIG_OBJECT.command_display_y,
            height=3,
            width=8,
            limit=6,
            title="Name:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=False,
        )
        self.spawn_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=18+CONFIG_OBJECT.command_display_y,
            height=3,
            width=12,
            text="Spawn",
        )
        self.cancel_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=22+CONFIG_OBJECT.command_display_y,
            height=3,
            width=12, 
            text="Cancel"
        )
        self.selected_button = self.all_ships
    
    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Spawn ship:"
        )
        self.all_ships.render(console)
        self.system_x.render(console)
        self.system_y.render(console)
        self.local_x.render(console)
        self.local_y.render(console)
        self.friendy_hostile.render(console)
        self.hull_percent.render(console)
        self.ship_name.render(console)
        self.cancel_button.render(console)
        self.spawn_button.render(console)
    
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            
            return DebugHandler(self.engine)

        if self.spawn_button.cursor_overlap(event):
            
            self.spawn_ship()
        
        elif self.all_ships.cursor_overlap(event):
            
            self.all_ships.handle_click(event)
            
            ship_class_nation = ALL_SHIP_CLASSES[self.all_ships.index_key].nation
            
            self.friendy_hostile.is_active = ship_class_nation in self.engine.game_data.scenerio.get_set_of_allied_nations
            
            self.all_ships.is_active = True
            
            self.system_x.is_active = False
            
            self.system_y.is_active = False
            
            self.local_x.is_active = False
            
            self.local_y.is_active = False
            
            self.hull_percent.is_active = False
            
            self.ship_name.is_active = False
            
            self.selected_button = self.all_ships
        
        elif self.system_x.cursor_overlap(event):
            
            self.all_ships.is_active = False
            
            self.system_x.is_active = True
            
            self.system_y.is_active = False
            
            self.local_x.is_active = False
            
            self.local_y.is_active = False
            
            self.hull_percent.is_active = False
            
            self.ship_name.is_active = False
            
            self.selected_button = self.system_x
        
        elif self.system_y.cursor_overlap(event):
            
            self.all_ships.is_active = False
            
            self.system_x.is_active = False
            
            self.system_y.is_active = True
            
            self.local_x.is_active = False
            
            self.local_y.is_active = False
            
            self.hull_percent.is_active = False
            
            self.ship_name.is_active = False
            
            self.selected_button = self.system_y
        
        elif self.local_x.cursor_overlap(event):
            
            self.all_ships.is_active = False
            
            self.system_x.is_active = False
            
            self.system_y.is_active = False
            
            self.local_x.is_active = True
            
            self.local_y.is_active = False
            
            self.hull_percent.is_active = False
            
            self.ship_name.is_active = False
            
            self.selected_button = self.local_x
            
        elif self.local_y.cursor_overlap(event):
            
            self.all_ships.is_active = False
            
            self.system_x.is_active = False
            
            self.system_y.is_active = False
            
            self.local_x.is_active = False
            
            self.local_y.is_active = True
            
            self.hull_percent.is_active = False
            
            self.ship_name.is_active = False
            
            self.selected_button = self.local_y
        
        elif self.hull_percent.cursor_overlap(event):
            
            self.all_ships.is_active = False
            
            self.system_x.is_active = False
            
            self.system_y.is_active = False
            
            self.local_x.is_active = False
            
            self.local_y.is_active = False
            
            self.hull_percent.is_active = True
            
            self.ship_name.is_active = False
            
            self.selected_button = self.hull_percent
        
        elif self.ship_name.cursor_overlap(event):
            
            self.all_ships.is_active = False
            
            self.system_x.is_active = False
            
            self.system_y.is_active = False
            
            self.local_x.is_active = False
            
            self.local_y.is_active = False
            
            self.hull_percent.is_active = False
            
            self.ship_name.is_active = True
            
            self.selected_button = self.ship_name
            
        elif self.cancel_button.cursor_overlap(event):
            
            return DebugHandler(self.engine)
        
        if self.spawn_button.cursor_overlap(event):
            
            self.spawn_ship()
        else:
            x, y = select_sector_space(event)

            if x is not False and y is not False:
                
                self.system_x.set_text(x)
                self.system_y.set_text(y)
            else:
                x,y = select_sub_sector_space(event)
                
                if x is not False and y is not False:
                    
                    self.local_x.set_text(x)
                    self.local_y.set_text(y)
    
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:
        
        if event.sym == tcod.event.K_ESCAPE:
            
            return DebugHandler(self.engine)
        
        elif event.sym in confirm:
            
            self.spawn_ship()
        else:
            self.selected_button.handle_key(event)
            
            if self.selected_button is self.all_ships:
                
                ship_class_nation = ALL_SHIP_CLASSES[self.all_ships.index_key].nation
                
                self.friendy_hostile.is_active = ship_class_nation in self.engine.game_data.scenerio.get_set_of_allied_nations
        
    def spawn_ship(self):
        
        s_x, s_y = self.system_x.add_up(), self.system_y.add_up()
        l_x, l_y = self.local_x.add_up(), self.local_y.add_up()
        
        game_data = self.engine.game_data
        
        ships_in_same_sector = [
            ship for ship in game_data.total_starships if ship.sector_coords.x == s_x and 
            ship.sector_coords.y == s_y and ship.ship_status != STATUS_OBLITERATED
        ]
        for ship in ships_in_same_sector:
            
            if ship.local_coords.x == l_x and ship.local_coords.y == l_y:
                
                self.engine.message_log.add_message(
                    f"The selected ship spawn spot {l_x}, {l_y} in sector {s_x}, {s_y} is blocked by the ship {ship.name}.", colors.red
                )
                return
        
        sub_sector:SubSector = self.engine.game_data.grid[s_y][s_x]
        
        local_xy = Coords(x=l_x, y=l_y)
        
        if local_xy in sub_sector.safe_spots:
            
            ship_class:ShipClass = ALL_SHIP_CLASSES[self.all_ships.index_key]
        
            selected_ship_is_friendly = ship_class.nation in game_data.scenerio.allied_nations
            
            ship_is_mission_critical = ship_class in game_data.scenerio.mission_critical_ships
            
            ship_ai = game_data.allied_ai if selected_ship_is_friendly else game_data.difficulty
            
            name_ = self.ship_name.send()
            
            name = name_ if name_ else ship_class.nation.generate_ship_name(
                ship_class.nation.ship_names is None or ship_class.is_automated
            )
            new_ship = Starship(
                ship_class,
                ship_ai,
                xCo=l_x,
                yCo=l_y,
                secXCo=s_x,
                secYCo=s_y,
                name=name
            )
            new_ship.game_data = game_data
            
            new_ship.hull = round(ship_class.max_hull * self.hull_percent.add_up() * 0.01)
            
            if selected_ship_is_friendly:
                
                game_data.all_allied_ships.append(new_ship)
                
                if ship_is_mission_critical:
                    
                    game_data.target_allied_ships.append(new_ship)
            else:
                game_data.all_enemy_ships.append(new_ship)
                
                if ship_is_mission_critical:
                    
                    game_data.target_enemy_ships.append(new_ship)
                    
            game_data.all_other_ships.append(new_ship)
            game_data.total_starships.append(new_ship)
            
            game_data.update_mega_sector_display()
            
            if s_x == game_data.player.sector_coords.x and s_y == game_data.player.sector_coords.y:
                
                game_data.ships_in_same_sub_sector_as_player = game_data.grab_ships_in_same_sub_sector(
                    game_data.player, accptable_ship_statuses={
                        STATUS_ACTIVE, STATUS_CLOAK_COMPRIMISED, STATUS_CLOAKED, STATUS_DERLICT, STATUS_HULK
                    }
                )
                game_data.visible_ships_in_same_sub_sector_as_player = [
                    ship for ship in game_data.ships_in_same_sub_sector_as_player if ship.ship_status.is_visible
                ]
            self.engine.message_log.add_message(
                f"The new ship {name} has been created in system {s_x}, {s_y}, at position {l_x}, {l_y}.", colors.green
            )
        else:
            try:
                p = sub_sector.planets_dict[local_xy]
                
                self.engine.message_log.add_message(
                    "Unable to create the new ship as there is a planet in the way"
                )
            except KeyError:
                try:
                    s = sub_sector.stars_dict
                    
                    self.engine.message_log.add_message(
                        "Unable to create the new ship as there is a star in the way"
                    )
                except KeyError:
                    pass

class ShipEditing(MainGameEventHandler):
    
    def __init__(self, engine: Engine, ship:Starship) -> None:
        super().__init__(engine)
        
        self.ship = ship
        
        self.ship_name = TextHandeler(
            x=2+CONFIG_OBJECT.command_display_x,
            y=3+CONFIG_OBJECT.command_display_y,
            limit=14,
            height=3,
            width=16,
            title="Ship Name:",
            text_char_list=[c for c in ship.name],
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=True,
        )
        self.ship_hull = NumberHandeler(
            x=2+CONFIG_OBJECT.command_display_x,
            y=7+CONFIG_OBJECT.command_display_y,
            limit=4,
            height=3,
            width=7,
            title="Hull:",
            starting_value=ship.hull,
            max_value=ship.ship_class.max_hull - ship.hull_damage,
            min_value=round(-0.5 * ship.ship_class.max_hull),
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=False
        )
        self.ship_energy = NumberHandeler(
            x=11+CONFIG_OBJECT.command_display_x,
            y=7+CONFIG_OBJECT.command_display_y,
            limit=4,
            height=3,
            width=9,
            title="Energy:",
            starting_value=ship.power_generator.energy,
            max_value=ship.ship_class.max_energy,
            min_value=0,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=False
        )
        all_activatable_elements:List[InputHanderer] = [self.ship_name, self.ship_energy, self.ship_hull]
        try:
            self.ship_able_crew = NumberHandeler(
                x=2+CONFIG_OBJECT.command_display_x,
                y=11+CONFIG_OBJECT.command_display_y,
                limit=4,
                height=3,
                width=7,
                title="A. Crew:",
                starting_value=ship.crew.able_crew,
                max_value=ship.ship_class.max_crew - ship.crew.injured_crew,
                min_value=0,
                active_fg=colors.white,
                inactive_fg=colors.grey,
                bg=colors.black,
                initally_active=False
            )
            self.ship_injured_crew = NumberHandeler(
                x=11+CONFIG_OBJECT.command_display_x,
                y=11+CONFIG_OBJECT.command_display_y,
                limit=4,
                height=3,
                width=7,
                title="I. Crew:",
                starting_value=ship.crew.injured_crew,
                max_value=ship.ship_class.max_crew - ship.crew.able_crew,
                min_value=0,
                active_fg=colors.white,
                inactive_fg=colors.grey,
                bg=colors.black,
                initally_active=False
            )
            all_activatable_elements.append(self.ship_able_crew)
            all_activatable_elements.append(self.ship_injured_crew)
        except AttributeError:
            pass
        try:
            self.ship_shields = NumberHandeler(
                x=2+CONFIG_OBJECT.command_display_x,
                y=15+CONFIG_OBJECT.command_display_y,
                limit=4,
                height=3,
                title="Shields:",
                width=10,
                starting_value=ship.shield_generator.shields,
                max_value=self.ship.shield_generator.get_max_shields,
                min_value=0,
                active_fg=colors.white,
                inactive_fg=colors.grey,
                bg=colors.black,
                initally_active=False
            )
            all_activatable_elements.append(self.ship_shields)
        except AttributeError:
            pass
        try:
            self.cloak_cooldown = NumberHandeler(
                x=2+CONFIG_OBJECT.command_display_x,
                y=19+CONFIG_OBJECT.command_display_y,
                limit=2,
                height=3,
                title="C.C:",
                width=6,
                starting_value=self.ship.cloak.cloak_cooldown,
                max_value=self.ship.ship_class.cloak_cooldown,
                min_value=0,
                active_fg=colors.white,
                inactive_fg=colors.grey,
                bg=colors.black,
                initally_active=False
            )
            all_activatable_elements.append(self.cloak_cooldown)
        except AttributeError:
            pass
        self.active_element = self.ship_name
        
        self.all_activatable_elements = tuple(all_activatable_elements)
        
        self.confirm_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=18+CONFIG_OBJECT.command_display_y,
            height=3,
            width=12,
            text="Confirm",
        )
        self.cancel_button = SimpleElement(
            x=2+CONFIG_OBJECT.command_display_x,
            y=22+CONFIG_OBJECT.command_display_y,
            height=3,
            width=12, 
            text="Cancel"
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        super().on_render(console)
        render_command_box(
            console=console,
            gameData=self.engine.game_data,
            title="Edit ship:"
        )
        self.ship_name.render(console)
        self.ship_hull.render(console)
        self.ship_energy.render(console)
        try:
            self.ship_able_crew.render(console)
            self.ship_injured_crew.render(console)
        except AttributeError:
            pass
        try:
            self.ship_shields.render(console)
        except AttributeError:
            pass
        self.cancel_button.render(console)
        self.confirm_button.render(console)
    
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[OrderOrHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            
            return DebugHandler(self.engine)
        try:
            if self.ship_able_crew.cursor_overlap(event):
                
                self.active_element = self.ship_able_crew
                
                for e in self.all_activatable_elements:
                    
                    e.is_active = e is self.ship_able_crew
                return
            elif self.ship_injured_crew.cursor_overlap(event):
                
                self.active_element = self.ship_injured_crew
                
                for e in self.all_activatable_elements:
                    
                    e.is_active = e is self.ship_injured_crew
                return
        except AttributeError:
            pass
        try:
            if self.ship_shields.cursor_overlap(event):
                
                self.active_element = self.ship_shields
                
                for e in self.all_activatable_elements:
                    
                    e.is_active = e is self.ship_shields
                return
        except AttributeError:
            pass
        try:
            if self.cloak_cooldown.cursor_overlap(event):
                
                self.active_element = self.cloak_cooldown
                
                for e in self.all_activatable_elements:
                    
                    e.is_active = e is self.cloak_cooldown
                return
        except AttributeError:
            pass
        
        if self.ship_name.cursor_overlap(event):
            
            self.active_element = self.ship_name
            
            for e in self.all_activatable_elements:
                    
                e.is_active = e is self.ship_name
                
        elif self.ship_hull.cursor_overlap(event):
            
            self.active_element = self.ship_hull
            
            for e in self.all_activatable_elements:
                    
                e.is_active = e is self.ship_hull
                
        elif self.ship_energy.cursor_overlap(event):
            
            self.active_element = self.ship_energy
            
            for e in self.all_activatable_elements:
                    
                e.is_active = e is self.ship_energy
        
        elif self.confirm_button.cursor_overlap(event):
            
            self.assign_values()
            
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[OrderOrHandler]:
        
        if event.sym == tcod.event.K_ESCAPE:
            
            return DebugHandler(self.engine)
        
        if event.sym in confirm:
            
            self.assign_values()
        else:
            self.active_element.handle_key(event)
        
    def assign_values(self):
        
        self.ship.hull = self.ship_hull.add_up()
        self.ship.power_generator.energy = self.ship_energy.add_up()
        self.ship.name = self.ship_name.send()
        try:
            self.ship.crew.able_crew = self.ship_able_crew.add_up()
            self.ship.crew.injured_crew = self.ship_injured_crew.add_up()
        except AttributeError:
            pass
        try:
            self.ship.shield_generator.shields = self.ship_shields.add_up()
        except AttributeError:
            pass
        try:
            self.ship.cloak.cloak_cooldown = self.cloak_cooldown.add_up()
        except AttributeError:
            pass
        self.engine.game_data.ship_scan = self.ship.scan_for_print(1)
        