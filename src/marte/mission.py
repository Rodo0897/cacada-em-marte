"""Regras de Caçada em Marte independentes das telas e do áudio."""
from dataclasses import dataclass, field
from math import sin
import random

import pygame as pg

WIDTH, HEIGHT = 1000, 660
ARENA = pg.Rect(22, 89, 956, 505)
MAX_POWER = 100
COMBO_SECONDS = 4.0


@dataclass(frozen=True)
class ShipSpec:
    name: str
    description: str
    speed: int
    max_lives: int
    fire_delay: float
    color: tuple[int, int, int]
    barrels: tuple[int, ...] = (0,)
    charge_gain: int = 12


SHIPS = {
    "ares": ShipSpec("Ares", "Ganha energia do super mais rápido.", 455, 3, .19,
                     (104, 233, 231), charge_gain=17),
    "cometa": ShipSpec("Cometa", "Mais veloz e com disparos duplos.", 525, 3, .24,
                       (255, 220, 118), barrels=(-12, 12)),
    "bastiao": ShipSpec("Bastião", "Uma vida extra e menor velocidade.", 365, 4, .18,
                        (190, 166, 255)),
}


@dataclass(frozen=True)
class MapSpec:
    name: str
    boss_name: str
    boss_hp: int
    obstacle_interval: float


MAPS = (
    MapSpec("Cânion Ares", "Mandíbula Rubra", 24, 4.2),
    MapSpec("Calota Boreal", "Sentinela Boreal", 38, 3.3),
)
WAVES = ("Ronda no cânion", "Bloqueio de Ares", "Travessia polar", "Cerco à calota")
# Quantidade, intervalo de surgimento e velocidade inicial em pixels por segundo.
PATTERNS = ((6, .82, 82), (8, .70, 103), (8, .67, 116), (10, .56, 136))
SHIP_SIZES = {"player": (36, 30), "scout": (34, 26), "guard": (46, 30),
              "boss": (145, 60)}
ENEMY_POINTS = {"scout": 100, "guard": 200, "boss": 1000}


def centered_rect(x, y, size):
    rect = pg.Rect((0, 0), size)
    rect.center = round(x), round(y)
    return rect


@dataclass(eq=False)
class Ship:
    x: float
    y: float
    kind: str
    hp: int = 1
    speed: float = 0
    phase: float = 0
    clock: float = 0
    fire: float = 0
    max_hp: int = 1

    @property
    def rect(self):
        return centered_rect(self.x, self.y, SHIP_SIZES[self.kind])


@dataclass(eq=False)
class Obstacle:
    x: float
    y: float
    vx: float = 0
    speed: float = 116
    hp: int = 3

    @property
    def rect(self):
        return centered_rect(self.x, self.y, (40, 37))


@dataclass(eq=False)
class PowerUp:
    x: float
    y: float
    kind: str

    @property
    def rect(self):
        return centered_rect(self.x, self.y, (28, 28))


@dataclass(eq=False)
class Laser:
    x: float
    y: float
    vy: float
    hostile: bool = False
    vx: float = 0
    kind: str = "normal"
    damage: int = 1
    hits: set[Ship | Obstacle] = field(default_factory=set, repr=False)

    @property
    def rect(self):
        size = (34, 42) if self.kind == "super" else (7, 18)
        return centered_rect(self.x, self.y, size)


