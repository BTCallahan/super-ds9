from __future__ import annotations
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING, Union
import tcod

from coords import Coords
from space_objects import Planet, Star, SubSector
from starship import Starship
from data_globals import STATUS_HULK, CloakStatus
import colors
from get_config import CONFIG_OBJECT
from torpedo import ALL_TORPEDO_TYPES

if TYPE_CHECKING:
    from tcod import Console
    from game_data import GameData

#sys_width = config_object.subsector_width * 2 - 1
#sys_height = config_object.subsector_height * 2 - 1

def create_grid():

    st1 = " " + ("| " * (CONFIG_OBJECT.subsector_width - 1))

    st2 = "-" + ("+-" * (CONFIG_OBJECT.subsector_width - 1))

    st3 = st2 + "\n" + st1

    st4 = [st1] + [st3 for s in range(CONFIG_OBJECT.subsector_height - 1)]

    st5 = "\n".join(st4)
    
    return st5

GRID = create_grid()

def print_system(console:Console, gamedata:GameData):

    x = CONFIG_OBJECT.subsector_display_x
    y = CONFIG_OBJECT.subsector_display_y
    width = CONFIG_OBJECT.subsector_width
    heigth = CONFIG_OBJECT.subsector_height

    player = gamedata.player
    
    console.print_box(
        x=x+1,
        y=y+1,
        width=width * 2,
        height=heigth * 2,
        string=GRID,
        fg=colors.blue,
    )
    
    console.draw_frame(
        x=x + (player.local_coords.x * 2),
        y=y + (player.local_coords.y * 2),
        width=3,
        height=3,
        fg=colors.yellow,
        clear=False
    )
    
    if player.game_data.selected_ship_planet_or_star is not None:
        
        selected = player.game_data.selected_ship_planet_or_star
        
        console.draw_frame(
            x=x + (selected.local_coords.x * 2),
            y=y + (selected.local_coords.y * 2),
            height=3,
            width=3,
            fg=colors.orange,
            clear=False
        )

    console.draw_frame(
        x=x,
        y=y,
        width=width * 2 + 1,
        height=heigth * 2 + 1,
        title="System",
        clear=False
        )

    sector:SubSector = player.get_sub_sector

    for c, star in sector.stars_dict.items():

        console.print(
            x=x + (c.x * 2) + 1, 
            y=y + (c.y * 2) + 1, 
            string="*", 
        fg=star.color,bg=star.bg
        )

    ships = gamedata.visible_ships_in_same_sub_sector_as_player
    
    #number_of_ships = len(ships)

    for c, planet in sector.planets_dict.items():
        
        console.print(
            x=x + (c.x * 2) + 1, 
            y=y + (c.y * 2) + 1, 
            string="#", 
            fg=planet.planet_habbitation.color
        )

    for s in ships:
        if s.ship_status.is_visible:
            
            """
            console.draw_frame(
                x=x + (s.local_coords.x * 2),
                y=y + (s.local_coords.y * 2), 
                width=3,
                height=3,
                fg=colors.white
            )
            """
            
            console.print(
                x=x + (s.local_coords.x * 2) + 1, 
                y=y + (s.local_coords.y * 2) + 1, 
                string=s.ship_class.symbol, 
                fg=s.ship_status.override_color if s.ship_status.override_color else s.ship_class.nation.nation_color
            )
    
    console.print(
        x=x + (player.local_coords.x * 2) + 1, 
        y=y + (player.local_coords.y * 2) + 1, 
        string=player.ship_class.symbol, fg=colors.lime)
    
