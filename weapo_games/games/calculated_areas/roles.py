from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Roles disponibles en Áreas Calculadas."""

    ADDER = "adder"
    SUBTRACTOR = "subtractor"
    SWAPPER = "swapper"


ROLE_NAMES: dict[Role, str] = {
    Role.ADDER: "Sumador",
    Role.SUBTRACTOR: "Restador",
    Role.SWAPPER: "Intercambiador",
}

ROLE_COLORS: dict[Role, str] = {
    Role.ADDER: "#2E7D32",
    Role.SUBTRACTOR: "#C62828",
    Role.SWAPPER: "#1565C0",
}

ROLE_SYMBOLS: dict[Role, str] = {
    Role.ADDER: "●",
    Role.SUBTRACTOR: "▲",
    Role.SWAPPER: "■",
}
