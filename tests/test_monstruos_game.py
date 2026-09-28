import pytest

from weapo_games.games.monstruos import MonstruosGame


def test_update_player_changes_editable_fields() -> None:
    game = MonstruosGame(["Ana", "Luis"])
    player = game.players[0]

    game.update_player(player, "Alicia", 42, ["Daga", "Hielo"])

    assert player.name == "Alicia"
    assert player.score == 42
    assert player.inventory == ["Daga", "Hielo"]


def test_players_start_with_five_points() -> None:
    game = MonstruosGame(["Ana", "Luis"])

    assert [player.score for player in game.players] == [5, 5]


def test_update_player_rejects_duplicate_names() -> None:
    game = MonstruosGame(["Ana", "Luis"])

    with pytest.raises(ValueError, match="nombre distinto"):
        game.update_player(game.players[0], "Luis", 10, [])


def test_sort_players_by_score_is_descending_and_stable_on_ties() -> None:
    game = MonstruosGame(["Ana", "Luis", "Marta"])
    game.players[0].score = 20
    game.players[1].score = 50
    game.players[2].score = 50

    game.sort_players_by_score()

    assert [player.name for player in game.players] == ["Luis", "Marta", "Ana"]


def test_ice_is_released_on_the_throwers_turn_after_reordering() -> None:
    game = MonstruosGame(
        ["Ana", "Luis"],
        monsters=[{"id": 1, "nombre": "Monstruo", "hpMax": 20, "recompensas": []}],
    )
    game.players[0].inventory.append("Hielo")
    game.start_round()
    game.use_item("Hielo", [0])
    assert game.active[0].frozen_by == game.players[0].player_id
    game.finish_turn()
    game.use_item("Daga", [0])
    game.finish_turn()

    game.reorder_players(["Luis", "Ana"])
    game.start_round()
    game.begin_turn()
    assert game.active[0].frozen_by == game.players[1].player_id
    game.finish_turn()
    game.begin_turn()
    assert game.active[0].frozen_by is None


def test_bomb_explodes_on_the_throwers_turn_after_reordering() -> None:
    game = MonstruosGame(
        ["Ana", "Luis"],
        monsters=[{"id": 1, "nombre": "Monstruo", "hpMax": 20, "recompensas": []}],
    )
    game.players[0].inventory.append("Bomba")
    game.start_round()
    game.use_item("Bomba", [0])
    game.finish_turn()
    game.use_item("Daga", [0])
    game.finish_turn()

    game.reorder_players(["Luis", "Ana"])
    game.start_round()
    game.begin_turn()
    assert game.active[0].bomb_by == game.players[1].player_id
    game.finish_turn()
    game.begin_turn()
    assert game.active[0].bomb_by is None
    assert game.active[0].hp == 8