def print_mega_sector(console:Console, gamedata:GameData):
    """
*--------------
|+0*1 +1*1
|+0C5 +0C0
|+0F2 +0F0
|


"""
    x = CONFIG_OBJECT.sector_display_x
    y = CONFIG_OBJECT.sector_display_y

    sector_width=CONFIG_OBJECT.sector_width
    sector_height=CONFIG_OBJECT.sector_height

    player_coords = gamedata.player.sector_coords

    console.draw_frame(x=x, y=y, width=1+sector_width*5, height=1+sector_height*4, title="Systems", clear=False)

    console.draw_frame(x=player_coords.x * 5, y=player_coords.y * 4, width=6, height=5)

    for i, sector_y in enumerate(gamedata.grid):
        for j, sector_x in enumerate(sector_y):
            i2 = i * 4 + 1
            j2 = j * 5 + 1

            console.print(
                x=x+j2, y=y+i2,
                string=f"*{sector_x.total_stars}", fg=colors.yellow
            )
            if sector_x.barren_planets + sector_x.unfriendly_planets > 0:
                console.print(
                    x=x+j2, y=y+i2+1,
                    string=f"+{sector_x.barren_planets + sector_x.unfriendly_planets}", fg=colors.planet_barren
                )
            if sector_x.friendly_planets > 0:
                console.print(
                    x=x+j2, y=y+i2+2,
                    string=f"+{sector_x.friendly_planets}", fg=colors.planet_allied
                )
            hostile_ships = sector_x.display_hostile_ships
            
            if hostile_ships > 0:
                console.print(
                    x=x+j2+2, y=y+i2,
                    string=f"E{hostile_ships}", fg=colors.red if hostile_ships > 0 else colors.cyan
                )
            allied_ships = sector_x.display_allied_ships

            if allied_ships > 0:
                console.print(
                    x=x+j2+2, y=y+i2+1,
                    string=f"F{allied_ships}", fg=colors.green if allied_ships > 0 else colors.cyan
                )
            if sector_x.objectives:
                
                console.print(
                    x=x+j2+2, y=y+i2+2,
                    string=f"M{sector_x.objectives}", fg=colors.cyan
                )
            
def get_system_color(percentage:float, reverse:bool):

    if reverse:
        if percentage < 0.1:
            return colors.green
        if percentage < 0.25:
            return colors.lime
        if percentage < 0.5:
            return colors.yellow
        
        return colors.orange if percentage < 0.75 else  colors.red

    else:
        if percentage > 0.9:
            return colors.green
        if percentage > 0.75:
            return colors.lime
        if percentage > 0.5:
            return colors.yellow

        return colors.orange if percentage > 0.25 else  colors.red

