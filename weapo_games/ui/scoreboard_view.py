from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from weapo_games.games.calculated_areas.game import AREA_IDS, CalculatedAreasGame


class AreaScoreToken(QWidget):
    """Ficha grande que muestra solamente la puntuación final de un área."""

    COLORS = {
        "circle": "#2E7D32",
        "square": "#1565C0",
        "triangle": "#C62828",
    }

    def __init__(self, area_id: str, area_name: str, symbol: str, score: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.area_id = area_id
        self.area_name = area_name
        self.symbol = symbol
        self.score = score
        self.setFixedSize(220, 190)

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001
        del event
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            shape = QPainterPath()
            if self.area_id == "circle":
                shape.addEllipse(10, 4, 200, 180)
            elif self.area_id == "triangle":
                shape.moveTo(QPointF(110, 4))
                shape.lineTo(QPointF(211, 184))
                shape.lineTo(QPointF(9, 184))
                shape.closeSubpath()
            else:
                shape.addRect(10, 4, 200, 180)

            painter.fillPath(shape, QColor(self.COLORS[self.area_id]))
            painter.setPen(QPen(Qt.GlobalColor.white, 4))
            painter.drawPath(shape)

            painter.setPen(Qt.GlobalColor.white)
            name_font = QFont(painter.font())
            name_font.setPixelSize(19)
            name_font.setBold(True)
            painter.setFont(name_font)
            painter.drawText(25, 34, 170, 25, Qt.AlignmentFlag.AlignCenter, self.area_name.upper())

            score_font = QFont(painter.font())
            score_font.setPixelSize(62)
            score_font.setBold(True)
            painter.setFont(score_font)
            painter.drawText(25, 65, 170, 82, Qt.AlignmentFlag.AlignCenter, str(self.score))
        finally:
            painter.end()


class ScoreboardView(QWidget):
    back_requested = Signal()

    def __init__(self, game: CalculatedAreasGame, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.game = game
        self.setObjectName("scoreboardView")
        self.area_tokens: dict[str, AreaScoreToken] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Puntuaciones finales")
        title.setObjectName("gameHeader")
        self.round_label = QLabel()
        self.round_label.setObjectName("roundLabel")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.round_label)
        root.addLayout(header)

        subtitle = QLabel("Resultado final de cada área")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)

        board = QFrame()
        board.setObjectName("scoreBoard")
        board.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QGridLayout(board)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setHorizontalSpacing(28)
        layout.setVerticalSpacing(18)

        positions = {
            "circle": (0, 1),
            "triangle": (1, 0),
            "square": (1, 2),
        }
        for area_id in AREA_IDS:
            area = game.areas[area_id]
            token = AreaScoreToken(area_id, area.name, area.symbol, area.score, board)
            self.area_tokens[area_id] = token
            layout.addWidget(token, *positions[area_id], alignment=Qt.AlignmentFlag.AlignCenter)
        for column in range(3):
            layout.setColumnStretch(column, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)
        root.addWidget(board, 1)

        back_button = QPushButton("Volver al juego")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_requested)
        root.addWidget(back_button)

        self.refresh()

    def refresh(self) -> None:
        self.round_label.setText(f"Ronda {self.game.round_number}")
        for area_id, token in self.area_tokens.items():
            token.score = self.game.areas[area_id].score
            token.update()
