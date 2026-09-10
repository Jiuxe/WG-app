from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QStackedWidget

from weapo_games.games.calculated_areas.game import CalculatedAreasGame
from weapo_games.services.save_manager import SaveManager
from weapo_games.ui.calculated_areas_view import CalculatedAreasView
from weapo_games.ui.load_game_view import LoadGameView
from weapo_games.ui.main_menu import MainMenu
from weapo_games.ui.new_game_menu import NewGameMenu
from weapo_games.ui.scoreboard_view import ScoreboardView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Weapo Games")
        self.resize(1400, 820)
        self.setMinimumSize(1120, 680)

        self.save_manager = SaveManager()
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_menu = MainMenu()
        self.new_game_menu = NewGameMenu()
        self.load_game_view = LoadGameView(self.save_manager)
        self.game_view: CalculatedAreasView | None = None
        self.scoreboard_view: ScoreboardView | None = None

        self.stack.addWidget(self.main_menu)
        self.stack.addWidget(self.new_game_menu)
        self.stack.addWidget(self.load_game_view)

        self.main_menu.new_game_requested.connect(self.show_new_game_menu)
        self.main_menu.load_game_requested.connect(self.show_load_game_menu)
        self.main_menu.exit_requested.connect(QApplication.instance().quit)
        self.new_game_menu.back_requested.connect(self.show_main_menu)
        self.new_game_menu.calculated_areas_requested.connect(self.start_new_game)
        self.load_game_view.back_requested.connect(self.show_main_menu)
        self.load_game_view.load_requested.connect(self.load_game)

        self.show_main_menu()

    def show_main_menu(self) -> None:
        self.stack.setCurrentWidget(self.main_menu)

    def show_new_game_menu(self) -> None:
        self.stack.setCurrentWidget(self.new_game_menu)

    def show_load_game_menu(self) -> None:
        self.load_game_view.refresh()
        self.stack.setCurrentWidget(self.load_game_view)

    def _show_game(self, game: CalculatedAreasGame) -> None:
        if self.game_view is not None:
            self.stack.removeWidget(self.game_view)
            self.game_view.deleteLater()
        if self.scoreboard_view is not None:
            self.stack.removeWidget(self.scoreboard_view)
            self.scoreboard_view.deleteLater()
            self.scoreboard_view = None

        self.game_view = CalculatedAreasView(game, self.save_manager)
        self.game_view.back_to_menu_requested.connect(self.show_main_menu)
        self.game_view.scores_requested.connect(self.show_scoreboard)
        self.stack.addWidget(self.game_view)
        self.stack.setCurrentWidget(self.game_view)

        self.scoreboard_view = ScoreboardView(game)
        self.scoreboard_view.back_requested.connect(self.show_game)
        self.stack.addWidget(self.scoreboard_view)

    def show_game(self) -> None:
        if self.game_view is not None:
            self.game_view.refresh()
            self.stack.setCurrentWidget(self.game_view)

    def show_scoreboard(self) -> None:
        if self.scoreboard_view is not None:
            self.scoreboard_view.refresh()
            self.stack.setCurrentWidget(self.scoreboard_view)

    def start_new_game(self) -> None:
        self._show_game(CalculatedAreasGame())

    def load_game(self, path: Path) -> None:
        try:
            game = self.save_manager.load_game(path)
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo cargar", str(exc))
            return
        self._show_game(game)
