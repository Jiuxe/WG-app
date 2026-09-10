# Weapo Games — Aplicación de escritorio en Python

## Objetivo general

Desarrolla una aplicación de escritorio en Python llamada **Weapo Games**.

La aplicación funcionará como una colección de juegos de mesa digitales. Desde el menú principal, el usuario podrá:

1. Crear una partida nueva.
2. Cargar una partida guardada.
3. Salir de la aplicación.

La primera versión debe incluir un único juego llamado **Áreas Calculadas**.

La aplicación debe funcionar completamente en local, sin servidor, sin conexión a Internet y sin cuentas de usuario.

---

# 1. Requisitos técnicos generales

* Lenguaje: Python 3.10 o superior.
* Tipo de aplicación: escritorio.
* Interfaz gráfica: utilizar una librería adecuada para interfaces de escritorio en Python.
* Guardado de partidas: archivos JSON almacenados localmente.
* El código debe estar dividido en módulos y clases.
* La lógica del juego debe estar separada de la interfaz gráfica.
* Se deben incluir validaciones y manejo de errores.
* La aplicación debe poder ejecutarse desde un archivo principal, por ejemplo:

```bash
python main.py
```

La estructura sugerida es:

```text
weapo_games/
├── main.py
├── ui/
│   ├── main_menu.py
│   ├── new_game_menu.py
│   └── calculated_areas_view.py
├── games/
│   └── calculated_areas/
│       ├── game.py
│       ├── player.py
│       ├── area.py
│       └── roles.py
├── services/
│   └── save_manager.py
├── saves/
└── assets/
```

---

# 2. Menú principal

La pantalla inicial debe mostrar el título:

**Weapo Games**

Debe contener los siguientes botones:

## Nueva partida

Abre una pantalla con la lista de juegos disponibles.

Inicialmente solo aparecerá:

* Áreas Calculadas

Al seleccionar el juego, se inicia una partida nueva.

## Cargar partida

Muestra una lista con las partidas guardadas localmente.

Cada guardado debe mostrar, como mínimo:

* Nombre de la partida.
* Juego al que pertenece.
* Fecha y hora del guardado.
* Número de ronda.

El usuario podrá seleccionar un guardado y continuar la partida desde el estado almacenado.

## Salir

Cierra la aplicación.

---

# 3. Juego: Áreas Calculadas

## 3.1. Concepto

Áreas Calculadas es un juego de roles ocultos.

Los jugadores se colocan en una de tres áreas. Al finalizar cada ronda, los roles de los jugadores modifican las puntuaciones de las áreas.

Las tres áreas son:

* Área Círculo.
* Área Cuadrado.
* Área Triángulo.

Cada área empieza con una puntuación de:

```text
0
```

Las puntuaciones pueden ser positivas, cero o negativas.

---

# 4. Roles

Cada jugador tiene un único rol oculto.

## Sumador

Representación:

* Forma: círculo.
* Color: verde.

Efecto:

* Al finalizar la ronda, suma `+1` a la puntuación del área en la que se encuentra.

Ejemplo:

```text
Puntuación del área antes de resolver: 2
Número de sumadores en el área: 3
Puntuación después de los sumadores: 5
```

## Restador

Representación:

* Forma: triángulo.
* Color: rojo.

Efecto:

* Al finalizar la ronda, resta `-1` a la puntuación del área en la que se encuentra.

Ejemplo:

```text
Puntuación del área antes de resolver: 2
Número de restadores en el área: 2
Puntuación después de los restadores: 0
```

## Intercambiador

Representación:

* Forma: cuadrado.
* Color: azul.

Efecto:

* Si el jugador se ha movido de un área a otra durante la ronda, intercambia las puntuaciones del área de origen y del área de destino.
* Si permanece en la misma área, no realiza ninguna acción.
* Si durante una ronda se arrastra varias veces al jugador, se tendrá en cuenta:

  * Como origen, el área en la que comenzó la ronda.
  * Como destino, el área en la que terminó la ronda.

Ejemplo:

```text
El jugador empieza la ronda en Círculo.
El jugador termina la ronda en Triángulo.

Después de aplicar sumas y restas:
Círculo = 4
Triángulo = -1

El intercambiador cambia los valores:
Círculo = -1
Triángulo = 4
```

---

# 5. Orden de resolución de una ronda

Al pulsar el botón **Finalizar ronda**, las acciones deben resolverse en este orden:

1. Contar los sumadores de cada área.
2. Sumar `+1` por cada sumador.
3. Contar los restadores de cada área.
4. Restar `-1` por cada restador.
5. Resolver los intercambiadores que se hayan movido.
6. Actualizar el contador de ronda.
7. Guardar como posición inicial de la siguiente ronda el área actual de cada jugador.

