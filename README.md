# Weapo Games — MVP

Aplicación de escritorio en Python que funciona completamente en local. Incluye el primer juego, **Áreas Calculadas**, con roles ocultos, jugadores arrastrables, tres áreas, resolución de rondas y guardado JSON.

## Funciones incluidas

- Menú principal con nueva partida, cargar partida y salir.
- Selección del juego Áreas Calculadas.
- Añadir y eliminar jugadores durante la ronda 0.
- Reparto aleatorio y equilibrado de roles, con cantidades configurables por rol.
- Fichas arrastrables desde la reserva y entre áreas.
- Slots individuales para todos los jugadores, con validación de ocupación.
- Mostrar u ocultar roles y puntuaciones.
- Resolución de sumadores, restadores e intercambiadores.
- Resumen de cada ronda.
- Guardado local y carga desde archivos JSON.
- Detección de archivos de guardado corruptos.
- Pruebas automatizadas de la lógica.

## Requisitos

- Python 3.10 o superior.
- Windows, Linux o macOS.

## Instalación en Windows

Abre PowerShell dentro de la carpeta del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## Ejecutar

```powershell
python main.py
```

También puedes ejecutar `run_windows.bat` después de instalar las dependencias.

## Ejecutar las pruebas

```powershell
pip install -r requirements-dev.txt
pytest
```

## Crear ejecutable para Linux

Desde Linux, ejecuta:

```bash
chmod +x build_linux.sh
./build_linux.sh
```

El binario se generará en `dist/WeapoGames`. Es un ejecutable autocontenido; los
guardados del binario se almacenan en `~/.local/share/weapo-games/saves/`.

## Cómo jugar

1. Pulsa **Nueva partida** y selecciona **Áreas Calculadas**.
2. Añade los jugadores desde la columna izquierda.
3. Pulsa **Asignar roles**.
4. Arrastra cada ficha a un slot libre de una de las tres áreas.
5. Mueve las fichas entre áreas durante la ronda.
6. Pulsa **Finalizar ronda** para aplicar los efectos.
7. Usa **Guardar partida** para crear un JSON en la carpeta `saves/`.

## Reglas implementadas

1. Los sumadores aportan puntos según Fibonacci estándar en función de cuántos haya en el área: `0, 1, 2, 3, 5, 8...`.
2. Los restadores restan `2^n` puntos al área donde terminan la ronda, siendo `n` la cantidad de restadores del área; con 0 restadores no se aplica ninguna resta.
3. Primero se resuelven todas las sumas y restas.
4. Después se resuelven los intercambiadores por número de jugador ascendente.
5. Un intercambiador usa como origen el área donde comenzó la ronda y como destino el área donde terminó.
6. Un intercambiador que no cambia de área no hace nada.
7. Tras resolver la ronda, la posición actual se convierte en el origen de la siguiente.

## Estructura

```text
weapo_games_mvp/
├── main.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── run_windows.bat
├── assets/
├── saves/
├── tests/
└── weapo_games/
    ├── app.py
    ├── games/
    │   └── calculated_areas/
    │       ├── area.py
    │       ├── game.py
    │       ├── player.py
    │       └── roles.py
    ├── services/
    │   └── save_manager.py
    └── ui/
        ├── calculated_areas_view.py
        ├── load_game_view.py
        ├── main_menu.py
        ├── main_window.py
        ├── new_game_menu.py
        └── widgets.py
```

## Guardados

Los guardados se crean en:

```text
saves/
```

Cada guardado contiene la ronda, las puntuaciones, los jugadores, los roles, las posiciones y los ajustes de visibilidad. Los archivos se escriben primero como temporales y después reemplazan el destino final.

## Siguiente fase sugerida

- Animaciones al mover fichas.
- Edición del nombre de una partida en curso.
- Borrado de guardados desde el menú de carga.
- Historial visual de rondas.
- Sonidos y recursos gráficos propios.
- Empaquetado como `.exe` con PyInstaller.
