# from timeit import timeit

# py = timeit("astar.main()", "import astar", number=100)
# cy = timeit("astarc.main()", "import astarc", number=100)

# print(py / cy)


from build.astarc import *


def main() -> int:
    from os import system
    from time import perf_counter, sleep
    import random

    # TODO: GLITCHY AS F xD
    display = True
    delay = 0.5

    game_board = Board(4, 4)
    for i in game_board:
        for j in i:
            j.wall = not random.randint(0, 4)
    
    astar = AStar(game_board)
    
    astar.start_pos = game_board[0, 0]
    astar.end_pos = game_board[-1, -1]

    path = set()
    def write() -> None:
        for level in game_board:
            for g in level:
                if g in path:
                    print('0', end=" ")
                elif g.wall:
                    print('\\', end=" ")
                elif g in astar.been_traveled:
                    print('.', end=" ")
                else:
                    print(' ', end=" ")
            print()

    def run() -> str:
        nonlocal path
        astar.open_set.heappush(astar.start_pos)
        while astar.open_set.length:
            astar.current_pos = astar.open_set.rem_fir()

            if display:
                system('cls')
                write()
                sleep(delay)

            state = astar.step()
            if state:
                system('cls')
                path = astar.recreate_path(astar.current_pos)
                write()
                return "Path Found"
        return "Path Not Found"

    if display:
        start = perf_counter()
        print(run())
        print((perf_counter()-start)*1000)
    else:

        if_path = astar.calculate_path()
        if if_path:
            path = astar.recreate_path(astar.current_pos)
        write()

    return 0


if __name__ == '__main__':
    main()
