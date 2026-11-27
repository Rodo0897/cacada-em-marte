"""Cenário e desenhos vetoriais feitos com as primitivas do Pygame."""
from math import sin, cos
import random

import pygame as pg

from .mission import WIDTH, HEIGHT, ARENA

CREAM = (255, 239, 221)
MUTED = (206, 173, 163)
ORANGE = (255, 152, 98)
CYAN = (104, 233, 231)
RED = (255, 105, 119)
INK = (18, 15, 28)


def ship(surface, center, kind, time=0, scale=1, accent=CYAN, variant=""):
    x, y = center
    if kind == "player":
        outline = [(0, -22), (8, -6), (23, 15), (10, 13), (0, 17), (-10, 13), (-23, 15), (-8, -6)]
        variants = {
            "cometa": [(0, -28), (6, -8), (26, 9), (14, 18), (0, 10),
                       (-14, 18), (-26, 9), (-6, -8)],
            "bastiao": [(0, -17), (12, -14), (27, 1), (23, 19), (-23, 19),
                        (-27, 1), (-12, -14)],
        }
        outline = variants.get(variant, outline)
        colors = (tuple(channel // 2 for channel in accent), accent, (225, 255, 244))
    elif kind == "boss":
        outline = [(0, 33), (24, 18), (57, 25), (77, 2), (61, -26), (24, -18),
                   (0, -28), (-24, -18), (-61, -26), (-77, 2), (-57, 25), (-24, 18)]
        colors = ((94, 39, 66), RED, (255, 204, 157))
        if variant == "boreal":
            outline = [(0, 33), (25, 13), (77, 20), (67, -22), (38, -10),
                       (18, -31), (-18, -31), (-38, -10), (-67, -22), (-77, 20), (-25, 13)]
            colors = ((44, 57, 101), (154, 215, 255), (237, 253, 255))
    else:
        width = 25 if kind == "guard" else 19
        outline = [(0, 16), (width, 5), (width - 3, -12), (0, -6),
                   (-width + 3, -12), (-width, 5)]
        colors = ((106, 45, 60), ORANGE if kind == "scout" else RED, (255, 220, 166))

    def point(dx, dy):
        return round(x + dx * scale), round(y + dy * scale)

    if kind == "player":
        tip = 30 + 5 * sin(time * 27)
        pg.draw.polygon(surface, (40, 136, 163), [point(-7, 13), point(0, tip), point(7, 13)])
        pg.draw.polygon(surface, accent, [point(-3, 14), point(0, tip - 5), point(3, 14)])
    shape = [point(px, py) for px, py in outline]
    pg.draw.polygon(surface, colors[0], shape)
    pg.draw.polygon(surface, colors[1], shape, max(1, round(scale)))
    if kind == "boss":
        for offset in (-48, -25, 25, 48):
            pg.draw.line(surface, colors[1], point(offset, -9), point(offset * .8, 9), 3)
    cockpit = [point(0, -8), point(5, 2), point(0, 8), point(-5, 2)]
    pg.draw.polygon(surface, colors[2], cockpit)


def draw_laser(surface, rect, style, color, kind="normal"):
    x, y = rect.center
    if kind == "super":
        pg.draw.polygon(surface, (46, 114, 155),
                        [(x, rect.top), (rect.right, y), (x, rect.bottom), (rect.left, y)])
        pg.draw.polygon(surface, CYAN,
                        [(x, rect.top + 4), (x + 10, y), (x, rect.bottom - 4), (x - 10, y)])
        pg.draw.line(surface, CREAM, (x, rect.top + 9), (x, rect.bottom - 9), 3)
    elif style == "banana":
        points = [(x - 5, y - 8), (x + 3, y - 6), (x + 7, y - 1), (x + 5, y + 5),
                  (x - 5, y + 9), (x - 1, y + 2), (x - 1, y - 2)]
        pg.draw.polygon(surface, (255, 221, 91), points)
        pg.draw.lines(surface, (150, 93, 55), True, points, 1)
    elif style == "coco":
        for offset, width in ((4, 17), (0, 13), (-4, 8)):
            pg.draw.ellipse(surface, (180, 105, 66), (x - width // 2, y + offset - 3, width, 8))
        pg.draw.circle(surface, CREAM, (x - 2, y + 1), 1)
        pg.draw.circle(surface, CREAM, (x + 2, y + 1), 1)
    else:
        pg.draw.rect(surface, color, rect, border_radius=4)
        pg.draw.rect(surface, CREAM, rect.inflate(-4, -5), border_radius=2)


def draw_obstacle(surface, obstacle):
    x, y = round(obstacle.x), round(obstacle.y)
    points = [(x - 22, y - 5), (x - 14, y - 17), (x + 2, y - 20),
              (x + 18, y - 10), (x + 22, y + 5), (x + 9, y + 17), (x - 13, y + 13)]
    pg.draw.polygon(surface, (99, 76, 107), points)
    pg.draw.polygon(surface, (193, 148, 154), points, 2)
    pg.draw.line(surface, (160, 113, 122), (x - 13, y - 11), (x + 5, y + 5), 2)
    for index in range(obstacle.hp):
        pg.draw.circle(surface, ORANGE, (x - 5 + index * 5, y + 8), 1)


def draw_pickup(surface, pickup, time):
    x, y = round(pickup.x), round(pickup.y + sin(time * 8) * 2)
    color = {"repair": (132, 244, 156), "rapid": (255, 215, 103), "energy": CYAN}[pickup.kind]
    pg.draw.circle(surface, (28, 30, 53), (x, y), 14)
    pg.draw.circle(surface, color, (x, y), 14, 2)
    if pickup.kind == "repair":
        pg.draw.line(surface, color, (x - 6, y), (x + 6, y), 3)
        pg.draw.line(surface, color, (x, y - 6), (x, y + 6), 3)
    elif pickup.kind == "rapid":
        for dx in (-4, 4):
            pg.draw.line(surface, color, (x + dx, y + 5), (x + dx, y - 5), 3)
    else:
        pg.draw.lines(surface, color, False, [(x + 3, y - 7), (x - 4, y + 1),
                                             (x + 3, y + 1), (x - 2, y + 7)], 2)


class Sky:
    def __init__(self):
        rng = random.Random(23)
        self.base = pg.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = (y / HEIGHT) ** 2
            pg.draw.line(self.base, (int(14 + 40*t), int(13 + 7*t), int(29 + 8*t)), (0, y), (WIDTH, y))
        self.stars = [(rng.randrange(WIDTH), rng.randrange(HEIGHT), rng.choice((12, 25, 42)),
                       rng.randrange(60, 194)) for _ in range(132)]
        self.land = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        for color, baseline, height, step in [((91, 39, 53), 540, 92, 54),
                                               ((67, 30, 46), 593, 82, 49),
                                               ((41, 23, 39), 637, 77, 65)]:
            ridge = [(x, baseline - rng.randrange(0, height)) for x in range(0, WIDTH + step, step)]
            pg.draw.polygon(self.land, color, ridge + [(WIDTH, HEIGHT), (0, HEIGHT)])
        for x in range(600, 946, 68):
            pg.draw.line(self.land, (121, 64, 67), (x, 592), (x + 20, 572), 1)
            pg.draw.rect(self.land, (175, 99, 84), (x + 20, 572, 22, 4), 1)
        self.planet = pg.Surface((360, 360), pg.SRCALPHA)
        for radius in range(164, 135, -2):
            pg.draw.circle(self.planet, (255, 115, 83, 16), (180, 180), radius, 1)
        pg.draw.circle(self.planet, (176, 68, 63), (180, 180), 136)
        for i in range(1600):
            x, y = rng.randrange(46, 314), rng.randrange(46, 314)
            if (x - 180)**2 + (y - 180)**2 < 132**2:
                pg.draw.line(self.planet, rng.choice(((192, 78, 70), (145, 54, 60), (204, 93, 76))),
                             (x, y), (x + rng.randrange(1, 5), y))
        pg.draw.circle(self.planet, (250, 141, 100), (180, 180), 136, 2)
        self.small_planet = pg.transform.smoothscale(self.planet, (230, 230))
        self.polar_sky = self.make_polar_sky(rng)
        self.veil = pg.Surface(ARENA.size, pg.SRCALPHA)
        self.veil.fill((15, 10, 26, 117))

    @staticmethod
    def make_polar_sky(rng):
        sky = pg.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            t = (y / HEIGHT) ** 1.5
            pg.draw.line(sky, (int(11 + 11*t), int(18 + 30*t), int(35 + 43*t)), (0, y), (WIDTH, y))
        aurora = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        for number in range(23):
            ridge = [(x, 193 + 39 * sin(x / 125 + number / 52) + number * 2)
                     for x in range(0, WIDTH + 12, 12)]
            pg.draw.lines(aurora, (97, 238, 211, 36 - number), False, ridge, 3)
        sky.blit(aurora, (0, 0))
        for color, baseline, height, step in [((57, 75, 111), 525, 104, 49),
                                               ((46, 64, 101), 584, 89, 68),
                                               ((27, 43, 76), 624, 65, 74)]:
            ridge = [(x, baseline - rng.randrange(0, height)) for x in range(0, WIDTH + step, step)]
            pg.draw.polygon(sky, color, ridge + [(WIDTH, HEIGHT), (0, HEIGHT)])
            for a, b in zip(ridge[::2], ridge[1::2]):
                pg.draw.line(sky, (105, 147, 175), a, b, 1)
        return sky

    def draw(self, screen, time, menu=False, map_index=0):
        screen.blit(self.polar_sky if map_index else self.base, (0, 0))
        for x, y, speed, light in self.stars:
            color = (light, int(light * .83), int(light * .91))
            pg.draw.circle(screen, color, (x, int(y + time * speed * .25) % HEIGHT),
                           2 if speed == 42 and light > 135 else 1)
        if menu:
            screen.blit(self.planet, (579, 110))
            for radius in (158, 174):
                rect = pg.Rect(0, 0, radius * 2, radius * 2)
                rect.center = (759, 290)
                pg.draw.arc(screen, (119, 82, 94), rect, .42, 2.8, 1)
                pg.draw.arc(screen, (119, 82, 94), rect, 3.56, 5.94, 1)
        elif not map_index:
            screen.blit(self.small_planet, (728, 193))
            screen.blit(self.veil, ARENA)
        if not map_index:
            screen.blit(self.land, (0, 0))


class Particles:
    def __init__(self):
        self.items = []

    def burst(self, x, y, color, count):
        for _ in range(count):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(45, 225)
            life = random.uniform(.24, .65)
            self.items.append([x, y, cos(angle)*speed, sin(angle)*speed, life, color])

    def update(self, dt):
        for item in self.items:
            item[0] += item[2] * dt
            item[1] += item[3] * dt
            item[4] -= dt
        self.items = [item for item in self.items if item[4] > 0]

    def draw(self, screen):
        for x, y, _, _, life, color in self.items:
            pg.draw.circle(screen, color, (int(x), int(y)), max(1, round(life * 6)))
