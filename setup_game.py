from engine import Engine
from get_config import config_object
from game_data import GameData
from typing import Optional
import input_handelers
import tcod, lzma, pickle
from tcod import constants
from textwrap import wrap
from ui_related import NumberHandeler, TextHandeler, ButtonBox, confirm
import colors

def set_up_help_text():


    ht = '''
Background and objectives:

Like the 1971 Star Trek game, the object of the game is to use a Starfleet ship to destroy as many enemy warships as possible before time runs out. Unlike that game, there are a number of diffrences.

The Enterprise has been replaced by the USS Defiant, and the player must stop a Domminion onslught. Furthermore, he player is not required the destroy all of the enemy ships; destroying %75 of the attackers should count as a sucess.

User Interface: 

The player has four screens avaliable to him/her, the local or subsector screen, the sector screen, the desplay readouts for the systems of the player's ship, and the sensor readouts for the currently selected enemy ship (if any).

Local Screen:

This shows the position of the player's ship in the subsector, along with the positions of enemy ships, stars, and planets. The objects and enties can be encounted in space are as follows:

@ - The player. Your ship.

F - Basic Fighter. Standard enemy attack ship.

A - Advanced Fighter. An improved version of the basic fighter, it boast a small torpedo complement and \
more powerful energy weapons.

C - Battlecruiser. A much more dangerous enemy.

B - Battleship. The most powerful Domminion ship that you can be expected to face.

* - Star.

+ - Planet. Planets may be allied, hostile, or barren planet.

 - Empty space.
 
Sector Screen:

Each sector will have a condenced data output showing what objects arepresent in the sector

+2*1
+0C5
+1F2

The numbers beside each plus sign represent the number of barren, allied, and hostile planets in the system respctively.

The number to the right of the asterisk (*) shows how many stars are present, while the 'C' and 'F' show the number of large and and small ships. Think of the C standing for 'Cruiser' and the F standing for 'Fighter'.

Avaliable Commands:

To enter a command, type in a letter followed by one or two numbers seperated by a colon. The avalible commands are: 

(P)hasers, 
(T)orpedos, 
(M)ove, 
(W)arp, 
(C)hange target, 
recharge (S)hields, 
(R)epair, or 
(H)elp. 

Most commands require one number to be entered with a colon seperating them: (letter):(number). The exceptions are the commands (m)ove, (w)arp, and (t)orpedos require two (or three, if easy mode is selected).

(W)arp:

except for moving, warping, and firing torpedos require one two numbers to be entered use the following format: @:# or @:#:#, with
    
    '''

    ht2 = ht.splitlines()

    width=config_object.screen_width

    for h in ht2:
        if len(h) > width:
            for a in wrap(h, width=width, fix_sentence_endings=True):
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

def setUpGame(
        *,
        easy_aim:bool, easy_move:bool, easy_warp:bool, torpedo_warning:bool, crash_warning:bool, two_d_movment:bool
    ):
    #print('beginning setup')
    #global GRID, PLAYER, TOTAL_STARSHIPS

    gameDataGlobal = GameData(
        subsecsX=config_object.sector_width,
        subsecsY=config_object.sector_height,
        subsecSizeX=config_object.subsector_width,
        subsecSizeY=config_object.subsector_height,
        easyAim=easy_aim,
        easyMove=easy_move,
        two_d_movment=two_d_movment,
        easyWarp=easy_warp,
        torpedo_warning=torpedo_warning,
        crash_warning=crash_warning,
        noOfAdFighters=10,
        noOfFighters=12,
        noOfCruisers=5,
        noOfBattleships=3,
        turnsLeft=80
    )

    engine = Engine(
        filename="",
        player=gameDataGlobal.player,
        easy_aim=easy_aim,
        easy_navigation=easy_move,
        easy_warp=easy_warp,
        torpedo_warning=torpedo_warning,
        crash_warning=crash_warning
    )

    engine.game_data = gameDataGlobal

    gameDataGlobal.engine = engine

    gameDataGlobal.setUpGame()
    return engine

