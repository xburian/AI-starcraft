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
    isAttacking: bool = False
    closeRadius: int = 8
    groupSize: int = 0
    attackGroup = []

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
            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= 30 and command_center.is_idle:
                command_center.train(UnitTypeId.SCV)

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 20 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=command_center)
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=command_center)

            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 8:
                    if self.can_afford(UnitTypeId.BARRACKS):
                        print('[INFO] gonna build barracks')
                        await self.build(
                            UnitTypeId.BARRACKS,
                            near=command_center.position.towards(self.game_info.map_center, 8))

            if self.structures(UnitTypeId.BARRACKS).amount > 0 and self.structures(UnitTypeId.REFINERY).amount < 2:
                if self.can_afford(UnitTypeId.REFINERY) and not self.already_pending(UnitTypeId.REFINERY):
                    gs = self.vespene_geyser.closer_than(self.closeRadius, command_center)
                    for g in gs:
                        if await self.can_place(UnitTypeId.REFINERY, g.position):
                            if self.workers.gathering.exists:
                                print('[INFO] gonna build refinery')
                                print(self.structures(UnitTypeId.REFINERY).amount)
                                worker = self.workers.gathering.closest_to(g)
                                worker.build(UnitTypeId.REFINERY, g)      

            if self.structures(UnitTypeId.BARRACKS).amount > 5 and self.structures(UnitTypeId.FACTORY).amount < 1:
                if self.can_afford(UnitTypeId.FACTORY) and not self.already_pending(UnitTypeId.FACTORY):
                    print('[INFO] gonna build factory')
                    await self.build(UnitTypeId.FACTORY, near=command_center.position.towards(self.game_info.map_center,8))
            
            if self.structures(UnitTypeId.BARRACKS).amount > 5 and self.structures(UnitTypeId.STARPORT).amount < 1:
                if self.can_afford(UnitTypeId.STARPORT) and not self.already_pending(UnitTypeId.STARPORT):
                    print('[INFO] gonna build starport')
                    await self.build(UnitTypeId.STARPORT, near=command_center.position.towards(self.game_info.map_center,8))

            # -----------------------------------------------------------------------------------
            # Trenovani jednotek
            # -----------------------------------------------------------------------------------

            if self.structures(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.MARINE):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                    barrack.train(UnitTypeId.MARINE)

            if self.structures(UnitTypeId.STARPORT).amount == 1:
                for stp in self.structures(UnitTypeId.STARPORT).idle:
                    if self.can_afford(UnitTypeId.VIKINGFIGHTER):
                        stp.train(UnitTypeId.VIKINGFIGHTER)

            # Trénování jednotky Reaper
            # Pouze, má-li bot postavené Barracks a může si jednotku dovolit
            if self.structures(UnitTypeId.BARRACKS) and self.can_afford(UnitTypeId.REAPER):
                # Každá budova Barracks trénuje v jeden čas pouze jednu jednotku (úspora zdrojů)
                for barrack in self.structures(UnitTypeId.BARRACKS).idle:
                    barrack.train(UnitTypeId.REAPER)

            if self.enemy_units.not_flying.closer_than(40, self.townhalls[0]):
                enemyUnitAround = self.enemy_units.not_flying.closer_than(40, self.townhalls[0])
                for unit in self.units.filter(lambda u: u.type_id != UnitTypeId.SCV).closer_than(40, command_center):
                    if unit not in self.attackGroup:
                        unit.attack(enemyUnitAround[0])
            else:
                for unit in self.units.filter(lambda u: u.type_id != UnitTypeId.SCV).closer_than(40, command_center):
                    if unit not in self.attackGroup:
                        unit.move(command_center)

            idle_marines = self.units(UnitTypeId.MARINE)
            idle_reapers = self.units(UnitTypeId.REAPER)
            idle_vikings = self.units(UnitTypeId.VIKING)

            for attacker in self.attackGroup:
                if attacker not in self.units:
                    self.attackGroup.remove(attacker)

            if idle_marines.amount > 20 + self.groupSize and self.isAttacking == False:
                print('[INFO] bot is attacking')
                for unit in self.attackGroup:
                    unit.move(command_center)
                
                for i in range(int(idle_marines.amount/3)):
                    self.attackGroup.append(idle_marines[i])
                
                for i in range(int(idle_reapers.amount/3)):
                    self.attackGroup.append(idle_reapers[i])

                for i in range(int(idle_vikings.amount/3)):
                    self.attackGroup.append(idle_vikings[i])

                self.isAttacking = True

                target = self.enemy_structures.random_or(
                    self.enemy_start_locations[0]).position

                for unit in self.attackGroup:
                    unit.attack(target)

            if self.isAttacking and len(self.attackGroup) == 0:
                print('[INFO] Attack group dismiss')
                self.attackGroup = []
                self.isAttacking = False

            # Zbylý SCV bot pošle těžit minerály nejblíže Command Center
            for scv in self.workers.idle:
                scv.gather(self.mineral_field.closest_to(command_center))

            if self.step == 360:
                self.closeRadius = 30 

            if self.step % 30 == 0:
                self.groupSize += 1
                await self.distribute_workers()
                print('------------------------')
                print('[INFO] group size' + str(self.groupSize))
                print('[INFO] marine',self.units.filter(lambda u: u.type_id == UnitTypeId.MARINE).amount)
                print('[INFO] reapers',self.units.filter(lambda u: u.type_id == UnitTypeId.REAPER).amount)
                print('[INFO] vikings',self.units.filter(lambda u: u.type_id == UnitTypeId.VIKINGFIGHTER).amount)
                print('[INFO] ' + str(len(self.attackGroup)))
                print('[INFO] ' + str(self.isAttacking))
                print('------------------------')