class Mission:
    def __init__(self, seed=None, ship_id="ares"):
        self.rng = random.Random(seed)
        self.ship_id = ship_id
        self.spec = SHIPS[ship_id]
        self.player = Ship(WIDTH / 2, ARENA.bottom - 35, "player")
        self.enemies: list[Ship] = []
        self.lasers: list[Laser] = []
        self.obstacles: list[Obstacle] = []
        self.powerups: list[PowerUp] = []
        self.events: list[tuple[str, float, float]] = []
        self.max_lives = self.spec.max_lives
        self.lives = self.max_lives
        self.score = 0
        self.combo = 1
        self.combo_chain = 0
        self.combo_timer = 0.0
        self.power = 0
        self.weapon_time = 0.0
        self.burst_time = 0.0
        self.cooldown = 0.0
        self.shield = 0.0
        self.wave = 0
        self.map_index = 0
        self.defeated_bosses = 0
        self.boss_deployed = False
        self.result = None
        self.breaches = 0
        self._kills = 0
        self._drop_index = 0
        self._start_wave()

    @property
    def map_wave(self):
        return self.wave % 2 + 1

    @property
    def map(self):
        return MAPS[self.map_index]

    def _start_wave(self):
        self.remaining = PATTERNS[self.wave][0]
        self.spawn_timer = 0.0
        self.hazard_timer = self.map.obstacle_interval
        self.banner = 1.65
        self.banner_title = WAVES[self.wave]
        self.banner_subtitle = f"{self.map.name.upper()}   /   ONDA {self.map_wave}/2"

    def step(self, dt, direction=0, shoot=False, super_fire=False):
        """Move as entidades, resolve contatos e avança a fase quando acaba."""
        self.events.clear()
        if self.result:
            return
        self._tick_timers(dt)
        self.player.x += direction * self.spec.speed * dt
        self.player.x = max(ARENA.left + 23, min(ARENA.right - 23, self.player.x))
        self._fire_player(shoot, super_fire)
        if self.banner == 0 and not self.boss_deployed:
            self.spawn(dt)
            self._spawn_obstacle(dt)
        self.move_enemies(dt)
        self._move_obstacles(dt)
        self.move_lasers(dt)
        self.resolve_contacts()
        if not self.result:
            self._move_powerups(dt)
            self.progress_wave()

    def _tick_timers(self, dt):
        self.shield = max(0, self.shield - dt)
        self.cooldown = max(0, self.cooldown - dt)
        self.banner = max(0, self.banner - dt)
        self.weapon_time = max(0, self.weapon_time - dt)
        self.burst_time = max(0, self.burst_time - dt)
        self.combo_timer = max(0, self.combo_timer - dt)
        if self.combo_timer == 0:
            self._reset_combo()

    def _fire_player(self, shoot, super_fire):
        x, y = self.player.x, self.player.y
        if super_fire and self.power == MAX_POWER:
            self.power = 0
            self.burst_time = .42
            # Três faixas perfurantes atingem cada alvo no máximo uma vez por faixa.
            for offset, drift in ((-30, -120), (0, 0), (30, 120)):
                self.lasers.append(Laser(x + offset, y - 28, -610, vx=drift,
                                         kind="super", damage=8))
            self.events.append(("super", x, y))
        if shoot and self.cooldown == 0:
            for offset in self.spec.barrels:
                self.lasers.append(Laser(x + offset, y - 22, -710))
            self.cooldown = self.spec.fire_delay * (.56 if self.weapon_time else 1)
            self.events.append(("laser", x, y))

    def spawn(self, dt):
        if not self.remaining:
            return
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        count, interval, speed = PATTERNS[self.wave]
        speed += (count - self.remaining) * 2
        x = self.rng.randint(85, WIDTH - 85)
        guard = self.wave > 0 and self.remaining % (2 if self.wave == 3 else 3) == 0
        hp = 2 if guard else 1
        self.enemies.append(Ship(x, ARENA.top - 22, "guard" if guard else "scout",
                                 hp, speed, self.rng.random() * 6, fire=1.45, max_hp=hp))
        self.remaining -= 1
        self.spawn_timer = interval

    def _spawn_obstacle(self, dt):
        self.hazard_timer -= dt
        if self.hazard_timer > 0:
            return
        x = self.rng.randint(80, WIDTH - 80)
        self.obstacles.append(Obstacle(x, ARENA.top - 25, self.rng.choice((-48, 48)),
                                       94 + self.map_index * 32))
        self.hazard_timer = self.map.obstacle_interval

    def move_enemies(self, dt):
        for enemy in self.enemies:
            enemy.clock += dt
            if enemy.kind == "boss":
                self._move_boss(enemy, dt)
                continue
            enemy.y += enemy.speed * dt
            enemy.x += 68 * sin(enemy.clock * 3 + enemy.phase) * dt
            enemy.x = max(ARENA.left + 28, min(ARENA.right - 28, enemy.x))
            if enemy.kind == "guard" and ARENA.top + 35 < enemy.y < ARENA.bottom - 120:
                enemy.fire -= dt
                if enemy.fire <= 0:
                    self.lasers.append(Laser(enemy.x, enemy.rect.bottom + 10, 245, True))
                    enemy.fire = 1.65

    def _move_boss(self, enemy, dt):
        stage = self.map_index
        enemy.y = min(206, enemy.y + 118 * dt)
        enemy.x = WIDTH / 2 + (278 + 46 * stage) * sin(enemy.clock * (.78 + stage * .24))
        if enemy.y < 154 or self.banner > 0:
            return
        enemy.fire -= dt
        if enemy.fire > 0:
            return
        if stage == 0:
            speeds, fall_speed, delay = (-125, 0, 125), 282, 1.26
        else:
            # O Sentinela mira a região da nave e espalha um leque mais aberto.
            aim = max(-145, min(145, (self.player.x - enemy.x) * .44))
            speeds = tuple(aim + offset for offset in (-176, -88, 0, 88, 176))
            fall_speed, delay = 312, 1.05
        for vx in speeds:
            self.lasers.append(Laser(enemy.x, enemy.rect.bottom + 10, fall_speed, True, vx))
        enemy.fire = delay

    def _move_obstacles(self, dt):
        for obstacle in self.obstacles:
            obstacle.x += obstacle.vx * dt
            obstacle.y += obstacle.speed * dt
            if not ARENA.left + 22 <= obstacle.x <= ARENA.right - 22:
                obstacle.vx *= -1
                obstacle.x = max(ARENA.left + 22, min(ARENA.right - 22, obstacle.x))

    def move_lasers(self, dt):
        for laser in self.lasers[:]:
            laser.x += laser.vx * dt
            laser.y += laser.vy * dt
            if not ARENA.colliderect(laser.rect):
                self.lasers.remove(laser)
                continue
            if laser.hostile:
                if laser.rect.colliderect(self.player.rect):
                    self.lasers.remove(laser)
                    self.hurt()
                continue
            self._hit_targets(laser)

    def _hit_targets(self, laser):
        # As rochas interceptam o tiro normal. O super continua após o impacto.
        for target in [*self.obstacles, *self.enemies]:
            if target in laser.hits or not laser.rect.colliderect(target.rect):
                continue
            target.hp -= laser.damage
            if target.hp <= 0:
                self._destroy_target(target)
            else:
                self.events.append(("spark", laser.x, laser.y))
            if laser.kind != "super":
                self.lasers.remove(laser)
                return
            laser.hits.add(target)

    def _destroy_target(self, target):
        self.events.append(("burst", target.x, target.y))
        if isinstance(target, Obstacle):
            self.obstacles.remove(target)
            self.score += 30
            self._charge(5)
            return
        self.enemies.remove(target)
        if target.kind == "boss":
            self.defeated_bosses += 1
            self.score += ENEMY_POINTS["boss"] * self.defeated_bosses
            self._charge(30)
            return
        self.combo_chain += 1
        self.combo = min(5, 1 + self.combo_chain // 3)
        self.combo_timer = COMBO_SECONDS
        self.score += ENEMY_POINTS[target.kind] * self.combo
        self._charge(self.spec.charge_gain)
        self._kills += 1
        if self._kills % 3 == 0:
            drops = ("energy", "rapid", "repair")
            self.powerups.append(PowerUp(target.x, target.y, drops[self._drop_index % len(drops)]))
            self._drop_index += 1

    def _charge(self, amount):
        self.power = min(MAX_POWER, self.power + amount)

    def _reset_combo(self):
        self.combo_chain = 0
        self.combo = 1
        self.combo_timer = 0.0

    def resolve_contacts(self):
        for obstacle in self.obstacles[:]:
            if obstacle.rect.colliderect(self.player.rect):
                self.obstacles.remove(obstacle)
                self.events.append(("burst", obstacle.x, obstacle.y))
                self.hurt()
            elif obstacle.rect.top >= ARENA.bottom:
                self.obstacles.remove(obstacle)
        for enemy in self.enemies[:]:
            if enemy.kind == "boss":
                continue
            if enemy.rect.colliderect(self.player.rect):
                self.enemies.remove(enemy)
                self.events.append(("burst", enemy.x, enemy.y))
                self.hurt()
            elif enemy.rect.top >= ARENA.bottom:
                self.enemies.remove(enemy)
                self._reset_combo()
                self.breaches += 1
                if self.breaches == 3:
                    self.breaches = 0
                    self.hurt()

    def _move_powerups(self, dt):
        for pickup in self.powerups[:]:
            pickup.y += 146 * dt
            if pickup.rect.colliderect(self.player.rect):
                self.powerups.remove(pickup)
                self.events.append((f"pickup_{pickup.kind}", pickup.x, pickup.y))
                if pickup.kind == "repair":
                    if self.lives < self.max_lives:
                        self.lives += 1
                    else:
                        self.score += 100
                elif pickup.kind == "rapid":
                    self.weapon_time = 6
                elif pickup.kind == "energy":
                    self._charge(38)
            elif pickup.rect.top >= ARENA.bottom:
                self.powerups.remove(pickup)

    def hurt(self):
        if self.shield or self.result:
            return
        self.lives -= 1
        self.shield = 1.05
        self._reset_combo()
        self.events.append(("hurt", self.player.x, self.player.y))
        if self.lives == 0:
            self.result = "defeat"

    def progress_wave(self):
        if self.enemies or self.remaining:
            return
        if self.boss_deployed:
            if self.map_index == len(MAPS) - 1:
                self.result = "victory"
                return
            self.lives = min(self.max_lives, self.lives + 1)
            self.wave += 1
            self.map_index += 1
            self.boss_deployed = False
            self.breaches = 0
            self._reset_combo()
            self.lasers.clear()
            self.obstacles.clear()
            self.powerups.clear()
            self._start_wave()
            self.events.append(("map", WIDTH / 2, 0))
        elif self.map_wave == 2:
            self.boss_deployed = True
            self.lasers = [laser for laser in self.lasers if not laser.hostile]
            self.obstacles.clear()
            self.banner = 1.65
            self.banner_title = self.map.boss_name
            self.banner_subtitle = f"{self.map.name.upper()}   /   CHEFE"
            hp = self.map.boss_hp
            self.enemies.append(Ship(WIDTH / 2, ARENA.top - 38, "boss", hp, fire=.75, max_hp=hp))
            self.events.append(("boss", WIDTH / 2, 0))
        else:
            self.wave += 1
            self.lasers = [laser for laser in self.lasers if not laser.hostile]
            self._start_wave()
            self.events.append(("wave", WIDTH / 2, 0))
