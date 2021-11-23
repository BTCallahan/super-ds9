from __future__ import annotations
from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING
from functools import wraps, cache, lru_cache
import tcod

from coords import Coords
from space_objects import Planet, Star, SubSector
from starship import ShipStatus, Starship
from data_globals import PlanetHabitation, planet_habitation_color_dict
import colors
from get_config import config_object

if TYPE_CHECKING:
    from tcod import Console
    from game_data import GameData

planet_color_dict = {
    PlanetHabitation.PLANET_BARREN : colors.planet_barren,
    PlanetHabitation.PLANET_BOMBED_OUT : colors.planet_barren,
    PlanetHabitation.PLANET_HOSTILE : colors.planet_hostile,
    PlanetHabitation.PLANET_ANGERED : colors.planet_hostile,
    PlanetHabitation.PLANET_PREWARP : colors.planet_hostile,
    PlanetHabitation.PLANET_FRIENDLY : colors.planet_allied
}

def print_subsector(console:Console, gamedata:GameData):

    x = config_object.subsector_display_x
    y = config_object.subsector_display_y
    width = config_object.subsector_width
    heigth = config_object.subsector_height

    condition, condition_color = gamedata.condition_str, gamedata.condition_color

    player = gamedata.player
    
    console.draw_frame(
        x=x + (player.local_coords.x * 2),
        y=y + (player.local_coords.y * 2),
        width=3,
        height=3,
        fg=colors.yellow,
        clear=False
    )

    console.draw_frame(
        x=x,
        y=y,
        width=width * 2 + 2,
        height=heigth * 2 + 2,
        title=condition,
        fg=condition_color,
        bg=colors.black
        )

    sector:SubSector = player.get_sub_sector

    for c, star in sector.stars_dict.items():

        console.print(
            x=x + (c.x * 2) + 1, 
            y=y + (c.y * 2) + 1, 
            string="*", 
        fg=star.color
        )

    ships = gamedata.ships_in_same_sub_sector_as_player
    
    #number_of_ships = len(ships)

    for c, planet in sector.planets_dict.items():

        """
        planet_color = planet_color_dict[planet.planetType]
        if planet_color == colors.planet_allied and number_of_ships > 0:
            planet_color = colors.planet_frightened

        console.print(x=x+c.x, y=y+c.y, string="#", 
        fg=planet_color
        )
        """
        console.print(
            x=x + (c.x * 2) + 1, 
            y=y + (c.y * 2) + 1, 
            string="#", 
            fg=planet_habitation_color_dict[planet.planet_habbitation]
        )

    for s in ships:

        console.print(
            x=x + (s.local_coords.x * 2) + 1, 
            y=y + (s.local_coords.y * 2) + 1, 
            string=s.ship_data.symbol, 
            fg=colors.red if s.ship_status == ShipStatus.ACTIVE else colors.grey)
    
    console.print(
        x=x + (player.local_coords.x * 2) + 1, 
        y=y + (player.local_coords.y * 2) + 1, 
        string=player.ship_data.symbol, fg=colors.lime)
    
