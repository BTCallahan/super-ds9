from __future__ import annotations
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from typing import TYPE_CHECKING, Final, Iterable, List, Tuple
import colors
from nation import ALL_NATIONS, Nation
from starship import Starship

if TYPE_CHECKING:
    from game_data import GameData

def evaluate_ships(ships:Iterable[Starship]):
    """This is a pretyy complex function. It looks at the score values of the iterable of starships that was passed in and evaluate them. Idealy, it would check to see what the mission objective is to know how to score them. For example, for the mission objective was to find derlict ships and capture them befre the enemy could destroy them, then it would devide the iterable into three lists. The first list is for captured ship. These would be scored based on the condition they were in. The second list would be for ship that are still delrict. Pherhaps these would be treated as failures on the players fart for failing to capture them, and be scored at zero, or perhaps they woiuld be scored at half their condition. Finally the ships that were destroyed would be scored at zero. 

    Args:
        ships (Iterable[Starship]): Ad itterable of Starship objects

    Returns:
        [tuple[float]]: total_ships, number_of_alive_ships, number_of_captured_ships, number_of_derlict_ships, number_of_destroyed_ships, highest_possible_score, total_alive_ships_scores, total_captured_ships_scores, total_derlict_ship_scores, total_destroyed_ship_scores
    """
    total_ships = len(ships)
    
    _highest_possible_score = [ship.calculate_ship_stragic_value()[0] for ship in ships]
    
    highest_possible_score = sum(_highest_possible_score)
    
    _alive_ships = [ship for ship in ships if ship.ship_status.is_active]
    
    alive_ships = [ship for ship in _alive_ships if not ship.ship_is_captured]
    
    number_of_alive_ships = len(alive_ships)
    
    captured_ships = [ship for ship in _alive_ships if ship.ship_is_captured]
    
    number_of_captured_ships = len(captured_ships)
    
    destroyed_ships = [ship for ship in ships if ship.ship_status.is_destroyed]
    
    number_of_destroyed_ships = len(destroyed_ships)
    
    derlict_ships = [ship for ship in ships if ship.ship_status.is_recrewable]
    
    number_of_derlict_ships = len(derlict_ships)
    
    _alive_ships_scores = (
        (ship.calculate_ship_stragic_value()) for ship in alive_ships
    )
    alive_ships_scores = tuple(
        ship[1] for ship in _alive_ships_scores
    )
    _captured_ships_scores = (
        (ship.calculate_ship_stragic_value()) for ship in captured_ships
    )
    captured_ships_scores = tuple(
        ship[1] for ship in _captured_ships_scores
    )
    _derlict_ship_scores = (
        (ship.calculate_ship_stragic_value(value_multiplier_for_derlict=1.0)) for ship in derlict_ships
    )
    derlict_ship_scores = tuple(
        ship[1] for ship in _derlict_ship_scores
    )
    destroyed_ship_scores = tuple(
        (ship.calculate_ship_stragic_value(value_multiplier_for_destroyed=0.0)[0]) for ship in destroyed_ships
    )
    total_alive_ships_scores = sum(alive_ships_scores)
    total_captured_ships_scores = sum(captured_ships_scores)
    total_derlict_ship_scores = sum(derlict_ship_scores)
    total_destroyed_ship_scores = sum(destroyed_ship_scores)
    return (
        total_ships,
        number_of_alive_ships,
        number_of_captured_ships,
        number_of_derlict_ships,
        number_of_destroyed_ships,
        highest_possible_score,
        total_alive_ships_scores,
        total_captured_ships_scores,
        total_derlict_ship_scores,
        total_destroyed_ship_scores
    )

def join_strings(strings:Iterable[str]):
    
    a = strings[-1]
    
    rest = strings[:-1]
    
    n = rest + ["and " + a]
    
    return ", ".join(n)

