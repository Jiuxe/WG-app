from __future__ import annotations

from math import ceil

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from weapo_games.games.calculated_areas.player import Player
from weapo_games.games.calculated_areas.roles import ROLE_COLORS

PLAYER_MIME_PREFIX = "weapo-player:"


class PlayerToken(QFrame):
    """Ficha cuadrada arrastrable que representa a un jugador."""

    def __init__(self, player: Player, reveal_role: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.player = player
        self._press_position = QPoint()
        self.setFixedSize(58, 58)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        background = "#171717"
        if reveal_role and player.role is not None:
            background = ROLE_COLORS[player.role]

        self.setStyleSheet(
            f"""
            PlayerToken {{
                background: {background};
                border: 2px solid #F5F5F5;
                border-radius: 8px;
            }}
            QLabel {{
                color: white;
                font-size: 20px;
                font-weight: 700;
                background: transparent;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        number = QLabel(str(player.id), self)
        number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(number)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return
        distance = (event.position().toPoint() - self._press_position).manhattanLength()
        if distance < 8:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"{PLAYER_MIME_PREFIX}{self.player.id}")
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.position().toPoint())
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


class SlotDropWidget(QFrame):
    player_dropped = Signal(int, str, int)

    def __init__(
        self,
        area_id: str,
        slot_index: int,
        player: Player | None,
        roles_visible: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.area_id = area_id
        self.slot_index = slot_index
        self.setAcceptDrops(True)
        self.setFixedSize(64, 64)
        self.setProperty("occupied", player is not None)
        self.setObjectName("playerSlot")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        if player is not None:
            layout.addWidget(PlayerToken(player, roles_visible, self))

    def dragEnterEvent(self, event) -> None:  # noqa: N802, ANN001
        text = event.mimeData().text() if event.mimeData().hasText() else ""
        if text.startswith(PLAYER_MIME_PREFIX):
            event.acceptProposedAction()
            self.setProperty("dragActive", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802, ANN001
        self._clear_drag_style()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802, ANN001
        self._clear_drag_style()
        text = event.mimeData().text()
        try:
            player_id = int(text.removeprefix(PLAYER_MIME_PREFIX))
        except ValueError:
            event.ignore()
            return

        self.player_dropped.emit(player_id, self.area_id, self.slot_index)
        event.acceptProposedAction()

    def _clear_drag_style(self) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)


class AreaDropWidget(QFrame):
    player_dropped = Signal(int, str, int)

    def __init__(
        self,
        area_id: str,
        name: str,
        symbol: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.area_id = area_id
        self.area_name = name
        self.setObjectName("areaCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(230)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(10)

        self.symbol_label = QLabel(symbol)
        self.symbol_label.setObjectName("areaSymbol")
        self.symbol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label = QLabel(name)
        self.name_label.setObjectName("areaName")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label = QLabel("?")
        self.score_label.setObjectName("areaScore")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slots_widget = QWidget()
        self.slots_layout = QGridLayout(self.slots_widget)
        self.slots_layout.setContentsMargins(0, 0, 0, 0)
        self.slots_layout.setHorizontalSpacing(10)
        self.slots_layout.setVerticalSpacing(10)
        self.slots_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.main_layout.addWidget(self.symbol_label)
        self.main_layout.addWidget(self.name_label)
        self.main_layout.addWidget(self.score_label)
        self.main_layout.addWidget(self.slots_widget, 1)

    def set_state(
        self,
        score: int,
        scores_visible: bool,
        players: list[Player],
        total_slots: int,
        roles_visible: bool,
    ) -> None:
        self.score_label.setText(str(score) if scores_visible else "?")

        while self.slots_layout.count():
            item = self.slots_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        visible_slots = max(1, total_slots)
        players_by_slot = {
            player.current_slot: player
            for player in players
            if isinstance(player.current_slot, int)
        }
        columns = max(1, min(3, ceil(visible_slots ** 0.5)))

        for slot_index in range(visible_slots):
            slot = SlotDropWidget(
                area_id=self.area_id,
                slot_index=slot_index,
                player=players_by_slot.get(slot_index),
                roles_visible=roles_visible,
                parent=self.slots_widget,
            )
            slot.player_dropped.connect(self.player_dropped.emit)
            self.slots_layout.addWidget(slot, slot_index // columns, slot_index % columns)
