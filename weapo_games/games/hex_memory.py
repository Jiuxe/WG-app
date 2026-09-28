from __future__ import annotations

import re
import random
from dataclasses import dataclass
from pathlib import Path


class HexBoardError(ValueError):
    """Error al interpretar o preparar un tablero hexagonal."""


@dataclass(frozen=True)
class HexCell:
    row: int
    column: int
    value: int
    letter: str


@dataclass(frozen=True)
class HexLine:
    cells: tuple[HexCell, HexCell, HexCell]
    total: int


class HexMemoryGame:
    """Lógica de una ronda del juego de memoria hexagonal."""

    DEFAULT_SHAPE = (3, 4, 5, 4, 3)

    def __init__(
        self,
        rows: list[list[int]],
        duration_seconds: int = 90,
        round_number: int = 1,
        automatic: bool = False,
        image_mode: bool = False,
        image_path: Path | None = None,
    ) -> None:
        if not rows or any(not row for row in rows):
            raise HexBoardError("El tablero debe contener al menos una fila con números.")
        if sum(map(len, rows)) > 26:
            raise HexBoardError("El tablero no puede tener más de 26 números para asignar letras A-Z.")
        if duration_seconds < 1:
            raise HexBoardError("La duración debe ser de al menos 1 segundo.")
        self.rows = [list(row) for row in rows]
        self.duration_seconds = duration_seconds
        self.round_number = round_number
        self.automatic = automatic
        self.image_mode = image_mode
        self.image_path = image_path
        self.target_min, self.target_max = self.target_range(round_number)
        self.cells = tuple(
            HexCell(row_index, column_index, value, chr(65 + index))
            for index, (row_index, column_index, value) in enumerate(
                (item for row_index, row in enumerate(self.rows) for item in ((row_index, column_index, value) for column_index, value in enumerate(row)))
            )
        )
        self._by_position = {(cell.row, cell.column): cell for cell in self.cells}
        self.lines = self._find_lines()
        self.target, self.target_lines = self._choose_target()

    @classmethod
    def generated(cls, duration_seconds: int = 90, round_number: int = 1) -> "HexMemoryGame":
        """Crea un tablero 3-4-5-4-3 con números aleatorios y objetivo válido."""
        for _ in range(100):
            values = [random.randint(1, 10) for _ in range(sum(cls.DEFAULT_SHAPE))]
            rows: list[list[int]] = []
            offset = 0
            for size in cls.DEFAULT_SHAPE:
                rows.append(values[offset : offset + size])
                offset += size
            try:
                return cls(rows, duration_seconds, round_number, automatic=True)
            except HexBoardError:
                continue
        fallback_value = 2 if round_number <= 5 else 5 if round_number <= 8 else 7
        return cls(
            [[fallback_value] * size for size in cls.DEFAULT_SHAPE],
            duration_seconds,
            round_number,
            automatic=True,
        )

    @classmethod
    def image_round(cls, duration_seconds: int = 90, round_number: int = 1) -> "HexMemoryGame":
        """Crea una ronda determinista asociada a uno de los tableros ilustrados."""
        rng = random.Random(9100 + round_number)
        for _ in range(500):
            values = [rng.randint(1, 10) for _ in range(sum(cls.DEFAULT_SHAPE))]
            rows: list[list[int]] = []
            offset = 0
            for size in cls.DEFAULT_SHAPE:
                rows.append(values[offset : offset + size])
                offset += size
            try:
                return cls(
                    rows,
                    duration_seconds,
                    round_number,
                    automatic=True,
                    image_mode=True,
                    image_path=cls.image_asset_path(round_number),
                )
            except HexBoardError:
                continue
        raise HexBoardError(f"No se pudo preparar la solución del tablero de imágenes {round_number}.")

    @staticmethod
    def image_asset_path(round_number: int) -> Path:
        root = Path(__file__).resolve().parents[2]
        return root / "img" / "hexagono" / f"ronda-{round_number:02d}.png"

    @staticmethod
    def hidden_image_asset_path() -> Path:
        root = Path(__file__).resolve().parents[2]
        return root / "img" / "hexagono" / "tablero-oculto.png"

    @staticmethod
    def target_range(round_number: int) -> tuple[int, int]:
        if round_number <= 5:
            return 5, 10
        if round_number <= 8:
            return 10, 20
        return 20, 25

    @classmethod
    def from_text(cls, text: str, duration_seconds: int = 90) -> "HexMemoryGame":
        if text.count("(") != text.count(")"):
            raise HexBoardError("Cada fila debe estar cerrada entre paréntesis.")
        matches = re.findall(r"\(([^()]*)\)", text)
        if not matches:
            raise HexBoardError("Usa filas entre paréntesis, por ejemplo: (1,2,3),(1,2,3,4),(1,2,3).")
        rows: list[list[int]] = []
        for match in matches:
            parts = [part.strip() for part in match.split(",") if part.strip()]
            if not parts:
                raise HexBoardError("No puede haber filas vacías.")
            try:
                row = [int(part) for part in parts]
            except ValueError as exc:
                raise HexBoardError("Todos los elementos del tablero deben ser números enteros.") from exc
            rows.append(row)
        if re.sub(r"[\s,()\d+-]", "", text):
            raise HexBoardError("El formato solo admite números enteros separados por comas y paréntesis.")
        return cls(rows, duration_seconds, automatic=False)

    def _find_lines(self) -> tuple[HexLine, ...]:
        # Se usan las coordenadas geométricas de los centros. En la forma
        # 3-4-5-4-3, cada fila se desplaza media celda respecto a la anterior.
        # Así solo pasan las tres direcciones rectas de una colmena: horizontal
        # y las dos diagonales. Las tres celdas deben ser consecutivas.
        candidates: set[tuple[tuple[int, int], ...]] = set()
        center = {
            (row, column): (2 * column - (len(self.rows[row]) - self.DEFAULT_SHAPE[0]), row)
            for row, values in enumerate(self.rows)
            for column in range(len(values))
        }

        # Horizontales: tres hexágonos consecutivos de una misma fila.
        for row, values in enumerate(self.rows):
            for column in range(len(values) - 2):
                candidates.add(((row, column), (row, column + 1), (row, column + 2)))

        # Diagonales: probamos los tres centros de cada columna geométrica de
        # tres filas consecutivas y comprobamos que el vector sea constante.
        for first_row in range(len(self.rows) - 2):
            for first_column in range(len(self.rows[first_row])):
                first = (first_row, first_column)
                for middle_column in range(len(self.rows[first_row + 1])):
                    middle = (first_row + 1, middle_column)
                    for last_column in range(len(self.rows[first_row + 2])):
                        last = (first_row + 2, last_column)
                        if all(position in center for position in (first, middle, last)):
                            first_center, middle_center, last_center = (center[position] for position in (first, middle, last))
                            if (
                                middle_center[0] - first_center[0] == last_center[0] - middle_center[0]
                                and middle_center[0] != first_center[0]
                            ):
                                candidates.add((first, middle, last))
        return tuple(
            HexLine(tuple(self._by_position[position] for position in positions), sum(self._by_position[position].value for position in positions))
            for positions in sorted(candidates)
        )

    def _choose_target(self) -> tuple[int, tuple[HexLine, ...]]:
        grouped: dict[int, list[HexLine]] = {}
        for line in self.lines:
            grouped.setdefault(line.total, []).append(line)
        eligible = [
            (total, lines)
            for total, lines in grouped.items()
            if self.target_min <= total <= self.target_max and len(lines) >= 4
        ]
        if not eligible:
            raise HexBoardError(
                f"Este tablero no tiene al menos cuatro combinaciones válidas entre {self.target_min} y {self.target_max}."
            )
        total, lines = max(eligible, key=lambda item: (len(item[1]), -item[0]))
        return total, tuple(lines)

    def letter_for(self, row: int, column: int) -> str:
        return self._by_position[(row, column)].letter

    def formatted_target_lines(self) -> list[str]:
        return [" + ".join(cell.letter for cell in line.cells) for line in self.target_lines]

    def formatted_target_solutions(self) -> list[str]:
        return [
            f"{' + '.join(f'{cell.letter}({cell.value})' for cell in line.cells)} = {line.total}"
            for line in self.target_lines
        ]

    def shuffled_round(self) -> "HexMemoryGame":
        next_round = self.round_number + 1
        if self.automatic:
            if self.image_mode:
                return HexMemoryGame.image_round(self.duration_seconds, next_round)
            return HexMemoryGame.generated(self.duration_seconds, next_round)
        values = [cell.value for cell in self.cells]
        random.shuffle(values)
        rows = []
        offset = 0
        for row in self.rows:
            rows.append(values[offset : offset + len(row)])
            offset += len(row)
        try:
            return HexMemoryGame(rows, self.duration_seconds, next_round, automatic=False)
        except HexBoardError:
            return HexMemoryGame(self.rows, self.duration_seconds, next_round, automatic=False)