def print_ship_info(
    console:Console, 
    x:int, y:int, 
    width:int, height:int,
    self:Starship, 
    scan:Dict[str,Any],
    precision:int):

    #scan = self.scan_this_ship(precision)

    #info = OrderedDict()

    #info["shields"]
    
    ship_status = self.ship_status
    
    #assert ship_status.is_visible
    
    try:
        cloak_is_on = self.cloak.cloak_is_turned_on
    except AttributeError:
        cloak_is_on = False
    
    frame_fg = (
        colors.cloaked if self is self.game_data.player and cloak_is_on else colors.white
    )
    console.draw_frame(
        x=x, y=y, 
        width=width, height=height, 
        title=self.proper_name,
        fg=frame_fg, bg=colors.black
    )
    console.print(
        x=x+2, y=y+2,
        string=f"Position: {self.local_coords.x}, {self.local_coords.y}", fg=colors.white
    )
    if ship_status == STATUS_HULK:
        
        console.print_box(
            x+2, y=y+3,
            width=width - 4,
            height=4,
            string=f"Remains of the {self.proper_name}", fg=colors.white
        )
    else:
        add_to_y = 4
        
        for i, n, d, c, m in zip(
            range(3), 
            (
                "Shields:", "Hull:", "Energy:"
            ),
            (
                scan['shields'][0],
                scan['hull'][0],
                scan['energy'][0]
            ),
            (
                scan['shields'][1],
                scan['hull'][1],
                scan['energy'][1]
            ),
            (
                self.ship_class.max_shields,
                self.ship_class.max_hull,
                self.ship_class.max_energy, 
            )
        ):
            console.print(x=x+3, y=y+i+add_to_y, string=f"{n:>16}", fg=colors.white)
            console.print(x=x+3+16, y=y+i+add_to_y, string=f"{d: =4}", fg=c)
            console.print(x=x+3+16+4, y=y+i+add_to_y, string=f"/{m: =4}", fg=colors.white)
        try:
            hd, hc = scan["hull_damage"]
            n = "Perm. Hull Dam.:"
            add_to_y+=1
            console.print(x=x+3, y=y+i+add_to_y, string=f"{n:>16}", fg=colors.white)
            console.print(x=x+3+16, y=y+i+add_to_y, string=f"{hd: =4}", fg=hc)
            
        except KeyError:
            pass
        
        add_to_y+=3
        
        if not self.ship_class.is_automated:
            try:
                injured_crew_amount = scan['injured_crew'][0]
                injured_crew_color = scan['injured_crew'][1]
                r=2
            except KeyError:
                injured_crew_amount=0
                injured_crew_color=colors.white
                r=1
                
            for i, n, d, c, m in zip(
                range(r), 
                (
                    "Able Crew:", "Injured Crew:"
                ),
                (
                    scan['able_crew'][0],
                    injured_crew_amount
                ),
                (
                    scan['able_crew'][1],
                    injured_crew_color
                ),
                (
                    self.ship_class.max_crew,
                    self.ship_class.max_crew
                )
            ):
                console.print(x=x+3, y=y+i+add_to_y, string=f"{n:>16}", fg=colors.white)
                console.print(x=x+3+16, y=y+i+add_to_y, string=f"{d: =4}", fg=c)
                console.print(x=x+3+16+4, y=y+i+add_to_y, string=f"/{m: =4}", fg=colors.white)
            add_to_y += r
            
        if self.ship_type_can_cloak:
            d_n = scan["cloak_cooldown"][0]
            d_c = scan["cloak_cooldown"][1]
            m = self.ship_class.cloak_cooldown
            console.print(x=x+3, y=y+add_to_y, string=f"{'C. Cooldown:':>16}", fg=colors.white)
            console.print(x=x+3+16, y=y+add_to_y, string=f"{d_n: =4}", fg=d_c)
            console.print(x=x+3+16+4, y=y+add_to_y, string=f"/{m: =4}", fg=colors.white)
            add_to_y+=1
        
        add_to_y+=1
        
        if self.ship_class.ship_type_can_fire_torps:
            max_torps = self.ship_class.max_torpedos 
            console.print(
                x=x+3+2, y=y+add_to_y, string=f"Torpedo Tubes:{self.ship_class.torp_tubes: =2}", fg=colors.white
            )
            '''
            console.print(
                x=x+3+3, y=y+add_to_y+1, string=f"Max Torpedos:{max_torps: =2}", fg=colors.white
            )
            '''
            add_to_y+=1
            for i, t in enumerate(self.ship_class.torp_dict.keys()):
                console.print(
                    x=x+3, y=y+add_to_y, 
                    string=f"{t.cap_name + ':':>16}", fg=colors.white
                )
                console.print(
                    x=x+3+16, y=y+add_to_y,
                    string=f"{self.torpedo_launcher.torps[t]: =2}", fg=scan["torpedo_color"]
                )
                console.print(
                    x=x+3+16+4, y=y+add_to_y, 
                    string=f"/{max_torps: =2}", fg=colors.white
                )
                
                add_to_y+=1
        
        names, keys = self.ship_class.system_names, self.ship_class.system_keys

        add_to_y+=1
        
        sys_x_position = (width - 2) // 2

        console.print(x=x+sys_x_position, y=y+add_to_y, string="-- Systems --", alignment=tcod.CENTER, fg=colors.white)
        
        add_to_y+=1
        
        for n, k, i in zip(names, keys, range(len(keys))):

            scanned = scan[k][0]
            scan_color = scan[k][1]
            #k = keys[i-(s+3)]
            #n__n = f"{n:>17}"
            n__n = scan[k][2]
            s__s = f"{scanned}"
            console.print(x=x+3, y=y+i+add_to_y, string=f"{n__n}", fg=colors.white)
            console.print(x=x+3+17, y=y+i+add_to_y, string=f"{s__s}", fg=scan_color)
    
