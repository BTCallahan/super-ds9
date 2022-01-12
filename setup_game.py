from collections import OrderedDict
from decimal import Decimal
from random import choice, randint
import re
from ai import BaseAi, EasyEnemy, HardEnemy, MediumEnemy
from engine import Engine
from get_config import CONFIG_OBJECT
from game_data import GameData
from typing import Final, Optional
import input_handelers
from nation import ALL_NATIONS
from scenario import ALL_SCENERIOS, Scenerio
import tcod, lzma, pickle
from tcod import constants
from textwrap import wrap
from tcod import console
from ui_related import BooleanBox, NumberHandeler, SimpleElement, TextHandeler, ButtonBox, Selector, confirm
import colors
from global_functions import stardate

multispace_pattern = re.compile(r"([ ]{2,})")

#singleline_pattern = re.compile(r"([^\n][\n][\n])")

singleline_pattern = re.compile(r"[^\n ] \n[^\n ]")

def set_up_help_text():

    with open("README.md") as readme:
        
        contents = readme.read()
    
    contents_1 = multispace_pattern.sub(
        repl="", string=contents
    )
    
    contents_2 = singleline_pattern.sub(
        repl=lambda matchobj: matchobj.group(0)[0] + matchobj.group(0)[3],
        string=contents_1
    )
    
    #ht2 = ht.splitlines()

    ht2 = contents_2.splitlines()

    width=CONFIG_OBJECT.screen_width - 4

    for h in ht2:
        if len(h) > width:
            for a in wrap(h, width=width, fix_sentence_endings=False, drop_whitespace=False):
                yield a
        else:
            yield h

HELP_TEXT = tuple(set_up_help_text())

