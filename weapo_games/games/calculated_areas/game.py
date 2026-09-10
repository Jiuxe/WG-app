from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from .area import Area
from .player import Player
from .roles import ROLE_NAMES, Role

AREA_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    ("circle", "Círculo", "●"),
    ("square", "Cuadrado", "■"),
    ("triangle", "Triángulo", "▲"),
)
AREA_IDS: tuple[str, ...] = tuple(area_id for area_id, _, _ in AREA_DEFINITIONS)
SAVE_VERSION = 1
GAME_ID = "calculated_areas"


class GameRuleError(ValueError):
    """Error de validación provocado por una regla del juego."""


@dataclass(slots=True)
class RoundResult:
    finished_round: int
    new_round: int
    scores_before: dict[str, int]
    scores_after: dict[str, int]
    area_effects: dict[str, dict[str, int]]
    swaps: list[dict[str, Any]]

    def format_summary(self, area_names: dict[str, str]) -> str:
        lines = [f"Ronda {self.finished_round} finalizada", ""]

        for area_id in AREA_IDS:
            effect = self.area_effects[area_id]
            lines.extend(
                [
                    f"{area_names[area_id]}:",
                    f"  +{effect['adder_points']} por sumadores ({effect['adders']} jugador(es))",
                    f"  -{effect['subtractor_points']} por restadores ({effect['subtractors']} jugador(es))",
                    f"  Resultado antes de intercambios: {effect['score_after_delta']}",
                    "",
                ]
            )

        lines.append("Intercambios:")
        if not self.swaps:
            lines.append("  Ninguno")
        else:
            for swap in self.swaps:
                lines.append(
                    "  Jugador "
                    f"{swap['player_id']}: {area_names[swap['origin']]} ↔ "
                    f"{area_names[swap['destination']]}"
                )

        lines.extend(["", "Puntuaciones finales:"])
        for area_id in AREA_IDS:
            lines.append(f"  {area_names[area_id]}: {self.scores_after[area_id]}")

        return "\n".join(lines)


