from __future__ import annotations
from typing import TYPE_CHECKING, Iterable
from collections import defaultdict
from enum import Enum, auto
from random import choice, random, uniform, randrange
import colors
from coords import Coords
from data_globals import PlanetHabitation, life_supporting_planets
from game_data import GameData
from message_log import MessageLog
from string import ascii_uppercase

from torpedo import Torpedo

if TYPE_CHECKING:
    from starship import Starship








