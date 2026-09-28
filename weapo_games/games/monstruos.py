from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path


ITEMS = ("Daga", "Granada", "Espada doble", "Veneno", "Hielo", "Bomba", "Doblon")


@dataclass
class Monster:
    id: int
    name: str
    max_hp: int
    hp: int
    rewards: list[str]
    poisoned: bool = False
    frozen_by: int | None = None
    bomb_by: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Monster":
        return cls(data["id"], data["nombre"], data["hpMax"], data["hpMax"], list(data["recompensas"]))

    def snapshot(self) -> dict:
        return {"id": self.id, "name": self.name, "max_hp": self.max_hp, "hp": self.hp, "rewards": list(self.rewards), "poisoned": self.poisoned, "frozen": self.frozen_by is not None, "bomb": self.bomb_by is not None}

    def state_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "rewards": list(self.rewards),
            "poisoned": self.poisoned,
            "frozen_by": self.frozen_by,
            "bomb_by": self.bomb_by,
        }

    @classmethod
    def from_state(cls, data: dict) -> "Monster":
        return cls(
            int(data["id"]),
            str(data["name"]),
            int(data["max_hp"]),
            int(data["hp"]),
            list(data["rewards"]),
            bool(data.get("poisoned", False)),
            data.get("frozen_by"),
            data.get("bomb_by"),
        )


@dataclass
class Player:
    name: str
    score: int = 0
    inventory: list[str] = field(default_factory=lambda: ["Daga"])
    kills: list[tuple[int, str, int]] = field(default_factory=list)