class ScenerioEvaluation:
    
    @staticmethod
    def is_game_over(game_data:GameData):
        
        return not game_data.player.ship_status.is_active or game_data.is_time_up
    
    @staticmethod
    def generate_evaluation(game_data:GameData) -> Tuple[str, List[Tuple[str,str,Tuple[int,int,int]]]]:
        raise NotImplementedError
    
    @staticmethod
    def describe(amount:float, destroy_ship_classes:Iterable[str], protect_ship_classes:Iterable[str], capture_ship_classes:Iterable[str]):
        raise NotImplementedError
    
    @staticmethod
    def _the_player_did_bad_stuff(
        *, 
        planets_depopulated:int, planets_angered:int, times_hit_prewarp_planet:int, 
        prewarp_planets_depopulated:int, times_hit_poipulated_planet:int,
        player_nation:Nation
    ) -> List[str]:

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

            endingText.append(
f"Your ship records indcated that torpedos fired from your ship were the cause of the destruction of \
{how_many_planets_killed} ,"
            )

            if planets_angered > 0:
                endingText.append("civilizations,")

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
                    
                endingText.append(
f"{how_many_planets_angered} of which had good relations with the {player_nation.name_short} until you fired on them."
                )
            else:
                endingText.append("civilizations.")

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

                endingText.append(
                    f"Horrifyingly, {how_many_prewarp_planets_killed} of those planets were prewarp civilizations."
                )
        return endingText
        