def render_own_ship_info(console: Console, gamedata:GameData):

    start_x = CONFIG_OBJECT.your_ship_display_x
    start_y = CONFIG_OBJECT.your_ship_display_y
    width = CONFIG_OBJECT.your_ship_display_end_x - CONFIG_OBJECT.your_ship_display_x
    height = CONFIG_OBJECT.your_ship_display_end_y - CONFIG_OBJECT.your_ship_display_y

    print_ship_info(
        console=console,
        x=start_x,
        y=start_y,
        width=width,
        height=height,
        self=gamedata.player, 
        scan=gamedata.player_scan,
        precision=1)

def render_other_ship_info(console: Console, gamedata:GameData, ship:Optional[Starship]=None):

    start_x = CONFIG_OBJECT.other_ship_display_x
    start_y = CONFIG_OBJECT.other_ship_display_y
    width = CONFIG_OBJECT.other_ship_display_end_x - CONFIG_OBJECT.other_ship_display_x
    height = CONFIG_OBJECT.other_ship_display_end_y - CONFIG_OBJECT.other_ship_display_y
    
    ship_planet_or_star = gamedata.selected_ship_planet_or_star

    if ship_planet_or_star:

        if isinstance(ship_planet_or_star, Starship):

            if not gamedata.ship_scan:
                
                gamedata.ship_scan = gamedata.selected_ship_planet_or_star.scan_for_print(
                    gamedata.player.sensors.determin_precision
                )

            print_ship_info(
                console=console,
                x=start_x,
                y=start_y,
                width=width,
                height=height,
                self=ship_planet_or_star, 
                scan=gamedata.ship_scan,
                precision=gamedata.player.sensors.determin_precision
            )

        elif isinstance(ship_planet_or_star, Planet):

            console.draw_frame(
                x=start_x,
                y=start_y,
                width=width,
                height=height,
                title="Planet"
            )
            console.print(
                x=start_x+3,
                y=start_y+4,
                string=f"Planet at {ship_planet_or_star.local_coords.x}, {ship_planet_or_star.local_coords.y}"
            )
            planet_status = ship_planet_or_star.planet_habbitation.description

            console.print_box(
                x=start_x+3,
                y=start_y+6,
                width=width-6,
                height=6,
                string=f"Planet status: {planet_status}\n\nPlanet development: {ship_planet_or_star.infastructure:.3}"
            )
        elif isinstance(ship_planet_or_star, Star):

            console.draw_frame(
                x=start_x,
                y=start_y,
                width=width,
                height=height,
                title="Star"
            )
            x, y = ship_planet_or_star.local_coords.x, ship_planet_or_star.local_coords.y
            
            console.print_rect(
                x=start_x+3,
                y=start_y+4,
                string=f"{ship_planet_or_star.name} star at {x}, {y}",
                height=4,
                width=width - (3 + 2)
            )
    else:
        console.draw_frame(
        x=start_x, y=start_y, 
        width=width, height=height, 
        title="No Ship/Planet Selected"
    )

def print_message_log(console: Console, gamedata:GameData):

    gamedata.engine.message_log.render_messages(
        console=console,
        x=CONFIG_OBJECT.message_display_x,
        y=CONFIG_OBJECT.message_display_y,
        width=CONFIG_OBJECT.message_display_end_x - CONFIG_OBJECT.message_display_x,
        height=CONFIG_OBJECT.message_display_end_y - CONFIG_OBJECT.message_display_y,
        messages=gamedata.engine.message_log.messages
    )

def render_command_box(console: Console, gameData:GameData, title:str):

    console.draw_frame(
        x=CONFIG_OBJECT.command_display_x,
        y=CONFIG_OBJECT.command_display_y,
        width=CONFIG_OBJECT.command_display_end_x - CONFIG_OBJECT.command_display_x,
        height=CONFIG_OBJECT.command_display_end_y - CONFIG_OBJECT.command_display_y,
        title=title
    )

