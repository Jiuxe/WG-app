# Weapo Games App

## Inicio

Quiero crear una app de juego de escritorio en python.

El inicio de este juego sera un menu donde puedo crear una partida o cargar una nueva.

La pestaña de crear una nueva partida desplegara una lista de juegos disponibles.

El primer juego que crearemos sera el siguiente

## Primer Juego: Areas Calculadas

Es un juego de roles ocultos donde los jugadores se situaran en tres areas correspondientes a cada rol. Cada turno cada jugador podra decidir si moverse a otro area o quedarse en el que esta. Cada area tendra una puntuacion inicializandolo con 0 al principio del juego, este valor se modifica con el movimiento de los jugadores a este area o salida dependiendo del rol.

Los roles disponibles son los siguientes:

- Sumador (representado con un circulo y el color verde): Los jugadores con este rol sumarán +1 al area en el que este al final del turno.

- Restador (representado con un triangulo y el color rojo): Los jugadores con este rol restaran -1 al area en el que este al final del turno.

- Intercambiadores (representado con un cuadrado y el color azul): Los jugadores con este rol intercambiaran la puntuacion de las areas entre las que se haya movido en un turno.

Prioridad de roles: Primero se ejecuta la suma o resta de los jugadores y luego se intercambia el valor si este se aplica.

### Interfaz

La interfaz del juego se representara con 3 areas. Circulo, Cuadrado y Triangulo. Estas areas estaran en el medio de la pantalla. 

A la izquierda habra un area donde puedo agregar o quitar jugadores, que se veran como un cuadrado negro y numero en blanco en medio. Este numero dependera del numero de jugador que sea.

A la derecha habra un menu de botones:

- Un boton para asignar los roles a los jugadores (solo disponible en la ronda 0). 

- Un boton para mostrar la puntuacion actual de cada area

- Un boton para mostrar el rol de cada jugador. Al pulsar el boton quiero que cada cuadrado de cada jugador se vuelva del color del rol al que pertenece. Sumador - Verde, Restador - Rojo, Intercambiador - Azul. Si vuelvo a pulsar el boton volveran al estado original de todos en negro.

- Un boton para guardar la partida. Quiero que los guardados se hagan en local.

- Un boton para finalizar la ronda, donde se sumara el contador de ronda que estara arriba en el centro de la pantalla. Este boton provocara que se ejecute la accion de los roles sobre las areas en las que estan contenidos en el momento actual.

El cuadrado que representa a los jugadores quiero poder agarrarlos y arrastrarlo a las areas correspondientes.

Las areas deben tener slot, que representaran la cantidad de jugadores que caben en esta area. El sloty se representara como un cuadrado vacio transparente.
