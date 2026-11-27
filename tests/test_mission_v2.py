"""Regras de campanha, super, power-ups e estilos de nave."""
import unittest

from src.marte.mission import (
    ARENA,
    MAPS,
    MAX_POWER,
    Laser,
    Mission,
    Obstacle,
    PowerUp,
    Ship,
)

FRAME = 1 / 60


class CampaignRulesTests(unittest.TestCase):
    def test_campaign_visits_both_bosses_and_awards_victory(self):
        mission = Mission(seed=17)
        visited_waves = set()
        bosses = []
        for _ in range(2400):
            visited_waves.add((mission.map_index, mission.map_wave))
            for enemy in mission.enemies:
                if enemy.y < ARENA.top + 26:
                    continue
                if enemy.kind == "boss" and mission.map_index == len(bosses):
                    bosses.append((mission.map.boss_name, enemy.max_hp))
                # Trava a mira nos inimigos para testar só as regras de campanha.
                mission.lasers.append(Laser(enemy.x, enemy.y, 0, damage=enemy.hp))
            mission.step(FRAME)
            if mission.result:
                break
        self.assertEqual(visited_waves, {(0, 1), (0, 2), (1, 1), (1, 2)})
        self.assertEqual(bosses, [(area.boss_name, area.boss_hp) for area in MAPS])
        self.assertEqual(mission.defeated_bosses, 2)
        self.assertEqual(mission.result, "victory")
        self.assertGreater(mission.score, 3000)

    def test_later_waves_spawn_faster_enemies(self):
        mission = Mission(seed=7)
        mission.banner = 0
        mission.step(FRAME)
        first_speed = mission.enemies[0].speed
        mission.wave = 3
        mission.map_index = 1
        mission._start_wave()
        mission.banner = 0
        mission.step(FRAME)
        self.assertGreater(mission.enemies[-1].speed, first_speed)

    def test_passive_player_is_defeated(self):
        mission = Mission(seed=4)
        for _ in range(2400):
            mission.step(FRAME)
            if mission.result:
                break
        self.assertEqual(mission.result, "defeat")
        self.assertEqual(mission.lives, 0)

    def test_movement_limits_and_cometa_double_shot(self):
        mission = Mission(seed=2, ship_id="cometa")
        mission.step(FRAME, direction=1, shoot=True)
        self.assertEqual(len(mission.lasers), 2)
        self.assertEqual(abs(mission.lasers[0].x - mission.lasers[1].x), 24)
        for _ in range(100):
            mission.step(FRAME, direction=1)
        self.assertLessEqual(mission.player.rect.right, ARENA.right)

    def test_bastiao_extra_life_and_contact_invulnerability(self):
        mission = Mission(seed=3, ship_id="bastiao")
        self.assertEqual(mission.lives, 4)
        for _ in range(2):
            mission.lasers.append(Laser(mission.player.x, mission.player.y, 338, True))
        mission.step(FRAME)
        self.assertEqual(mission.lives, 3)
        self.assertGreater(mission.shield, 0)

    def test_combo_and_powerup_drop(self):
        mission = Mission(seed=5)
        for _ in range(3):
            mission.enemies.append(Ship(500, 220, "scout"))
            mission.lasers.append(Laser(500, 220, -710))
            mission.step(FRAME)
        self.assertEqual(mission.score, 400)
        self.assertEqual(mission.combo, 2)
        self.assertEqual(mission.power, 51)
        self.assertEqual(mission.powerups[0].kind, "energy")
        for _ in range(245):
            mission.step(FRAME)
        self.assertEqual(mission.combo, 1)

    def test_powerups_apply_only_after_collection(self):
        mission = Mission(seed=3)
        mission.lives = 2
        for kind in ("repair", "energy", "rapid"):
            mission.powerups.append(PowerUp(mission.player.x, mission.player.y - 16, kind))
            mission.step(FRAME)
        self.assertEqual(mission.lives, 3)
        self.assertEqual(mission.power, 38)
        self.assertGreater(mission.weapon_time, 5)
        self.assertFalse(mission.powerups)

    def test_asteroid_intercepts_and_scores_when_destroyed(self):
        mission = Mission(seed=8)
        rock = Obstacle(500, 220, speed=0, hp=2)
        enemy = Ship(500, 220, "scout")
        mission.enemies.append(enemy)
        mission.obstacles.append(rock)
        for _ in range(2):
            mission.lasers.append(Laser(500, 231, -710))
            mission.step(FRAME)
        self.assertTrue(enemy in mission.enemies)
        self.assertFalse(mission.obstacles)
        self.assertEqual(mission.score, 30)

    def test_super_spends_full_meter_and_pierces_without_repeat_damage(self):
        mission = Mission(seed=11)
        mission.power = MAX_POWER - 1
        mission.step(FRAME, super_fire=True)
        self.assertFalse(mission.lasers)
        mission.power = MAX_POWER
        target = Obstacle(mission.player.x, mission.player.y - 130, speed=0, hp=12)
        mission.obstacles.append(target)
        mission.step(FRAME, super_fire=True)
        self.assertEqual(mission.power, 0)
        self.assertEqual(len(mission.lasers), 3)
        rock = Obstacle(mission.player.x, mission.player.y - 169, speed=0)
        mission.obstacles.append(rock)
        for _ in range(18):
            mission.step(FRAME)
        self.assertEqual(target.hp, 4)
        self.assertNotIn(rock, mission.obstacles)

