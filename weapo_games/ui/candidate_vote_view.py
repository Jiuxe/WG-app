from __future__ import annotations

import io
import random

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QColorDialog, QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QComboBox, QWidget,
)

from weapo_games.games.candidate_vote.game import Candidate, CandidateVoteGame, Voter
from weapo_games.services.local_vote_server import LocalVoteServer


class CandidateSetupView(QWidget):
    started = Signal(object)
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.rows: list[tuple[QLineEdit, QComboBox, QPushButton]] = []
        root = QVBoxLayout(self); root.setContentsMargins(70, 40, 70, 40); root.setSpacing(16)
        title = QLabel("Nueva votación"); title.setObjectName("pageTitle"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)
        root.addWidget(QLabel("Declara los jugadores y selecciona si cada uno es votante o candidato."))
        self.list_layout = QVBoxLayout(); self.list_layout.setSpacing(8)
        root.addLayout(self.list_layout)
        buttons = QHBoxLayout()
        add = QPushButton("+ Añadir jugador"); add.clicked.connect(self._add_row)
        start = QPushButton("Comenzar partida"); start.clicked.connect(self._start)
        buttons.addWidget(add); buttons.addStretch(); buttons.addWidget(start)
        root.addLayout(buttons); root.addStretch()
        back = QPushButton("Volver"); back.setObjectName("secondaryButton"); back.clicked.connect(self.back_requested)
        root.addWidget(back)
        self._add_row(); self._add_row()

    def _add_row(self) -> None:
        name = QLineEdit(); name.setPlaceholderText("Nombre del votante")
        color = QPushButton(); color.setFixedWidth(90); color.setProperty("candidateColor", random.choice(("#D1495B", "#4F86C6", "#45B97C", "#A66DD4", "#F08A4B", "#E05B8D"))); self._paint(color)
        kind = QComboBox(); kind.addItems(["Votante", "Candidato"]); kind.currentTextChanged.connect(lambda value: self._update_kind(name, color, value))
        color.clicked.connect(lambda: self._choose_color(color))
        remove = QPushButton("Quitar"); remove.setObjectName("secondaryButton")
        row = QHBoxLayout(); row.addWidget(name, 1); row.addWidget(kind); row.addWidget(color); row.addWidget(remove)
        container = QWidget(); container.setLayout(row); self.list_layout.addWidget(container)
        self.rows.append((name, kind, color)); remove.clicked.connect(lambda: self._remove_row(container, name))
        self._update_kind(name, color, kind.currentText())

    @staticmethod
    def _update_kind(name: QLineEdit, color: QPushButton, value: str) -> None:
        name.setPlaceholderText("Nombre del " + value.lower())
        color.setVisible(value == "Candidato")
        color.setEnabled(value == "Candidato")

    def _remove_row(self, container: QWidget, name: QLineEdit) -> None:
        if len(self.rows) <= 1: return
        self.rows = [(n, k, c) for n, k, c in self.rows if n is not name]
        container.deleteLater()

    def _choose_color(self, button: QPushButton) -> None:
        chosen = QColorDialog.getColor(QColor(button.property("candidateColor")), self)
        if chosen.isValid(): button.setProperty("candidateColor", chosen.name()); self._paint(button)

    @staticmethod
    def _paint(button: QPushButton) -> None:
        color = button.property("candidateColor"); button.setText(color); button.setStyleSheet(f"background:{color}; color:white; font-weight:800;")

    def _start(self) -> None:
        candidates = [Candidate(i, name.text().strip(), color.property("candidateColor")) for i, (name, kind, color) in enumerate(self.rows, 1) if name.text().strip() and kind.currentText() == "Candidato"]
        voters = [Voter(i, name.text().strip()) for i, (name, kind, _color) in enumerate(self.rows, 1) if name.text().strip() and kind.currentText() == "Votante"]
        if not candidates: QMessageBox.warning(self, "Faltan candidatos", "Declara al menos un candidato."); return
        if not voters: QMessageBox.warning(self, "Faltan votantes", "Declara al menos un votante."); return
        self.started.emit(CandidateVoteGame(candidates, voters))


