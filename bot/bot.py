from typing import List
from sc2.bot_ai import BotAI, Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit


class MarineRushBot(BotAI):
    NAME: str = "MarineRushBot"
    RACE: Race = Race.Terran
    stage: int = 0
    step: int = 0
    closeRadius: int = 8

    async def on_unit_took_damage(self, unit: UnitTypeId.MARINE, amount_damage_taken: float):
        enemyUnitAround = self.enemy_units.not_flying.closer_than(20, self.townhalls[0])

    async def on_unit_took_damage(self, unit: UnitTypeId.REAPER, amount_damage_taken: float):
        target = self.enemy_structures.random_or(
        self.enemy_start_locations[0]).position

        idle_marines = self.units(UnitTypeId.MARINE).idle
        for marine in idle_marines:
                marine.attack(target)

    async def on_step(self, iteration: int):
        # Jestliže mám Command Center
        self.step += 1
        if self.townhalls:
            # První Command Center
            command_center = self.townhalls[0]

            # -----------------------------------------------------------------------------------
            # Trenovani stavitelu, budov
            # -----------------------------------------------------------------------------------

            # Trénování SCV
            # Bot trénuje nová SCV, jestliže je jich méně než 21
            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= 22 and command_center.is_idle:
                command_center.train(UnitTypeId.SCV)

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 10 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=command_center.position.towards(self.game_info.map_center, 12))

            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 6:
                    if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                        await self.build(
                            UnitTypeId.BARRACKS,
                            near=command_center.position.towards(self.game_info.map_center, 8))

            if (self.structures(UnitTypeId.BARRACKS) or self.already_pending(UnitTypeId.BARRACKS)) and self.structures(UnitTypeId.REFINERY).amount <= 4:
                if self.can_afford(UnitTypeId.REFINERY) and not self.already_pending(UnitTypeId.REFINERY):
                    print('gonna build refinery')
                    gs = self.vespene_geyser.closer_than(self.closeRadius, command_center)
                    for g in gs:
                        if await self.can_place(UnitTypeId.REFINERY, g.position):
                            if self.workers.gathering.exists:
                                worker = self.workers.gathering.closest_to(g)
                                worker.build(UnitTypeId.REFINERY, g)      

            if self.structures(UnitTypeId.FACTORY).amount < 1:
                if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                    print('gonna build factory')
                    await self.build(UnitTypeId.FACTORY, near=command_center.position.towards(self.game_info.map_center,8))
            
            if self.structures(UnitTypeId.STARPORT).amount < 1:
                if self.can_afford(UnitTypeId.STARPORT) and not self.already_pending(UnitTypeId.STARPORT):
                    print('gonna build starport')
                    await self.build(UnitTypeId.STARPORT, near=command_center.position.towards(self.game_info.map_center,8))

            # -----------------------------------------------------------------------------------
            # Trenovani jednotek
            # -----------------------------------------------------------------------------------

            # Trénování jednotky Marine
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            if self.structures(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.MARINE):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                    barrack.train(UnitTypeId.MARINE)

            # Trénování jednotky Reaper
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            if self.structures(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.REAPER):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                    barrack.train(UnitTypeId.REAPER)

            if self.units(UnitTypeId.STARPORT).exists and self.structures(UnitTypeId.STARPORT) and not self.already_pending(UnitTypeId.STARPORT) and self.can_afford(UnitTypeId.VIKING):
                for sp in self.structures(UnitTypeId.STARPORT):
                    print('gonna build viking')
                    sp.train(UnitTypeId.VIKING)

            # -----------------------------------------------------------------------------------
            # Útok s jednotkou Marine
            # -----------------------------------------------------------------------------------

            if self.enemy_units.not_flying.closer_than(15, self.townhalls[0]):
                enemyUnitAround = self.enemy_units.not_flying.closer_than(15, self.townhalls[0])
                for unit in self.units.filter(lambda u: u.type_id != UnitTypeId.SCV).closer_than(30, command_center):
                    unit.attack(enemyUnitAround[0])
            else:
                for unit in self.units.filter(lambda u: u.type_id != UnitTypeId.SCV).closer_than(30, command_center):
                    unit.move(command_center)

            idle_marines = self.units(UnitTypeId.MARINE).idle
            idle_reapers = self.units(UnitTypeId.REAPER).idle
            idle_vikings = self.units(UnitTypeId.VIKING).idle

            if idle_marines.amount > 50 or idle_reapers.amount > 30 and idle_vikings.amount > 5:
                target = self.enemy_structures.random_or(
                    self.enemy_start_locations[0]).position
                for marine in idle_marines:
                    marine.attack(target)
                for reaper in idle_reapers:
                    reaper.attack(target)
                for viking in idle_vikings:
                    viking.attack(target)

            # Zbylý SCV bot pošle těžit minerály nejblíže Command Center
            rafineryCount = self.structures(UnitTypeId.REFINERY).amount
            count = rafineryCount*3
            i = 0
            for scv in self.workers.idle:
                if i < count and rafineryCount > 0:
                    print('going to work to refinery')
                    scv.gather(self.structures(UnitTypeId.REFINERY).closest_to(command_center))
                else:
                    scv.gather(self.mineral_field.closest_to(command_center))
                i += 1

            if self.step == 180:
                self.closeRadius = 30 
            
            if self.step % 30 == 0:
                print('------------------------')
                print('marine',self.units.filter(lambda u: u.type_id == UnitTypeId.MARINE).amount)
                print('reapers',self.units.filter(lambda u: u.type_id == UnitTypeId.REAPER).amount)
                print('vikings',self.units.filter(lambda u: u.type_id == UnitTypeId.VIKING).amount)