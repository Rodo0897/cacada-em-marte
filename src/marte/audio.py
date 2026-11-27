"""Sons PCM sintetizados com a biblioteca padrão e tocados pelo Pygame."""
from array import array
from io import BytesIO
from math import pi, sin
from pathlib import Path
import wave
import random

import pygame as pg

RATE = 22050
SOUND_DIR = Path(__file__).resolve().parents[2] / "assets" / "sons"
EFFECTS = {
    "laser": (.11, 1150, 310),
    "burst": (.28, 150, 42, .66),
    "hurt": (.38, 175, 56, .35),
    "wave": (.35, 320, 820),
    "select": (.10, 480, 780),
    "victory": (.68, 330, 880),
    "defeat": (.62, 250, 65),
    "super": (.39, 100, 830, .15),
    "pickup": (.22, 550, 1150),
}
TRACKS = ("menu", "canion", "calota")
ALIASES = {"boss": "wave", "map": "wave",
           "pickup_repair": "pickup", "pickup_rapid": "pickup", "pickup_energy": "pickup"}


def effect(duration, start, end, noise=0):
    rng = random.Random(12)
    samples = array("h")
    phase = 0.0
    for index in range(int(duration * RATE)):
        time = index / RATE
        progress = time / duration
        phase += 2 * pi * (start + (end - start) * progress) / RATE
        tone = (1 - noise) * sin(phase) + noise * rng.uniform(-1, 1)
        envelope = min(1, time * 220) * (1 - progress) ** 2
        samples.append(round(14500 * tone * envelope))
    return samples


def soundtrack(name):
    """Cria um loop de quatro compassos, somando baixo e arpejo."""
    chords = ((55, 130.81, 164.81, 220), (43.65, 130.81, 174.61, 220),
              (36.71, 110, 146.83, 196), (49, 123.47, 146.83, 196))
    samples = array("h")
    tempo, transposition, note_gain = {
        "menu": (.30, 1, 700),
        "canion": (.22, 1, 930),
        "calota": (.19, 1.12246, 1040),
    }[name]
    step_size = round(tempo * RATE)
    for bass, *notes in chords:
        for step in range(8):
            note = notes[(0, 1, 2, 1, 0, 2, 1, 2)[step]]
            for index in range(step_size):
                time = index / RATE
                beat = min(1, time * 95) * (1 - index / step_size)
                bass_wave = sin(2 * pi * transposition * bass * time)
                note_wave = sin(2 * pi * transposition * note * time)
                tone = 1250 * bass_wave + note_gain * note_wave
                samples.append(round(tone * beat))
    return samples


class Audio:
    def __init__(self):
        self.muted = False
        self.track = None
        self.music_buffer = None
        self.effects = {}
        if pg.mixer.get_init() is None:
            return
        self.effects = {name: load_sound(name) for name in EFFECTS}
        self.effects["laser"].set_volume(.38)
        self.set_track("menu")

    def set_track(self, name):
        if not self.effects or self.track == name:
            return
        pg.mixer.music.stop()
        try:
            pg.mixer.music.load(str(SOUND_DIR / f"{name}.wav"))
            self.music_buffer = None
        except (FileNotFoundError, pg.error):
            # Mantém a trilha disponível se a pasta de áudio ficar incompleta.
            self.music_buffer = BytesIO()
            write_wave(self.music_buffer, name)
            self.music_buffer.seek(0)
            pg.mixer.music.load(self.music_buffer, "wav")
        self.track = name
        pg.mixer.music.set_volume(0 if self.muted else .54)
        pg.mixer.music.play(-1)

    def play(self, key):
        key = ALIASES.get(key, key)
        if not self.muted and key in self.effects:
            self.effects[key].play()

    def toggle(self):
        self.muted = not self.muted
        if self.track:
            pg.mixer.music.set_volume(0 if self.muted else .54)
            if self.muted:
                for sound in self.effects.values():
                    sound.stop()


def samples_for(name):
    return soundtrack(name) if name in TRACKS else effect(*EFFECTS[name])


def load_sound(name):
    try:
        return pg.mixer.Sound(str(SOUND_DIR / f"{name}.wav"))
    except (FileNotFoundError, pg.error):
        return pg.mixer.Sound(buffer=samples_for(name))


def write_wave(destination, name):
    with wave.open(destination, "wb") as out:
        out.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        out.writeframes(samples_for(name).tobytes())


def export_sounds():
    """Gera os arquivos originais distribuídos com o projeto."""
    SOUND_DIR.mkdir(parents=True, exist_ok=True)
    for name in (*TRACKS, *EFFECTS):
        write_wave(str(SOUND_DIR / f"{name}.wav"), name)


if __name__ == "__main__":
    export_sounds()