class CalculatedAreasGame:
    """Lógica independiente de interfaz para el juego Áreas Calculadas."""

    def __init__(self, name: str = "Nueva partida") -> None:
        now = datetime.now().isoformat(timespec="seconds")
        self.name = name.strip() or "Nueva partida"
        self.round_number = 0
        self.players: list[Player] = []
        self.areas: dict[str, Area] = {
            area_id: Area(area_id, area_name, symbol)
            for area_id, area_name, symbol in AREA_DEFINITIONS
        }
        self.scores_visible = False
        self.roles_visible = False
        self.created_at = now
        self.updated_at = now

    @property
    def roles_assigned(self) -> bool:
        return bool(self.players) and all(player.role is not None for player in self.players)

    @property
    def area_names(self) -> dict[str, str]:
        return {area_id: area.name for area_id, area in self.areas.items()}

    def _touch(self) -> None:
        self.updated_at = datetime.now().isoformat(timespec="seconds")

    def _ensure_setup_round(self, action: str) -> None:
        if self.round_number != 0:
            raise GameRuleError(f"No se puede {action} después de la ronda 0.")

    def _get_player(self, player_id: int) -> Player:
        for player in self.players:
            if player.id == player_id:
                return player
        raise GameRuleError(f"No existe el jugador {player_id}.")

    @staticmethod
    def _fibonacci_sum(count: int) -> int:
        """Devuelve el valor Fibonacci para count sumadores: 0, 1, 2, 3, 5..."""
        if count <= 0:
            return 0
        previous, current = 1, 2
        for _ in range(count - 1):
            previous, current = current, previous + current
        return previous

    def add_player(self) -> Player:
        self._ensure_setup_round("añadir jugadores")
        next_id = max((player.id for player in self.players), default=0) + 1
        player = Player(id=next_id)
        self.players.append(player)
        self._touch()
        return player

    def remove_last_player(self) -> Player:
        self._ensure_setup_round("eliminar jugadores")
        if not self.players:
            raise GameRuleError("No hay jugadores que eliminar.")
        removed = self.players.pop()
        self._normalize_slots()
        self._touch()
        return removed

    def assign_roles(
        self,
        rng: random.Random | None = None,
        *,
        role_counts: Mapping[Role, int] | None = None,
    ) -> dict[Role, int]:
        self._ensure_setup_round("asignar roles")
        if not self.players:
            raise GameRuleError("Añade al menos un jugador antes de asignar roles.")

        rng = rng or random.Random()
        if role_counts is None:
            base, remainder = divmod(len(self.players), len(Role))
            roles = list(Role)
            rng.shuffle(roles)
            role_counts = {
                role: base + (1 if index < remainder else 0)
                for index, role in enumerate(roles)
            }
        else:
            role_counts = {role: role_counts.get(role, 0) for role in Role}
            invalid_counts = [
                count
                for count in role_counts.values()
                if not isinstance(count, int) or count < 0
            ]
            if invalid_counts:
                raise GameRuleError("La cantidad de cada rol debe ser un entero no negativo.")
            if sum(role_counts.values()) != len(self.players):
                raise GameRuleError(
                    "La suma de las cantidades de roles debe coincidir con el número de jugadores."
                )

        role_pool: list[Role] = []
        for role, count in role_counts.items():
            role_pool.extend([role] * count)
        rng.shuffle(role_pool)

        counts = {role: 0 for role in Role}
        for player, role in zip(sorted(self.players, key=lambda item: item.id), role_pool, strict=True):
            player.role = role
            counts[role] += 1

        self._touch()
        return counts

    def set_player_role(self, player_id: int, role: Role) -> None:
        """Asigna manualmente un rol a un jugador durante la configuración."""
        self._ensure_setup_round("modificar roles")
        if not isinstance(role, Role):
            raise GameRuleError("El rol indicado no es válido.")
        player = self._get_player(player_id)
        player.role = role
        self._touch()

    def _normalize_slots(self) -> None:
        """Compacta los slots de cada área sin alterar la posición por área."""
        for area_id in AREA_IDS:
            area_players = sorted(
                (player for player in self.players if player.current_area == area_id),
                key=lambda player: (
                    player.current_slot if isinstance(player.current_slot, int) else 10**9,
                    player.id,
                ),
            )
            for slot_index, player in enumerate(area_players):
                player.current_slot = slot_index

    def move_player(
        self,
        player_id: int,
        destination_area: str,
        destination_slot: int | None = None,
    ) -> None:
        if destination_area not in self.areas:
            raise GameRuleError("El área de destino no existe.")

        player = self._get_player(player_id)
        capacity = len(self.players)
        if capacity < 1:
            raise GameRuleError("No hay slots disponibles.")

        occupied_slots = {
            other.current_slot
            for other in self.players
            if other.id != player_id
            and other.current_area == destination_area
            and isinstance(other.current_slot, int)
        }

        if destination_slot is None:
            destination_slot = next(
                (index for index in range(capacity) if index not in occupied_slots),
                None,
            )
            if destination_slot is None:
                raise GameRuleError("No hay slots libres en el área de destino.")

        if not isinstance(destination_slot, int) or not 0 <= destination_slot < capacity:
            raise GameRuleError("El slot de destino no es válido.")
        if destination_slot in occupied_slots:
            raise GameRuleError("El slot de destino ya está ocupado.")

        if player.current_area is None:
            player.current_area = destination_area
            player.current_slot = destination_slot
            player.round_start_area = destination_area
        else:
            player.current_area = destination_area
            player.current_slot = destination_slot
        self._touch()

    def validate_for_resolution(self) -> None:
        if not self.players:
            raise GameRuleError("No se puede finalizar una ronda sin jugadores.")
        if not self.roles_assigned:
            raise GameRuleError("Todos los jugadores deben tener un rol asignado.")

        unplaced = [str(player.id) for player in self.players if player.current_area not in self.areas]
        if unplaced:
            raise GameRuleError(
                "Todos los jugadores deben estar colocados en un área. "
                f"Faltan: {', '.join(unplaced)}."
            )

    def resolve_round(self) -> RoundResult:
        self.validate_for_resolution()

        scores_before = {area_id: area.score for area_id, area in self.areas.items()}
        area_effects: dict[str, dict[str, int]] = {}

        # 1) Sumas y restas.
        for area_id in AREA_IDS:
            area_players = [player for player in self.players if player.current_area == area_id]
            adders = sum(player.role is Role.ADDER for player in area_players)
            subtractors = sum(player.role is Role.SUBTRACTOR for player in area_players)
            adder_points = self._fibonacci_sum(adders)
            subtractor_points = 2**subtractors if subtractors >= 1 else 0
            delta = adder_points - subtractor_points
            self.areas[area_id].score += delta
            area_effects[area_id] = {
                "adders": adders,
                "adder_points": adder_points,
                "subtractors": subtractors,
                "subtractor_points": subtractor_points,
                "delta": delta,
                "score_after_delta": self.areas[area_id].score,
            }

        # 2) Intercambiadores, en orden de número de jugador.
        swaps: list[dict[str, Any]] = []
        swappers = sorted(
            (player for player in self.players if player.role is Role.SWAPPER),
            key=lambda player: player.id,
        )
        for player in swappers:
            origin = player.round_start_area
            destination = player.current_area
            if origin is None or destination is None or origin == destination:
                continue
            if origin not in self.areas or destination not in self.areas:
                raise GameRuleError(
                    f"El movimiento del intercambiador {player.id} contiene un área inválida."
                )

            self.areas[origin].score, self.areas[destination].score = (
                self.areas[destination].score,
                self.areas[origin].score,
            )
            swaps.append(
                {
                    "player_id": player.id,
                    "origin": origin,
                    "destination": destination,
                }
            )

        finished_round = self.round_number
        self.round_number += 1
        for player in self.players:
            player.round_start_area = player.current_area

        self._touch()
        scores_after = {area_id: area.score for area_id, area in self.areas.items()}
        return RoundResult(
            finished_round=finished_round,
            new_round=self.round_number,
            scores_before=scores_before,
            scores_after=scores_after,
            area_effects=area_effects,
            swaps=swaps,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "save_version": SAVE_VERSION,
            "game": GAME_ID,
            "name": self.name,
            "round": self.round_number,
            "scores_visible": self.scores_visible,
            "roles_visible": self.roles_visible,
            "players": [player.to_dict() for player in self.players],
            "areas": {area_id: area.to_dict() for area_id, area in self.areas.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CalculatedAreasGame":
        if not isinstance(data, dict):
            raise ValueError("El guardado no contiene un objeto JSON válido.")
        if data.get("game") != GAME_ID:
            raise ValueError("El guardado no pertenece a Áreas Calculadas.")
        if data.get("save_version") != SAVE_VERSION:
            raise ValueError("La versión del guardado no es compatible.")

        game = cls(name=str(data.get("name") or "Partida cargada"))

        round_number = data.get("round", 0)
        if not isinstance(round_number, int) or round_number < 0:
            raise ValueError("El número de ronda del guardado no es válido.")
        game.round_number = round_number

        raw_players = data.get("players", [])
        if not isinstance(raw_players, list):
            raise ValueError("La lista de jugadores del guardado no es válida.")
        game.players = [Player.from_dict(item) for item in raw_players]

        player_ids = [player.id for player in game.players]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("El guardado contiene jugadores duplicados.")

        raw_areas = data.get("areas", {})
        if not isinstance(raw_areas, dict) or set(raw_areas) != set(AREA_IDS):
            raise ValueError("El guardado no contiene las tres áreas requeridas.")

        loaded_areas = {area_id: Area.from_dict(raw_areas[area_id]) for area_id in AREA_IDS}
        if any(area.id != area_id for area_id, area in loaded_areas.items()):
            raise ValueError("Los identificadores de las áreas no coinciden.")
        game.areas = loaded_areas

        for player in game.players:
            if player.current_area is not None and player.current_area not in game.areas:
                raise ValueError(f"El jugador {player.id} está en un área inexistente.")
            if player.round_start_area is not None and player.round_start_area not in game.areas:
                raise ValueError(f"El origen del jugador {player.id} no es válido.")
            if player.current_area is None:
                player.current_slot = None
            elif player.current_slot is not None and (
                not isinstance(player.current_slot, int)
                or not 0 <= player.current_slot < max(1, len(game.players))
            ):
                raise ValueError(f"El slot del jugador {player.id} no es válido.")

        # Los guardados antiguos pueden no incluir current_slot. Se compactan
        # también los posibles huecos o duplicados para recuperar un estado válido.
        game._normalize_slots()

        game.scores_visible = bool(data.get("scores_visible", False))
        game.roles_visible = bool(data.get("roles_visible", False))
        game.created_at = str(data.get("created_at") or datetime.now().isoformat(timespec="seconds"))
        game.updated_at = str(data.get("updated_at") or game.created_at)
        return game

    def role_assignment_text(self) -> str:
        counts = {role: 0 for role in Role}
        for player in self.players:
            if player.role:
                counts[player.role] += 1
        return "\n".join(f"{ROLE_NAMES[role]}: {counts[role]}" for role in Role)
