# Weapo Games — MVP

Aplicación de escritorio en Python que funciona completamente en local. Incluye **Áreas Calculadas**, **Votación de candidatos** y **Memoria hexagonal**, con una web local para votar desde móviles mediante QR.

## Funciones incluidas

- Menú principal con nueva partida, cargar partida y salir.
- Selección del juego Áreas Calculadas.
- Selección de Votación de candidatos.
- Tablero de memoria hexagonal adyacente con forma automática 3-4-5-4-3, patrón manual opcional y temporizador editable.
- Conversión automática de números a letras y generación de un objetivo con al menos cuatro líneas válidas de tres números.
- Ventana privada de soluciones para el máster.
- Dificultad progresiva del objetivo: rondas 1-5 entre 5 y 10, rondas 6-8 entre 10 y 20 y desde la ronda 9 entre 20 y 25. Los números de las celdas siempre están entre 1 y 10.
- Modalidad alternativa con 10 tableros ilustrados y un tablero oculto para las letras.
- Candidatos con nombre, color y puntuación visible por barras.
- Servidor web local y QR para emitir votos desde dispositivos de la misma red.
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

Para usar **Votación de candidatos**, selecciónalo en **Nueva partida**, declara los
nombres y colores y pulsa **Comenzar partida**. Pulsa **Mostrar QR** y escanéalo
desde dispositivos conectados a la misma red Wi-Fi que el ordenador. La ventana
principal debe permanecer abierta mientras se reciben los votos.

Para usar **Memoria hexagonal**, selecciónalo en **Nueva partida** y elige la modalidad. En **Tablero generado / manual**, se crea un tablero adyacente con filas 3-4-5-4-3; también puedes pulsar **Introducir patrón manual** y escribir las cinco filas con el formato `(1,2,3),(1,2,3,4),(1,2,3,4,5),(1,2,3,4),(1,2,3)`. En **Tableros con imágenes**, se juegan 10 rondas ilustradas con sus soluciones asociadas. Cuando termine el tiempo, los números se convertirán en letras y aparecerá el objetivo. El botón **Soluciones del máster** abre una ventana privada con todas las combinaciones válidas de ese tablero.

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
