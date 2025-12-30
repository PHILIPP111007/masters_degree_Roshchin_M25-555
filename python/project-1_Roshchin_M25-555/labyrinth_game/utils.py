import math
import sys

from labyrinth_game.constants import (
    COMMANDS,
    EVENT_COIN,
    EVENT_SWORD,
    EVENT_TRAP,
    IF_RANDOM_EVENT,
    ROOMS,
)
from labyrinth_game.types import GAME_STATE, ROOM


def show_help():
    """Prints help message"""

    print("\nДоступные команды:")

    keys = COMMANDS.keys()
    max_len = len(max(keys, key=lambda x: len(x)))
    for key, value in COMMANDS.items():
        print(key, " " * (max_len - len(key)), value)


def describe_current_room(game_state: GAME_STATE):
    """Describes current room"""

    current_room: ROOM = ROOMS[game_state["current_room"]]

    if current_room["items"]:
        items = "Заметные предметы: "
        items += ", ".join(current_room["items"])
    else:
        items = ""

    exits = current_room["exits"]
    exits_str = "Выходы:\n"
    for direction, room in exits.items():
        exits_str += f"{direction} -> {room}\n"

    puzzle = current_room["puzzle"]
    puzzle_str = ""
    if puzzle is not None:
        puzzle_str += puzzle[0]

    print(f"== {game_state['current_room']} ==")
    print(f"== {current_room['description']} ==")
    if items:
        print(items)

    print(exits_str)

    if puzzle_str:
        print(puzzle_str)


def solve_puzzles(game_state: GAME_STATE) -> GAME_STATE | None:
    """Solve puzzle"""

    current_room: ROOM = ROOMS[game_state["current_room"]]

    if current_room["puzzle"] is None:
        print("Загадок здесь нет.")
        return

    puzzle = current_room["puzzle"][0]
    correct_answer = current_room["puzzle"][1]
    print(puzzle)

    user_answer = input("Ваш ответ: ")

    if user_answer == correct_answer[0] or user_answer == correct_answer[1]:
        print("Вы разгадали загадку!")
        current_room["puzzle"] = None

        game_state["rewards"] += 1

        if game_state["current_room"] == "treasure_room":
            game_state["game_over"] = True
            current_room["items"].remove("treasure chest")
            print("Вы прошли игру!")
        ROOMS[game_state["current_room"]] = current_room
    else:
        print("Неверно, попробуйте еще снова.")

    return game_state


def attempt_open_treasure(game_state: GAME_STATE) -> GAME_STATE:
    """Attempt open treasure"""

    current_room: ROOM = ROOMS[game_state["current_room"]]
    items = current_room["items"]
    user_items = game_state["player_inventory"]

    if "treasure chest" in items:
        if "treasure_key" in user_items or "rusty_key" in user_items:
            print("Вы применяете ключ, и замок щелкает. Сундук открыт!")

            current_room["items"].remove("treasure chest")
            if "treasure_key" in user_items:
                user_items.remove("treasure_key")
            elif "rusty_key" in user_items:
                user_items.remove("rusty_key")

            game_state["game_over"] = True
            game_state["player_inventory"] = user_items
            print("Вы прошли игру!")
            sys.exit(0)
        else:
            print("У вас нет ключей.")
            answer = input("Сундук заперт. ... Ввести код (да/нет)")
            if answer == "да":
                solve_puzzles(game_state=game_state)
            else:
                print("Вы отступаете от сундука.")
    else:
        print("Сундук уже открыт или отсутствует.")

    return game_state


def pseudo_random(seed: int, modulo: int) -> int:
    """Gets pseudo random number from seed and modulo"""

    value = (math.sin(seed) * 10_000) % 1
    result = int(value * modulo)
    return result


def trigger_trap(game_state: GAME_STATE):
    """Triggers trap"""

    if "torch" in game_state["player_inventory"]:
        print("Вы чуть не наткнулись на ловушкку.")
    else:
        print("Сработала ловушка!")
        n = pseudo_random(seed=1, modulo=10)
        game_state["life"] -= n
        print(f"Вы потеряли {n} сердец")

        if game_state["life"] <= 0:
            print("Вы проиграли.")
            game_state["game_over"] = True

            sys.exit(0)
        else:
            items_count = len(game_state["player_inventory"])

            if items_count != 0:
                n = pseudo_random(seed=1, modulo=items_count)
                item = game_state["player_inventory"][n]
                print(f"Вы потеряли {item}")
                game_state["player_inventory"].remove(item)


def random_event(game_state: GAME_STATE, room: ROOM):
    """Get random event"""

    if_random_event = pseudo_random(seed=1, modulo=11)

    if if_random_event == IF_RANDOM_EVENT:
        event_type = pseudo_random(seed=1, modulo=4)

        if event_type == EVENT_COIN:
            game_state["coins"] += 1
            print(f"Вы подняли монетку! Всего у вас {game_state['coins']} монет.")
        elif event_type == EVENT_SWORD:
            print("Игрок слышит шорох...")
            sword = "sword" in game_state["player_inventory"]
            if sword:
                print("Вы отпугнули существо.")
        elif event_type == EVENT_TRAP:
            if room["trap"]:
                trigger_trap(game_state=game_state)
