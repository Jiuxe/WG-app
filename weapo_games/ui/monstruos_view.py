from __future__ import annotations

import webbrowser
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QRadioButton, QSpinBox, QVBoxLayout, QWidget,
)

from weapo_games.games.monstruos import MonstruosGame
from weapo_games.services.monstruos_presentation_server import MonstruosPresentationServer
from weapo_games.services.save_manager import SaveManager


class MonstruosSetupView(QWidget):
    started = Signal(object)
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(90, 50, 90, 50)
        title = QLabel("Monstruos de Halloween")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        intro = QLabel("Añade los jugadores. El orden de esta lista será el orden de los turnos.")
        intro.setObjectName("subtitle")
        intro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(intro)
        row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre del jugador")
        self.name_edit.returnPressed.connect(self._add)
        add = QPushButton("Añadir")
        add.clicked.connect(self._add)
        row.addWidget(self.name_edit)
        row.addWidget(add)
        root.addLayout(row)
        self.players = QListWidget()
        self.players.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        root.addWidget(self.players, 1)
        actions = QHBoxLayout()
        back = QPushButton("Volver")
        back.setObjectName("secondaryButton")
        back.clicked.connect(self.back_requested)
        start = QPushButton("Comenzar partida")
        start.clicked.connect(self._start)
        actions.addWidget(back)
        actions.addStretch()
        actions.addWidget(start)
        root.addLayout(actions)

    def _add(self) -> None:
        name = self.name_edit.text().strip()
        if name:
            self.players.addItem(name)
            self.name_edit.clear()

    def _start(self) -> None:
        names = [self.players.item(i).text() for i in range(self.players.count())]
        if not names:
            QMessageBox.warning(self, "Faltan jugadores", "Añade al menos un jugador.")
            return
        if len(set(names)) != len(names):
            QMessageBox.warning(self, "Nombres repetidos", "Cada jugador debe tener un nombre distinto.")
            return
        self.started.emit(MonstruosGame(names))


MONSTER_IMAGES_DIR = Path(__file__).resolve().parents[2] / "img" / "monstruos"


