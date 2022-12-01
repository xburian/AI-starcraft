from sc2.bot_ai import BotAI, Race
from sc2.ids.unit_typeid import UnitTypeId


class MarineRushBot(BotAI):
    NAME: str = "MarineRushBot"
    RACE: Race = Race.Terran

    async def on_unit_took_damage(self, unit: UnitTypeId.MARINE, amount_damage_taken: float):
        print('MARINE took demage')
        target = self.enemy_structures.random_or(
        self.enemy_start_locations[0]).position

        idle_marines = self.units(UnitTypeId.MARINE).idle
        for marine in idle_marines:
                marine.attack(target)

    async def on_step(self, iteration: int):
        # Jestliže mám Command Center
        if self.townhalls:
            # První Command Center
            command_center = self.townhalls[0]

            # -----------------------------------------------------------------------------------
            # Trenovani stavitelu, budov
            # -----------------------------------------------------------------------------------

            # Trénování SCV
            # Bot trénuje nová SCV, jestliže je jich méně než 17
            if self.can_afford(UnitTypeId.SCV) and self.supply_workers <= 16 and command_center.is_idle:
                command_center.train(UnitTypeId.SCV)

            # Postav Supply Depot, jestliže zbývá méně než 6 supply a je využito více než 13
            if self.supply_left < 6 and self.supply_used >= 14 and not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.can_afford(UnitTypeId.SUPPLYDEPOT):
                    # Budova bude postavena poblíž Command Center směrem ke středu mapy
                    # SCV pro stavbu bude vybráno automaticky viz dokumentace
                    await self.build(
                        UnitTypeId.SUPPLYDEPOT,
                        near=command_center.position.towards(self.game_info.map_center, 8))

            # Stavba Barracks
            # Bot staví tak dlouho, dokud si může dovolit stavět Barracks a jejich počet je menší než 6
            if self.tech_requirement_progress(UnitTypeId.BARRACKS) == 1:
                # Je jich méně než 6 nebo se již nějaké nestaví
                if self.structures(UnitTypeId.BARRACKS).amount < 6:
                    if self.can_afford(UnitTypeId.BARRACKS) and not self.already_pending(UnitTypeId.BARRACKS):
                        await self.build(
                            UnitTypeId.BARRACKS,
                            near=command_center.position.towards(self.game_info.map_center, 8))
                if self.structures(UnitTypeId.REFINERY).amount == 0:
                    if self.can_afford(UnitTypeId.REFINERY) and not self.already_pending(UnitTypeId.REFINERY):
                        gs = self.vespene_geyser.closer_than(10, command_center)
                        for g in gs:
                            if await self.can_place(UnitTypeId.REFINERY, g.position):
                                if self.workers.gathering.exists:
                                    worker = self.workers.gathering.closest_to(g)
                                    print(str(worker) + 'is going to build REFINERY')
                                    worker.build(UnitTypeId.REFINERY, g)        

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

            # -----------------------------------------------------------------------------------
            # Útok s jednotkou Marine
            # -----------------------------------------------------------------------------------

            # Má-li bot více než 15 volných jednotek Marine, zaútočí na náhodnou nepřátelskou budovu nebo se přesune na jeho startovní pozici
            idle_marines = self.units(UnitTypeId.MARINE).idle
            if idle_marines.amount > 15:
                target = self.enemy_structures.random_or(
                    self.enemy_start_locations[0]).position
                for marine in idle_marines:
                    marine.attack(target)

            # Zbylý SCV bot pošle těžit minerály nejblíže Command Center
            for scv in self.workers.idle:
                scv.gather(self.mineral_field.closest_to(command_center))