def print_mega_sector(console:Console, gamedata:GameData):
    """
*--------------
|+0*1 +1*1
|+0C5 +0C0
|+0F2 +0F0
|


"""
    x = config_object.sector_display_x
    y = config_object.sector_display_y

    sector_width=config_object.sector_width
    sector_height=config_object.sector_height

    player_coords = gamedata.player.sector_coords

    console.draw_frame(x=x, y=y, width=1+sector_width*5, height=1+sector_height*4, title="Sub-Sectors", clear=False)

    console.draw_frame(x=player_coords.x * 5, y=player_coords.y * 4, width=6, height=5)

    for i, sector_y in enumerate(gamedata.grid):
        for j, sector_x in enumerate(sector_y):
            i2 = i * 4 + 1
            j2 = j * 5 + 1

            if sector_x.barren_planets > 0:
                console.print(
                    x=x+j2, y=y+i2,
                    string=f"+{sector_x.barren_planets}", fg=colors.planet_barren
                )

            if sector_x.friendlyPlanets > 0:
                console.print(
                    x=x+j2, y=y+i2+1,
                    string=f"+{sector_x.friendlyPlanets}", fg=colors.planet_allied
                )

            if sector_x.unfriendlyPlanets > 0:
                console.print(
                    x=x+j2, y=y+i2+2,
                    string=f"+{sector_x.unfriendlyPlanets}", fg=colors.planet_hostile
                )

            console.print(
                x=x+j2+2, y=y+i2,
                string=f"*{sector_x.total_stars}", fg=colors.yellow
            )

            big_ships = sector_x.bigShips
            
            if big_ships > 0:
                console.print(
                    x=x+j2+2, y=y+i2+1,
                    string=f"C{big_ships}", fg=colors.red if big_ships > 0 else colors.cyan
                )

            small_ships = sector_x.smallShips

            if small_ships > 0:
                console.print(
                    x=x+j2+2, y=y+i2+2,
                    string=f"F{small_ships}", fg=colors.red if small_ships > 0 else colors.cyan
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

    console.draw_frame(
        x=x, y=y, 
        width=width, height=height, 
        title=self.name
    )

    y_plus = 2

    console.print(
        x=x+2, y=y+2,
        string=f"Position: {self.local_coords.x}, {self.local_coords.y}" 
    )

    for i, n, d, m in zip(
        range(4, 4+5), 
        (
            "Shields:", "Hull:", "Energy:", "Able Crew:", "Injured Crew:"
        ),
        (
            scan['shields'],
            scan['hull'],
            scan['energy'],
            scan['able_crew'],
            scan['injured_crew']
        ),
        (
            self.ship_data.max_shields,
            self.ship_data.max_hull,
            self.ship_data.max_energy, 
            self.ship_data.max_crew,
            self.ship_data.max_crew
        )
    ):
        console.print(x=x+2, y=y+i, string=f"{n:>16}{d: =4}/{m: =4}")

    from torpedo import ALL_TORPEDO_TYPES

    s = 11

    if self.ship_data.ship_type_can_fire_torps:
        max_torps = self.ship_data.max_torpedos 
        console.print(x=x+2, y=y+s, string=f"Torpedo Tubes: {self.ship_data.torp_tubes}" )
        console.print(x=x+2, y=y+s+1, string=f"Max Torps: {max_torps: =2}")
        s+=2
        for i, t in enumerate(self.ship_data.torp_types):
            console.print(x=x+2, y=y+s, string=f"{ALL_TORPEDO_TYPES[t].capName + ':':>16}{self.torps[t]: =2}"
            )
            s+=1
    
    names, keys = self.ship_data.system_names, self.ship_data.system_keys

    end = s+2

    console.print(x=x+2, y=y+end-1, string="-- Systems --")
    
    for n, k, i in zip(names, keys, range(len(keys))):

        scanned = scan[k]
        #k = keys[i-(s+3)]
        n__n = f"{n:>16}"
        s__s = f"{scanned:7.2%}"
        console.print(x=x+2, y=y+i+end, string=f"{n__n}{s__s}")
    
def render_own_ship_info(console: Console, gamedata:GameData):

    start_x = config_object.your_ship_display_x
    start_y = config_object.your_ship_display_y
    width = config_object.your_ship_display_end_x - config_object.your_ship_display_x
    height = config_object.your_ship_display_end_y - config_object.your_ship_display_y

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

    start_x = config_object.other_ship_display_x
    start_y = config_object.other_ship_display_y
    width = config_object.other_ship_display_end_x - config_object.other_ship_display_x
    height = config_object.other_ship_display_end_y - config_object.other_ship_display_y
    
    ship_planet_or_star = gamedata.selected_ship_planet_or_star

    if ship_planet_or_star:

        if isinstance(ship_planet_or_star, Starship):

            print_ship_info(
                console=console,
                x=start_x,
                y=start_y,
                width=width,
                height=height,
                self=ship_planet_or_star, 
                scan=gamedata.ship_scan,
                precision=gamedata.player.determin_precision
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

            planet_status = ""

            if ship_planet_or_star.infastructure == 0.0:

                planet_status = "Uninhabited"


            elif ship_planet_or_star.planet_habbitation == PlanetHabitation.PLANET_PREWARP:

                planet_status = "Pre-Warp"

            else:

                planet_status = "Hostile" if ship_planet_or_star.planet_habbitation in {PlanetHabitation.PLANET_ANGERED, PlanetHabitation.PLANET_HOSTILE} else "Friendly"

            console.print(
                x=start_x+3,
                y=start_y+6,
                string=f"Planet status: {planet_status}"
            )
        elif isinstance(ship_planet_or_star, Star):

            console.draw_frame(
                x=start_x,
                y=start_y,
                width=width,
                height=height,
                title="Star"
            )

            console.print_rect(
                x=start_x+3,
                y=start_y+4,
                string=f"{ship_planet_or_star.name} star at {ship_planet_or_star.local_coords.x}, {ship_planet_or_star.local_coords.y}",
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
        x=config_object.message_display_x,
        y=config_object.message_display_y,
        width=config_object.message_display_end_x - config_object.message_display_x,
        height=config_object.message_display_end_y - config_object.message_display_y,
        messages=gamedata.engine.message_log.messages
    )

def render_command_box(console: Console, gameData:GameData, title:str):

    console.draw_frame(
        x=config_object.command_display_x,
        y=config_object.command_display_y,
        width=config_object.command_display_end_x - config_object.command_display_x,
        height=config_object.command_display_end_y - config_object.command_display_y,
        title=title
    )

def render_position(console: Console, gameData:GameData):
    #console.draw_frame()
    console.draw_frame(
        x=config_object.position_info_x,
        y=config_object.position_info_y,
        width=config_object.position_info_end_x - config_object.position_info_x,
        height=config_object.position_info_end_y - config_object.position_info_y,
        
    )
    console.print(
        x=config_object.position_info_x+1,
        y=config_object.position_info_y+1,
        string= f"Local pos: {gameData.player.local_coords}"
    )
    console.print(
        x=config_object.position_info_x+1,
        y=config_object.position_info_y+2,
        string= f"Sector pos: {gameData.player.sector_coords}"
    )

    pass

def select_ship_planet_star(game_data:GameData, event: "tcod.event.MouseButtonDown") -> bool:

        x,y = config_object.subsector_display_x, config_object.subsector_display_y

        width, height = config_object.subsector_width, config_object.subsector_height

        x_range = range(x+1, x+2+width*2, 2)
        y_range = range(y+1, y+1+height*2, 2)

        if event.tile.x in x_range and event.tile.y in y_range:
            x_ajusted = (event.tile.x - (x + 1)) // 2
            y_ajusted = (event.tile.y - (y + 1)) // 2

            subsector = game_data.player.get_sub_sector
            co = Coords(x_ajusted, y_ajusted)
            try:
                planet = subsector.planets_dict[co]

                game_data.selected_ship_planet_or_star = planet

                return True
            except KeyError:
                try:
                    star = subsector.stars_dict[co]
                    game_data.selected_ship_planet_or_star = star
                    return True
                except KeyError:
                    
                    ships_in_same_sector = game_data.grab_ships_in_same_sub_sector(game_data.player)

                    for ship in ships_in_same_sector:
                        if ship.local_coords.x == x_ajusted and ship.local_coords.y == y_ajusted:
                            if game_data.selected_ship_planet_or_star is not ship:
                                game_data.selected_ship_planet_or_star = ship
                                game_data.ship_scan = ship.scan_this_ship(game_data.player.determin_precision)
                            #self.engine.game_data.selectedEnemyShip = ship
                            return True
        return False


def select_sub_sector_space(event: "tcod.event.MouseButtonDown"):

    x,y = config_object.subsector_display_x, config_object.subsector_display_y

    width, height = config_object.subsector_width, config_object.subsector_height

    x_range = range(x+1, x+2+width*2, 2)
    y_range = range(y+1, y+1+height*2, 2)

    tile = event.tile

    if tile.x in x_range and tile.y in y_range:
        x_ajusted = (tile.x - (x + 1)) // 2
        y_ajusted = (tile.y - (y + 1)) // 2
        print(f"{tile.x} {tile.y} {x_ajusted} {y_ajusted}")
        return x_ajusted, y_ajusted
    
    return False, False

def select_sector_space(event: "tcod.event.MouseButtonDown"):

    x,y = config_object.sector_display_x, config_object.sector_display_y

    width, height = config_object.sector_width, config_object.sector_height

    x_range = range(x+1, width*5+x+2)
    y_range = range(y+1, height*4+y+2)

    tile = event.tile

    if tile.x in x_range and tile.y in y_range:
        x_ajusted = (tile.x - (x + 1)) // 5
        y_ajusted = (tile.y - (y + 1)) // 4
        print(f"{tile.x} {tile.y} {x_ajusted} {y_ajusted}")
        return x_ajusted, y_ajusted
    return False, False

def is_click_within_bounds(event: "tcod.event.MouseButtonDown", *, x:int, y:int, height:int, width:int):

    return x <= event.tile.x <= x + width and y <= event.tile.y <= y + height