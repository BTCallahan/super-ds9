from __future__ import annotations
from collections import Counter
from random import choice, choices
from typing import TYPE_CHECKING, List, Optional, Tuple
from data_globals import PlanetHabitation

from order import Order, PhaserOrder, RechargeOrder, RepairOrder, TorpedoOrder, WarpOrder

from torpedo import torpedo_types

if TYPE_CHECKING:
    from starship import Starship
    from space_objects import SubSector
    from game_data import GameData

class BaseAi(Order):

    pass


def find_unopressed_planets(game_data:GameData, ship:Starship):

    for y in game_data.grid:
        for x in y:
            
            sector:SubSector = x

            if sector.coords != ship.sectorCoords:

                for planet in sector.planets_dict.values():

                    if planet.planet_habbitation == PlanetHabitation.PLANET_FRIENDLY:
                        yield planet.sectorCoords

class HostileEnemy(BaseAi):

    def __init__(self, entity: Starship):
        self.entity = entity
        self.target:Optional[Starship] = None
        #self.path: List[Tuple[int, int]] = []
    
    def perform(self) -> None:
        if not self.target:
            self.target = self.game_data.player
        
        order:Optional[Order] = None

        if self.entity.energy <= 0:
            order =  RepairOrder(self.entity, 1)
        else:
            #scan = self.target.scanThisShip(self.entity.determinPrecision)
            scan = self.target.scan_this_ship(self.entity.determinPrecision)
            eS_HP = self.entity.shields
            fireTorp = 0
            firePhaser = 0
            recharge = 0
            repair = 1
            opress = 0
            ram = 0
            
            if self.entity.ship_can_fire_torps and self.entity.checkTorpedoLOS(self.entity.game_data.player):

                fireTorp = self.entity.simulateTorpedoHit(self.target)

                extraDamChance = 1.0 - min(scan["shields"] * 2.0 / self.target.shipData.maxShields, 1.0)

                #to hit: (4.0 / distance) + sensors * 1.25 > EnemyImpuls + rand(-0.25, 0.25)

                #assume that:
                #player has 1000 max shields and 350 shields
                #attacker has 80% trop system
                #attacker has 60% sensor system
                #player has 85% impulsive system
                #distance is 5.75 units

                #1000 / 350 + 0.8 + 0.6 - 0.85 + (5.75 * 0.25)
                #2.857142857142857 + 1.4 - 0.85 + 1.4375
                #4.257142857142857 - 2.2875
            if self.entity.energy > 0:
                if self.entity.sysEnergyWep.isOpperational:
                    firePhaser = self.entity.simulatePhaserHit(self.target, 10)
                    #firePhaser = (s.sysEnergyWeap.getEffectiveValue + s.sysSensors.getEffectiveValue - scan[5]) * 10
                    #assume that:
                    #attacker has
                if self.entity.sysShield.isOpperational:
                    
                    recharge = (self.entity.get_max_shields - self.entity.shields)
                if self.entity.sysImpulse.isOpperational:
                    ram = (self.entity.sysImpulse.getEffectiveValue / (self.entity.hull_percentage + self.entity.shields_percentage) - (self.target.sysImpulse.getEffectiveValue / (self.target.hull_percentage + self.target.shields_percentage)))
            total = fireTorp + firePhaser + recharge + repair

            #if self.entity.game_data.player.sectorCoords != self.entity.sectorCoords:

            unopressed_planets = tuple(find_unopressed_planets(self.entity.game_data, self.entity))

            planet_counter = Counter(unopressed_planets)

            opress =  planet_counter.most_common(1)[0][1]

            ch = choices([TorpedoOrder, PhaserOrder, RechargeOrder, RepairOrder, WarpOrder], weights=[round(fireTorp * 100), round(firePhaser * 100), round(recharge* 10), repair * 10, opress * 10])[0]
            if ch is TorpedoOrder:

                """
                ktValue = max((1, round(0, (scan["shields"] + scan["hull"]) / torpedo_types[self.entity.torpedoLoaded].damage)))
                """
                
                order = TorpedoOrder.from_coords(self.entity, amount=self.entity.shipData.maxTorps, x=self.target.localCoords.x, y=self.target.localCoords.y)
                #finsih this later
            elif ch is PhaserOrder:
                keValue = scan["shields"] + scan["hull"]
                #en = max(0, min(keValue, self.entity.energy))
                order = PhaserOrder(self.entity, keValue, target=self.target)
            elif ch is RechargeOrder:
                reValue = min(self.entity.shipData.maxShields - self.entity.shields, self.entity.energy)
                order = RechargeOrder(self.entity, reValue)
            elif ch is RepairOrder:
                #unopressed_systems = 
                order = RepairOrder(self.entity, 1)
            else:
                co = planet_counter.most_common(1)[0][0]

                order = WarpOrder(self.entity, co.x, co.y)
            
        order.perform()