class QRDialog(QDialog):
    def __init__(self, url: str, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.setWindowTitle("QR para votar")
        layout = QVBoxLayout(self); label = QLabel(); label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            import qrcode
            image = qrcode.make(url); buffer = io.BytesIO(); image.save(buffer, format="PNG")
            pixmap = QPixmap(); pixmap.loadFromData(buffer.getvalue()); label.setPixmap(pixmap.scaled(360, 360, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except ImportError:
            label.setText("Instala la dependencia qrcode para mostrar el QR.")
        layout.addWidget(label); layout.addWidget(QLabel(url)); buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close); buttons.rejected.connect(self.reject); layout.addWidget(buttons)


class CandidateVoteView(QWidget):
    back_to_menu_requested = Signal()

    def __init__(self, game: CandidateVoteGame, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.game = game; self.server = LocalVoteServer(game); self.finished = False
        root = QVBoxLayout(self); root.setContentsMargins(24, 20, 24, 20); root.setSpacing(14)
        top = QHBoxLayout(); title = QLabel("Votación de candidatos"); title.setObjectName("gameHeader"); top.addWidget(title); top.addStretch()
        self.url_label = QLabel(f"Votación activa en {self.server.url}"); self.url_label.setObjectName("subtitle"); top.addWidget(self.url_label); root.addLayout(top)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget(); self.grid = QGridLayout(container); self.grid.setSpacing(14); scroll.setWidget(container); root.addWidget(scroll, 1)
        actions = QHBoxLayout(); qr = QPushButton("Mostrar QR"); qr.clicked.connect(self._show_qr); self.stop_button = QPushButton("Detener votación"); self.stop_button.setObjectName("primaryDangerButton"); self.stop_button.clicked.connect(self._finish_voting); self.finish_button = QPushButton("Finalizar partida"); self.finish_button.setEnabled(False); self.finish_button.clicked.connect(self._leave); menu = QPushButton("Volver al menú"); menu.setObjectName("secondaryButton"); menu.clicked.connect(self._leave)
        actions.addWidget(qr); actions.addStretch(); actions.addWidget(self.stop_button); actions.addWidget(self.finish_button); actions.addWidget(menu); root.addLayout(actions)
        self.timer = QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(500); self.refresh()

    def refresh(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0); widget = item.widget()
            if widget: widget.deleteLater()
        vote_names = self.game.vote_names_by_candidate()
        for index, candidate in enumerate(self.game.snapshot()):
            card = QFrame(); card.setObjectName("candidateCard"); layout = QVBoxLayout(card); layout.setContentsMargins(16, 16, 16, 16)
            name = QLabel(candidate.name); name.setObjectName("candidateName"); name.setAlignment(Qt.AlignmentFlag.AlignCenter); name.setStyleSheet(f"background:#101318; color:white; border:4px solid {candidate.color}; border-radius:8px; padding:12px;")
            score = QLabel(str(candidate.score)); score.setObjectName("candidateScore"); score.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bars = QVBoxLayout(); bars.setSpacing(3)
            names = vote_names.get(candidate.id, [])
            for vote_index in range(candidate.score):
                bar = QFrame(); bar.setFixedHeight(32); bar.setMinimumWidth(180); bar.setStyleSheet(f"background:{candidate.color}; border-radius:5px;")
                if self.finished:
                    bar_layout = QHBoxLayout(bar); bar_layout.setContentsMargins(8, 0, 8, 0)
                    label = QLabel(names[vote_index] if vote_index < len(names) else "Voto")
                    label.setStyleSheet("color:white; background:transparent; font-weight:700;")
                    bar_layout.addWidget(label)
                bars.addWidget(bar)
            layout.addWidget(name); layout.addWidget(score); layout.addLayout(bars); self.grid.addWidget(card, 0, index)

    def _show_qr(self) -> None: QRDialog(self.server.url, self).exec()

    def _finish_voting(self) -> None:
        if self.finished: return
        self.finished = True; self.timer.stop(); self.server.stop()
        self.stop_button.setEnabled(False); self.finish_button.setEnabled(True)
        self.url_label.setText("Puntuación detenida"); self.refresh()

    def _leave(self) -> None:
        if not self.finished:
            self.timer.stop(); self.server.stop()
        self.back_to_menu_requested.emit()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._leave(); event.accept()
