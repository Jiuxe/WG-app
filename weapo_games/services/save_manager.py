from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from weapo_games.games.calculated_areas.game import CalculatedAreasGame


@dataclass(frozen=True, slots=True)
class SaveInfo:
    path: Path
    name: str
    game: str
    round_number: int
    updated_at: str
    error: str | None = None


class SaveManager:
    """Gestiona partidas JSON locales con escritura atómica."""

    def __init__(self, save_directory: Path | None = None) -> None:
        if save_directory is not None:
            resolved_save_directory = save_directory
        elif getattr(sys, "frozen", False):
            # En modo one-file, los módulos se extraen a una carpeta temporal.
            # Los guardados deben sobrevivir al cierre y a futuras versiones.
            data_home = Path(
                os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
            )
            resolved_save_directory = data_home / "weapo-games" / "saves"
        else:
            project_root = Path(__file__).resolve().parents[2]
            resolved_save_directory = project_root / "saves"

        self.save_directory = resolved_save_directory
        self.save_directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_filename(name: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_-]+", "_", name.strip())
        normalized = normalized.strip("_") or "partida"
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        return f"{normalized}_{timestamp}.json"

    def save_game(self, game: CalculatedAreasGame, save_name: str) -> Path:
        clean_name = save_name.strip()
        if not clean_name:
            raise ValueError("El nombre del guardado no puede estar vacío.")

        game.name = clean_name
        game.updated_at = datetime.now().isoformat(timespec="seconds")
        payload = game.to_dict()

        # Comprobar serialización antes de tocar el archivo final.
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        target = self.save_directory / self._safe_filename(clean_name)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(target)
        return target

    def load_game(self, path: Path | str) -> CalculatedAreasGame:
        save_path = Path(path)
        try:
            data: Any = json.loads(save_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"No se pudo leer el guardado: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("El archivo de guardado contiene JSON corrupto.") from exc

        return CalculatedAreasGame.from_dict(data)

    def list_saves(self) -> list[SaveInfo]:
        results: list[SaveInfo] = []
        for path in sorted(
            self.save_directory.glob("*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        ):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                results.append(
                    SaveInfo(
                        path=path,
                        name=str(data.get("name") or path.stem),
                        game=str(data.get("game") or "Desconocido"),
                        round_number=int(data.get("round", 0)),
                        updated_at=str(data.get("updated_at") or "Sin fecha"),
                    )
                )
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                results.append(
                    SaveInfo(
                        path=path,
                        name=path.stem,
                        game="Desconocido",
                        round_number=0,
                        updated_at="Sin fecha",
                        error=str(exc),
                    )
                )
        return results