class MonstruosGame:
    """Estado y reglas de Monstruos de Halloween."""

    def __init__(self, player_names: list[str], monsters: list[dict] | None = None) -> None:
        if not player_names or any(not name.strip() for name in player_names):
            raise ValueError("Debe haber al menos un jugador con nombre.")
        source = self.load_monsters() if monsters is None else monsters
        self.players = [Player(name.strip(), score=5) for name in player_names]
        self._deck = [Monster.from_dict(item) for item in source]
        self.active: list[Monster] = [self._deck.pop(0) for _ in range(min(3, len(self._deck)))]
        self.queue: list[Monster] = [self._deck.pop(0) for _ in range(min(5, len(self._deck)))]
        self.current_player = 0
        self.turn_number = 0
        self.round_active = False
        self.published = self.presentation_state()

    @staticmethod
    def load_monsters() -> list[dict]:
        path = Path(__file__).with_name("monstruos.json")
        return json.loads(path.read_text(encoding="utf-8"))

    def to_dict(self) -> dict:
        return {
            "game": "Monstruos",
            "save_version": 1,
            "turn": self.turn_number,
            "current_player": self.current_player,
            "round_active": self.round_active,
            "deck": [monster.state_dict() for monster in self._deck],
            "active": [monster.state_dict() for monster in self.active],
            "queue": [monster.state_dict() for monster in self.queue],
            "players": [
                {
                    "name": player.name,
                    "score": player.score,
                    "inventory": list(player.inventory),
                    "kills": [list(kill) for kill in player.kills],
                }
                for player in self.players
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonstruosGame":
        players_data = data.get("players")
        if not isinstance(players_data, list) or not players_data:
            raise ValueError("El guardado de Monstruos no contiene jugadores válidos.")
        game = cls([str(player["name"]) for player in players_data], monsters=[])
        game.players = [
            Player(
                name=str(player["name"]),
                score=int(player.get("score", 0)),
                inventory=list(player.get("inventory", ["Daga"])),
                kills=[(int(kill[0]), str(kill[1]), int(kill[2])) for kill in player.get("kills", [])],
            )
            for player in players_data
        ]
        game._deck = [Monster.from_state(monster) for monster in data.get("deck", [])]
        game.active = [Monster.from_state(monster) for monster in data.get("active", [])]
        game.queue = [Monster.from_state(monster) for monster in data.get("queue", [])]
        game.current_player = int(data.get("current_player", 0)) % len(game.players)
        game.turn_number = int(data.get("turn", 0))
        game.round_active = bool(data.get("round_active", False))
        game.published = game.presentation_state()
        return game

    def player_order(self) -> list[str]:
        return [player.name for player in self.players]

    def reorder_players(self, names: list[str]) -> None:
        by_name = {player.name: player for player in self.players}
        if set(names) != set(by_name) or len(names) != len(self.players):
            raise ValueError("Orden de jugadores no válido.")
        self.players = [by_name[name] for name in names]

    def update_player(self, player: Player, name: str, score: int, inventory: list[str]) -> None:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("El nombre del jugador no puede estar vacío.")
        if any(other is not player and other.name == clean_name for other in self.players):
            raise ValueError("Cada jugador debe tener un nombre distinto.")
        player.name = clean_name
        player.score = score
        player.inventory = inventory

    def sort_players_by_score(self) -> None:
        """Ordena de mayor a menor puntuación manteniendo el orden en los empates."""
        self.players.sort(key=lambda player: player.score, reverse=True)

    def start_round(self) -> None:
        if self.round_active:
            raise ValueError("Ya hay una ronda en curso.")
        self.round_active = True
        self.current_player = 0
        self.turn_number += 1

    def current(self) -> Player:
        return self.players[self.current_player]

    def _monster(self, slot: int) -> Monster:
        if slot not in (0, 1, 2) or slot >= len(self.active):
            raise ValueError("Objetivo no válido.")
        return self.active[slot]

    def _damage(self, monster: Monster, amount: int, attacker: Player, kills: list[Monster]) -> None:
        if monster.frozen_by is not None:
            return
        monster.hp -= amount
        if monster.hp <= 0 and monster in self.active:
            monster.hp = 0
            attacker.score += monster.max_hp
            attacker.inventory.extend(monster.rewards)
            attacker.kills.append((self.turn_number, monster.name, monster.max_hp))
            kills.append(monster)

    def _resolve_dead(self, kills: list[Monster]) -> None:
        for dead in kills:
            if dead not in self.active:
                continue
            index = self.active.index(dead)
            replacement = self.queue.pop(0) if self.queue else (self._deck.pop(0) if self._deck else None)
            if replacement:
                self.active[index] = replacement
            else:
                self.active.pop(index)
            if self.queue and len(self.queue) < 5 and self._deck:
                self.queue.append(self._deck.pop(0))

    def begin_turn(self) -> list[str]:
        """Resuelve bombas y descongela el monstruo al volver al lanzador."""
        player = self.current()
        events: list[str] = []
        for monster in self.active:
            if monster.frozen_by == self.current_player:
                monster.frozen_by = None
            if monster.bomb_by == self.current_player:
                kills: list[Monster] = []
                self._damage(monster, 10, player, kills)
                monster.bomb_by = None
                events.append(f"La bomba explota contra {monster.name}.")
                self._resolve_dead(kills)
        return events

    def use_item(self, item: str, slots: list[int], sword_mode: str = "single") -> list[str]:
        player = self.current()
        if item == "Doblon":
            raise ValueError("El Doblon no puede usarse en combate.")
        if item not in player.inventory or item not in ITEMS:
            raise ValueError("El objeto no está en el inventario.")
        if not slots or any(slot < 0 or slot >= len(self.active) for slot in slots):
            raise ValueError("Selecciona un objetivo válido.")
        if item == "Espada doble":
            if sword_mode == "split" and len(slots) != 2:
                raise ValueError("La espada doble en modo dividido necesita dos objetivos.")
            if sword_mode != "split" and len(slots) != 1:
                raise ValueError("La espada doble normal necesita un objetivo.")
        elif len(slots) != 1:
            raise ValueError("Este objeto solo admite un objetivo.")
        if item == "Bomba":
            target = self._monster(slots[0])
            target.bomb_by = self.current_player
        else:
            kills: list[Monster] = []
            damage = {"Daga": 2, "Granada": 6, "Hielo": 3}.get(item)
            if item == "Espada doble":
                damage = 2 if sword_mode == "split" else 4
            for slot in slots:
                target = self._monster(slot)
                if item == "Veneno":
                    target.poisoned = True
                else:
                    self._damage(target, damage or 0, player, kills)
                if item == "Hielo" and target in self.active and target.hp > 0:
                    target.frozen_by = self.current_player
            self._resolve_dead(kills)
        if item not in ("Daga", "Doblon"):
            player.inventory.remove(item)
        # El veneno se aplica al final del turno, incluso sobre reemplazos no.
        poisoned_kills: list[Monster] = []
        for monster in list(self.active):
            if monster.poisoned:
                self._damage(monster, 1, player, poisoned_kills)
        self._resolve_dead(poisoned_kills)
        return []

    def finish_turn(self) -> bool:
        self.current_player += 1
        if self.current_player >= len(self.players):
            self.round_active = False
            self.current_player = 0
            self.published = self.presentation_state()
            return True
        return False

    def presentation_state(self) -> dict:
        return {"active": [monster.snapshot() for monster in self.active], "queue": [monster.snapshot() for monster in self.queue], "players": [{"name": p.name, "score": p.score, "kills": list(p.kills)} for p in self.players]}

    def publish(self) -> None:
        self.published = copy.deepcopy(self.presentation_state())
