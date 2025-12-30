import sys

from labyrinth_game.player_actions import (
    get_input,
    move_player,
    show_inventory,
    take_item,
    use_item,
)
from labyrinth_game.types import GAME_STATE
from labyrinth_game.utils import describe_current_room, show_help, solve_puzzles

game_state = {
    "player_inventory": [],  # Инвентарь игрока
    "current_room": "entrance",  # Текущая комната
    "game_over": False,  # Значения окончания игры
    "steps_taken": 0,  # Количество шагов
    "rewards": 0,  # награда за ответы на загадки
    "life": 10,
    "coins": 0,
}


def process_command(game_state: GAME_STATE, command: str):
    """Command processing"""

    command = command.split(" ")

    first_command_part = command[0]
    try:
        second_command_part = command[1]
    except Exception:
        second_command_part = ""

    match first_command_part:
        case "look":
            describe_current_room(game_state=game_state)
        case "use":
            item_name = " ".join(command[1:])
            use_item(game_state=game_state, item_name=item_name)
        case "go":
            move_player(game_state=game_state, direction=second_command_part)
        case "take":
            item_name = " ".join(command[1:])
            take_item(game_state=game_state, item_name=item_name)
        case "inventory":
            show_inventory(game_state=game_state)
        case "solve":
            solve_puzzles(game_state=game_state)
        case "quit" | "exit":
            print("Выход из игры.")
            sys.exit(0)
        case "help":
            show_help()
        case _:
            print("Такой команды нет.")


def main():
    """Main function"""

    print("Добро пожаловать в Лабиринт сокровищ!")
    show_help()

    while True:
        try:
            print()
            command = get_input()
            process_command(game_state=game_state, command=command)
        except KeyboardInterrupt:
            print("Выход из игры.")
            sys.exit(0)


if __name__ == "__main__":
    main()
