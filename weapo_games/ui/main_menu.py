from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class MainMenu(QWidget):
    new_game_requested = Signal()
    load_game_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(140, 90, 140, 90)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("WEAPO GAMES")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Colección local de juegos de mesa")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        new_button = QPushButton("Nueva partida")
        load_button = QPushButton("Cargar partida")
        exit_button = QPushButton("Salir")
        exit_button.setObjectName("secondaryButton")

        new_button.clicked.connect(self.new_game_requested)
        load_button.clicked.connect(self.load_game_requested)
        exit_button.clicked.connect(self.exit_requested)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(new_button)
        layout.addWidget(load_button)
        layout.addWidget(exit_button)
        layout.addStretch()
