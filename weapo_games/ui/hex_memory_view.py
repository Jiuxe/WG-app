from __future__ import annotations

import re

from PySide6.QtCore import QPointF, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QMessageBox,
    QLineEdit, QPushButton, QPlainTextEdit, QSpinBox, QVBoxLayout, QWidget,
)

from weapo_games.games.hex_memory import HexBoardError, HexCell, HexMemoryGame


class HexSolutionsDialog(QDialog):
    def __init__(self, game: HexMemoryGame, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Soluciones del máster — ronda {game.round_number}")
        self.resize(470, 420)
        layout = QVBoxLayout(self)
        title = QLabel(f"Objetivo: {game.target}\nSoluciones válidas: {len(game.target_lines)}")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        solutions = QPlainTextEdit("\n".join(game.formatted_target_solutions()))
        solutions.setReadOnly(True)
        layout.addWidget(solutions)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class HexCellWidget(QWidget):
    def __init__(self, cell: HexCell, revealed: bool, show_numbers: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cell = cell
        self.revealed = revealed
        self.show_numbers = show_numbers
        self.setFixedSize(92, 82)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        points = QPolygonF(
            [QPointF(46, 2), QPointF(87, 22), QPointF(87, 60), QPointF(46, 80), QPointF(5, 60), QPointF(5, 22)]
        )
        painter.setBrush(QColor("#F5C542" if not self.revealed else "#303846"))
        painter.setPen(QColor("#FFD75E" if not self.revealed else "#596577"))
        painter.drawPolygon(points)
        painter.setPen(QColor("#111318" if not self.revealed else "#F3F5F7"))
        painter.setFont(QFont("Segoe UI", 24 if not self.show_numbers else 18, QFont.Weight.Bold))
        if not self.revealed:
            text = str(self.cell.value)
        elif self.show_numbers:
            text = f"{self.cell.letter}\n{self.cell.value}"
        else:
            text = self.cell.letter
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)


class HexImageBoardWidget(QWidget):
    """Muestra un tablero ilustrado y superpone sus números o letras."""

    def __init__(self, game: HexMemoryGame, revealed: bool, show_numbers: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.game = game
        self.revealed = revealed
        self.show_numbers = show_numbers
        self.setMinimumSize(560, 560)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        image_path = self.game.hidden_image_asset_path() if self.revealed else self.game.image_path
        pixmap = QPixmap(str(image_path)) if image_path else QPixmap()
        if not pixmap.isNull():
            scaled = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.fillRect(self.rect(), QColor("#171B22"))
            x, y, scaled = 0, 0, self.size()

        board_width = scaled.width()
        board_height = scaled.height()
        origin_x = x + board_width * 0.5
        origin_y = y + board_height * 0.5
        pitch_x = board_width * 0.162
        pitch_y = board_height * 0.148
        tile_width = board_width * 0.13
        tile_height = board_height * 0.15
        painter.setPen(QColor("#111318" if not self.revealed else "#F8FAFC"))
        for cell in self.game.cells:
            row_length = len(self.game.rows[cell.row])
            center_x = origin_x + (cell.column - (row_length - 1) / 2) * pitch_x
            center_y = origin_y + (cell.row - 2) * pitch_y
            rect_x = center_x - tile_width / 2
            rect_y = center_y - tile_height / 2
            painter.setFont(QFont("Segoe UI", max(16, int(tile_height * (0.26 if self.show_numbers else 0.34))), QFont.Weight.Bold))
            if not self.revealed:
                text = str(cell.value)
            elif self.show_numbers:
                text = f"{cell.letter}\n{cell.value}"
            else:
                text = cell.letter
            painter.drawText(int(rect_x), int(rect_y), int(tile_width), int(tile_height), Qt.AlignmentFlag.AlignCenter, text)


class HexMemorySetupView(QWidget):
    started = Signal(object)
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(70, 42, 70, 42)
        root.setSpacing(14)
        title = QLabel("Nueva memoria hexagonal")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        intro = QLabel("El tablero predeterminado genera automáticamente la forma 3–4–5–4–3. También puedes introducir los números manualmente.")
        intro.setObjectName("subtitle")
        intro.setWordWrap(True)
        root.addWidget(intro)
        self.image_mode = False
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Modalidad:"))
        self.text_mode_button = QPushButton("Tablero generado / manual")
        self.text_mode_button.clicked.connect(lambda: self._set_mode(False))
        self.image_mode_button = QPushButton("Tableros con imágenes")
        self.image_mode_button.setObjectName("secondaryButton")
        self.image_mode_button.clicked.connect(lambda: self._set_mode(True))
        mode_row.addWidget(self.text_mode_button)
        mode_row.addWidget(self.image_mode_button)
        mode_row.addStretch()
        root.addLayout(mode_row)

        self.text_edit = QPlainTextEdit("(1,2,3),(1,2,3,4),(1,2,3,4,5),(1,2,3,4),(1,2,3)")
        self.text_edit.setPlaceholderText("(1,2,3),(1,2,3,4),(1,2,3,4,5),(1,2,3,4),(1,2,3)")
        self.text_edit.setMaximumHeight(100)
        self.text_edit.setVisible(False)
        root.addWidget(self.text_edit)
        self.manual_button = QPushButton("Introducir patrón manual")
        self.manual_button.setObjectName("secondaryButton")
        self.manual_button.clicked.connect(self._toggle_manual)
        root.addWidget(self.manual_button)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Tiempo visible (segundos):"))
        self.duration = QSpinBox()
        self.duration.setRange(1, 3600)
        self.duration.setValue(90)
        controls.addWidget(self.duration)
        controls.addStretch()
        root.addLayout(controls)
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
        root.addStretch()

    def _start(self) -> None:
        try:
            if self.text_edit.isVisible():
                game = HexMemoryGame.from_text(self.text_edit.toPlainText(), self.duration.value())
                if tuple(len(row) for row in game.rows) != HexMemoryGame.DEFAULT_SHAPE:
                    raise HexBoardError("El patrón manual debe tener exactamente 3, 4, 5, 4 y 3 números por fila.")
            elif not self.image_mode:
                game = HexMemoryGame.generated(self.duration.value())
            else:
                game = HexMemoryGame.image_round(self.duration.value(), 1)
        except HexBoardError as exc:
            QMessageBox.warning(self, "Tablero no válido", str(exc))
            return
        self.started.emit(game)

    def _toggle_manual(self) -> None:
        manual = not self.text_edit.isVisible()
        self.text_edit.setVisible(manual)
        self.manual_button.setText("Usar generación automática" if manual else "Introducir patrón manual")

    def _set_mode(self, image_mode: bool) -> None:
        self.image_mode = image_mode
        self.text_mode_button.setObjectName("secondaryButton" if image_mode else "")
        self.image_mode_button.setObjectName("" if image_mode else "secondaryButton")
        self.text_mode_button.style().unpolish(self.text_mode_button)
        self.text_mode_button.style().polish(self.text_mode_button)
        self.image_mode_button.style().unpolish(self.image_mode_button)
        self.image_mode_button.style().polish(self.image_mode_button)
        self.text_edit.setVisible(False if image_mode else self.text_edit.isVisible())
        self.manual_button.setVisible(not image_mode)


class HexMemoryView(QWidget):
    back_to_menu_requested = Signal()

    def __init__(self, game: HexMemoryGame, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.game = game
        self.revealed = False
        self.show_numbers = False
        self.remaining = game.duration_seconds
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(14)
        top = QHBoxLayout()
        self.title_label = QLabel(f"Memoria hexagonal — ronda {game.round_number}")
        self.title_label.setObjectName("gameHeader")
        top.addWidget(self.title_label)
        top.addStretch()
        self.timer_label = QLabel()
        self.timer_label.setObjectName("roundLabel")
        top.addWidget(self.timer_label)
        root.addLayout(top)
        subtitle = QLabel("Memoriza la posición de los números. Después encuentra tres números alineados que sumen el objetivo.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(28)
        board_card = QFrame()
        board_card.setObjectName("gameCard")
        self.board_layout = QVBoxLayout(board_card)
        self.board_layout.setContentsMargins(28, 28, 28, 28)
        # Un hexágono mide 82 px de alto útil; -22 deja 60 px entre centros,
        # que es la separación necesaria para que las filas compartan lados.
        self.board_layout.setSpacing(-22)
        body.addWidget(board_card, 1)
        side = QFrame()
        side.setObjectName("sidePanel")
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(24, 24, 24, 24)
        side_layout.addWidget(QLabel("Objetivo"))
        self.target_label = QLabel("?")
        self.target_label.setObjectName("targetNumber")
        self.target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(self.target_label)
        self.hints_label = QLabel("Cuando termine el tiempo, busca tres letras alineadas.")
        self.hints_label.setWordWrap(True)
        self.hints_label.setObjectName("subtitle")
        side_layout.addWidget(self.hints_label)
        answer_title = QLabel("Tu combinación")
        answer_title.setObjectName("panelTitle")
        side_layout.addWidget(answer_title)
        answer_row = QHBoxLayout()
        self.answer_edit = QLineEdit()
        self.answer_edit.setPlaceholderText("A+B+C")
        self.answer_edit.setEnabled(False)
        self.answer_edit.returnPressed.connect(self._check_answer)
        answer_row.addWidget(self.answer_edit)
        self.check_button = QPushButton("Aceptar")
        self.check_button.setObjectName("secondaryButton")
        self.check_button.setEnabled(False)
        self.check_button.clicked.connect(self._check_answer)
        answer_row.addWidget(self.check_button)
        side_layout.addLayout(answer_row)
        self.answer_feedback = QLabel()
        self.answer_feedback.setWordWrap(True)
        side_layout.addWidget(self.answer_feedback)
        side_layout.addStretch()
        body.addWidget(side, 0)
        root.addLayout(body, 1)
        actions = QHBoxLayout()
        menu = QPushButton("Volver al menú")
        menu.setObjectName("secondaryButton")
        menu.clicked.connect(self._leave)
        self.finish_button = QPushButton("Finalizar turno")
        self.finish_button.clicked.connect(self._finish_or_next)
        self.master_button = QPushButton("Soluciones del máster")
        self.master_button.setObjectName("secondaryButton")
        self.master_button.clicked.connect(self._show_master_solutions)
        self.show_numbers_button = QPushButton("Mostrar números")
        self.show_numbers_button.setObjectName("secondaryButton")
        self.show_numbers_button.setEnabled(False)
        self.show_numbers_button.clicked.connect(self._show_numbers)
        actions.addWidget(menu)
        actions.addStretch()
        actions.addWidget(self.master_button)
        actions.addWidget(self.show_numbers_button)
        actions.addWidget(self.finish_button)
        root.addLayout(actions)

        self.clock = QTimer(self)
        self.clock.timeout.connect(self._tick)
        self.clock.start(1000)
        self._render()

    def _render(self) -> None:
        while self.board_layout.count():
            item = self.board_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if self.game.image_mode:
            self.board_layout.addWidget(HexImageBoardWidget(self.game, self.revealed, self.show_numbers))
        else:
            for row_index, row in enumerate(self.game.rows):
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                # El ancho útil del hexágono es 82 px dentro de un widget de 92.
                row_layout.setSpacing(-10)
                row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                for column_index, _value in enumerate(row):
                    cell = self.game._by_position[(row_index, column_index)]
                    row_layout.addWidget(HexCellWidget(cell, self.revealed, self.show_numbers))
                self.board_layout.addWidget(row_widget)
        self.timer_label.setText(f"{self.remaining:02d}s" if not self.revealed else "Tiempo agotado")
        if self.revealed:
            self.target_label.setText(str(self.game.target))
            if self.show_numbers:
                solutions = "\n".join(self.game.formatted_target_solutions())
                self.hints_label.setText(f"Soluciones ({len(self.game.target_lines)}):\n{solutions}")
            else:
                self.hints_label.setText("Encuentra tres letras alineadas que sumen el objetivo.")
        else:
            self.target_label.setText("?")

    def _tick(self) -> None:
        if self.revealed:
            return
        self.remaining -= 1
        if self.remaining <= 0:
            self._reveal()
        else:
            self.timer_label.setText(f"{self.remaining:02d}s")

    def _reveal(self) -> None:
        self.revealed = True
        self.clock.stop()
        self.finish_button.setText("Nueva ronda")
        self.show_numbers_button.setEnabled(True)
        self.answer_edit.setEnabled(True)
        self.check_button.setEnabled(True)
        self._render()

    def _show_numbers(self) -> None:
        if not self.revealed:
            return
        self.show_numbers = True
        self.show_numbers_button.setEnabled(False)
        self._render()

    def _show_master_solutions(self) -> None:
        HexSolutionsDialog(self.game, self).exec()

    def _check_answer(self) -> None:
        if not self.revealed:
            return
        letters = [letter.upper() for letter in re.findall(r"[A-Za-z]", self.answer_edit.text())]
        if len(letters) != 3 or len(set(letters)) != 3:
            self.answer_feedback.setText("Escribe exactamente tres letras distintas, por ejemplo: A+B+C.")
            self.answer_feedback.setStyleSheet("color: #F08A4B;")
            return
        answer = frozenset(letters)
        valid = any(answer == frozenset(cell.letter for cell in line.cells) for line in self.game.target_lines)
        if valid:
            self.answer_feedback.setText("✓ Correcto: esa combinación es una solución.")
            self.answer_feedback.setStyleSheet("color: #45B97C; font-weight: 700;")
        else:
            self.answer_feedback.setText("✗ No es una solución válida para este tablero.")
            self.answer_feedback.setStyleSheet("color: #D1495B; font-weight: 700;")

    def _finish_or_next(self) -> None:
        if not self.revealed:
            self._reveal()
            return
        if self.game.image_mode and self.game.round_number >= 10:
            self.finish_button.setText("10 rondas completadas")
            self.finish_button.setEnabled(False)
            return
        self.game = self.game.shuffled_round()
        self.revealed = False
        self.show_numbers = False
        self.remaining = self.game.duration_seconds
        self.title_label.setText(f"Memoria hexagonal — ronda {self.game.round_number}")
        self.finish_button.setText("Finalizar turno")
        self.show_numbers_button.setEnabled(False)
        self.answer_edit.clear()
        self.answer_edit.setEnabled(False)
        self.check_button.setEnabled(False)
        self.answer_feedback.clear()
        self.clock.start(1000)
        self._render()

    def _leave(self) -> None:
        self.clock.stop()
        self.back_to_menu_requested.emit()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._leave()
        event.accept()