Si varios intercambiadores se han movido durante la misma ronda, deben resolverse en orden ascendente por número de jugador.

Ejemplo:

```text
Jugador 2: intercambia Círculo y Cuadrado.
Jugador 5: intercambia Cuadrado y Triángulo.

Primero se resuelve el jugador 2.
Después se resuelve el jugador 5.
```

Este orden debe ser determinista y repetible.

---

# 6. Configuración de la partida

La partida comienza en la ronda:

```text
Ronda 0
```

Durante la ronda 0 se podrá:

* Añadir jugadores.
* Eliminar jugadores.
* Asignar roles.
* Colocar jugadores en las áreas.

El botón **Asignar roles** solo estará habilitado en la ronda 0.

Los roles se asignarán aleatoriamente y de la forma más equilibrada posible entre los jugadores.

Ejemplo con siete jugadores:

```text
3 sumadores
2 restadores
2 intercambiadores
```

La diferencia entre la cantidad de jugadores de cada rol no debería ser superior a uno siempre que sea posible.

Una vez iniciada la ronda 1:

* No se podrán volver a asignar roles.
* No se podrán añadir jugadores.
* No se podrán eliminar jugadores.

Antes de finalizar la ronda 0 se debe validar que:

* Hay al menos un jugador.
* Todos los jugadores tienen un rol.
* Todos los jugadores están colocados en un área.

---

# 7. Interfaz de la partida

La pantalla se dividirá en tres columnas principales.

## 7.1. Zona izquierda: jugadores

Debe incluir:

* Botón para añadir jugador.
* Botón para eliminar el último jugador.
* Lista o zona con los jugadores disponibles.

Cada jugador se representará como un cuadrado negro con su número en blanco.

Ejemplo:

```text
┌─────┐
│  1  │
└─────┘
```

La numeración debe comenzar en 1 y ser correlativa.

Cuando se muestra el rol de los jugadores:

* Sumador: cuadrado verde.
* Restador: cuadrado rojo.
* Intercambiador: cuadrado azul.

Cuando se ocultan los roles, todos deben volver a mostrarse en negro.

El número del jugador siempre debe permanecer visible.

---

## 7.2. Zona central: áreas

En el centro de la pantalla deben aparecer las tres áreas:

* Círculo.
* Cuadrado.
* Triángulo.

Cada área debe incluir:

* Nombre o forma identificativa.
* Puntuación actual.
* Slots disponibles para jugadores.
* Jugadores colocados en ella.

Los slots se representarán como cuadrados vacíos o transparentes con borde visible.

Ejemplo:

```text
Área Círculo

[Jugador 1] [Slot vacío]
[Jugador 4] [Slot vacío]
```

Los jugadores deben poder arrastrarse:

* Desde la zona izquierda hacia un área.
* Desde un área hacia otra.
* Entre diferentes slots de una misma área.

Cada jugador solo puede ocupar un slot.

Un slot solo puede contener un jugador.

La interfaz debe impedir colocar un jugador fuera de un slot válido.

La cantidad de slots debe ser suficiente para permitir que todos los jugadores puedan entrar en una misma área.

Si cambia el número de jugadores durante la ronda 0, la cantidad de slots debe actualizarse.

---

## 7.3. Zona derecha: menú de acciones

Debe incluir los siguientes botones.

### Asignar roles

* Solo disponible durante la ronda 0.
* Asigna aleatoriamente los roles.
* Debe pedir confirmación si los roles ya habían sido asignados.

### Mostrar u ocultar puntuaciones

Debe funcionar como un interruptor:

* Primera pulsación: muestra las puntuaciones de las áreas.
* Segunda pulsación: oculta las puntuaciones.

Cuando estén ocultas, se puede mostrar un símbolo como:

```text
?
```

### Mostrar u ocultar roles

Debe funcionar como un interruptor:

* Primera pulsación: muestra los colores correspondientes a los roles.
* Segunda pulsación: vuelve a mostrar todos los jugadores en negro.

### Guardar partida

Abre un cuadro de diálogo para introducir el nombre del guardado.

La partida se almacena localmente en formato JSON.

Debe guardarse:

* Nombre de la partida.
* Juego.
* Fecha y hora.
* Número de ronda.
* Puntuación de cada área.
* Lista de jugadores.
* Número de cada jugador.
* Rol de cada jugador.
* Área actual de cada jugador.
* Área inicial de cada jugador en la ronda actual.
* Estado de visibilidad de roles.
* Estado de visibilidad de puntuaciones.

