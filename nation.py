from typing import Optional, Tuple

class Nation:
    __slots__ = (
        "nation_color", 
        "name_long", 
        "name_short", 
        "energy_weapon_name",
        "energy_weapon_name_plural",
        "ship_prefix",
        "congrats_text",
        "captain_rank_name",
        "commander")

    def __init__(self, *, 
        nation_color:Tuple[int,int,int], 
        name_long:str, 
        name_short:str, 
        energy_weapon_name:str, 
        energy_weapon_name_plural: str,
        energy_cannon_name:str,
        energy_cannon_name_plural:str,
        ship_prefix:str,
        congrats_text:str,
        captain_rank_name:str,
        comander_rank_name:str,
        ship_color:Tuple[int,int,int],
        ship_names:Optional[Tuple[str]]=None
    ) -> None:
        self.nation_color = nation_color
        self.name_long = name_long
        self.name_short = name_short
        self.energy_weapon_name = energy_weapon_name
        self.energy_weapon_name_plural = energy_weapon_name_plural
        self.energy_cannon_name = energy_cannon_name
        self.energy_cannon_name_plural = energy_cannon_name_plural
        self.ship_prefix = ship_prefix
        self.congrats_text = congrats_text
        self.captain_rank_name = captain_rank_name
        self.comander_rank_name = comander_rank_name
        self.ship_names = ship_names
        self.ship_color = ship_color
    
    def ship_name(self, name:str):
        return f"{self.ship_prefix} {name}" if self.ship_prefix else name

federation = Nation(
    nation_color= (50, 45, 235),
    name_long="United Federation of Planets",
    name_short="Federation",
    energy_weapon_name="Phaser array",
    energy_weapon_name_plural="Phaser arrays",
    energy_cannon_name="Phaser cannon",
    energy_cannon_name_plural="Phaser cannons",
    ship_prefix="U.S.S.",
    congrats_text="Well Done!",
    captain_rank_name="Captain",
    comander_rank_name="Admiral"
)

dominion = Nation(
    nation_color=(210, 20, 227),
    name_long="Dominion",
    name_short="Dominion",
    energy_weapon_name="Phased Poleron array",
    energy_weapon_name_plural="Phased Poleron arrays",
    energy_cannon_name="Phased Poleron cannon",
    energy_cannon_name_plural="Phased Poleron cannons",
    ship_prefix="D.D.S.",
    congrats_text="Victory is Life!",
    captain_rank_name="First",
    comander_rank_name="Founder"
)

klingon = Nation(
    nation_color=(231, 50, 12),
    name_long="Kingon Empire",
    name_short="Kingon",
    energy_weapon_name="Disruptor array",
    energy_weapon_name_plural="Disruptor arrays",
    energy_cannon_name="Disruptor cannon",
    energy_cannon_name_plural="Disruptor cannons",
    ship_prefix="I.K.S.",
    congrats_text="Qapah!",
    captain_rank_name="Captain",
    comander_rank_name="General"
)

romulan = Nation(
    nation_color=(10, 10, 240),
    name_long="Romulan Star Empire",
    name_short="Romulan",
    energy_weapon_name="Disruptor array",
    energy_weapon_name_plural="Disruptor arrays",
    energy_cannon_name="Disruptor cannon",
    energy_cannon_name_plural="Disruptor cannons",
    ship_prefix="",
    congrats_text="Victory!",
    captain_rank_name="Commander",
    comander_rank_name="Admiral"
)

cardassian = Nation(
    nation_color=(237, 227, 16),
    name_long="Cardassian Union",
    name_short="Cardassian",
    energy_weapon_name="Compresser array",
    energy_weapon_name_plural="Compresser arrays",
    energy_cannon_name="Compresser pluse cannon",
    energy_cannon_name_plural="Compresser pluse cannons",
    ship_prefix="",# C.U.W. ?
    congrats_text="Excellent.",
    captain_rank_name="Gul",
    comander_rank_name="Legate"
)