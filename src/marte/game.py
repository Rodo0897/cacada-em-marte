"""Janela, controles e telas de Caçada em Marte."""
import math

import pygame as pg

from .art import (
    CREAM, MUTED, ORANGE, CYAN, RED, INK, Sky, Particles, ship, draw_laser,
    draw_obstacle, draw_pickup,
)
from .audio import Audio, RATE
from .mission import ARENA, WIDTH, HEIGHT, MAPS, SHIPS, Mission
from .profile import PILOT_MAX_LENGTH, SHIP_PRICES, SHOT_STYLES, Profile

STYLE_NAMES = {"laser": "Laser", "banana": "Banana", "coco": "Cocô"}
PICKUP_LABELS = {"repair": "Reparo", "rapid": "Tiro rápido", "energy": "Energia"}


class Game:
    def __init__(self, profile_path=None):
        pg.mixer.pre_init(RATE, -16, 1, 512)
        pg.init()
        try:
            self.screen = pg.display.set_mode((WIDTH, HEIGHT), pg.SCALED)
        except pg.error:
            self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Caçada em Marte")
        icon = pg.Surface((56, 56), pg.SRCALPHA)
        ship(icon, (28, 24), "player", scale=.85)
        pg.display.set_icon(icon)
        pg.key.stop_text_input()
        self.clock = pg.time.Clock()
        self.audio = Audio()
        self.sky = Sky()
        self.particles = Particles()
        self.profile = Profile(profile_path)
        self.fonts = {}
        self.time = 0
        self.running = True
        self.state = "menu"
        self.mission = Mission(ship_id=self.profile.equipped)
        self.selection = 0
        self.shop_index = 0
        self.shop_message = ""
        self.name_input = ""
        self.last_reward = 0
        self.pickup_label = ""
        self.pickup_notice = 0
        self.choices = (("Iniciar missão", "play"), ("Hangar e tiros", "shop"),
                        ("Ranking local", "ranking"), ("História e controles", "story"),
                        ("Sair", "quit"))
        self.buttons = [pg.Rect(62, 340 + index * 46, 318, 39) for index in range(5)]
        self.shop_cards = [pg.Rect(60 + index * 302, 196, 276, 235) for index in range(3)]
        self.style_button = pg.Rect(60, 459, 430, 54)
        self.dim = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        self.dim.fill((12, 10, 22, 191))

    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(60) / 1000, 1 / 30)
                for event in pg.event.get():
                    self.handle(event)
                if self.running:
                    self.update(dt)
                    self.draw()
                    pg.display.flip()
        finally:
            pg.quit()

    def handle(self, event):
        if event.type == pg.QUIT:
            self.running = False
        elif event.type == pg.WINDOWFOCUSLOST and self.state == "play":
            self.state = "pause"
        elif self.state == "name" and event.type == pg.TEXTINPUT:
            remaining = PILOT_MAX_LENGTH - len(self.name_input)
            clean = "".join(char for char in event.text if char.isprintable())
            self.name_input += clean[:remaining]
        elif event.type == pg.KEYDOWN:
            self.key(event.key)
        elif event.type in (pg.MOUSEMOTION, pg.MOUSEBUTTONDOWN):
            clicked = event.type == pg.MOUSEBUTTONDOWN and event.button == 1
            if self.state == "menu":
                for index, rect in enumerate(self.buttons):
                    if rect.collidepoint(event.pos):
                        self.selection = index
                        if clicked:
                            self.activate()
                        break
            elif self.state == "shop" and clicked:
                if self.style_button.collidepoint(event.pos):
                    self.cycle_style()
                else:
                    for index, card in enumerate(self.shop_cards):
                        if card.collidepoint(event.pos):
                            self.shop_index = index
                            self.buy_ship()
                            break

    def activate(self):
        self.audio.play("select")
        _, choice = self.choices[self.selection]
        if choice == "play":
            self.name_input = self.profile.pilot
            self.state = "name"
            pg.key.start_text_input()
        elif choice == "quit":
            self.running = False
        else:
            self.shop_index = list(SHIPS).index(self.profile.equipped)
            self.shop_message = ""
            self.state = choice

    def start(self):
        pg.key.stop_text_input()
        self.mission = Mission(ship_id=self.profile.equipped)
        self.particles = Particles()
        self.last_reward = 0
        self.pickup_notice = 0
        self.state = "play"

    def menu_key(self, key):
        if key in (pg.K_UP, pg.K_DOWN, pg.K_w, pg.K_s):
            step = -1 if key in (pg.K_UP, pg.K_w) else 1
            self.selection = (self.selection + step) % len(self.choices)
            self.audio.play("select")
        elif key in (pg.K_RETURN, pg.K_SPACE):
            self.activate()
        elif key == pg.K_ESCAPE:
            self.running = False

    def name_key(self, key):
        if key == pg.K_BACKSPACE:
            self.name_input = self.name_input[:-1]
        elif key == pg.K_RETURN:
            self.profile.set_pilot(self.name_input)
            self.start()
        elif key == pg.K_ESCAPE:
            pg.key.stop_text_input()
            self.state = "menu"

    def buy_ship(self):
        ship_id = list(SHIPS)[self.shop_index]
        if self.profile.select_ship(ship_id):
            self.shop_message = f"{SHIPS[ship_id].name} equipada."
            self.audio.play("select")
        else:
            self.shop_message = "Créditos insuficientes para esta nave."

    def cycle_style(self):
        index = SHOT_STYLES.index(self.profile.shot_style)
        self.profile.set_shot_style(SHOT_STYLES[(index + 1) % len(SHOT_STYLES)])
        self.audio.play("select")

    def shop_key(self, key):
        if key in (pg.K_LEFT, pg.K_RIGHT, pg.K_a, pg.K_d):
            step = -1 if key in (pg.K_LEFT, pg.K_a) else 1
            self.shop_index = (self.shop_index + step) % len(SHIPS)
            self.shop_message = ""
        elif key == pg.K_RETURN:
            self.buy_ship()
        elif key == pg.K_t:
            self.cycle_style()
        elif key == pg.K_ESCAPE:
            self.state = "menu"

    def key(self, key):
        if self.state == "name":
            self.name_key(key)
        elif key == pg.K_m:
            self.audio.toggle()
        elif self.state == "menu":
            self.menu_key(key)
        elif self.state == "shop":
            self.shop_key(key)
        elif self.state in ("story", "ranking") and key in (pg.K_ESCAPE, pg.K_RETURN):
            self.state = "menu"
        elif self.state == "play" and key in (pg.K_ESCAPE, pg.K_p):
            self.state = "pause"
        elif self.state == "pause":
            if key in (pg.K_ESCAPE, pg.K_p, pg.K_RETURN):
                self.state = "play"
            elif key == pg.K_q:
                self.state = "menu"
        elif self.state in ("victory", "defeat"):
            if key == pg.K_RETURN:
                self.start()
            elif key == pg.K_ESCAPE:
                self.state = "menu"

    def update(self, dt):
        if self.state == "pause":
            return
        if self.state != "play":
            self.audio.set_track("menu")
        self.time += dt
        self.particles.update(dt)
        if self.state != "play":
            return
        self.pickup_notice = max(0, self.pickup_notice - dt)
        keys = pg.key.get_pressed()
        direction = int(keys[pg.K_RIGHT] or keys[pg.K_d]) - int(keys[pg.K_LEFT] or keys[pg.K_a])
        self.mission.step(dt, direction, keys[pg.K_SPACE], keys[pg.K_x])
        self.audio.set_track(("canion", "calota")[self.mission.map_index])
        for kind, x, y in self.mission.events:
            self.audio.play(kind)
            if kind in ("burst", "hurt", "spark", "super") or kind.startswith("pickup"):
                count = {"burst": 22, "hurt": 16, "spark": 5, "super": 27}.get(kind, 18)
                self.particles.burst(x, y, ORANGE if kind in ("burst", "spark") else CYAN, count)
            if kind.startswith("pickup"):
                pickup_kind = kind.partition("_")[2]
                self.pickup_label = PICKUP_LABELS.get(pickup_kind, "Melhoria coletada")
                self.pickup_notice = 1.25
        if self.mission.result:
            self.state = self.mission.result
            # A troca de tela impede que a mesma partida seja registrada a cada quadro.
            self.last_reward = self.profile.record(self.mission.score, self.mission.map_index + 1,
                                                   self.mission.result)
            self.audio.play(self.state)

    def font(self, size, bold):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = pg.font.SysFont("bahnschrift,arial,dejavusans", size, bold=bold)
        return self.fonts[key]

    def label(self, value, size, x, y, color=CREAM, bold=False, center=False, max_width=None):
        font = self.font(size, bold)
        if max_width:
            while font.size(value)[0] > max_width and len(value) > 1:
                value = value.rstrip("…")[:-1] + "…"
                if value == "…":
                    break
        text = font.render(value, True, color)
        rect = text.get_rect(midtop=(x, y)) if center else text.get_rect(topleft=(x, y))
        self.screen.blit(text, rect)

    def panel(self, rect, edge=(119, 76, 90), fill=INK):
        pg.draw.rect(self.screen, fill, rect, border_radius=9)
        pg.draw.rect(self.screen, edge, rect, 1, border_radius=9)

    def draw(self):
        in_mission = self.state in ("play", "pause", "victory", "defeat")
        self.sky.draw(self.screen, self.time, not in_mission, self.mission.map_index if in_mission else 0)
        if in_mission:
            self.draw_mission()
            if self.state != "play":
                self.draw_overlay()
        else:
            pages = {"menu": self.draw_menu, "story": self.draw_story,
                     "shop": self.draw_shop, "ranking": self.draw_ranking, "name": self.draw_name}
            pages[self.state]()
        pg.draw.line(self.screen, (109, 69, 87), (24, 613), (976, 613))
        self.label("NICOLAS E RODRIGO   /   PROJETO A3", 15, 25, 627, MUTED)
        sound = "sem áudio" if not self.audio.effects else ("mudo" if self.audio.muted else "ligado")
        self.label(f"M   /   SOM: {sound.upper()}", 15, 810, 627, MUTED)

    def draw_menu(self):
        self.label("ARCADE 2D   /   COLÔNIA ARES", 16, 64, 88, ORANGE, True)
        self.label("CAÇADA", 86, 55, 118, CREAM, True)
        self.label("EM MARTE", 86, 55, 194, ORANGE, True)
        self.label("Proteja a colônia. Intercepte a frota.", 22, 64, 289, MUTED)
        color = SHIPS[self.profile.equipped].color
        ship(self.screen, (762, 291 + math.sin(self.time * 2) * 10), "player",
             self.time, 4, accent=color, variant=self.profile.equipped)
        for index, ((title, _), rect) in enumerate(zip(self.choices, self.buttons)):
            selected = index == self.selection
            self.panel(rect, ORANGE if selected else (119, 76, 90),
                       (78, 38, 48) if selected else INK)
            self.label(title, 20, rect.x + 18, rect.y + 8, CREAM, selected)
        self.label("W / S   Selecionar     ENTER   Confirmar", 16, 64, 579, MUTED)

    def draw_story(self):
        self.panel(pg.Rect(61, 62, 878, 523))
        self.label("RELATÓRIO DE MISSÃO   /   2150", 17, 91, 87, ORANGE, True)
        self.label("Defenda a colônia Ares", 46, 90, 113, CREAM, True)
        lines = ("A primeira cidade humana de Marte perdeu contato com a Terra.",
                 "Você pilota a última nave de defesa. Atravesse o cânion e a calota.",
                 "Vença a Mandíbula Rubra e a Sentinela Boreal para salvar a colônia.")
        for index, line in enumerate(lines):
            self.label(line, 21, 92, 174 + 27 * index)
        pg.draw.line(self.screen, (119, 76, 90), (92, 265), (908, 265))
        self.label("CONTROLES", 17, 92, 285, ORANGE, True)
        self.label("REGRAS", 17, 470, 285, ORANGE, True)
        for index, (key, help_text) in enumerate((
            ("A / D", "Mover (ou setas)"), ("ESPAÇO", "Segurar para atirar"),
            ("X", "Super com 100% de carga"), ("P / ESC", "Pausar"), ("M", "Silenciar"),
        )):
            y = 321 + 34 * index
            self.label(key, 18, 92, y, CYAN, True)
            self.label(help_text, 18, 201, y)
        for index, line in enumerate((
            "Inimigos e asteroides dão pontos ao cair.",
            "Abates em sequência elevam o combo até ×5.",
            "Desvie dos tiros e colete as melhorias.",
            "A cada 3 fugas, você perde uma vida.",
            "Sem vidas, a missão termina em derrota.",
        )):
            self.label(line, 18, 470, 321 + 34 * index)
        self.label("ESC ou ENTER   /   Voltar", 16, 93, 535, MUTED)

    def draw_name(self):
        self.panel(pg.Rect(235, 181, 530, 276), ORANGE)
        self.label("Nome no ranking", 42, 500, 216, CREAM, True, True)
        self.label("Use um nome ou apelido para identificar a pontuação.", 19, 500, 279, MUTED, center=True)
        self.panel(pg.Rect(297, 320, 406, 51), CYAN)
        self.label(self.name_input or "Piloto", 23, 315, 332,
                   CREAM if self.name_input else MUTED, max_width=370)
        self.label("ENTER   Iniciar      ESC   Voltar", 17, 500, 402, ORANGE, center=True)

    def draw_shop(self):
        self.panel(pg.Rect(38, 60, 924, 521))
        self.label("Hangar", 48, 60, 87, CREAM, True)
        self.label(f"{self.profile.credits} CRÉDITOS", 23, 727, 112, ORANGE, True)
        self.label("Ganhe créditos ao concluir partidas.", 18, 63, 154, MUTED)
        for index, ((ship_id, spec), card) in enumerate(zip(SHIPS.items(), self.shop_cards)):
            active = index == self.shop_index
            self.panel(card, spec.color if active else (119, 76, 90), (35, 27, 47))
            center = card.centerx
            ship(self.screen, (center, 251), "player", self.time, 1.55,
                 accent=spec.color, variant=ship_id)
            self.label(spec.name, 28, center, 300, CREAM, True, True)
            for line_index, line in enumerate(self.ship_ability(ship_id)):
                self.label(line, 17, center, 341 + line_index * 20, MUTED, center=True)
            if ship_id == self.profile.equipped:
                status = "EQUIPADA"
            elif ship_id in self.profile.unlocked:
                status = "EQUIPAR"
            else:
                status = f"COMPRAR · {SHIP_PRICES[ship_id]} CR"
            self.label(status, 17, center, 399, spec.color, True, True)
        self.panel(self.style_button, (119, 76, 90), (35, 27, 47))
        style = self.profile.shot_style
        self.label(f"T   Estilo do tiro: {STYLE_NAMES[style]}", 20, 79, 473, CREAM)
        draw_laser(self.screen, pg.Rect(440, 472, 7, 18), style, CYAN)
        self.label("A / D   Nave     ENTER   Usar     ESC   Voltar", 16, 61, 539, MUTED)
        if self.shop_message or self.profile.warning:
            self.label(self.profile.warning or self.shop_message, 15, 512, 471, ORANGE)

    @staticmethod
    def ship_ability(ship_id):
        return {
            "ares": ("Carrega o super", "mais depressa"),
            "cometa": ("Dois disparos", "e movimento mais veloz"),
            "bastiao": ("Uma vida extra", "e movimento mais lento"),
        }[ship_id]

    def draw_ranking(self):
        self.panel(pg.Rect(62, 60, 876, 521))
        self.label("Ranking local", 48, 91, 85, CREAM, True)
        for title, x in (("#", 92), ("PILOTO", 146), ("PONTOS", 490), ("MAPA", 676), ("RESULTADO", 769)):
            self.label(title, 17, x, 157, ORANGE, True)
        for index, entry in enumerate(self.profile.ranking, start=1):
            y = 191 + (index - 1) * 32
            if index % 2:
                pg.draw.rect(self.screen, (35, 27, 47), (83, y - 2, 835, 28), border_radius=4)
            result = "Vitória" if entry["result"] == "victory" else "Derrota"
            for value, x in ((str(index), 93), (entry["pilot"], 146),
                             (str(entry["score"]), 491), (str(entry["map"]), 677), (result, 770)):
                self.label(value, 19, x, y, CREAM, max_width=325 if x == 146 else None)
        if not self.profile.ranking:
            self.label("Conclua uma partida com pontos para estrear o ranking.", 22, 500, 283, MUTED, center=True)
        self.label(self.profile.warning or "ESC ou ENTER   /   Voltar", 16, 91, 542, MUTED)

    def draw_mission(self):
        mission = self.mission
        map_spec = MAPS[mission.map_index]
        self.panel(pg.Rect(22, 16, 956, 61))
        self.label(map_spec.name.upper(), 19, 41, 24, ORANGE, True)
        stage = "CHEFE" if mission.boss_deployed else f"ONDA {mission.map_wave}/2"
        self.label(f"MAPA {mission.map_index + 1}/{len(MAPS)}   •   {stage}", 16, 41, 50)
        self.label("PONTOS", 15, 340, 24, MUTED)
        self.label(f"{mission.score:06}   ×{mission.combo}", 23, 340, 42, CREAM, True)
        self.label("VIDAS", 15, 555, 24, MUTED)
        for index in range(mission.max_lives):
            x = 563 + index * 24
            color = CYAN if index < mission.lives else (91, 69, 89)
            pg.draw.polygon(self.screen, color, [(x, 46), (x + 7, 55), (x, 62), (x - 7, 55)])
        self.label(f"FUGAS {mission.breaches}/3", 13, 655, 46, MUTED)
        ready = mission.power >= 100
        self.label("X   SUPER PRONTO" if ready else f"SUPER   {int(mission.power)}%", 15, 734, 24,
                   CYAN if ready else MUTED, True)
        pg.draw.rect(self.screen, (54, 47, 69), (734, 52, 219, 8), border_radius=3)
        pg.draw.rect(self.screen, CYAN, (734, 52, round(219 * min(100, mission.power) / 100), 8),
                     border_radius=3)
        edge = (106, 148, 177) if mission.map_index else (129, 77, 93)
        pg.draw.rect(self.screen, edge, ARENA, 1, border_radius=5)
        pg.draw.line(self.screen, edge, (ARENA.left + 8, ARENA.bottom - 2),
                     (ARENA.right - 8, ARENA.bottom - 2))
        self.screen.set_clip(ARENA.inflate(-2, -2))
        if mission.lives and (not mission.shield or int(mission.shield * 13) % 2 == 0):
            ship(self.screen, (mission.player.x, mission.player.y), "player", self.time,
                 accent=mission.spec.color, variant=mission.ship_id)
        for obstacle in mission.obstacles:
            draw_obstacle(self.screen, obstacle)
        for pickup in mission.powerups:
            draw_pickup(self.screen, pickup, self.time)
        for enemy in mission.enemies:
            variant = "boreal" if enemy.kind == "boss" and mission.map_index else ""
            ship(self.screen, (enemy.x, enemy.y), enemy.kind, variant=variant)
            if enemy.kind == "boss":
                bar = pg.Rect(0, 0, 139, 6)
                bar.midtop = round(enemy.x), round(enemy.y + 39)
                pg.draw.rect(self.screen, INK, bar)
                pg.draw.rect(self.screen, CYAN if variant else RED,
                             (bar.x, bar.y, round(bar.w * enemy.hp / enemy.max_hp), bar.h))
        for laser in mission.lasers:
            style = "laser" if laser.hostile else self.profile.shot_style
            draw_laser(self.screen, laser.rect, style, RED if laser.hostile else CYAN, laser.kind)
        self.particles.draw(self.screen)
        self.screen.set_clip(None)
        if self.pickup_notice:
            self.label(self.pickup_label, 19, 500, 477, CYAN, True, True)
        if mission.weapon_time > 0:
            self.label(f"TIRO RÁPIDO  {mission.weapon_time:.1f}s", 16, 38, 569, ORANGE, True)
        if mission.banner > 0:
            self.panel(pg.Rect(254, 241, 492, 126), edge)
            self.label(mission.banner_subtitle.upper(), 16, 500, 262, ORANGE, True, True)
            self.label(mission.banner_title, 34, 500, 285, CREAM, True, True)
            if mission.boss_deployed:
                caption = ("O sinal da frota vem desta nave." if mission.map_index
                           else "A frota bloqueou a saída do cânion.")
            elif mission.map_index == 1:
                caption = "A frota recuou até a calota. Intercepte os reforços."
            else:
                caption = "Intercepte as naves antes que cheguem à colônia."
            self.label(caption, 17, 500, 333, MUTED, center=True)

    def draw_overlay(self):
        self.screen.blit(self.dim, (0, 0))
        self.panel(pg.Rect(220, 191, 560, 265), ORANGE)
        title, detail, controls = {
            "pause": ("Missão pausada", "A colônia está aguardando.", "P / ESC   Continuar     •     Q   Menu"),
            "victory": ("Colônia a salvo", "Os dois chefes foram derrotados.", "ENTER   Jogar de novo     •     ESC   Menu"),
            "defeat": ("Sinal perdido", "A nave da colônia ficou sem vidas.", "ENTER   Tentar de novo     •     ESC   Menu"),
        }[self.state]
        self.label(title, 48, 500, 216, CREAM, True, True)
        self.label(detail, 22, 500, 282, MUTED, center=True)
        if self.state != "pause":
            self.label(f"{self.mission.score} PONTOS   /   +{self.last_reward} CRÉDITOS",
                       21, 500, 334, CYAN, True, True)
            if self.profile.warning:
                self.label(self.profile.warning, 15, 500, 369, ORANGE, center=True)
        self.label(controls, 19, 500, 404, ORANGE, center=True)
