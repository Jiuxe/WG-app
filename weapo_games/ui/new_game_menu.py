from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class NewGameMenu(QWidget):
    calculated_areas_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(70, 50, 70, 50)
        outer.setSpacing(20)

        title = QLabel("Nueva partida")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        game_card = QFrame()
        game_card.setObjectName("gameCard")
        card_layout = QHBoxLayout(game_card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(24)

        symbol = QLabel("●  ■  ▲")
        symbol.setObjectName("gameSymbol")
        symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        name = QLabel("Áreas Calculadas")
        name.setObjectName("gameName")
        description = QLabel(
            "Juego de roles ocultos en el que los jugadores modifican e intercambian "
            "las puntuaciones de tres áreas."
        )
        description.setWordWrap(True)
        description.setObjectName("subtitle")
        play_button = QPushButton("Crear partida")
        play_button.clicked.connect(self.calculated_areas_requested)

        text_layout.addWidget(name)
        text_layout.addWidget(description)
        text_layout.addSpacing(8)
        text_layout.addWidget(play_button)

        card_layout.addWidget(symbol, 1)
        card_layout.addLayout(text_layout, 3)

        back_button = QPushButton("Volver")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_requested)

        outer.addWidget(title)
        outer.addSpacing(20)
        outer.addWidget(game_card)
        outer.addStretch()
        outer.addWidget(back_button)
