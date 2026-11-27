"""Integração das telas, da partida e do perfil com SDL virtual."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame as pg

from src.marte.game import Game
from src.marte.profile import Profile


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.profile_path = Path(temp.name) / "perfil.json"
        self.game = Game(self.profile_path)
        self.addCleanup(pg.quit)

    def press(self, key):
        self.game.handle(pg.event.Event(pg.KEYDOWN, key=key))
        if self.game.running:
            self.game.draw()
            pg.display.flip()

    def test_navigation_and_pause(self):
        game = self.game
        self.press(pg.K_w)
        self.press(pg.K_w)
        self.press(pg.K_RETURN)
        self.assertEqual(game.state, "story")
        self.press(pg.K_ESCAPE)
        game.handle(pg.event.Event(pg.MOUSEBUTTONDOWN, pos=game.buttons[0].center, button=1))
        self.assertEqual(game.state, "name")
        game.name_input = ""
        game.handle(pg.event.Event(pg.TEXTINPUT, text="Márcia"))
        self.press(pg.K_RETURN)
        self.assertEqual(game.profile.pilot, "Márcia")
        self.assertEqual(game.state, "play")
        game.update(1 / 60)
        self.assertEqual(game.audio.track, "canion")
        self.press(pg.K_p)
        banner = game.mission.banner
        game.update(1 / 60)
        self.assertEqual(banner, game.mission.banner)
        self.press(pg.K_RETURN)
        game.handle(pg.event.Event(pg.WINDOWFOCUSLOST))
        self.assertEqual(game.state, "pause")
        self.press(pg.K_q)
        game.update(1 / 60)
        self.assertEqual(game.state, "menu")
        self.assertEqual(game.audio.track, "menu")
        self.press(pg.K_m)
        self.assertTrue(game.audio.muted)
        self.press(pg.K_ESCAPE)
        self.assertFalse(game.running)

    def test_completed_run_unlocks_ship_and_saves_style(self):
        game = self.game
        game.profile.set_pilot("Teste")
        game.start()
        game.mission.map_index = 1
        game.mission.wave = 3
        game.update(1 / 60)
        self.assertEqual(game.audio.track, "calota")
        game.mission.score = 2500
        game.mission.result = "victory"
        game.update(1 / 60)
        game.update(1 / 60)
        self.assertEqual(game.state, "victory")
        self.assertEqual(game.last_reward, 600)
        self.assertEqual(len(game.profile.ranking), 1)
        game.draw()
        self.press(pg.K_ESCAPE)
        self.press(pg.K_s)
        self.press(pg.K_RETURN)
        self.assertEqual(game.state, "shop")
        self.press(pg.K_d)
        self.press(pg.K_RETURN)
        self.press(pg.K_t)
        self.assertEqual(game.profile.equipped, "cometa")
        self.assertEqual(game.profile.credits, 250)
        saved = Profile(self.profile_path)
        self.assertEqual(saved.equipped, "cometa")
        self.assertEqual(saved.shot_style, "banana")
        self.assertEqual(saved.ranking[0]["map"], 2)
        self.press(pg.K_ESCAPE)
        self.press(pg.K_s)
        self.press(pg.K_RETURN)
        self.assertEqual(game.state, "ranking")
        self.press(pg.K_ESCAPE)
        game.start()
        self.assertEqual(game.mission.ship_id, "cometa")
        self.assertEqual(game.mission.score, 0)
        game.mission.result = "defeat"
        game.update(1 / 60)
        game.draw()
        self.press(pg.K_RETURN)
        self.assertEqual(game.state, "play")
        self.assertEqual(game.mission.lives, game.mission.max_lives)

    def test_main_loop_processes_quit(self):
        pg.event.post(pg.event.Event(pg.QUIT))
        self.game.run()
        self.assertFalse(pg.get_init())


if __name__ == "__main__":
    unittest.main()
