"""Verifica a loja e o ranking sem tocar nos dados do jogador."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.marte.profile import Profile, RANKING_LIMIT, SHIP_PRICES


class ProfileTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "dados" / "perfil.json"

    def test_record_and_purchase_persist_without_charging_twice(self):
        profile = Profile(self.path)
        self.assertFalse(profile.select_ship("cometa"))
        self.assertEqual(profile.equipped, "ares")
        profile.set_pilot("  Nícolas  ")
        profile.set_shot_style("banana")
        self.assertEqual(profile.record(2500, 2, "victory"), 600)
        self.assertTrue(profile.select_ship("cometa"))

        restored = Profile(self.path)
        self.assertEqual(restored.pilot, "Nícolas")
        self.assertEqual(restored.shot_style, "banana")
        self.assertEqual(restored.equipped, "cometa")
        self.assertEqual(restored.ranking[0], {
            "pilot": "Nícolas", "score": 2500, "map": 2, "result": "victory",
        })
        self.assertTrue(restored.select_ship("ares"))
        self.assertTrue(restored.select_ship("cometa"))
        self.assertEqual(restored.credits, 600 - SHIP_PRICES["cometa"])

    def test_ranking_keeps_best_scores_and_prioritizes_victory_on_ties(self):
        profile = Profile(self.path)
        for score in range(1, 16):
            profile.record(score, 1, "defeat")
        profile.record(15, 2, "victory")
        ranking = Profile(self.path).ranking
        self.assertEqual(len(ranking), RANKING_LIMIT)
        self.assertEqual([row["score"] for row in ranking], [15, 15, 14, 13, 12, 11, 10, 9, 8, 7])
        self.assertEqual(ranking[0]["result"], "victory")

    def test_cancelled_mission_and_zero_point_defeat_do_not_rank(self):
        profile = Profile(self.path)
        self.assertEqual(profile.record(500, 1, "pause"), 0)
        self.assertEqual(profile.record(0, 1, "defeat"), 0)
        self.assertEqual(Profile(self.path).ranking, [])
        self.assertEqual(Profile(self.path).credits, 0)

    def test_profile_recovers_from_corruption_and_reports_write_error(self):
        self.path.parent.mkdir()
        self.path.write_text("quebrado!", encoding="utf-8")
        damaged = Profile(self.path)
        self.assertTrue(damaged.warning)
        self.assertEqual(damaged.credits, 0)
        damaged.set_pilot("Rodrigo")
        self.assertFalse(damaged.warning)
        self.assertEqual(Profile(self.path).pilot, "Rodrigo")

        invalid_path = self.path / "perfil.json"
        read_only = Profile(invalid_path)
        read_only.set_shot_style("coco")
        self.assertEqual(read_only.shot_style, "coco")
        self.assertTrue(read_only.warning)