class StartupScreen(input_handelers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""

        console.print(x=console.width // 2 - 5, y=console.height // 2, string="SUPER DS9")
        console.print(x=console.width // 2 - 9, y=console.height // 2 + 2, string="Press any key to begin")

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


    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:
        #print("Main menu")
        return MainMenu()

class MainMenu(input_handelers.BaseEventHandler):

    def __init__(self) -> None:
        self.instructions = (
            "[N]ew Game",
            "[I]nstructions",
            "[Q]uit"
        )
        self.instructions_width = max([len(a) for a in self.instructions])
        
    def on_render(self, console: tcod.Console) -> None:
        console.print(
            x=(console.width // 2) - (self.instructions_width // 2), 
            y=(console.height // 2) - 1, string=self.instructions[0]
        )
        console.print(
            x=(console.width // 2) - (self.instructions_width // 2), 
            y=(console.height // 2), string=self.instructions[1]
        )
        console.print(
            x=(console.width // 2) - (self.instructions_width // 2), 
            y=(console.height // 2) + 1, string=self.instructions[2]
        )

    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:
        #print("Key down")
        if event.sym == tcod.event.K_n:
            #print("New game")
            return NewGame()
        elif event.sym == tcod.event.K_i:
            return Instructions()
        elif event.sym == tcod.event.K_q:
            raise SystemExit
            
class Instructions(input_handelers.BaseEventHandler):

    def __init__(self) -> None:
        super().__init__()
        self.text = HELP_TEXT
        self._index = 0
        self._max_index = max(0, len(self.text) - (1 + config_object.screen_height))
    
    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value:int):
        if value < 0:
            self._index = 0
        else:
            self._index = self._max_index if value > self._max_index else value

    def on_render(self, console: tcod.Console) -> None:

        try:

            help_text = HELP_TEXT[self.index:self.index + config_object.screen_height]
        
        except IndexError:

            help_text = HELP_TEXT[self.index:]

        for i, t in enumerate(help_text):

            console.print(x=0, y=i, string=t)
    
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return MainMenu()
        if event.sym == tcod.event.K_UP:
            self.index -= 1
        elif event.sym == tcod.event.K_PAGEUP:
            self.index -= 10
        elif event.sym == tcod.event.K_DOWN:
            self.index += 1
        elif event.sym == tcod.event.K_PAGEUP:
            self.index += 10
        
        return super().ev_keydown(event)

class NewGame(input_handelers.BaseEventHandler):

    TITLE = "Options"

    def __init__(self) -> None:
        self.ship_name = TextHandeler(16, ["D","e","f","i","e","n","t"])
        self.captain_name = TextHandeler(16,["S","i","s","k","o"])

        self.easy_aim = False
        self.easy_warp = True
        self.easy_navigation = True
        self.two_d_movement = False
        self.torpedo_warning = True
        self.crash_warning = True

        self.text_handeler = None

        self.ship_name_button = ButtonBox(
            x=10,
            y=8,
            height=3,
            width=18,
            title="Ship Name:",
            text=self.ship_name.text_to_print
        )

        self.captain_name_button = ButtonBox(
            x=35,
            y=8,
            height=3,
            width=18,
            title="Captain Name:",
            text=self.captain_name.text_to_print
        )

        self.number_handeler = NumberHandeler(
            limit=8,
            max_value=1200,
            min_value=50,
            wrap_around=True,
            starting_value=100
        )

        self.number_button = ButtonBox(
            x=55,
            y=8,
            height=3,
            width=10,
            title="Numbers",
            text=self.number_handeler.text_to_print,
            alignment=constants.RIGHT
        )

        self.new_game_button = ButtonBox(
            x=60,
            y=15,
            height=3,
            width=12,
            text="Okay"
        )

        self.cancel_button = ButtonBox(
            x=60,
            y=30,
            height=3,
            width=12,
            text="Cancel"
        )

        self.options_button = ButtonBox(
            x=6,
            y=15,
            height=40,
            width=6+35+4,
            title="Options",
            text=""
        )

        self.aim_button = ButtonBox(
            x=10,
            y=20,
            width=30,
            height=4,
            title="Easy (A)im",
            text=""
        )

        self.warp_button = ButtonBox(
            x=10,
            y=25,
            width=30,
            height=4,
            title="Easy (W)arping",
            text=""
        )

        self.move_button = ButtonBox(
            x=10,
            y=30,
            width=30,
            height=4,
            title="Easy (M)ovement",
            text=""
        )

        self.two_d_movement_button = ButtonBox(
            x=10,
            y=35,
            width=30,
            height=5,
            title="2-(D) Movement",
            text=""
        )

        self.warn_torpedo_button = ButtonBox(
            x=10,
            y=41,
            width=30,
            height=5,
            title="(T)orpedo Warnings",
            text=""
        )

        self.warn_crash_button = ButtonBox(
            x=10,
            y=47,
            width=30,
            height=5,
            title="(C)rash Warnings",
            text=""
        )

    def on_render(self, console: tcod.Console) -> None:

        self.captain_name_button.render(
            console,
            text=self.captain_name.text_to_print,
            fg=colors.white if self.text_handeler is self.captain_name else colors.grey,
            bg=colors.black,
            cursor_position=self.captain_name.cursor
        )

        """
        console.print(
            x=self.captain_name_button.x+1+self.captain_name.cursor,
            y=self.captain_name_button.y+1,
            string=self.captain_name.get_char_after_cursor(),
            fg=colors.black,
            bg=colors.white if self.text_handeler is self.captain_name else colors.grey
        )
        """
        
        self.ship_name_button.render(
            console,
            text=self.ship_name.text_to_print,
            fg=colors.white if self.text_handeler is self.ship_name else colors.grey,
            bg=colors.black,
            cursor_position=self.ship_name.cursor
        )

        """
        console.print(
            x=self.ship_name_button.x+1+self.ship_name.cursor,
            y=self.ship_name_button.y+1,
            string=self.ship_name.get_char_after_cursor(),
            fg=colors.black,
            bg=colors.white if self.text_handeler is self.ship_name else colors.grey
        )
        """

        self.number_button.render(
            console,
            text=self.number_handeler.text_to_print,
            fg=colors.white if self.text_handeler is self.number_handeler else colors.grey,
            bg=colors.black,
            cursor_position=self.number_handeler.cursor

        )

        self.new_game_button.render(
            console
        )

        self.cancel_button.render(
            console
        )

        self.options_button.render(
            console,
            fg=colors.grey if self.text_handeler else colors.white,
            bg=colors.black,
        )

        self.aim_button.render(
            console=console,
            text=f"Aim torpedos by entering {'coordants' if self.easy_aim else 'a heading'}",
            fg=colors.green if self.easy_aim else colors.red,
            bg=colors.black,
        )

        self.move_button.render(
            console=console,
            text=f"Navigate ship by entering {'coordants' if self.easy_navigation else 'a heading'}",
            fg=colors.green if self.easy_navigation else colors.red,
            bg=colors.black,
        )
        
        self.warp_button.render(
            console=console,
            text=f"Warp ship by entering {'coordants' if self.easy_warp else 'a heading'}",
            fg=colors.green if self.easy_warp else colors.red,
            bg=colors.black,
        )

        self.two_d_movement_button.render(
            console=console,
            text="Ships will only collide with another object if they end their path on it" if self.two_d_movement else "Ship will collide with any objects between them and their destination",
            fg=colors.green if not self.two_d_movement else colors.red,
            bg=colors.black,
        )

        self.warn_torpedo_button.render(
            console=console,
            text=f"The player will{'' if self.torpedo_warning else ' not'} be warned before firing on a populated planet",
            fg=colors.green if self.torpedo_warning else colors.red,
            bg=colors.black,
        )

        self.warn_crash_button.render(
            console=console,
            text=f"The player will{'' if self.crash_warning else ' not'} be warned before entering a heading that will crash into an object",
            fg=colors.green if self.crash_warning else colors.red,
            bg=colors.black,
        )

    def ev_mousebuttondown(self, event: "tcod.event.MouseButtonDown") -> Optional[input_handelers.BaseEventHandler]:

        if self.cancel_button.cursor_overlap(event):
            return MainMenu()

        if self.new_game_button.cursor_overlap(event):
            return input_handelers.CommandEventHandler(setUpGame(
                easy_aim=self.easy_aim,
                easy_move=self.easy_navigation,
                easy_warp=self.easy_warp,
                torpedo_warning=self.torpedo_warning,
                crash_warning=self.crash_warning,
                two_d_movment=self.two_d_movement
            ))

        if self.captain_name_button.cursor_overlap(event):
            self.text_handeler = self.captain_name
        elif self.ship_name_button.cursor_overlap(event):
            self.text_handeler = self.ship_name
        
        elif self.number_button.cursor_overlap(event):
            self.text_handeler = self.number_handeler
        
        elif self.options_button.cursor_overlap(event):
            self.text_handeler = None

            if self.move_button.cursor_overlap(event):
                self.easy_navigation = not self.easy_navigation
            elif self.warp_button.cursor_overlap(event):
                self.easy_warp = not self.easy_warp
            elif self.aim_button.cursor_overlap(event):
                self.easy_aim = not self.easy_aim
            elif self.two_d_movement_button.cursor_overlap(event):
                self.two_d_movement = not self.two_d_movement
            elif self.warn_torpedo_button.cursor_overlap(event):
                self.torpedo_warning = not self.torpedo_warning
            elif self.warn_crash_button.cursor_overlap(event):
                self.crash_warning = not self.crash_warning
        
    def ev_keydown(self, event: "tcod.event.KeyDown") -> Optional[input_handelers.BaseEventHandler]:

        if event.sym == tcod.event.K_ESCAPE:
            return MainMenu()
        if event.sym in confirm:

            return input_handelers.CommandEventHandler(setUpGame(
                easy_aim=self.easy_aim,
                easy_move=self.easy_navigation,
                easy_warp=self.easy_warp,
                torpedo_warning=self.torpedo_warning,
                warn_before_crash=self.crash_warning
            ))

        if self.text_handeler:
            self.text_handeler.handle_key(event)
            """
            if event.sym in {tcod.event.K_LEFT, tcod.event.K_RIGHT}:
                self.text_handeler.cursor_move(event.sym)
            elif event.sym == tcod.event.K_BACKSPACE:
                self.text_handeler.delete()
            elif event.sym == tcod.event.K_DELETE:
                self.text_handeler.delete(True)
            else:
                key = self.text_handeler.translate_key(event)
                if key:
                    self.text_handeler.insert(key)
            """
        else:
            if event.sym == tcod.event.K_a:
                self.easy_aim = not self.easy_aim
            elif event.sym == tcod.event.K_w:
                self.easy_warp = not self.easy_warp
            elif event.sym == tcod.event.K_m:
                self.easy_navigation = not self.easy_navigation
            elif event.sym == tcod.event.K_d:
                self.two_d_movement = not self.two_d_movement
            elif event.sym == tcod.event.K_t:
                self.torpedo_warning = not self.torpedo_warning
            elif event.sym == tcod.event.K_c:
                self.crash_warning = not self.crash_warning


        return super().ev_keydown(event)