def load_game(filename: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine

def set_up_game(
        *,
        easy_aim:bool, easy_move:bool, easy_warp:bool, torpedo_warning:bool, crash_warning:bool, three_d_movment:bool,
        ship_name:str, captain_name:str, scenario:Scenerio, difficulty:type[BaseAi]

    ):
    #print('beginning setup')
    #global GRID, PLAYER, TOTAL_STARSHIPS
    
    ships = OrderedDict()

    game_data = GameData(
        subsecs_x = CONFIG_OBJECT.sector_width,
        subsecs_y = CONFIG_OBJECT.sector_height,
        subsec_size_x = CONFIG_OBJECT.subsector_width,
        subsec_size_y = CONFIG_OBJECT.subsector_height,
        easy_aim = easy_aim,
        easy_move = easy_move,
        three_d_movment = three_d_movment,
        easy_warp = easy_warp,
        torpedo_warning = torpedo_warning,
        crash_warning = crash_warning,
        current_datetime = scenario.create_date_time(),
        starting_stardate = stardate(scenario.create_date_time()),
        ending_stardate = stardate(scenario.enddate),
        scenerio=scenario,
        difficulty=difficulty
    )

    engine = Engine(
        filename = "",
        player = game_data.player,
        easy_aim = easy_aim,
        easy_navigation = easy_move,
        easy_warp = easy_warp,
        torpedo_warning = torpedo_warning,
        crash_warning = crash_warning
    )

    engine.game_data = game_data

    game_data.engine = engine

    game_data.set_up_game(ship_name, captain_name)
    return engine

class StartupScreen(input_handelers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""

        console.print(x=console.width // 2 - 5, y=console.height // 2, string="SUPER DS9")
        console.print(x=console.width // 2 - 9, y=console.height // 2 + 2, string="Press any key to begin")

        
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:
        #print("Main menu")
        return MainMenu()
        #return Debug()

class Debug(input_handelers.BaseEventHandler):
    
    def __init__(self) -> None:
        
        self.number_handeler = NumberHandeler(
            limit=8,
            max_value=1200,
            min_value=50,
            wrap_around=True,
            starting_value=100,
            x=55,
            y=3,
            height=3,
            width=10,
            title="Numbers",
            alignment=constants.RIGHT,
            initally_active=True,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
        )
        
        t=wrap(
"This is a test of the wrap function. I am testing this is see why there are lines in the text. Turning \
off drop_whitespace has no effect, nor does turning off replace_whitespace, so at the moment I'm a bit \
stuck on what to do about the situation.", replace_whitespace=False
        )
        
        self.text_wrap_handler = SimpleElement(
            x=70, y=12, 
            height=15, width=25,
            text="\n".join(t),
            alignment=tcod.LEFT
        )
    
    def on_render(self, console: tcod.Console) -> None:
        
        hw = 12

        console.draw_frame(
            x=0,
            y=0,
            width=hw,
            height=hw,
            bg=(255, 0, 0),
            fg=(0, 255, 0),
            bg_blend=constants.BKGND_ADD,
            title="testDF", 
        )

        console.draw_frame(
            x=0,
            y=hw*2,
            width=hw,
            height=hw,
            bg_blend=constants.BKGND_ADD,
            title="testDF", 
        )

        console.draw_rect(
            x=hw,
            y=hw,
            width=hw,
            height=hw,
            bg=(255, 0, 0),
            fg=(0, 255, 0),
            bg_blend=constants.BKGND_ADD,
            ch=ord("A")
        )
        console.print_box(
            x=2*hw,
            y=0,
            width=hw,
            height=hw,
            string="testPB",
            bg=(255, 0, 0),
            fg=(0, 255, 0),
            bg_blend=constants.BKGND_ADD, 
            alignment=constants.RIGHT
        )

        console.print_box(
            x=2*hw,
            y=2*hw,
            width=hw,
            height=hw,
            string="testPB",

            bg_blend=constants.BKGND_ADD, 
            alignment=constants.RIGHT
        )

        console.print_frame(
            x=3*hw,
            y=hw,
            width=hw,
            height=hw,
            string="testPF",
            bg_blend=constants.BKGND_ADD,
        )
        console.print_rect(
            x=4*hw,
            y=0,
            width=hw,
            height=hw,
            string="testPR",
            bg_blend=constants.BKGND_ADD,
            alignment=constants.RIGHT,
        )

        a = Decimal(12.3 + 45 / 7193)

        s_str = f"{a}\n{a:.4}\n{a:.4g}\n{a:8.4}\n{a:=.4}\n{a:>.4}\n{a:<.4}\n{a:0.4}\n{a:2.4}\n{a:1.4}"

        console.print(
            x=3*hw,
            y=2*hw+14,
            string=s_str
        )
        
        self.number_handeler.render(
            console,
        )
        
        le = 5
        ma= "AAAaaa"
        console.print(
            x=60,y=45,
            string=f"{ma:>{le}}"
        )
        
        self.text_wrap_handler.render(console)
        
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:
        
        if event.sym == tcod.event.K_ESCAPE:
            return MainMenu()
        self.number_handeler.handle_key(event)

class MainMenu(input_handelers.BaseEventHandler):

    def __init__(self) -> None:
        
        ng = "(N)ew Game"
        ins = "(I)nstructions"
        qu = "(Q)uit"
        
        instructions_width = max([len(a) for a in (ng, ins, qu)])
        
        start_y = (CONFIG_OBJECT.screen_height // 2) - (9 // 2)
        start_x = (CONFIG_OBJECT.screen_width // 2) - (instructions_width // 2)
        
        self.new_game = SimpleElement(
            y=start_y,
            x=start_x,
            text=ng,
            active_fg=colors.white,
            bg=colors.black,
            height=3,
            width=instructions_width+2,
            alignment=tcod.CENTER
        )
        
        self.instructions = SimpleElement(
            y=start_y+3,
            x=start_x,
            text=ins,
            active_fg=colors.white,
            bg=colors.black,
            height=3,
            width=instructions_width+2,
            alignment=tcod.CENTER
        )
        
        self.quit = SimpleElement(
            y=start_y+6,
            x=start_x,
            text=qu,
            active_fg=colors.white,
            bg=colors.black,
            height=3,
            width=instructions_width+2,
            alignment=tcod.CENTER
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        self.new_game.render(console)
        
        self.instructions.render(console)
        
        self.quit.render(console)
        
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:
        #print("Key down")
        if event.sym == tcod.event.K_n:
            #print("New game")
            return SelectScenerio()
        elif event.sym == tcod.event.K_i:
            return Instructions()
        elif event.sym == tcod.event.K_q:
            raise SystemExit
    
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[input_handelers.BaseEventHandler]:
        if self.new_game.cursor_overlap(event):
            return SelectScenerio()
        if self.instructions.cursor_overlap(event):
            return Instructions()
        if self.quit.cursor_overlap(event):
            raise SystemExit
            
class Instructions(input_handelers.BaseEventHandler):

    def __init__(self) -> None:

        self.text = HELP_TEXT
        self._index = 0
        try:
            self.print_text = "\n".join(self.text[self._index : self._index + (CONFIG_OBJECT.screen_height - 8)])
        except IndexError:
            self.print_text = "\n".join(self.text[self._index : ])
                
        self.text_display = SimpleElement(
            x=2, y=2,
            width=CONFIG_OBJECT.screen_width - 4,
            height=CONFIG_OBJECT.screen_height - 8,
            title="Instructions",
            text=self.print_text, 
            alignment=tcod.LEFT
        )
        self.back_button = SimpleElement(
            x=2, y=CONFIG_OBJECT.screen_height-5,
            width=6, height=3,
            text="Back"
        )
        self._max_index = max(0, len(self.text) - (CONFIG_OBJECT.screen_height // 2))
    
    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value:int):
        old = self._index
        if value < 0:
            self._index = 0
        else:
            self._index = self._max_index if value > self._max_index else value
        if old != self._index:
            try:
                self.print_text = "\n".join(self.text[self._index : self._index + (CONFIG_OBJECT.screen_height - 8)])
            except IndexError:
                self.print_text = "\n".join(self.text[self._index : ])
            finally:
                self.text_display.text = self.print_text
            
    def on_render(self, console: tcod.Console) -> None:

        self.text_display.render(console)
        self.back_button.render(console)
    
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return MainMenu()
        if event.sym == tcod.event.K_UP:
            self.index -= 1
        elif event.sym == tcod.event.K_PAGEUP:
            self.index -= 50
        elif event.sym == tcod.event.K_DOWN:
            self.index += 1
        elif event.sym == tcod.event.K_PAGEDOWN:
            self.index += 50
    
    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[input_handelers.BaseEventHandler]:
        
        if self.back_button.cursor_overlap(event):
            return MainMenu()
    
class SelectScenerio(input_handelers.BaseEventHandler):

    TITLE = "Select Scenario"
    
    def __init__(self) -> None:
        self.select = 0
        
        self.max_select = len(ALL_SCENERIOS)
        names = tuple(s.name for s in ALL_SCENERIOS.values())
        keys = tuple(ALL_SCENERIOS.keys())
        
        self.title_box = Selector(
            x=10,
            y=4,
            width=26,
            height=CONFIG_OBJECT.screen_height - 8,
            index_items=names,
            keys=keys,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black
        )
        
        self.index_key = self.title_box.index_key
        
        self.cancel_button = SimpleElement(
            x=40,
            y=6,
            text="Cancel",
            width=8,
            height=3,
            active_fg=colors.white,
            bg=colors.black
        )
        
        self.confirm_button = SimpleElement(
            x=50,
            y=6,
            text="Confirm",
            width=10,
            height=3,
            active_fg=colors.white,
            bg=colors.black
        )
        
        scen = ALL_SCENERIOS[self.index_key]
        
        self.describe = SimpleElement(
            x=40,
            y=26,
            title="Description:",
            text=scen.description,
            width=40,
            height=12,
            alignment=tcod.LEFT,
            active_fg=colors.white,
            bg=colors.black
        )
        
    def on_render(self, console: tcod.Console) -> None:
        
        self.cancel_button.render(console)
        
        self.confirm_button.render(console)
        
        self.title_box.render(console)
            
        self.describe.render(console)
        
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:
        
        if event.sym == tcod.event.K_ESCAPE:
            
            return MainMenu()
        
        if event.sym in confirm:
            
            return NewGame(ALL_SCENERIOS[self.title_box.index_key])
        else:
            self.title_box.handle_key(event)
            self.index_key = self.title_box.index_key
            self.describe.text = ALL_SCENERIOS[self.index_key].description

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[input_handelers.BaseEventHandler]:
        
        if self.cancel_button.cursor_overlap(event):
            
            return MainMenu()
        
        if self.confirm_button.cursor_overlap(event):
            
            return NewGame(ALL_SCENERIOS[self.title_box.index_key])
        
        if self.title_box.cursor_overlap(event):
            
            self.title_box.handle_click(event)
            self.index_key = self.title_box.index_key
            self.describe.text = ALL_SCENERIOS[self.index_key].description
        
class NewGame(input_handelers.BaseEventHandler):

    TITLE = "Options"

    __all_okay:Final = ""

    __please_enter_ship_name:Final = "Please enter a name for your ship"
    
    __please_enter_captain_name:Final = "Please enter your name"
    
    __please_enter_both_names:Final = "Please enter your name and a name for your ship"

    def __init__(self, scenario:Optional[Scenerio]=None) -> None:
        
        self.scenario = scenario if scenario else ALL_SCENERIOS["DOM_STRIKE"]
        
        self.rand_ship_names = ALL_NATIONS[scenario.your_nation].ship_names
        
        self.ship_name = TextHandeler(
            limit=16, 
            text_char_list=list(self.scenario.default_ship_name),
            x=10,
            y=8,
            height=3,
            width=18,
            title="Ship Name:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=False,
        )
        
        self.captain_name = TextHandeler(
            limit=16, text_char_list=list(self.scenario.default_captain_name),
            x=32,
            y=8,
            height=3,
            width=18,
            title="Captain Name:",
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
        )
        
        self.warning_text = self.__all_okay
        
        self.new_game_button = SimpleElement(
            x=54,
            y=8,
            height=3,
            width=12,
            text="Okay"
        )

        self.cancel_button = SimpleElement(
            x=70,
            y=8,
            height=3,
            width=12,
            text="Cancel"
        )

        self.options_button = ButtonBox(
            x=6,
            y=15,
            height=38,
            width=76,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            title="Options",
            text="",
            initally_active=False
        )

        self.aim_button = BooleanBox(
            x=10,
            y=17,
            width=30,
            height=4,
            title="Easy (A)im",
            active_text="Aim torpedos by entering an x and y coord",
            inactive_text="Aim torpedos by entering a heading from 0 to 359",
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black,
            initally_active=False
        )
        
        self.random_ship_name_button = SimpleElement(
            x=45,
            y=17,
            height=3,
            width=30,
            title="(R)andom Ship Name",
            text="Randomly selects a ship name",
            active_fg=colors.white,
            bg=colors.black
        )
        
        self.difficulty = Selector(
            x=45, 
            y=22,
            width=30,
            height=5,
            active_fg=colors.white,
            inactive_fg=colors.grey,
            bg=colors.black,
            initally_active=True,
            title="Difficulty",
            index_items=("Easy", "Medium", "Hard"),
            wrap_item=False,
            keys=(EasyEnemy, MediumEnemy, HardEnemy)
        )

        self.warp_button = BooleanBox(
            x=10,
            y=22,
            width=30,
            height=4,
            title="Easy (W)arping",
            active_text="Warp ship by entering an x and y coord",
            inactive_text="Warp ship by entering a heading",
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black
        )

        self.move_button = BooleanBox(
            x=10,
            y=27,
            width=30,
            height=4,
            title="Easy (M)ovement",
            active_text="Navigate ship by entering an x and y coord",
            inactive_text="Navigate ship by entering a heading",
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black
        )

        self.three_d_movement_button = BooleanBox(
            x=10,
            y=32,
            width=30,
            height=7,
            title="3-(D) Movement",
            active_text="When moving via impulse, ships will only collide with another object only if it is in the same spot as their destination",
            inactive_text="When moving via impulse, ship will collide with any objects between them and their destination",
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black
        )

        self.warn_torpedo_button = BooleanBox(
            x=10,
            y=40,
            width=30,
            height=5,
            title="(T)orpedo Warnings",
            active_text="The player will be warned before firing on a populated planet",
            inactive_text="The player will not be warned before firing on a populated planet",
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black
        )

        self.warn_crash_button = BooleanBox(
            x=10,
            y=46,
            width=30,
            height=6,
            title="(C)rash Warnings",
            active_text="The player will be warned before entering a heading that will crash into an object",
            inactive_text="The player will not be warned before entering a heading that will crash into an object",
            active_fg=colors.green,
            inactive_fg=colors.red,
            bg=colors.black
        )
        
        self.text_handeler = self.captain_name

    def on_render(self, console: tcod.Console) -> None:

        self.captain_name.render(
            console,            
        )
        
        console.print_box(
            x=56,
            y=30,
            string=self.warning_text,
            width=20,
            height=4,
        )
        
        self.ship_name.render(
            console,
        )
        
        self.new_game_button.render(console)

        self.cancel_button.render(console)

        self.options_button.render(
            console,
        )
        
        self.random_ship_name_button.render(console)

        self.aim_button.render(
            console=console,
        )

        self.move_button.render(
            console=console,
        )
        
        self.warp_button.render(
            console=console,
        )

        self.three_d_movement_button.render(
            console=console,
        )

        self.warn_torpedo_button.render(
            console=console,
        )

        self.warn_crash_button.render(
            console=console,
        )
        
        self.difficulty.render(console=console)

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[input_handelers.BaseEventHandler]:

        if self.cancel_button.cursor_overlap(event):
            return MainMenu()

        if self.new_game_button.cursor_overlap(event):
            
            no_cap_name = self.captain_name.is_empty
            no_ship_name = self.ship_name.is_empty
            
            if no_cap_name:
                
                self.warning_text = self.__please_enter_both_names if no_ship_name else self.__please_enter_captain_name
                
            elif no_ship_name:
                
                self.warning_text = self.__please_enter_ship_name
            else:
                
                difficulty = self.difficulty.index_key
                
                return input_handelers.CommandEventHandler(
                    set_up_game(
                        easy_aim=self.aim_button.is_active,
                        easy_move=self.move_button.is_active,
                        easy_warp=self.warp_button.is_active,
                        torpedo_warning=self.warn_torpedo_button.is_active,
                        crash_warning=self.warn_crash_button.is_active,
                        three_d_movment=self.three_d_movement_button.is_active,
                        ship_name=self.ship_name.send(),
                        captain_name=self.captain_name.send(),
                        scenario=self.scenario,
                        difficulty=difficulty
                    )
                )

        if self.captain_name.cursor_overlap(event):
            
            self.text_handeler = self.captain_name
            
            self.options_button.is_active = False
            self.captain_name.is_active = True
            self.ship_name.is_active = False
            
        elif self.ship_name.cursor_overlap(event):
            self.text_handeler = self.ship_name
            
            self.options_button.is_active = False
            self.captain_name.is_active = False
            self.ship_name.is_active = True
        
        elif self.options_button.cursor_overlap(event):
            self.text_handeler = None
            self.options_button.is_active = True
            self.captain_name.is_active = False
            self.ship_name.is_active = False
            
            if self.move_button.cursor_overlap(event):
                
                self.move_button.is_active = not self.move_button.is_active
                
            elif self.warp_button.cursor_overlap(event):
                
                self.warp_button.is_active = not self.warp_button.is_active
                
            elif self.aim_button.cursor_overlap(event):
                
                self.aim_button.is_active = not self.aim_button.is_active
                
            elif self.three_d_movement_button.cursor_overlap(event):
                
                self.three_d_movement_button.is_active = not self.three_d_movement_button.is_active
                
            elif self.warn_torpedo_button.cursor_overlap(event):
                
                self.warn_torpedo_button.is_active = not self.warn_torpedo_button.is_active
                
            elif self.warn_crash_button.cursor_overlap(event):
                
                self.warn_crash_button.is_active = not self.warn_crash_button.is_active
                
            elif self.random_ship_name_button.cursor_overlap(event):
            
                self.ship_name.set_text(choice(self.rand_ship_names))
                
            elif self.difficulty.cursor_overlap(event):
                
                self.difficulty.handle_click(event)
        
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return MainMenu()
        if event.sym in confirm:
            
            difficulty = self.difficulty.index_key

            return input_handelers.CommandEventHandler(
                set_up_game(
                    easy_aim=self.aim_button.is_active,
                    easy_move=self.move_button.is_active,
                    easy_warp=self.warp_button.is_active,
                    torpedo_warning=self.warn_torpedo_button.is_active,
                    crash_warning=self.warn_crash_button.is_active,
                    three_d_movment=self.three_d_movement_button.is_active,
                    ship_name=self.ship_name.send(),
                    captain_name=self.captain_name.send(),
                    scenario=self.scenario,
                    difficulty=difficulty
                )
            )

        if self.text_handeler:
            self.text_handeler.handle_key(event)
                
            if not self.captain_name.is_empty and not self.ship_name.is_empty:
                
                self.warning_text = self.__all_okay
        else:
            if event.sym == tcod.event.K_a:
                
                self.aim_button.is_active = not self.aim_button.is_active
                
            elif event.sym == tcod.event.K_w:
                
                self.warp_button.is_active = not self.warp_button.is_active
                
            elif event.sym == tcod.event.K_m:
                
                self.move_button.is_active = not self.move_button.is_active
                
            elif event.sym == tcod.event.K_d:
                
                self.three_d_movement_button.is_active = not self.three_d_movement_button.is_active
                
            elif event.sym == tcod.event.K_t:
                
                self.warn_torpedo_button.is_active = not self.warn_torpedo_button.is_active
                
            elif event.sym == tcod.event.K_c:
                
                self.warn_crash_button.is_active = not self.warn_crash_button.is_active
                
            elif event.sym == tcod.event.K_r:
                
                self.ship_name.set_text(choice(self.rand_ship_names))
