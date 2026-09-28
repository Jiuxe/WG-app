from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from weapo_games.ui.main_window import MainWindow

APP_STYLE = """
QWidget {
    background-color: #101318;
    color: #F3F5F7;
    font-family: "Segoe UI";
    font-size: 14px;
}
QLabel#mainTitle {
    font-size: 52px;
    font-weight: 900;
    letter-spacing: 4px;
    color: #F5C542;
}
QLabel#pageTitle {
    font-size: 34px;
    font-weight: 800;
    color: #F5C542;
}
QLabel#subtitle {
    color: #AEB6C2;
}
QLabel#gameName, QLabel#gameHeader, QLabel#panelTitle {
    font-size: 22px;
    font-weight: 800;
}
QLabel#monsterRoundCounter {
    font-size: 20px;
    font-weight: 800;
    color: #F5C542;
    padding-left: 8px;
}
QLabel#roundLabel {
    font-size: 28px;
    font-weight: 900;
    color: #F5C542;
}
QLabel#gameSymbol {
    font-size: 50px;
    color: #F5C542;
}
QPushButton {
    min-height: 42px;
    padding: 6px 16px;
    border: 1px solid #D8A91B;
    border-radius: 8px;
    background-color: #F5C542;
    color: #111318;
    font-weight: 800;
}
QPushButton:hover {
    background-color: #FFD75E;
}
QPushButton:pressed {
    background-color: #D8A91B;
}
QPushButton:disabled {
    color: #6F747C;
    background-color: #2B2F36;
    border-color: #3A3F48;
}
QPushButton#secondaryButton {
    color: #F3F5F7;
    background-color: #242932;
    border-color: #444B57;
}
QPushButton#secondaryButton:hover {
    background-color: #303642;
}
QPushButton#inventoryItem:checked {
    background-color: #2F9E5B;
    border-color: #7CFFAA;
    color: white;
}
QPushButton#targetMonster {
    min-width: 190px;
    min-height: 170px;
    background-color: #231B25;
    border: 3px solid #6B4054;
    border-radius: 14px;
    color: #F3F5F7;
    font-weight: 800;
}
QPushButton#targetMonster[monsterState="frozen"] {
    background-color: #214C78;
    border-color: #5DA9E9;
}
QPushButton#targetMonster[monsterState="poisoned"] {
    background-color: #7A2938;
    border-color: #ED7180;
}
QPushButton#targetMonster[monsterState="selected"] {
    background-color: #2F9E5B;
    border-color: #7CFFAA;
    color: white;
}
QPushButton#primaryDangerButton {
    background-color: #D1495B;
    border-color: #D1495B;
    color: white;
}
QPushButton#primaryDangerButton:hover {
    background-color: #E05B6D;
}
QFrame#gameCard, QFrame#sidePanel, QFrame#areaCard {
    background-color: #1A1F27;
    border: 1px solid #343B47;
    border-radius: 14px;
}
QFrame#monsterCard {
    background-color: #231B25;
    border: 1px solid #6B4054;
    border-radius: 14px;
    min-width: 150px;
}
QLabel#monsterIcon { font-size: 42px; }
QLabel#monsterName { font-size: 17px; font-weight: 800; color: #F6D7A7; }
QLabel#monsterHp { font-size: 20px; font-weight: 900; color: #E86C75; }
QLabel#monsterEffect { color: #B9C2D0; min-height: 18px; }
QLabel#targetNumber {
    font-size: 64px;
    font-weight: 900;
    color: #F5C542;
}
QFrame#candidateCard {
    background-color: #1A1F27;
    border: 1px solid #343B47;
    border-radius: 14px;
    min-width: 230px;
}
QLabel#candidateName {
    font-size: 20px;
    font-weight: 800;
}
QLabel#candidateScore {
    font-size: 42px;
    font-weight: 900;
    color: #F5C542;
}
QLabel#areaSymbol {
    font-size: 44px;
    color: #F5C542;
}
QLabel#areaName {
    font-size: 21px;
    font-weight: 800;
}
QLabel#areaScore {
    font-size: 34px;
    font-weight: 900;
}
QFrame#playerSlot {
    background: transparent;
    border: 2px dashed rgba(150, 158, 170, 150);
    border-radius: 9px;
}
QFrame#playerSlot[occupied="true"] {
    border-color: transparent;
}
QFrame#playerSlot[dragActive="true"] {
    border: 3px solid #F5C542;
    background-color: rgba(245, 197, 66, 35);
}
QListWidget#saveList, QScrollArea#playerPool {
    background-color: #171B22;
    border: 1px solid #343B47;
    border-radius: 10px;
}
QListWidget#saveList::item {
    padding: 14px;
    border-bottom: 1px solid #343B47;
}
QListWidget#saveList::item:selected {
    background-color: #3A3421;
    color: white;
}
QMessageBox, QInputDialog {
    background-color: #1A1F27;
}
"""


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Weapo Games")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()
    return app.exec()