class PlayerEditDialog(QDialog):
    def __init__(self, player, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Editar jugador: {player.name}")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(player.name)
        self.score_edit = QSpinBox()
        self.score_edit.setRange(-999999, 999999)
        self.score_edit.setValue(player.score)
        self.inventory_edit = QLineEdit(", ".join(player.inventory))
        self.inventory_edit.setPlaceholderText("Ej.: Daga, Hielo")
        form.addRow("Nombre:", self.name_edit)
        form.addRow("Puntos:", self.score_edit)
        form.addRow("Inventario:", self.inventory_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, int, list[str]]:
        inventory = [item.strip() for item in self.inventory_edit.text().split(",") if item.strip()]
        return self.name_edit.text(), self.score_edit.value(), inventory


def _monster_value(monster: dict | object, key: str):
    """Obtiene datos tanto de snapshots (dict) como de Monster en una partida."""
    if isinstance(monster, dict):
        return monster[key]
    return {
        "id": monster.id,
        "name": monster.name,
        "hp": monster.hp,
        "max_hp": monster.max_hp,
        "poisoned": monster.poisoned,
        "frozen": monster.frozen_by is not None,
        "bomb": monster.bomb_by is not None,
    }[key]


def _monster_image_path(name: str) -> Path:
    return MONSTER_IMAGES_DIR / f"{name}.jpg"


def _card(monster: dict | object, compact: bool = False, public: bool = False) -> QFrame:
    frame = QFrame()
    frame.setObjectName("monsterCard")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12 if compact else 18, 12, 12 if compact else 18, 12)
    monster_id = _monster_value(monster, "id")
    monster_name = _monster_value(monster, "name")
    image = QLabel()
    image.setObjectName("monsterIcon")
    image.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pixmap = QPixmap(str(_monster_image_path(monster_name)))
    if not pixmap.isNull():
        image.setPixmap(pixmap.scaled(
            150 if not compact else 105,
            150 if not compact else 105,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
    else:
        image.setText("🎃" if monster_id % 3 == 1 else "👻" if monster_id % 3 == 2 else "🕷️")
    name = QLabel(monster_name)
    name.setObjectName("monsterName")
    name.setAlignment(Qt.AlignmentFlag.AlignCenter)
    name.setWordWrap(True)
    hp_text = f"❤ {_monster_value(monster, 'max_hp')}" if public else f"❤ {_monster_value(monster, 'hp')} / {_monster_value(monster, 'max_hp')}"
    hp = QLabel(hp_text)
    hp.setObjectName("monsterHp")
    hp.setAlignment(Qt.AlignmentFlag.AlignCenter)
    effects = []
    if not public and _monster_value(monster, "poisoned"): effects.append("☠ Veneno")
    if not public and _monster_value(monster, "frozen"): effects.append("❄ Congelado")
    if not public and _monster_value(monster, "bomb"): effects.append("💣 Bomba")
    effect = QLabel(" · ".join(effects))
    effect.setObjectName("monsterEffect")
    effect.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(image)
    layout.addWidget(name)
    layout.addWidget(hp)
    layout.addWidget(effect)
    return frame


class MonstruosView(QWidget):
    back_to_menu_requested = Signal()

    def __init__(self, game: MonstruosGame, save_manager: SaveManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.game = game
        self.save_manager = save_manager
        self.presentation_server: MonstruosPresentationServer | None = None
        self.save_ok = False
        self.last_save_path: Path | None = None
        self.selected_item: str | None = None
        self.selected_slots: set[int] = set()
        self.sword_mode = "single"
        self.master_root = QVBoxLayout(self)
        self.master_root.setContentsMargins(28, 22, 28, 22)
        self._build_header()
        self.body = QVBoxLayout()
        self.master_root.addLayout(self.body, 1)
        self.show_master()
        self._save_state()

    def _build_header(self) -> None:
        row = QHBoxLayout()
        title = QLabel("Monstruos de Halloween")
        title.setObjectName("gameHeader")
        row.addWidget(title)
        self.round_counter = QLabel()
        self.round_counter.setObjectName("monsterRoundCounter")
        row.addWidget(self.round_counter)
        row.addStretch()
        master = QPushButton("Vista Master")
        master.clicked.connect(self.show_master)
        players = QPushButton("Abrir ventana de Jugadores")
        players.setObjectName("secondaryButton")
        players.clicked.connect(self.open_players_window)
        save = QPushButton("Guardar partida")
        save.setObjectName("saveStatusButton")
        save.clicked.connect(self._manual_save)
        self.save_button = save
        refresh = QPushButton("Refrescar")
        refresh.setObjectName("secondaryButton")
        refresh.clicked.connect(self.show_players)
        back = QPushButton("Salir")
        back.setObjectName("secondaryButton")
        back.clicked.connect(self.back_to_menu_requested)
        row.addWidget(master)
        row.addWidget(players)
        row.addWidget(save)
        row.addWidget(refresh)
        row.addWidget(back)
        self.master_root.addLayout(row)
        self._refresh_round_counter()
        self._set_save_status(False)

    def open_players_window(self) -> None:
        self._save_state()
        if self.presentation_server is None:
            self.presentation_server = MonstruosPresentationServer(self.game, MONSTER_IMAGES_DIR)
        webbrowser.open(self.presentation_server.url)

    def _clear_body(self) -> None:
        while self.body.count():
            item = self.body.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget(): child.widget().deleteLater()

    def show_players(self) -> None:
        self._save_state()
        self._clear_body()
        state = self.game.published
        active = QHBoxLayout()
        for monster in state["active"]: active.addWidget(_card(monster, public=True))
        self.body.addLayout(active)
        queue_title = QLabel("PRÓXIMOS MONSTRUOS")
        queue_title.setObjectName("panelTitle")
        self.body.addWidget(queue_title)
        queue = QHBoxLayout()
        for monster in state["queue"]: queue.addWidget(_card(monster, True, public=True))
        self.body.addLayout(queue)
        hint = QLabel("Los cambios del Master aparecen al pulsar Refrescar.")
        hint.setObjectName("subtitle")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.addWidget(hint)

    def _save_state(self) -> bool:
        try:
            path = self.save_manager.save_monstruos(self.game)
            self.last_save_path = path
            return True
        except (OSError, TypeError, ValueError) as exc:
            self._set_save_status(False)
            QMessageBox.warning(
                self,
                "No se pudo guardar",
                f"{exc}\n\nRuta prevista:\n{self.save_manager.monstruos_autosave_path}",
            )
            return False

    def _manual_save(self) -> None:
        if self._save_state():
            self._set_save_status(True)

    def _set_save_status(self, saved: bool) -> None:
        self.save_ok = saved
        if saved:
            self.save_button.setText("Guardar partida ✓")
            self.save_button.setStyleSheet(
                "QPushButton#saveStatusButton { background-color: #2F9E5B; "
                "border-color: #7CFFAA; color: white; font-weight: 800; }"
            )
        else:
            self.save_button.setText("Guardar partida")
            self.save_button.setStyleSheet(
                "QPushButton#saveStatusButton { background-color: #A83248; "
                "border-color: #ED7180; color: white; font-weight: 800; }"
            )

    def _mark_unsaved(self) -> None:
        self._set_save_status(False)

    def _refresh_round_counter(self) -> None:
        self.round_counter.setText(f"Ronda {self.game.turn_number}")

    def show_master(self) -> None:
        self._clear_body()
        if self.game.round_active:
            self._show_turn()
            return
        order = QLabel("JUGADORES — arrastra para cambiar el orden")
        order.setObjectName("panelTitle")
        self.body.addWidget(order)
        player_actions = QHBoxLayout()
        sort_button = QPushButton("Ordenar por puntos ↓")
        sort_button.setObjectName("secondaryButton")
        sort_button.clicked.connect(self._sort_players_by_score)
        player_actions.addWidget(sort_button)
        player_actions.addStretch()
        self.body.addLayout(player_actions)
        listing = QListWidget()
        listing.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        player_colors = ("#263c52", "#49334f", "#3b4b35", "#4b3b2e", "#303b55", "#4b3040")
        for index, player in enumerate(self.game.players):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, player.name)
            item.setSizeHint(QSize(0, 126))
            card = QFrame()
            card.setObjectName("playerDashboardCard")
            card.setStyleSheet(f"QFrame#playerDashboardCard {{ background: {player_colors[index % len(player_colors)]}; border: 1px solid #68778a; border-radius: 12px; }}")
            card_layout = QHBoxLayout(card)
            summary = QVBoxLayout()
            summary.addWidget(QLabel(f"<b>{player.name}</b>"))
            summary.addWidget(QLabel(f"{player.score} puntos"))
            summary.addWidget(QLabel(f"Inventario: {', '.join(player.inventory)}"))
            edit = QPushButton("Editar")
            edit.setObjectName("secondaryButton")
            edit.clicked.connect(lambda checked=False, current_player=player: self._edit_player(current_player))
            summary.addWidget(edit)
            history = QVBoxLayout()
            history.addWidget(QLabel("<b>Bajas</b>"))
            kills = ", ".join(f"({turno}, {name}, {points})" for turno, name, points in player.kills)
            history.addWidget(QLabel(kills or "Sin bajas"))
            card_layout.addLayout(summary, 1)
            card_layout.addLayout(history, 2)
            listing.addItem(item)
            listing.setItemWidget(item, card)
        listing.model().rowsMoved.connect(lambda *_: self._sync_player_order(listing))
        self.body.addWidget(listing, 1)
        start = QPushButton("Ejecutar ronda")
        start.clicked.connect(self._start_round)
        self.body.addWidget(start)
        note = QLabel("Cada jugador confirma una acción y el turno pasa automáticamente al siguiente.")
        note.setObjectName("subtitle")
        self.body.addWidget(note)

    def _sync_player_order(self, listing: QListWidget) -> None:
        self.game.reorder_players([listing.item(i).data(Qt.ItemDataRole.UserRole) for i in range(listing.count())])
        self._mark_unsaved()

    def _sort_players_by_score(self) -> None:
        self.game.sort_players_by_score()
        self.game.publish()
        self._mark_unsaved()
        self.show_master()

    def _edit_player(self, player) -> None:
        dialog = PlayerEditDialog(player, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        name, score, inventory = dialog.values()
        try:
            self.game.update_player(player, name, score, inventory)
        except ValueError as exc:
            QMessageBox.warning(self, "Jugador no válido", str(exc))
            return
        self.game.publish()
        self._mark_unsaved()
        self.show_master()

    def _start_round(self) -> None:
        try:
            self.game.start_round()
            self._mark_unsaved()
            self._refresh_round_counter()
            events = self.game.begin_turn()
            if events: QMessageBox.information(self, "Inicio de turno", "\n".join(events))
            self.show_master()
        except ValueError as exc:
            QMessageBox.warning(self, "No se puede iniciar", str(exc))

    def _show_turn(self) -> None:
        player = self.game.current()
        heading = QLabel(f"TURNO DE {player.name.upper()}   ·   Jugador {self.game.current_player + 1}/{len(self.game.players)}")
        heading.setObjectName("roundLabel")
        self.body.addWidget(heading)
        content = QHBoxLayout()
        controls = QFrame()
        controls.setObjectName("sidePanel")
        control_layout = QVBoxLayout(controls)
        control_layout.addWidget(QLabel("Objeto"))
        self.item_buttons = []
        for index, item in enumerate(item for item in player.inventory if item != "Doblon"):
            button = QPushButton(item)
            button.setObjectName("inventoryItem")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=item: self._select_item(i))
            self.item_buttons.append(button)
            control_layout.addWidget(button)
        control_layout.addWidget(QLabel("Modo espada doble"))
        single = QRadioButton("4 daño a 1")
        split = QRadioButton("2 daño a 2")
        single.setChecked(True)
        single.toggled.connect(lambda checked: checked and setattr(self, "sword_mode", "single"))
        split.toggled.connect(lambda checked: checked and setattr(self, "sword_mode", "split"))
        control_layout.addWidget(single)
        control_layout.addWidget(split)
        self.confirm = QPushButton("Confirmar acción")
        self.confirm.clicked.connect(self._confirm)
        control_layout.addStretch()
        control_layout.addWidget(self.confirm)
        content.addWidget(controls)
        monsters = QVBoxLayout()
        monsters.addWidget(QLabel("Objetivos — selecciona uno o dos según el objeto"))
        target_row = QHBoxLayout()
        self.target_buttons = []
        for slot, monster in enumerate(self.game.active):
            button = QPushButton()
            button.setCheckable(True)
            button.setObjectName("targetMonster")
            image_path = _monster_image_path(monster.name)
            if image_path.exists():
                button.setIcon(QIcon(str(image_path)))
                button.setIconSize(QSize(110, 110))
            button.setText(f"{monster.name}\n❤ {monster.hp}/{monster.max_hp}")
            button.clicked.connect(lambda checked, s=slot: self._select_slot(s))
            target_row.addWidget(button)
            self.target_buttons.append(button)
        self._refresh_target_styles()
        monsters.addLayout(target_row)
        content.addLayout(monsters, 1)
        self.body.addLayout(content, 1)

    def _select_item(self, item: str) -> None:
        self.selected_item = item
        for button in self.item_buttons: button.setChecked(button.text() == item)

    def _select_slot(self, slot: int) -> None:
        if slot in self.selected_slots:
            self.selected_slots.remove(slot)
        elif self.sword_mode == "split":
            self.selected_slots.add(slot)
        else:
            self.selected_slots = {slot}
        for index, button in enumerate(self.target_buttons): button.setChecked(index in self.selected_slots)
        self._refresh_target_styles()

    def _refresh_target_styles(self) -> None:
        colors = {
            "default": ("#231B25", "#6B4054"),
            "frozen": ("#214C78", "#5DA9E9"),
            "poisoned": ("#7A2938", "#ED7180"),
            "selected": ("#2F9E5B", "#7CFFAA"),
        }
        for index, button in enumerate(self.target_buttons):
            monster = self.game.active[index]
            state = "selected" if index in self.selected_slots else "default"
            if state != "selected":
                if monster.frozen_by is not None:
                    state = "frozen"
                elif monster.poisoned:
                    state = "poisoned"
            background, border = colors[state]
            button.setStyleSheet(
                "QPushButton#targetMonster {"
                f"background-color: {background}; border: 3px solid {border};"
                "border-radius: 14px; color: #F3F5F7; font-weight: 800;}"
            )

    def shutdown_presentation_server(self) -> None:
        if self.presentation_server is not None:
            self.presentation_server.stop()
            self.presentation_server = None

    def closeEvent(self, event) -> None:
        self.shutdown_presentation_server()
        super().closeEvent(event)

    def _confirm(self) -> None:
        try:
            if not self.selected_item: raise ValueError("Selecciona un objeto.")
            self.game.use_item(self.selected_item, sorted(self.selected_slots), self.sword_mode)
            self._mark_unsaved()
            self.selected_item = None
            self.selected_slots.clear()
            if not self.game.active:
                self.game.round_active = False
                self.game.current_player = 0
                self.game.publish()
                self._save_state()
                QMessageBox.information(self, "Partida terminada", "Se ha eliminado al último monstruo.")
                self.show_master()
                return
            if self.game.finish_turn():
                self.game.publish()
                QMessageBox.information(self, "Ronda terminada", "La ronda ha terminado. El estado ya está listo para publicar.")
            else:
                events = self.game.begin_turn()
                if events: QMessageBox.information(self, "Inicio de turno", "\n".join(events))
            self.show_master()
        except ValueError as exc:
            QMessageBox.warning(self, "Acción no válida", str(exc))
