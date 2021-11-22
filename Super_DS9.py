#BTCallahan, 3/31/2018
#version 0.6, 5/5/2018
from get_config import config_object
from setup_game import StartupScreen
import tcod, traceback
import colors, exceptions, input_handelers
SHIP_ACTIONS = {'FIRE_ENERGY', 'FIRE_TORP', 'MOVE', 'WARP', 'RECHARGE', 'REPAIR'}


#gameDataGlobal = GameData.newGame()

"""
SUB_SECTORS_X = 8
SUB_SECTORS_Y = 8

SUB_SECTOR_SIZE_X = 8
SUB_SECTOR_SIZE_Y = 8

SUB_SECTORS_RANGE_X = range(0, SUB_SECTORS_X)
SUB_SECTORS_RANGE_Y = range(0, SUB_SECTORS_Y)

SUB_SECTOR_SIZE_RANGE_X = range(0, SUB_SECTOR_SIZE_X)
SUB_SECTOR_SIZE_RANGE_Y = range(0, SUB_SECTOR_SIZE_Y)
"""

#NO_OF_FIGHTERS = 20
#NO_OF_AD_FIGHTERS = 12
#NO_OF_CRUISERS = 5
#NO_OF_BATTLESHIPS = 1

DESTRUCTION_CAUSES = {'ENERGY', 'TORPEDO', 'RAMMED_ENEMY', 'RAMMED_BY_ENEMY', 'CRASH_BARREN', 'CRASH_HOSTILE', 'CRASH_FRIENDLY', 'WARP_BREACH'}

CAUSE_OF_DAMAGE = ''

SHIP_NAME = 'U.S.S. Defiant'
CAPTAIN_NAME = 'Sisko'

TURNS_LEFT = 100

EASY_MOVE = False
EASY_AIM = False

#EVENT_TEXT_TO_PRINT = []


class PlayerData:

    def __init__(self, light, heavy, angered, hostileHit, barrenHit, DBOdest, torpRes,
                 torpUsed, enRes, enUsed, warps):
        self.lightShipsDestroyed = light
        self.heavySHipsDestroyed = heavy
        self.planetsAngered = angered
        self.hostilePlanetsHit = hostileHit
        self.barrenPlanetsHit = barrenHit
        self.bigDumbObjectsDestroyed = DBOdest
        self.torpedosResulplied = torpRes
        self.torpedosFired = torpUsed
        self.energyResulplied = enRes
        self.energyUsed = enUsed
        self.timesGoneToWarp = warps

    @classmethod
    def newData(cls):
        return cls(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

#PLAYER_DATA = PlayerData.newData()

#GRID = []

#TOTAL_STARSHIPS = []

#ENEMY_SHIPS_IN_ACTION = []

#SELECTED_ENEMY_SHIP = None

#SHIPS_IN_SAME_SUBSECTOR = []

#PLAYER = None

"""
class Nation:
    def __init__(self, name, energyWeaponName, escapePodPercent)

"""

"""
def checkWarpCoreBreach(ship):
    global TOTAL_STARSHIPS

    for i in TOTAL_STARSHIPS:

        if i.sectorCoords == ship.sectorCoords and i.localCoords != ship.localCoords:

            dist = ship.localCoords.distance(i.localCoords)
            dam = max(0, dist / ship.warpBreachDist - 1)
            if dam > 0:
                i.takeDamage(ship.shipData.maxHull / 3)
                """

#printScreen()

def main():

    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    screen_width = config_object.screen_width
    screen_height = config_object.screen_height

    handler: input_handelers.BaseEventHandler = StartupScreen()

    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Super DS9",
        vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, input_handelers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), colors.error
                        )
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit.
            # TODO: Add the save function here
            #save_game(handler, "savegame.sav")
            raise
        except BaseException:  # Save on any other unexpected exception.
            # TODO: Add the save function here
            #save_game(handler, "savegame.sav")
            raise
        
if __name__ == "__main__":
    main()