### Finalizar ronda

Al pulsarlo:

1. Valida el estado de la partida.
2. Ejecuta las acciones de todos los roles.
3. Actualiza las puntuaciones.
4. Incrementa el número de ronda.
5. Actualiza las posiciones iniciales de los jugadores.
6. Refresca la interfaz.
7. Muestra un resumen de lo ocurrido.

Ejemplo de resumen:

```text
Ronda 2 finalizada

Círculo:
+2 por sumadores
-1 por restadores

Cuadrado:
+0 por sumadores
-2 por restadores

Intercambios:
Jugador 4 intercambió Círculo y Triángulo
```

---

# 8. Contador de ronda

En la parte superior y centrada debe aparecer:

```text
Ronda 0
```

Después de finalizar la primera ronda:

```text
Ronda 1
```

El contador debe formar parte del estado guardado.

---

# 9. Guardado local

Las partidas se almacenarán dentro de una carpeta:

```text
saves/
```

Cada archivo tendrá formato JSON.

Ejemplo:

```text
saves/partida_2026_06_21_183000.json
```

La escritura debe hacerse de forma segura:

1. Escribir primero en un archivo temporal.
2. Validar que el JSON puede serializarse.
3. Reemplazar el archivo anterior.

Si un guardado está corrupto:

* No debe cerrarse la aplicación.
* Debe mostrarse un mensaje de error.
* El resto de los guardados debe seguir disponible.

---

# 10. Modelo de datos orientativo

## Jugador

```python
{
    "id": 1,
    "role": "adder",
    "current_area": "circle",
    "round_start_area": "square"
}
```

## Área

```python
{
    "id": "circle",
    "name": "Círculo",
    "score": 0,
    "players": [1, 4]
}
```

## Partida

```python
{
    "save_version": 1,
    "game": "calculated_areas",
    "name": "Partida de prueba",
    "round": 2,
    "scores_visible": false,
    "roles_visible": false,
    "players": [],
    "areas": {},
    "created_at": "2026-06-21T18:30:00",
    "updated_at": "2026-06-21T18:45:00"
}
```

---

# 11. Validaciones

La aplicación debe impedir:

* Finalizar una ronda sin jugadores.
* Finalizar la ronda 0 sin asignar roles.
* Finalizar una ronda si algún jugador no está dentro de un área.
* Colocar dos jugadores en el mismo slot.
* Asignar roles después de la ronda 0.
* Añadir o eliminar jugadores después de la ronda 0.
* Cargar un archivo que no corresponda a Áreas Calculadas.
* Continuar una partida con datos inválidos.

Los errores deben mostrarse mediante mensajes comprensibles para el usuario.

---

# 12. Separación entre lógica e interfaz

La resolución de las rondas debe poder ejecutarse sin necesidad de abrir la interfaz gráfica.

Debe existir una clase similar a:

```python
class CalculatedAreasGame:
    def add_player(self): ...
    def remove_player(self): ...
    def assign_roles(self): ...
    def move_player(self, player_id, destination_area): ...
    def resolve_round(self): ...
    def to_dict(self): ...
    @classmethod
    def from_dict(cls, data): ...
```

La interfaz debe limitarse a:

* Mostrar el estado.
* Recoger las acciones del usuario.
* Llamar a los métodos de la lógica.
* Refrescar la pantalla.

---

# 13. Pruebas mínimas

Crear pruebas para comprobar:

1. Un sumador añade un punto.
2. Un restador quita un punto.
3. Varios sumadores y restadores se acumulan correctamente.
4. Un intercambiador cambia las puntuaciones entre origen y destino.
5. Un intercambiador que no se mueve no produce efecto.
6. Las sumas y restas ocurren antes de los intercambios.
7. Varios intercambiadores se resuelven por número de jugador.
8. Guardar y cargar conserva todo el estado.
9. No se puede finalizar una ronda con jugadores sin colocar.
10. No se pueden reasignar roles después de la ronda 0.

---

# 14. Entregables

Genera:

1. Código fuente completo.
2. Archivo `requirements.txt` o `pyproject.toml`.
3. Instrucciones para instalar las dependencias.
4. Instrucciones para ejecutar la aplicación.
5. Estructura de carpetas.
6. Sistema de guardado local.
7. Pruebas básicas de la lógica.
8. Un archivo README con explicación del proyecto.

Primero crea un MVP funcional y después mejora el diseño visual.

No implementes funciones multijugador en red, cuentas, servidores ni bases de datos remotas.
