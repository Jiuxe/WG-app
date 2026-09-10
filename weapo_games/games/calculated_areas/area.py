from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Area:
    id: str
    name: str
    symbol: str
    score: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "symbol": self.symbol,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Area":
        if not isinstance(data, dict):
            raise ValueError("Los datos del área no son válidos.")

        area_id = data.get("id")
        name = data.get("name")
        symbol = data.get("symbol")
        score = data.get("score", 0)

        if not isinstance(area_id, str) or not area_id:
            raise ValueError("El identificador del área no es válido.")
        if not isinstance(name, str) or not name:
            raise ValueError(f"El nombre del área {area_id!r} no es válido.")
        if not isinstance(symbol, str) or not symbol:
            raise ValueError(f"El símbolo del área {area_id!r} no es válido.")
        if not isinstance(score, int):
            raise ValueError(f"La puntuación del área {area_id!r} no es válida.")

        return cls(id=area_id, name=name, symbol=symbol, score=score)
