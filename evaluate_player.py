from __future__ import annotations
from collections import OrderedDict
from decimal import Decimal

from typing import TYPE_CHECKING, Final, List, Tuple

from nation import ALL_NATIONS, Nation
from order import Order



if TYPE_CHECKING:
    from game_data import GameData

class ScenerioEvaluation:
    
    @staticmethod
    def is_game_over(game_data:GameData):
        
        return not game_data.player.ship_status.is_active or game_data.is_time_up
    
    @staticmethod
    def generate_evaluation(game_data:GameData) -> Tuple[str, OrderedDict, Decimal]:
        raise NotImplementedError

class DestroyEvaluation(ScenerioEvaluation):
    
    @staticmethod
    def is_game_over(game_data: GameData):
        ships = [
            ship for ship in game_data.all_enemy_ships if ship.ship_status.is_active
        ]
        
        return not game_data.player.ship_status.is_active or game_data.is_time_up or not ships
    
    @staticmethod
    def generate_evaluation(game_data: GameData):
        
        evaluation_dictionary = OrderedDict()
        
        ending_text = []
        #total_ships = len(gameDataGlobal.total_starships) - 1
        
        all_enemy_ships = [ship for ship in game_data.all_enemy_ships if ship.ship_class.nation_code == game_data.scenerio.enemy_nation]
        
        number_of_total_ships = len(
            all_enemy_ships
        )
        
        number_of_active_enemy_ships = len(
            [ship for ship in all_enemy_ships if ship.ship_status.is_active]
        )
        
        number_of_killed_enemy_ships = number_of_total_ships - number_of_active_enemy_ships
        
        evaluation_dictionary["enemy_ships_destroyed"] = (number_of_killed_enemy_ships, number_of_total_ships)
        
        all_enemy_ship_scores = tuple(
            (ship.calculate_ship_stragic_value()) for ship in all_enemy_ships
        )
        
        percentage_of_ships_destroyed = number_of_killed_enemy_ships / number_of_total_ships
        
        point_values_of_destroyed_and_damage_ships = sum([
            m - v for m, v in all_enemy_ship_scores
        ])
        
        max_possible_destruction_score = sum(
            [m for m, v in all_enemy_ship_scores]
        )
        
        ship_destruction_score = sum(
            [
                v for m,v in all_enemy_ship_scores
            ]
        ) / len(all_enemy_ship_scores)
        
        ship_destruction_score = point_values_of_destroyed_and_damage_ships / max_possible_destruction_score
        
        evaluation_dictionary["destruction_score:"] = (
            round(point_values_of_destroyed_and_damage_ships), round(max_possible_destruction_score)
        )
        
        no_enemy_losses = number_of_active_enemy_ships == number_of_total_ships

        all_enemy_ships_destroyed = number_of_active_enemy_ships == 0
        
        

        planets_angered = game_data.player_record["planets_angered"]
        planets_depopulated = game_data.player_record["planets_depopulated"]
        prewarp_planets_depopulated = game_data.player_record["prewarp_planets_depopulated"]
        times_hit_planet = game_data.player_record["times_hit_planet"]
        times_hit_poipulated_planet = game_data.player_record["times_hit_poipulated_planet"]
        times_hit_prewarp_planet = game_data.player_record["times_hit_prewarp_planet"]

        did_the_player_do_bad_stuff = times_hit_poipulated_planet > 0

        #percentage_of_ships_destroyed = destroyed_ships / total_ships

        #destructionPercent = 1.0 - currentEnemyFleetValue / startingEnemyFleetValue
        starting_stardate = game_data.starting_stardate
        ending_stardate = game_data.ending_stardate - starting_stardate
        current_stardate = game_data.stardate - starting_stardate
        
        used_time = current_stardate - starting_stardate
        
        max_time = ending_stardate - starting_stardate
        
        time_left_percent = used_time / max_time
        
        evaluation_dictionary["time_used"] = (used_time, max_time)
        
        
        
        player_nation = game_data.player.ship_class.nation
        
        player_nation_short = player_nation.name_short
        
        captain_rank_name = player_nation.captain_rank_name
        comander_rank_name = player_nation.comander_rank_name
        navy_name = player_nation.navy_name
        
        enemy_nation = ALL_NATIONS[game_data.scenerio.enemy_nation]
        
        enemy_nation_name_short = enemy_nation.name_short
        enemy_nation_posessive = enemy_nation.name_possesive
        
        command = player_nation.command_name
        intel_name = player_nation.intelligence_agency
        
        congrats_text = player_nation.congrats_text
        
        minor_victory_percent = game_data.scenerio.victory_percent
        
        minor_defeat_percent = minor_victory_percent * 0.5
        
        major_victory_percent = minor_victory_percent + (1 - minor_victory_percent) * 0.5
        
        max_possible_value, player_value = game_data.player.calculate_ship_stragic_value()
        
        
        score_multiplier = (
            
        )
        
        overall_score = Decimal(
            point_values_of_destroyed_and_damage_ships * percentage_of_ships_destroyed
        ) * Decimal(0.5) * time_left_percent + Decimal(player_value)
        
        if did_the_player_do_bad_stuff:
            
            if ship_destruction_score >= minor_victory_percent:
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
                elif ship_destruction_score >= major_victory_percent:
                    
                    ending_text.append(
f"The mission was a resounding success. The {enemy_nation_name_short} fleet has suffered heavy losses and is \
attempting to regroup."
                    )
                elif ship_destruction_score >= minor_victory_percent:
                    
                    ending_text.append(
f"The mission was a successful one. "
                    )
                elif ship_destruction_score >= minor_defeat_percent:
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
                elif ship_destruction_score >= major_victory_percent:
                    ending_text.append(
f"Although you were victorous over the {enemy_nation_name_short} strike force, senior personel have \
questioned the reckless or your actions. {comander_rank_name} {game_data.scenerio.your_commanding_officer} has \
stated that a more cautous approch would resulted in the survival of your crew."
                    )
                elif ship_destruction_score >= minor_victory_percent:
                    ending_text.append(
f"While you were largly victorious over the attacking {enemy_nation_posessive} fleet, many senior officers \
have expressed dismay over your loss, and have expressed concern over training procedurals."
                    )
                elif percentage_of_ships_destroyed >= minor_defeat_percent:
                
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
        

        r = ''.join(ending_text), evaluation_dictionary, overall_score

        return r

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

class ProtectEvaluation(ScenerioEvaluation):
    
    @staticmethod
    def is_game_over(game_data: GameData):
        return not game_data.player.ship_status.is_active or game_data.is_time_up

SCENARIO_TYPES:Final = {
    "DESTROY":DestroyEvaluation
}