def render_position(console: Console, gameData:GameData):
    
    w = CONFIG_OBJECT.position_info_end_x - CONFIG_OBJECT.position_info_x
    h = CONFIG_OBJECT.position_info_end_y - CONFIG_OBJECT.position_info_y
    
    console.draw_frame(
        x=CONFIG_OBJECT.position_info_x,
        y=CONFIG_OBJECT.position_info_y,
        width=w,
        height=h,
        title=gameData.condition.text,
        fg=gameData.condition.fg,
        bg=gameData.condition.bg
    )   
    console.print_box(
        x=CONFIG_OBJECT.position_info_x+1,
        y=CONFIG_OBJECT.position_info_y+1,
        string=f"Local pos: {gameData.player.local_coords}\nSystem pos: {gameData.player.sector_coords}\nStardate: {gameData.stardate}\nEnding stardate: {gameData.ending_stardate}\n{gameData.warp_factor}\n{gameData.shields_description}",
        width=w-2,
        height=h-2
    )
    
def select_ship_planet_star(game_data:GameData, event: "tcod.event.MouseButtonDown") -> Union[Planet, Star, Starship, bool]:
    """Attempts to select the ship, planet, or star that the player is clicking on. Otherwise, it returns a boolean value depending on weither the cursor was positioned over a system grid square.

    Args:
        game_data (GameData): The GameData object.
        event (tcod.event.MouseButtonDown): The event containing the location of the click.

    Returns:
        Union[Planet, Star, Starship, bool]: If the mouse cursor is over a ship, planet, or star, that object will be returned. If not, then True will be returned. If the mouse cursor was not over a grid square, False will be returned.
    """

    x,y = CONFIG_OBJECT.subsector_display_x, CONFIG_OBJECT.subsector_display_y

    width, height = CONFIG_OBJECT.subsector_width, CONFIG_OBJECT.subsector_height

    x_range = range(x+1, x+2+width*2, 2)
    y_range = range(y+1, y+1+height*2, 2)

    if event.tile.x in x_range and event.tile.y in y_range:
        x_ajusted = (event.tile.x - (x + 1)) // 2
        y_ajusted = (event.tile.y - (y + 1)) // 2

        subsector = game_data.player.get_sub_sector
        co = Coords(x_ajusted, y_ajusted)
        try:
            planet = subsector.planets_dict[co]

            return planet
        except KeyError:
            try:
                star = subsector.stars_dict[co]
                
                return star
            except KeyError:
                
                for ship in game_data.ships_in_same_sub_sector_as_player:
                    if (
                        ship.local_coords.x == x_ajusted and ship.local_coords.y == y_ajusted and 
                        ship.ship_status.is_visible
                    ):
                        return ship
                return True
    else:
        return False

def select_sub_sector_space(event: "tcod.event.MouseButtonDown"):

    x,y = CONFIG_OBJECT.subsector_display_x, CONFIG_OBJECT.subsector_display_y

    width, height = CONFIG_OBJECT.subsector_width, CONFIG_OBJECT.subsector_height

    x_range = range(x+1, x+2+width*2, 2)
    y_range = range(y+1, y+1+height*2, 2)

    tile = event.tile

    if tile.x in x_range and tile.y in y_range:
        x_ajusted = (tile.x - (x + 1)) // 2
        y_ajusted = (tile.y - (y + 1)) // 2
        #print(f"{tile.x} {tile.y} {x_ajusted} {y_ajusted}")
        return x_ajusted, y_ajusted
    
    return False, False

def select_sector_space(event: "tcod.event.MouseButtonDown"):

    x,y = CONFIG_OBJECT.sector_display_x, CONFIG_OBJECT.sector_display_y

    width, height = CONFIG_OBJECT.sector_width, CONFIG_OBJECT.sector_height

    x_range = range(x+1, width*5+x+2)
    y_range = range(y+1, height*4+y+2)

    tile = event.tile

    if tile.x in x_range and tile.y in y_range:
        x_ajusted = (tile.x - (x + 1)) // 5
        y_ajusted = (tile.y - (y + 1)) // 4
        #print(f"{tile.x} {tile.y} {x_ajusted} {y_ajusted}")
        return x_ajusted, y_ajusted
    return False, False

def is_click_within_bounds(event: "tcod.event.MouseButtonDown", *, x:int, y:int, height:int, width:int):

    return x <= event.tile.x <= x + width and y <= event.tile.y <= y + height