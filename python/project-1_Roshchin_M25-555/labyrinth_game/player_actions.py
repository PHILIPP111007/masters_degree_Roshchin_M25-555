from labyrinth_game.constants import ROOMS
from labyrinth_game.types import GAME_STATE, ROOM
from labyrinth_game.utils import (
    attempt_open_treasure,
    describe_current_room,
    random_event,
)


def get_input() -> str:
    """Gets user input"""

    user_command = input("> ")
    return user_command


def show_inventory(game_state: GAME_STATE) -> None:
    """Get inventory"""

    inventory: list = game_state["player_inventory"]

    if len(inventory) > 0:
        inventory_str = ", ".join(inventory)
        print(inventory_str)
    else:
        print("Инвентарь пуст.")


def move_player(game_state: GAME_STATE, direction: str) -> GAME_STATE:
    """Move"""

    current_room: ROOM = ROOMS[game_state["current_room"]]

    exits: dict[str, str] = current_room["exits"]

    new_room = exits.get(direction)

    if new_room is not None:
        game_state["current_room"] = new_room
        game_state["steps_taken"] += 1
        describe_current_room(game_state=game_state)

        new_room_dict: ROOM = ROOMS[new_room]
        random_event(game_state=game_state, room=new_room_dict)
    else:
        print("Нельзя пойти в этом направлении.")

    return game_state


def take_item(game_state: GAME_STATE, item_name: str) -> GAME_STATE:
    """Take item from room"""

    current_room: ROOM = ROOMS[game_state["current_room"]]

    items = current_room["items"]

    if item_name in items:
        current_room["items"].remove(item_name)
        print(f"Вы подняли: {item_name}")
        game_state["player_inventory"].append(item_name)
    else:
        print("Такого предмета здесь нет.")

    ROOMS["current_room"] = current_room
    return game_state


def use_item(game_state: GAME_STATE, item_name: str):
    """Use existing item"""

    user_items = game_state["player_inventory"]

    if item_name in user_items:
        match item_name:
            case "torch":
                print("Стало светлее.")
            case "sword":
                print("Уверенность.")
            case "bronze box":
                game_state["player_inventory"].remove("bronze box")
                game_state["player_inventory"].append("rusty_key")
            case "rusty_key":
                game_state["player_inventory"].remove("rusty_key")
                print("Уверенность.")
            case "treasure_chest":
                game_state["player_inventory"].remove("treasure_chest")
                attempt_open_treasure(game_state=game_state)
            case _:
                print("Игрок не знает, как этот предмет использовать.")
    else:
        print("У вас нет такого предмета.")

    return game_state
