from __future__ import annotations

import random

import pytest

from weapo_games.games.calculated_areas.game import CalculatedAreasGame, GameRuleError
from weapo_games.games.calculated_areas.roles import Role
from weapo_games.services.save_manager import SaveManager


def placed_game(*roles: Role) -> CalculatedAreasGame:
    game = CalculatedAreasGame("Prueba")
    for role in roles:
        player = game.add_player()
        player.role = role
        game.move_player(player.id, "circle")
    return game


def test_adder_adds_one_point() -> None:
    game = placed_game(Role.ADDER)
    game.resolve_round()
    assert game.areas["circle"].score == 1


def test_subtractor_removes_one_point() -> None:
    game = placed_game(Role.SUBTRACTOR)
    game.resolve_round()
    assert game.areas["circle"].score == -2


def test_subtractors_use_power_of_two_for_the_area() -> None:
    game = placed_game(Role.SUBTRACTOR, Role.SUBTRACTOR, Role.SUBTRACTOR)
    result = game.resolve_round()
    assert game.areas["circle"].score == -8
    assert result.area_effects["circle"]["subtractor_points"] == 8


def test_adders_use_fibonacci_value_for_the_area() -> None:
    game = placed_game(Role.ADDER, Role.ADDER, Role.ADDER, Role.ADDER, Role.SUBTRACTOR)
    game.resolve_round()
    assert game.areas["circle"].score == 4


def test_adder_fibonacci_values() -> None:
    assert [CalculatedAreasGame._fibonacci_sum(count) for count in range(6)] == [0, 1, 2, 3, 5, 8]


def test_swapper_exchanges_origin_and_destination_scores() -> None:
    game = placed_game(Role.SWAPPER)
    game.areas["circle"].score = 5
    game.areas["triangle"].score = -2
    game.move_player(1, "triangle")

    result = game.resolve_round()

    assert game.areas["circle"].score == -2
    assert game.areas["triangle"].score == 5
    assert result.swaps[0]["player_id"] == 1


def test_swapper_that_does_not_move_has_no_effect() -> None:
    game = placed_game(Role.SWAPPER)
    game.areas["circle"].score = 7
    game.areas["square"].score = 2

    result = game.resolve_round()

    assert result.swaps == []
    assert game.areas["circle"].score == 7
    assert game.areas["square"].score == 2


def test_addition_and_subtraction_happen_before_swap() -> None:
    game = CalculatedAreasGame("Orden")

    adder = game.add_player()
    adder.role = Role.ADDER
    game.move_player(adder.id, "circle")

    swapper = game.add_player()
    swapper.role = Role.SWAPPER
    game.move_player(swapper.id, "circle")
    game.move_player(swapper.id, "square")

    game.areas["circle"].score = 2
    game.areas["square"].score = 9
    game.resolve_round()

    # Círculo sube a 3 y después se intercambia con Cuadrado (9).
    assert game.areas["circle"].score == 9
    assert game.areas["square"].score == 3


def test_multiple_swappers_resolve_by_player_id() -> None:
    game = CalculatedAreasGame("Intercambios")

    player_1 = game.add_player()
    player_1.role = Role.SWAPPER
    game.move_player(player_1.id, "circle")
    game.move_player(player_1.id, "square")

    player_2 = game.add_player()
    player_2.role = Role.SWAPPER
    game.move_player(player_2.id, "square")
    game.move_player(player_2.id, "triangle")

    game.areas["circle"].score = 1
    game.areas["square"].score = 2
    game.areas["triangle"].score = 3

    result = game.resolve_round()

    assert [swap["player_id"] for swap in result.swaps] == [1, 2]
    assert game.areas["circle"].score == 2
    assert game.areas["square"].score == 3
    assert game.areas["triangle"].score == 1


def test_save_and_load_preserves_state(tmp_path) -> None:
    manager = SaveManager(tmp_path)
    game = placed_game(Role.ADDER, Role.SUBTRACTOR, Role.SWAPPER)
    game.scores_visible = True
    game.roles_visible = True
    game.resolve_round()

    save_path = manager.save_game(game, "Partida completa")
    restored = manager.load_game(save_path)

    assert restored.to_dict() == game.to_dict()


def test_cannot_resolve_with_unplaced_players() -> None:
    game = CalculatedAreasGame()
    player = game.add_player()
    player.role = Role.ADDER

    with pytest.raises(GameRuleError, match="colocados"):
        game.resolve_round()


def test_roles_cannot_be_reassigned_after_round_zero() -> None:
    game = placed_game(Role.ADDER)
    game.resolve_round()

    with pytest.raises(GameRuleError, match="ronda 0"):
        game.assign_roles(random.Random(1))


def test_player_role_can_be_modified_manually() -> None:
    game = CalculatedAreasGame()
    game.add_player()

    game.set_player_role(1, Role.SWAPPER)

    assert game.players[0].role is Role.SWAPPER


def test_player_role_cannot_be_modified_after_round_zero() -> None:
    game = placed_game(Role.ADDER)
    game.resolve_round()

    with pytest.raises(GameRuleError, match="ronda 0"):
        game.set_player_role(1, Role.SWAPPER)


def test_role_distribution_is_balanced() -> None:
    game = CalculatedAreasGame()
    for _ in range(8):
        game.add_player()

    counts = game.assign_roles(random.Random(7))
    values = list(counts.values())

    assert max(values) - min(values) <= 1


def test_player_can_move_between_slots_in_same_area() -> None:
    game = CalculatedAreasGame()
    first = game.add_player()
    second = game.add_player()
    first.role = Role.ADDER
    second.role = Role.SUBTRACTOR
    game.move_player(first.id, "circle", 0)
    game.move_player(second.id, "circle", 1)

    game.move_player(first.id, "circle", 0)
    assert first.current_slot == 0

    with pytest.raises(GameRuleError, match="ocupado"):
        game.move_player(first.id, "circle", 1)

    game.move_player(second.id, "square", 0)
    game.move_player(first.id, "circle", 1)
    assert first.current_area == "circle"
    assert first.current_slot == 1
