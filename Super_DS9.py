#BTCallahan, 3/31/2018
#version 0.9.9, 12/21/2021
from get_config import config_object
from setup_game import StartupScreen
import tcod, traceback
import colors, exceptions, input_handelers

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