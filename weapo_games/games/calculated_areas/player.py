from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .roles import Role


@dataclass(slots=True)
class Player:
    id: int
    role: Role | None = None
    current_area: str | None = None
    current_slot: int | None = None
    round_start_area: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value if self.role else None,
            "current_area": self.current_area,
            "current_slot": self.current_slot,
            "round_start_area": self.round_start_area,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        if not isinstance(data, dict):
            raise ValueError("Los datos del jugador no son válidos.")

        player_id = data.get("id")
        if not isinstance(player_id, int) or player_id < 1:
            raise ValueError("El identificador del jugador no es válido.")

        raw_role = data.get("role")
        try:
            role = Role(raw_role) if raw_role is not None else None
        except ValueError as exc:
            raise ValueError(f"Rol desconocido para el jugador {player_id}.") from exc

        return cls(
            id=player_id,
            role=role,
            current_area=data.get("current_area"),
            current_slot=data.get("current_slot"),
            round_start_area=data.get("round_start_area"),
        )
