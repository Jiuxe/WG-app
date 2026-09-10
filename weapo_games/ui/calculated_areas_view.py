from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from weapo_games.games.calculated_areas.game import (
    AREA_IDS,
    CalculatedAreasGame,
    GameRuleError,
)
from weapo_games.games.calculated_areas.player import Player
from weapo_games.games.calculated_areas.roles import ROLE_NAMES, Role
from weapo_games.services.save_manager import SaveManager
from weapo_games.ui.widgets import AreaDropWidget, PlayerToken


class RoleDistributionDialog(QDialog):
    def __init__(self, player_count: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cantidad de roles")
        self._player_count = player_count

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"Indica cuántos jugadores habrá de cada rol (total: {player_count})."
        ))

        form = QFormLayout()
        self.inputs: dict[Role, QSpinBox] = {}
        base, remainder = divmod(player_count, len(Role))
        for index, role in enumerate(Role):
            input_box = QSpinBox()
            input_box.setRange(0, player_count)
            input_box.setValue(base + (1 if index < remainder else 0))
            input_box.valueChanged.connect(self._update_total)
            self.inputs[role] = input_box
            form.addRow(f"{ROLE_NAMES[role]}:", input_box)
        layout.addLayout(form)

        self.total_label = QLabel()
        self.total_label.setObjectName("subtitle")
        layout.addWidget(self.total_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._update_total()

    def _update_total(self) -> None:
        total = sum(input_box.value() for input_box in self.inputs.values())
        self.total_label.setText(f"Total seleccionado: {total} / {self._player_count}")
        self.ok_button.setEnabled(total == self._player_count)

    def role_counts(self) -> dict[Role, int]:
        return {role: input_box.value() for role, input_box in self.inputs.items()}


class ManualRoleDialog(QDialog):
    ROLE_CODES: tuple[Role, ...] = (Role.ADDER, Role.SUBTRACTOR, Role.SWAPPER)

    def __init__(self, players: list[Player], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Modificar rol")
        self.inputs: dict[int, QSpinBox] = {}

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Indica el rol de cada jugador: 0 = sumador, 1 = restador, 2 = intercambiador."
        ))

        form = QFormLayout()
        for player in sorted(players, key=lambda item: item.id):
            input_box = QSpinBox()
            input_box.setRange(0, 2)
            input_box.setValue(
                self.ROLE_CODES.index(player.role) if player.role in self.ROLE_CODES else 0
            )
            self.inputs[player.id] = input_box
            form.addRow(f"Jugador {player.id}:", input_box)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def roles(self) -> dict[int, Role]:
        return {
            player_id: self.ROLE_CODES[input_box.value()]
            for player_id, input_box in self.inputs.items()
        }


