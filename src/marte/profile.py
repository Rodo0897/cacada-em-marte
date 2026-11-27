"""Perfil local do piloto, loja e melhores pontuações."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


SHIP_PRICES = {"ares": 0, "cometa": 350, "bastiao": 650}
SHOT_STYLES = ("laser", "banana", "coco")
PILOT_MAX_LENGTH = 20
RANKING_LIMIT = 10
DEFAULT_PILOT = "Piloto"
FINAL_RESULTS = ("victory", "defeat")


def default_save_path():
    if os.name == "nt":
        fallback = Path.home() / "AppData" / "Local"
        data = Path(os.environ.get("LOCALAPPDATA") or fallback)
    else:
        fallback = Path.home() / ".local" / "share"
        data = Path(os.environ.get("XDG_DATA_HOME") or fallback)
    return data / "Cacada-em-Marte" / "perfil.json"


def clean_pilot(name):
    if not isinstance(name, str):
        return DEFAULT_PILOT
    printable = "".join(char for char in name if char.isprintable())
    return " ".join(printable.split())[:PILOT_MAX_LENGTH].strip() or DEFAULT_PILOT


def nonnegative_int(value):
    return max(0, value) if type(value) is int else 0


def ranking_key(entry):
    return entry["score"], entry["result"] == "victory", entry["map"]


def normalize_ranking(raw_ranking):
    ranking = []
    if not isinstance(raw_ranking, list):
        return ranking
    for row in raw_ranking:
        if not isinstance(row, dict) or row.get("result") not in FINAL_RESULTS:
            continue
        score = nonnegative_int(row.get("score"))
        result = row["result"]
        if score == 0 and result == "defeat":
            continue
        ranking.append({
            "pilot": clean_pilot(row.get("pilot")),
            "score": score,
            "map": max(1, nonnegative_int(row.get("map"))),
            "result": result,
        })
    return sorted(ranking, key=ranking_key, reverse=True)[:RANKING_LIMIT]


class Profile:
    """Guarda preferências, créditos e ranking entre partidas."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_save_path()
        self.credits = 0
        self.unlocked = ["ares"]
        self.equipped = "ares"
        self.shot_style = "laser"
        self.pilot = DEFAULT_PILOT
        self.ranking = []
        self.warning = ""
        self._load()

    def _load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Formato inesperado para o perfil")
        except FileNotFoundError:
            return
        except (OSError, ValueError, RecursionError):
            self.warning = "Não foi possível ler o perfil salvo."
            return

        self.credits = nonnegative_int(raw.get("credits"))
        saved_ships = raw.get("unlocked")
        if isinstance(saved_ships, list):
            self.unlocked.extend(ship for ship in SHIP_PRICES
                                 if ship != "ares" and ship in saved_ships)
        equipped = raw.get("equipped")
        if equipped in self.unlocked:
            self.equipped = equipped
        shot_style = raw.get("shot_style")
        if shot_style in SHOT_STYLES:
            self.shot_style = shot_style
        self.pilot = clean_pilot(raw.get("pilot"))
        self.ranking = normalize_ranking(raw.get("ranking"))

    def _save(self):
        payload = {
            "credits": self.credits,
            "unlocked": self.unlocked,
            "equipped": self.equipped,
            "shot_style": self.shot_style,
            "pilot": self.pilot,
            "ranking": self.ranking,
        }
        temporary_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Só substituímos o perfil anterior depois que o novo JSON está pronto.
            with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent,
                                    prefix="perfil-", suffix=".tmp", delete=False) as temp:
                temporary_path = Path(temp.name)
                json.dump(payload, temp, ensure_ascii=False, indent=2)
                temp.write("\n")
                temp.flush()
                os.fsync(temp.fileno())
            temporary_path.replace(self.path)
            self.warning = ""
        except (OSError, ValueError):
            self.warning = "Não foi possível salvar o perfil neste computador."
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def set_pilot(self, name):
        self.pilot = clean_pilot(name)
        self._save()

    def set_shot_style(self, style):
        if style in SHOT_STYLES:
            self.shot_style = style
            self._save()

    def select_ship(self, ship_id):
        """Equipa a nave, descontando o preço apenas na primeira compra."""
        if ship_id not in SHIP_PRICES:
            return False
        if ship_id not in self.unlocked:
            price = SHIP_PRICES[ship_id]
            if self.credits < price:
                return False
            self.credits -= price
            self.unlocked.append(ship_id)
        self.equipped = ship_id
        self._save()
        return True

    def record(self, score, map_number, result):
        """Registra uma partida concluída e devolve os créditos ganhos."""
        if result not in FINAL_RESULTS:
            return 0
        score = nonnegative_int(score)
        reward = score // 5 + (100 if result == "victory" else 0)
        self.credits += reward
        if score or result == "victory":
            self.ranking.append({
                "pilot": self.pilot,
                "score": score,
                "map": max(1, nonnegative_int(map_number)),
                "result": result,
            })
            self.ranking.sort(key=ranking_key, reverse=True)
            self.ranking = self.ranking[:RANKING_LIMIT]
        self._save()
        return reward
