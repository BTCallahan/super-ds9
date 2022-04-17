from __future__ import annotations
from math import ceil, floor
from random import uniform
from typing import TYPE_CHECKING, Dict, List
from components.starship_system import StarshipSystem
from data_globals import PRECISION_SCANNING_VALUES
from get_config import CONFIG_OBJECT
import colors

from global_functions import scan_assistant

if TYPE_CHECKING:
    from ship_class import ShipClass
    from nation import Nation

class LifeSupport(StarshipSystem):
        
    def __init__(self, ship_class:ShipClass) -> None:
        super().__init__("Life Support:")
        
        self.turn_without_lifesupport = 0

        self.able_crew = ship_class.max_crew
        self.injured_crew = 0
        
        # format is Dict[nation of ship that send over boarding party, List[able boarders, injured boarders]]
        self.hostiles_on_board: Dict[Nation, List[int,int]] = {}
    
    @property
    def is_derlict(self):
        
        return self.able_crew < 1 and self.injured_crew < 1
    
    @property
    def crew_readyness(self):
        
        return self.caluclate_crew_readyness(
            self.able_crew, self.injured_crew
        )
    
    @property
    def has_boarders(self):
        if self.hostiles_on_board:
            
            for v in self.hostiles_on_board.values():
                
                if v[0] + v[1] > 0:
                    return True
        return False
    
    def scan_crew_readyness(self, precision:int):
        
        return self.caluclate_crew_readyness(
            scan_assistant(self.able_crew, precision), scan_assistant(self.injured_crew, precision)
        )
    
    def caluclate_crew_readyness(self, able_crew:int, injured_crew:int):
        if self.starship.is_automated:
            return 1.0
        total = able_crew + injured_crew * 0.25
        return 0.0 if total == 0.0 else (total / self.starship.ship_class.max_crew) * 0.5 + 0.5

    @property
    def get_total_crew(self):
        return self.able_crew + self.injured_crew
    
    def heal_crew(self, percentage_of_injured_crew:float, minimal_crew_to_heal:int):
        
        p = percentage_of_injured_crew * self.get_effective_value
        
        heal_crew = min(self.injured_crew, ceil(self.injured_crew * p) + minimal_crew_to_heal)
        self.able_crew+= heal_crew
        self.injured_crew-= heal_crew
    
    def take_control_of_ship(
        self,        
        *, 
        able_crew:int, injured_crew:int=0, nation:Nation
    ):    
        self.able_crew = able_crew
        self.injured_crew = injured_crew
        
        self.starship.nation = nation
        
        self.starship.get_sub_sector.enable_ship(self.starship)
    
    def injuries_and_deaths(self, injured:int, killed_outright:int, killed_in_sickbay:int):
        
        self.able_crew -= injured + killed_outright
        self.injured_crew += injured - killed_in_sickbay
        
        if self.able_crew < 0:
            self.able_crew = 0
        
        if self.injured_crew < 0:
            self.injured_crew = 0
        
        if self.is_derlict:
                        
            self.starship.get_sub_sector.disable_ship(self.starship)

    def on_turn(self):
        
        are_hostiles_on_board = self.hostiles_on_board
        
        life_support_offline_past_critical = False
        
        if not self.is_opperational:
            
            self.turn_without_lifesupport += 1
            
            if self.turn_without_lifesupport > CONFIG_OBJECT.life_support_offline_turn_limit:
                
                life_support_offline_past_critical = True
                
        elif self.turn_without_lifesupport > 0:
            
            self.turn_without_lifesupport -= 1
        
        if are_hostiles_on_board or life_support_offline_past_critical:
            
            defender_is_player = self.starship.is_controllable
            
            in_same_system = self.starship.sector_coords == self.starship.game_data.player.sector_coords
            
            set_of_allied_nations = self.starship.game_data.scenerio.get_set_of_allied_nations
            set_of_enemy_nations = self.starship.game_data.scenerio.get_set_of_enemy_nations
            
            ship_is_on_players_side = self.starship.nation in set_of_allied_nations
            ship_is_on_enemy_side = self.starship.nation in set_of_enemy_nations
            
            keys_to_remove = []
            
            message_log = self.starship.game_data.engine.message_log
            
            if are_hostiles_on_board:
                
                all_defenders_died = False
                
                for k,v in self.hostiles_on_board.items():
                    
                    boarders_are_from_player = k == self.starship.game_data.scenerio.your_nation
                    
                    able_boarders, injured_boarders = v[0], v[1]
                    
                    total_borders = able_boarders + injured_boarders
                    
                    if total_borders > 0:
                                                                        
                        # if the boarding party is on the same side as the ships crew:
                        if ship_is_on_players_side == (
                            k in set_of_allied_nations
                        ) or ship_is_on_enemy_side == (
                            k in set_of_enemy_nations
                        ):
                            able = v[0]
                            injured = v[1]
                            
                            self.able_crew += able
                            self.injured_crew += injured
                            
                            if defender_is_player:
                                
                                message:List[str] = [f"The {k.name_short} force of"]
                                
                                if able > 0:
                                    
                                    message.append(f"{able} able boarders")
                                    
                                    if injured > 0:
                                        
                                        message.append("and")
                                
                                if injured > 0:
                                    
                                    message.append(f"{injured} boarders")
                                
                                message.append("intergrated into our crew.")
                                
                                message_log.add_message(
                                    " ".join(message), colors.cyan
                                )
                            elif in_same_system and boarders_are_from_player:
                                
                                message:List[str] = [f"Our boarding party of"]
                                
                                if able > 0:
                                    
                                    message.append(f"{able} crew menbers")
                                    
                                    if injured > 0:
                                        
                                        message.append("and")
                                
                                if injured > 0:
                                    
                                    message.append(f"{injured} injured crew")
                                                     
                                message.append(f"intergrated into the crew of the {self.starship.proper_name}.")
                                
                                message_log.add_message(" ".join(message_log), colors.cyan)
                            
                            v[0] = 0
                            v[1] = 0
                            
                            keys_to_remove.append(k)
                        else:                    
                            attacker_firepower = ceil(max(self.able_crew, self.injured_crew * 0.25) * 0.125)
                            
                            attacker_firepower_vs_able_crew = min(attacker_firepower, self.able_crew)
                            
                            attacker_firepower_vs_injured_crew = attacker_firepower - attacker_firepower_vs_able_crew
                            
                            # the defenders won't be abler to concintrate all of their firepower on the boarders
                            defender_firepower = ceil(
                                min(total_borders * 2, max(self.able_crew, self.injured_crew * 0.25)) * 0.125
                            )
                            defender_firepower_vs_able_boarders = min(defender_firepower, able_boarders)
                            
                            defender_firepower_vs_injured_boarders = (
                                attacker_firepower - defender_firepower_vs_able_boarders
                            )
                            injured = round(attacker_firepower_vs_able_crew * 0.4)
                            killed_outright = round(attacker_firepower_vs_able_crew * 0.6)
                            killed_in_sickbay = attacker_firepower_vs_injured_crew
                            
                            self.injuries_and_deaths(
                                injured, killed_outright,
                                killed_in_sickbay
                            )
                            all_defenders_died = self.is_derlict
                            
                            new_injured_boarders = round(
                                defender_firepower_vs_able_boarders * 0.4
                            ) - defender_firepower_vs_injured_boarders
                            
                            injured_boarders += new_injured_boarders
                            
                            injured_boarders_killed = 0
                            
                            able_boarders_killed = round(defender_firepower_vs_able_boarders * 0.6)
                            
                            able_boarders -= able_boarders_killed
                            
                            # the boarders don't have access to sickbay, so some of them die from their injuries
                            if injured_boarders > 0:
                                
                                f = able_boarders * 0.125
                                
                                injured_boarders_killed += int((f // 1) + (f % 1))
                                
                                injured_boarders -= injured_boarders_killed
                            
                            injured_boarders = max(0, injured_boarders)
                            able_boarders = max(0, able_boarders)
                            
                            did_defender_suffer_casulties = injured + killed_outright + killed_in_sickbay > 0
                            
                            did_attacker_suffer_casulties = (
                                injured_boarders_killed + able_boarders_killed + new_injured_boarders > 0
                            )
                            all_boarders_died = injured_boarders + able_boarders <= 0
                            
                            if all_defenders_died:
                                self.take_control_of_ship(
                                    able_crew=able_boarders, injured_crew=injured_boarders, nation=k
                                )
                                keys_to_remove.append(k)
                            
                            if defender_is_player and not all_defenders_died:
                                
                                if did_defender_suffer_casulties or did_attacker_suffer_casulties:
                                
                                    message:List[str] = []
                                    
                                    if did_defender_suffer_casulties:
                                        
                                        message.append(f"During the fighting with {k.name_short} forces, we suffered")
                                    
                                        if injured > 0:
                                            
                                            message.append(f"{injured}")
                                            
                                            if killed_outright > 0:
                                                
                                                message.append(f"injured and")
                                                
                                            elif killed_in_sickbay > 0:
                                                
                                                message.append(f"injured, as well as")
                                            else:
                                                message.append("injured.")
                                        
                                        if killed_outright > 0:
                                            
                                            message.append(f"{killed_outright}")
                                            
                                            message.append(
                                                f"killed, as well as" if killed_in_sickbay > 0 else "killed."
                                            )
                                        if killed_in_sickbay > 0:
                                            
                                            message.append(f"{killed_in_sickbay} deaths of wounded personel.")
                                    
                                    if did_attacker_suffer_casulties:
                                        
                                        message.append("We were able to")
                                        
                                        if new_injured_boarders > 0:
                                            
                                            message.append(f"injure {new_injured_boarders} of ")
                                            
                                            if able_boarders_killed > 0:
                                                
                                                message.append("attackers, and")
                                            
                                            elif injured_boarders_killed > 0:
                                                
                                                message.append("attackers, in addition")
                                            else:
                                                message.append("attackers.")
                                    
                                        if able_boarders_killed > 0:
                                            
                                            message.append(f"kill {able_boarders_killed} of")
                                            
                                            message.append("them and" if injured_boarders_killed > 0 else "them.")
                                            
                                        if injured_boarders_killed > 0:
                                            
                                            message.append(f"kill {injured_boarders_killed} injured combatants.")
                                        
                                        message_log.add_message(" ".join(message), colors.orange)
                                        
                                        if all_boarders_died:
                                            
                                            message_log.add_message(
                                                f"The last of the {k.name_long} attackers have been wiped out!",
                                                colors.cyan
                                            )
                            elif not defender_is_player and in_same_system and boarders_are_from_player:
                                
                                if did_defender_suffer_casulties or did_attacker_suffer_casulties:
                                
                                    if all_boarders_died:
                                        
                                        message_log.add_message(
                                            "We have lost contact with our boarding party.", colors.red
                                        )
                                    else:
                                        message:List[str] = [
f"During the fighting with {self.starship.nation.name_short} forces, our boarding party inflicted"
                                        ]
                                        if did_defender_suffer_casulties:
                                        
                                            if injured > 0:
                                                
                                                message.append(f"{injured}")
                                                
                                                if killed_outright > 0:
                                                    
                                                    message.append(f"injured and")
                                                    
                                                elif killed_in_sickbay > 0:
                                                    
                                                    message.append(f"injured, as well as")
                                                else:
                                                    message.append("injured.")
                                            
                                            if killed_outright > 0:
                                                
                                                message.append(f"{killed_outright}")
                                                
                                                message.append(
                                                    f"killed, as well as" if killed_in_sickbay > 0 else "killed."
                                                )
                                            if killed_in_sickbay > 0:
                                                
                                                message.append(f"{killed_in_sickbay} deaths of wounded personel.")
                                        
                                        if did_attacker_suffer_casulties:
                                            
                                            message.append(f"The crew of the {self.starship.proper_name} were able to")
                                            
                                            if new_injured_boarders > 0:
                                                
                                                message.append(f"injure {new_injured_boarders} of ")
                                                
                                                if able_boarders_killed > 0:
                                                    
                                                    message.append("our boarding party, and")
                                                
                                                elif injured_boarders_killed > 0:
                                                    
                                                    message.append("our boarding party, and they were also able to")
                                                else:
                                                    message.append("our boarding party.")
                                        
                                            if able_boarders_killed > 0:
                                                
                                                message.append(f"kill {able_boarders_killed} of")
                                                
                                                message.append("them and" if injured_boarders_killed > 0 else "them.")
                                                
                                            if injured_boarders_killed > 0:
                                                
                                                message.append(f"kill {injured_boarders_killed} injured combatants.")
                                        
                                        message_log.add_message(" ".join(message), colors.orange)
                                        
                                        if all_defenders_died:
                                            
                                            message_log.add_message(
                                                "Our forces have taken control of the ship!", colors.cyan
                                            )
                            if all_boarders_died:
                                
                                keys_to_remove.append(k)
                            else:
                                self.hostiles_on_board[k][0] = able_boarders
                                self.hostiles_on_board[k][1] = injured_boarders
                    else:
                        keys_to_remove.append(k)
            
            if life_support_offline_past_critical:
                
                critical_turns = self.turn_without_lifesupport - CONFIG_OBJECT.life_support_offline_turn_limit
                                
                _able_crew_deaths = critical_turns * uniform(0.1, 0.12)
            
                _injured_crew_deaths = critical_turns * uniform(0.12, 0.15)
                                                                            
                able_crew_deaths = min(round(self.able_crew * _able_crew_deaths), self.able_crew)
                
                injured_crew_deaths = min(round(self.injured_crew * _injured_crew_deaths), self.injured_crew)
                
                total_crew_deaths = able_crew_deaths + injured_crew_deaths
                
                if total_crew_deaths > 0:
                
                    self.injuries_and_deaths(0, able_crew_deaths, injured_crew_deaths)
                
                    all_defenders_died = self.is_derlict
                
                    if defender_is_player:
                        
                        message:List[str] = ["Our crew report that"]
                        
                        if able_crew_deaths > 0:
                            
                            m = "members" if able_crew_deaths > 1 else "member"
                            
                            message.append(f"{able_crew_deaths} able crew {m}")
                            
                            if injured_crew_deaths > 0:
                                
                                message.append("and")
                        
                        if injured_crew_deaths > 0:
                            
                            m2 = "members" if injured_crew_deaths > 1 else "member"
                            
                            message.append(f"{injured_crew_deaths} injured crew {m2}")
                        
                        message.append("have died from enviromental exposure.")
                        
                        self.starship.game_data.engine.message_log.add_message(
                            " ".join(message), colors.orange
                        )
                for k,v in self.hostiles_on_board.items():
                    
                    boarders_are_from_player = k == self.starship.game_data.scenerio.your_nation
                    
                    _able_boarder_deaths = critical_turns * uniform(0.12, 0.16)
            
                    _injured_boarder_deaths = critical_turns * uniform(0.14, 0.18)
                    
                    able_boarders, injured_boarders = v[0], v[1]
                                            
                    able_boarder_deaths = min(
                        round(_able_boarder_deaths * able_boarders), able_boarders
                    )
                    injured_boarder_deaths = min(
                        round(_injured_boarder_deaths * injured_boarders), injured_boarders
                    )
                    total_border_deaths = able_boarder_deaths + injured_boarder_deaths
                    
                    if total_border_deaths > 0:
                        
                        all_boarders_died = able_boarders + injured_boarders <= 0
                        
                        able_boarders -= able_boarder_deaths
                        
                        injured_boarders -= injured_boarder_deaths
                    
                        self.hostiles_on_board[k][0] = able_boarders
                        self.hostiles_on_board[k][1] = injured_boarders
                        
                        if defender_is_player:
                            
                            message:List[str] = ["Our crew report that"]
                            
                            if all_boarders_died:
                                
                                message.append("the last")
                            
                            if able_boarder_deaths > 0:
                                
                                message.append(f"{able_boarder_deaths} able")
                            
                                if injured_boarder_deaths > 0:
                                    
                                    message.append("and")
                            
                            if injured_boarder_deaths > 0:
                                
                                message.append(f"{injured_boarder_deaths} injured")
                            
                            message.append("boarders died from exposure.")
                            
                            message_log.add_message(" ".join(message), colors.orange)
                            
                        elif in_same_system and boarders_are_from_player:
                                
                            if all_boarders_died:
                                message_log.add_message("We have lost contact with our boarding party.", colors.red)
                            else:
                                message:List[str] = [
                                    f"Our forces aboard the {self.starship.name} report that they have suffered"
                                ]
                                if able_boarder_deaths > 0:
                                    
                                    ab = "members" if able_boarder_deaths > 1 else "member"
                                    
                                    message.append(f"{able_boarder_deaths} able crew {ab} deaths")
                                    
                                    if injured_boarder_deaths > 0:
                                        
                                        message.append("and")
                                
                                if injured_boarder_deaths > 0:
                                    
                                    ab2 = "members" if injured_boarder_deaths > 1 else "member"
                                    
                                    message.append(f"{injured_boarder_deaths} injured crew {ab2} deaths")
                                
                                message.append("from enviromental exposure.")
                                
                                message_log.add_message(
                                    " ".join(message), colors.orange
                                )
                                if all_defenders_died:
                                    
                                    message_log.add_message(
"All defending personel have expired from enviromental conditions. Our forces now have control of the ship!", 
                                        colors.cyan
                                    )
                        if all_boarders_died:
                            
                            keys_to_remove.append(k)
            
            for k in keys_to_remove:
                        
                del self.hostiles_on_board[k]

    def get_boarding_parties(self, viewer_nation:Nation, precision:int = 1):
        """This generates the number of boarding parties that the ship has

        Args:
            precision (int, optional): The precision value. 1 is best, higher values are worse. Must be an intiger that is not less then 0 and not more then 100. Defaults to 1.

        Raises:
            TypeError: Raised if precision is a float.
            ValueError: Rasied if precision is lower then 1 or higher then 100

        Yields:
            [Tuple[Nation, Tuple[int, int]]]: Tuples containing the nation, and a tuple with two intiger values
        """
        #scanAssistant = lambda v, p: round(v / p) * p
        if  isinstance(precision, float):
            raise TypeError("The value 'precision' MUST be a intiger inbetween 1 and 100")
        if precision not in PRECISION_SCANNING_VALUES:
            raise ValueError(
f"The intiger 'precision' MUST be one of the following: 1, 2, 5, 10, 15, 20, 25, 50, 100, 200, or 500. \
It's actually value is {precision}."
            )
        
        if precision == 1:
            
            for k,v in self.hostiles_on_board.items():
                
                if v[0] + v[1] > 0:
                    yield (k, tuple(v))
        else:
            for k,v in self.hostiles_on_board.items():
                
                if v[0] + v[1] > 0:
                    if k == viewer_nation:
                        
                        yield (k, tuple(v))
                    else:
                        yield (k, (scan_assistant(v[0], precision), scan_assistant(v[1], precision)))