class CalculatedAreasView(QWidget):
    back_to_menu_requested = Signal()
    scores_requested = Signal()

    def __init__(
        self,
        game: CalculatedAreasGame,
        save_manager: SaveManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.game = game
        self.save_manager = save_manager
        self.area_widgets: dict[str, AreaDropWidget] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 20)
        root.setSpacing(14)

        # Cabecera de ronda.
        top_bar = QHBoxLayout()
        game_name = QLabel("Áreas Calculadas")
        game_name.setObjectName("gameHeader")
        self.round_label = QLabel()
        self.round_label.setObjectName("roundLabel")
        self.round_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(game_name)
        top_bar.addStretch()
        top_bar.addWidget(self.round_label)
        top_bar.addStretch()
        top_bar.addSpacing(game_name.sizeHint().width())
        root.addLayout(top_bar)

        content = QHBoxLayout()
        content.setSpacing(14)

        # Columna izquierda: jugadores.
        self.players_panel = QFrame()
        self.players_panel.setObjectName("sidePanel")
        self.players_panel.setFixedWidth(220)
        players_layout = QVBoxLayout(self.players_panel)
        players_layout.setContentsMargins(14, 14, 14, 14)
        players_layout.setSpacing(10)

        players_title = QLabel("Jugadores")
        players_title.setObjectName("panelTitle")
        self.players_status = QLabel()
        self.players_status.setObjectName("subtitle")
        self.players_status.setWordWrap(True)

        player_buttons = QHBoxLayout()
        self.add_player_button = QPushButton("+ Añadir")
        self.remove_player_button = QPushButton("− Quitar")
        self.remove_player_button.setObjectName("secondaryButton")
        self.add_player_button.clicked.connect(self._add_player)
        self.remove_player_button.clicked.connect(self._remove_player)
        player_buttons.addWidget(self.add_player_button)
        player_buttons.addWidget(self.remove_player_button)

        self.pool_scroll = QScrollArea()
        self.pool_scroll.setWidgetResizable(True)
        self.pool_scroll.setObjectName("playerPool")
        self.pool_container = QWidget()
        self.pool_layout = QVBoxLayout(self.pool_container)
        self.pool_layout.setContentsMargins(8, 8, 8, 8)
        self.pool_layout.setSpacing(10)
        self.pool_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.pool_scroll.setWidget(self.pool_container)

        players_layout.addWidget(players_title)
        players_layout.addWidget(self.players_status)
        players_layout.addLayout(player_buttons)
        players_layout.addWidget(self.pool_scroll, 1)

        # Centro: áreas.
        center_scroll = QScrollArea()
        center_scroll.setWidgetResizable(True)
        center_scroll.setFrameShape(QFrame.Shape.NoFrame)
        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(14)

        for area_id in AREA_IDS:
            area = self.game.areas[area_id]
            widget = AreaDropWidget(area.id, area.name, area.symbol)
            widget.player_dropped.connect(self._move_player)
            self.area_widgets[area_id] = widget
            center_layout.addWidget(widget, 1)

        center_scroll.setWidget(center_container)

        # Derecha: acciones.
        actions_panel = QFrame()
        actions_panel.setObjectName("sidePanel")
        actions_panel.setFixedWidth(250)
        actions_layout = QVBoxLayout(actions_panel)
        actions_layout.setContentsMargins(14, 14, 14, 14)
        actions_layout.setSpacing(10)

        actions_title = QLabel("Acciones")
        actions_title.setObjectName("panelTitle")
        self.assign_roles_button = QPushButton("Asignar roles")
        self.modify_role_button = QPushButton("Modificar rol")
        self.scores_button = QPushButton()
        self.roles_button = QPushButton()
        save_button = QPushButton("Guardar partida")
        self.finish_round_button = QPushButton("Finalizar ronda")
        self.finish_round_button.setObjectName("primaryDangerButton")
        menu_button = QPushButton("Volver al menú")
        menu_button.setObjectName("secondaryButton")

        self.assign_roles_button.clicked.connect(self._assign_roles)
        self.modify_role_button.clicked.connect(self._modify_roles)
        self.scores_button.clicked.connect(self._show_scores)
        self.roles_button.clicked.connect(self._toggle_roles)
        save_button.clicked.connect(self._save_game)
        self.finish_round_button.clicked.connect(self._finish_round)
        menu_button.clicked.connect(self.back_to_menu_requested)

        self.role_summary = QLabel()
        self.role_summary.setObjectName("subtitle")
        self.role_summary.setWordWrap(True)

        actions_layout.addWidget(actions_title)
        actions_layout.addWidget(self.assign_roles_button)
        actions_layout.addWidget(self.modify_role_button)
        actions_layout.addWidget(self.scores_button)
        actions_layout.addWidget(self.roles_button)
        actions_layout.addWidget(save_button)
        actions_layout.addSpacing(8)
        actions_layout.addWidget(self.finish_round_button)
        actions_layout.addWidget(self.role_summary)
        actions_layout.addStretch()
        actions_layout.addWidget(menu_button)

        content.addWidget(self.players_panel)
        content.addWidget(center_scroll, 1)
        content.addWidget(actions_panel)
        root.addLayout(content, 1)

        self.refresh()

    def refresh(self) -> None:
        self.round_label.setText(f"Ronda {self.game.round_number}")
        self.players_status.setText(
            f"{len(self.game.players)} jugador(es). Arrastra las fichas a cualquiera de las áreas."
        )

        setup_enabled = self.game.round_number == 0
        self.add_player_button.setEnabled(setup_enabled)
        self.remove_player_button.setEnabled(setup_enabled and bool(self.game.players))
        self.assign_roles_button.setEnabled(setup_enabled and bool(self.game.players))
        self.modify_role_button.setEnabled(setup_enabled and self.game.roles_assigned)
        self.scores_button.setText("Mostrar puntuaciones")
        self.roles_button.setText(
            "Ocultar roles" if self.game.roles_visible else "Mostrar roles"
        )

        while self.pool_layout.count():
            item = self.pool_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        unplaced = [player for player in self.game.players if player.current_area is None]
        for player in sorted(unplaced, key=lambda item: item.id):
            self.pool_layout.addWidget(
                PlayerToken(player, self.game.roles_visible, self.pool_container),
                alignment=Qt.AlignmentFlag.AlignHCenter,
            )
        self.pool_layout.addStretch()

        total_slots = len(self.game.players)
        for area_id, widget in self.area_widgets.items():
            area = self.game.areas[area_id]
            players = sorted(
                (player for player in self.game.players if player.current_area == area_id),
                key=lambda item: item.id,
            )
            widget.set_state(
                score=area.score,
                scores_visible=self.game.scores_visible,
                players=players,
                total_slots=total_slots,
                roles_visible=self.game.roles_visible,
            )

        if self.game.roles_assigned:
            counts = {role: 0 for role in Role}
            for player in self.game.players:
                if player.role:
                    counts[player.role] += 1
            self.role_summary.setText(
                "Roles asignados:\n"
                + "\n".join(f"{ROLE_NAMES[role]}: {counts[role]}" for role in Role)
            )
        else:
            self.role_summary.setText("Los roles todavía no están asignados.")

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "No se pudo realizar la acción", message)

    def _add_player(self) -> None:
        try:
            self.game.add_player()
            self.refresh()
        except GameRuleError as exc:
            self._show_error(str(exc))

    def _remove_player(self) -> None:
        try:
            removed = self.game.remove_last_player()
            self.refresh()
            QMessageBox.information(self, "Jugador eliminado", f"Se eliminó el jugador {removed.id}.")
        except GameRuleError as exc:
            self._show_error(str(exc))

    def _move_player(self, player_id: int, area_id: str, slot_index: int) -> None:
        try:
            self.game.move_player(player_id, area_id, slot_index)
            self.refresh()
        except GameRuleError as exc:
            self._show_error(str(exc))

    def _assign_roles(self) -> None:
        if self.game.roles_assigned:
            answer = QMessageBox.question(
                self,
                "Reasignar roles",
                "Los roles ya están asignados. ¿Quieres volver a repartirlos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        dialog = RoleDistributionDialog(len(self.game.players), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            counts = self.game.assign_roles(role_counts=dialog.role_counts())
        except GameRuleError as exc:
            self._show_error(str(exc))
            return

        self.refresh()
        details = "\n".join(f"{ROLE_NAMES[role]}: {counts[role]}" for role in Role)
        QMessageBox.information(self, "Roles asignados", details)

    def _modify_roles(self) -> None:
        dialog = ManualRoleDialog(self.game.players, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            for player_id, role in dialog.roles().items():
                self.game.set_player_role(player_id, role)
        except GameRuleError as exc:
            self._show_error(str(exc))
            return

        self.refresh()

    def _show_scores(self) -> None:
        self.scores_requested.emit()

    def _toggle_roles(self) -> None:
        if not self.game.roles_assigned:
            self._show_error("Asigna los roles antes de intentar mostrarlos.")
            return
        self.game.roles_visible = not self.game.roles_visible
        self.refresh()

    def _save_game(self) -> None:
        name, accepted = QInputDialog.getText(
            self,
            "Guardar partida",
            "Nombre del guardado:",
            text=self.game.name,
        )
        if not accepted:
            return
        try:
            path = self.save_manager.save_game(self.game, name)
        except (OSError, ValueError) as exc:
            self._show_error(str(exc))
            return
        QMessageBox.information(
            self,
            "Partida guardada",
            f"La partida se guardó correctamente en:\n{path}",
        )

    def _finish_round(self) -> None:
        try:
            result = self.game.resolve_round()
        except GameRuleError as exc:
            self._show_error(str(exc))
            return

        self.refresh()
        QMessageBox.information(
            self,
            "Resumen de la ronda",
            result.format_summary(self.game.area_names),
        )