class DestroyEvaluation(ScenerioEvaluation):
    
    @staticmethod
    def is_game_over(game_data: GameData):
        
        return ScenerioEvaluation.is_game_over(game_data) or not [
            ship for ship in game_data.target_enemy_ships if 
            ship.ship_status.is_active or 
            ship.ship_status.is_recrewable
        ]
    
    @staticmethod
    def describe(amount:float, destroy_ship_classes:Iterable[str], protect_ship_classes:Iterable[str], capture_ship_classes:Iterable[str]):
        return f"To win, the player must disable, capture, destroy or damage at least {amount:.%} of the following ship classes: {join_strings(destroy_ship_classes)}."
    
    @staticmethod
    def generate_evaluation(game_data: GameData):
                
        ending_text = []
        #total_ships = len(gameDataGlobal.total_starships) - 1
        
        all_enemy_ships = [
            ship for ship in game_data.all_enemy_ships if 
            ship.ship_class not in game_data.scenerio.mission_critical_ships
        ]
        all_mission_critical_enemy_ships = game_data.target_enemy_ships
        
        total_ships, number_of_alive_ships, number_of_captured_ships, number_of_derlict_ships, number_of_destroyed_ships, highest_possible_score, total_alive_ships_scores, total_captured_ships_scores, total_derlict_ships_scores, total_destroyed_ships_scores = evaluate_ships(all_mission_critical_enemy_ships)
        
        alive_score_percentage = total_alive_ships_scores / highest_possible_score
        
        victory_percentage = 1 - alive_score_percentage
        
        destruction_score = total_destroyed_ships_scores + (
            highest_possible_score - (
                total_alive_ships_scores + total_captured_ships_scores + total_derlict_ships_scores
            )
        )
        minor_victory_percent = game_data.scenerio.victory_percent
        
        minor_defeat_percent = minor_victory_percent * 0.5
        
        major_victory_percent = minor_victory_percent + (1 - minor_victory_percent) * 0.5
        
        if destruction_score >= major_victory_percent:
            
            score_color =colors.green
            
        elif destruction_score >= minor_victory_percent:
        
            score_color = colors.lime
        else:
            score_color = colors.orange if destruction_score >= minor_defeat_percent else colors.red
        
        bonus_total_ships, bonus_number_of_alive_ships, bonus_number_of_captured_ships, bonus_number_of_derlict_ships, bonus_number_of_destroyed_ships, bonus_highest_possible_score, bonus_total_alive_ships_scores, bonus_total_captured_ships_scores, bonus_total_derlict_ships_scores, bonus_total_destroyed_ships_scores = evaluate_ships(all_enemy_ships)
        
        friendy_total_ships, number_of_alive_friendly_ships, number_of_captured_friendly_ships, number_of_derlict_friendy_ships, number_of_destroyed_friendy_ships, highest_possible_friendy_score, total_alive_friendy_ships_scores, total_captured_friendy_ships_scores, total_derlict_friendy_ships_scores, total_destroyed_friendy_ships_scores = evaluate_ships(game_data.all_allied_ships)
        
        evaluation_list:List[Tuple[str,str,Tuple[int,int,int]]] = [
            ("Total Target Enemy Ships:",  f"{total_ships:.2%}", colors.white),
            ("Percent of Target ships Survived:", f"{number_of_alive_ships / total_ships:.2%}", colors.red ),
            ("Percent of Target Ships Destroyed:", f"{number_of_destroyed_ships / total_ships:.2%}", score_color),
            ("Percent of Target Ships Captured:", f"{number_of_captured_ships / total_ships:.2%}", score_color),
            ("Percent of Target Ships Disabled:", f"{number_of_derlict_ships / total_ships:.2%}", score_color),
            ("Highest Possible Score:", f"{highest_possible_score:.2f}", colors.white),
            
            ("Total Victory Score:", f"{destruction_score:.2f}", score_color),
            ("Destruction Score:", f"{total_destroyed_ships_scores:.2f}", score_color),
            ("Captured Ship Score:", f"{total_captured_ships_scores:.2f}", score_color),
            ("Disabled Ship Score:", f"{total_derlict_ships_scores:.2f}", score_color),
            ("Points Remaining:", f"{total_alive_ships_scores:.2f}", colors.red)
        ]
        if bonus_total_ships > 0:
            
            evaluation_list.extend(
                [
                    ("Total Extra Enemy Ships:", f"{bonus_total_ships}", colors.white),
                    (
                        "Percent of Bonus Ships Survived:", 
                        f"{bonus_number_of_alive_ships / bonus_total_ships:.2%}", 
                        colors.orange
                    ),
                    (
                        "Percent of Bonus Ships Destroyed:", 
                        f"{bonus_number_of_destroyed_ships / bonus_total_ships:.2%}", 
                        colors.lime
                    ),
                    (
                        "Percent of Bonus Ships Captured:", 
                        f"{bonus_number_of_captured_ships / bonus_total_ships:.2%}", 
                        colors.lime
                    ),
                    (
                        "Percent of Bonus Ships Captured:", 
                        f"{bonus_number_of_derlict_ships / bonus_total_ships:.2%}", 
                        colors.lime
                    ),
                    ("Highest Possible Bonus Score:", f"{bonus_highest_possible_score:.2f}", colors.white),
                    ("Bonus Destruction Score:", f"{bonus_total_destroyed_ships_scores:.2f}", colors.lime),
                    ("Bonus Captured Ship Score:", f"{bonus_total_captured_ships_scores:.2f}", colors.lime),
                    ("Bonus Disabled Ship Score:", f"{bonus_total_derlict_ships_scores:.2f}", colors.lime),
                    ("Bonus Points Remaining:", f"{bonus_total_alive_ships_scores:.2f}", colors.white)
                ]
            )
        
        if friendy_total_ships > 0:
            
            evaluation_list.extend(
                [
                    ("Total Allied Ships:", f"{friendy_total_ships}", colors.white),
                    (
                        "Percent of Allied Ships Survived:", 
                        f"{number_of_alive_friendly_ships / friendy_total_ships:.2%}", 
                        colors.green
                    ),
                    (
                        "Percent of Allied Ships Destroyed:", 
                        f"{1 - (number_of_alive_friendly_ships / friendy_total_ships):.2%}", 
                        colors.orange
                    ),
                    (
                        "Percent of Allied Ships Captured:", 
                        f"{number_of_captured_friendly_ships / friendy_total_ships:.2%}", 
                        colors.orange
                    ),
                    (
                        "Percent of Allied Ships Captured:" 
                        f"{number_of_derlict_friendy_ships / friendy_total_ships:.2%}", 
                        colors.orange
                    ),
                    ("Highest Possible Allied Loss Score:", f"{highest_possible_friendy_score:.2f}", colors.red),
                    ("Allied Destruction Score:", f"{total_destroyed_friendy_ships_scores:.2f}", colors.lime),
                    ("Allied Captured Ship Score:", f"{total_captured_friendy_ships_scores:.2f}", colors.lime),
                    ("Allied Disabled Ship Score:", f"{total_derlict_friendy_ships_scores:.2f}", colors.lime),
                    ("Loss Points Remaining:", f"{total_alive_friendy_ships_scores:.2f}", colors.green)
                ]
            )
        
        planets_angered = game_data.player_record["planets_angered"]
        planets_depopulated = game_data.player_record["planets_depopulated"]
        prewarp_planets_depopulated = game_data.player_record["prewarp_planets_depopulated"]
        times_hit_planet = game_data.player_record["times_hit_planet"]
        times_hit_poipulated_planet = game_data.player_record["times_hit_poipulated_planet"]
        times_hit_prewarp_planet = game_data.player_record["times_hit_prewarp_planet"]

        did_the_player_do_bad_stuff = times_hit_poipulated_planet > 0

        time_used = game_data.date_time - game_data.scenerio.startdate
        time_left = game_data.scenerio.enddate - game_data.date_time

        starting_stardate = game_data.starting_stardate
        ending_stardate = game_data.ending_stardate - starting_stardate
        current_stardate = game_data.stardate - starting_stardate
        
        used_time = current_stardate - starting_stardate
        
        max_time = ending_stardate - starting_stardate
        
        time_left_percent = used_time / max_time
                
        evaluation_list.extend(
            [
                (
                    "Friendly Planets Angered:", 
                    f'{planets_angered}', 
                    colors.red if planets_angered else colors.green
                ),
                (
                    "Total Planets Depopulated:", 
                    f'{planets_depopulated}',
                    colors.red if planets_depopulated else colors.green
                ),
                (
                    "Prewarp Planets Depopulated:",
                    f'{prewarp_planets_depopulated}',
                    colors.red if prewarp_planets_depopulated else colors.green
                ),
                (
                    "No. of Planetary Torpedo Hits:", 
                    f'{times_hit_planet}',
                    colors.white
                ),
                (
                    "No. of Polulated Planetary Torpedo Hits:", 
                    f'{times_hit_poipulated_planet}',
                    colors.red if times_hit_poipulated_planet else colors.green
                ),
                (
                    "No. of Wrewarp Planetary Torpedo Hits:", 
                    f'{times_hit_prewarp_planet}',
                    colors.red if times_hit_prewarp_planet else colors.green
                ),
                (
                    "Time Used:",
                    f"{time_used}",
                    colors.white
                ),
                (
                    "Time Left:",
                    f"{time_left}",
                    colors.white
                )
            ]
        )        
        player_nation = game_data.scenerio.your_nation
        
        player_nation_short = player_nation.name_short
        
        captain_rank_name = player_nation.captain_rank_name
        comander_rank_name = player_nation.comander_rank_name
        navy_name = player_nation.navy_name
        
        enemy_nation = game_data.scenerio.main_enemy_nation
        
        enemy_nation_name_short = enemy_nation.name_short
        enemy_nation_posessive = enemy_nation.name_possesive
        
        command = player_nation.command_name
        intel_name = player_nation.intelligence_agency
        
        congrats_text = player_nation.congrats_text
        
        all_enemy_ships_destroyed = number_of_alive_ships == 0
        
        no_enemy_losses = number_of_alive_ships == total_ships
        
        if did_the_player_do_bad_stuff:
            
            if victory_percentage >= minor_victory_percent:
                ending_text.append(
f"While the attacking {enemy_nation_posessive} force was {'wiped out' if all_enemy_ships_destroyed else 'devstated'}, \
initial enthusiasm over your victory has given way to horror."
                )
            ending_text.extend(
                DestroyEvaluation._the_player_did_bad_stuff(
                    planets_depopulated=planets_depopulated,
                    planets_angered=planets_angered,
                    prewarp_planets_depopulated=prewarp_planets_depopulated,
                    times_hit_poipulated_planet=times_hit_poipulated_planet,
                    times_hit_prewarp_planet=times_hit_prewarp_planet,
                    player_nation=player_nation
                )
            )
            ending_text.append(
                "Your trial and sentencing is expected later this month." 
                if game_data.player.ship_status.is_active else 
                "Regretfully, prosecutors are unable to try you for your crimes due to you being dead."
            )    
        else:
            if game_data.player.ship_status.is_active:

                if all_enemy_ships_destroyed:

                    ending_text.append(
f"Thanks to your heroic efforts, mastery of tactical skill, and shrewd management of limited resources, \
you have completely destroyed the {enemy_nation_name_short} strike force. {congrats_text}")

                    if time_left_percent < 0.25:

                        ending_text.append(
"The enemy has been forced to relocate a large amount of their ships to this sector. In doing so, they have \
weakened their fleets in several key areas, including their holdings in the Alpha Quadrant."
                        )
                    elif time_left_percent < 0.5:

                        ending_text.append(
f"Intercepted communications have revealed that because of the total destruction of the enemy task \
force, the {game_data.player.name} has been designated as a priority target."
                        )
                    elif time_left_percent < 0.75:

                        ending_text.append(
f"We are making preparations for an offensive to capture critical systems. Because of your abilities \
{command} is offering you a promotion to the rank of {comander_rank_name}."
                        )
                    else:
                        ending_text.append(
f"The enemy is in complete disarray thanks to the speed at which you annilated the opposing fleet! \
Allied forces have exploited the chaos, making bold strikes into {enemy_nation_posessive} controlled space in the \
Alpha Quadrant. {intel_name} has predicted mass defections among from allied military. Because of your \
abilities {command} has weighed the possibility of a promotion to the rank of {comander_rank_name}, but \
ultimately decided that your skills are more urgently needed in the war.")
                elif victory_percentage >= major_victory_percent:
                    
                    ending_text.append(
f"The mission was a resounding success. The {enemy_nation_name_short} fleet has suffered heavy losses and is \
attempting to regroup."
                    )
                elif victory_percentage >= minor_victory_percent:
                    
                    ending_text.append(
f"The mission was a successful one. "
                    )
                elif victory_percentage >= minor_defeat_percent:
                    ending_text.append(
f"The mission was unsucessful. In spite of inflicting heavy damage in the {enemy_nation_posessive} fleet, they \
were still able to renforce their positions."
                    )
                elif not no_enemy_losses:
                    ending_text.append(
f"The mission was a failure. The casulties inflicted on the {enemy_nation_name_short} strike fore were insuficent \
to prevent them from taking key positions. In addition, they have also been able to renforce their positions. Expect \
to be demoted."
                    )
                else:
                    ending_text.append(
f"The mission was a complete and utter failure. No ships of the {enemy_nation_name_short} strike force were destroyed, \
allowing enemy forces to fortify their positions within the Alpha Quadrant. You can expect a court marshal in \
your future."
                    )
            else:
                if all_enemy_ships_destroyed:
                    ending_text.append(
f"Thanks to your sacrifice, mastery of tactial skill, and shrewd manadgement of limited resources, \
you have completly destroyed the {enemy_nation_posessive} strike force. Your hard fought sacrifice will be \
long remembered in the reccords of {navy_name} history. {congrats_text}!"
                    )
                elif victory_percentage >= major_victory_percent:
                    ending_text.append(
f"Although you were victorous over the {enemy_nation_name_short} strike force, senior personel have \
questioned the reckless or your actions. {comander_rank_name} {game_data.scenerio.your_commanding_officer} has \
stated that a more cautous approch would resulted in the survival of your crew."
                    )
                elif victory_percentage >= minor_victory_percent:
                    ending_text.append(
f"While you were largly victorious over the attacking {enemy_nation_posessive} fleet, many senior officers \
have expressed dismay over your loss, and have expressed concern over training procedurals."
                    )
                elif victory_percentage >= minor_defeat_percent:
                
                    ending_text.append(
f"Your mission was a failure. The casulties you influcted on the {enemy_nation_name_short} strike force hindered \
them, but not enough to truly make a diffrence."
                    )
                elif not no_enemy_losses:
                    after = 'shortly after' if time_left_percent < 0.25 else 'after'
                    ending_text.append(
f'The mission was a dismal failure. Your ship was destroyed {after} you engaged the enemy \
inspite of your tactial superority you inflicted vastly insufficent losses on the enemy.'
                    ) 
                else:
                    after = 'shortly after' if time_left_percent < 0.25 else 'after'
                
                    ending_text.append(
f'You are an embaressment to the {player_nation_short}. Your ship was destroyed {after} you engaged the enemy \
inspite of your tactial superority you inflicted no losses on the enemy.'
                    )
        
        r = ''.join(ending_text), evaluation_list

        return r

class ProtectEvaluation(ScenerioEvaluation):
    
    @staticmethod
    def is_game_over(game_data: GameData):
        
        return ScenerioEvaluation.is_game_over(game_data) or not [
            ship for ship in game_data.target_allied_ships if ship.ship_status.is_active
        ]

class CaptureEvaluation(ScenerioEvaluation):
    
    @staticmethod
    def is_game_over(game_data: GameData):
        return ScenerioEvaluation.is_game_over(game_data) or not [
            ship for ship in game_data.target_enemy_ships if 
            ship.ship_status.is_active or 
            ship.ship_status.is_recrewable or
            ship.ship_is_captured
        ]
    
    @staticmethod
    def generate_evaluation(game_data:GameData) -> Tuple[str, OrderedDict, Decimal]:
        raise NotImplementedError
    
    @staticmethod
    def describe(amount:float, destroy_ship_classes:Iterable[str], protect_ship_classes:Iterable[str], capture_ship_classes:Iterable[str]):
        return f"To win, the player must capture, at least {amount:.%} of the following ship classes: {', '.join(capture_ship_classes)}."

SCENARIO_TYPES:Final = {
    "DESTROY":DestroyEvaluation
}