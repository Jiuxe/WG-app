from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from weapo_games.services.save_manager import SaveInfo, SaveManager


class LoadGameView(QWidget):
    load_requested = Signal(object)
    back_requested = Signal()

    def __init__(self, save_manager: SaveManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.save_manager = save_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 50, 70, 50)
        layout.setSpacing(16)

        title = QLabel("Cargar partida")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.save_list = QListWidget()
        self.save_list.setObjectName("saveList")
        self.save_list.itemDoubleClicked.connect(self._load_selected)

        buttons = QHBoxLayout()
        back_button = QPushButton("Volver")
        back_button.setObjectName("secondaryButton")
        refresh_button = QPushButton("Actualizar")
        load_button = QPushButton("Cargar")

        back_button.clicked.connect(self.back_requested)
        refresh_button.clicked.connect(self.refresh)
        load_button.clicked.connect(self._load_selected)

        buttons.addWidget(back_button)
        buttons.addStretch()
        buttons.addWidget(refresh_button)
        buttons.addWidget(load_button)

        layout.addWidget(title)
        layout.addWidget(self.save_list, 1)
        layout.addLayout(buttons)

    def refresh(self) -> None:
        self.save_list.clear()
        saves = self.save_manager.list_saves()
        if not saves:
            item = QListWidgetItem("No hay partidas guardadas.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.save_list.addItem(item)
            return

        for save in saves:
            self.save_list.addItem(self._build_item(save))

    @staticmethod
    def _build_item(save: SaveInfo) -> QListWidgetItem:
        if save.error:
            text = f"⚠ {save.name}\nArchivo corrupto: {save.error}"
        else:
            readable_date = save.updated_at.replace("T", " ")
            text = (
                f"{save.name}\n"
                f"Áreas Calculadas · Ronda {save.round_number} · {readable_date}"
            )
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, str(save.path))
        if save.error:
            item.setFlags(Qt.ItemFlag.NoItemFlags)
        return item

    def _load_selected(self, *_args) -> None:
        item = self.save_list.currentItem()
        if item is None:
            return
        raw_path = item.data(Qt.ItemDataRole.UserRole)
        if raw_path:
            self.load_requested.emit(Path(raw_path))
