import copy
import math
from abc import ABC, abstractmethod

import numpy as np
from collections import namedtuple
from time import sleep, perf_counter


Coordinates = namedtuple("Coordinates", "x y")


class Heap:
    def __init__(self, size: int, fill: object = None):
        self.size = size
        # self.items = [Grid(0, 0, True, inf)] * self.size
        self.items = np.ndarray((size,), dtype=object)
        if fill is not None:
            for i in range(self.items.shape[0]):
                self.items[i] = copy.deepcopy(fill)
        self.current_count = 0

    def heappush(self, item):
        item.index = self.current_count
        self.items[self.current_count] = item
        self._sort_up(item)
        self.current_count += 1

    def _sort_up(self, item):
        parent = (item.index - 1) // 2
        while parent >= 0:
            parent_item = self.items[parent]
            if item < parent_item:
                self._swap(parent_item, item)
            else:
                break
            parent = (item.index - 1) // 2

    def rem_fir(self):
        first_item = self.items[0]
        self.current_count -= 1
        self.items[0] = self.items[self.current_count]
        self.items[0].index = 0
        self._sort_down(self.items[0])
        return first_item

    def _sort_down(self, item):
        while True:
            child_left = item.index*2+1
            child_right = item.index*2+2
            if child_left < self.current_count:
                swap_index = child_left
                if child_right < self.current_count:
                    if self.items[child_left] > self.items[child_right]:
                        swap_index = child_right
                if self.items[swap_index] < item:
                    self._swap(item, self.items[swap_index])
                else:
                    return
            else:
                return

    def _swap(self, item_a, item_b):
        self.items[item_a.index] = item_b
        self.items[item_b.index] = item_a
        item_a.index, item_b.index = item_b.index, item_a.index

    def __contains__(self, item):
        return self.items[item.index] == item

    def __len__(self):
        return self.current_count


class IHeapItem(ABC):
    @abstractmethod
    def heap_item(self) -> int:
        pass

    def __eq__(self, other) -> bool:
        pass

    def __lt__(self, other) -> bool:
        pass


def create_path(result):
    show = set([result])
    result = result.previous
    while result is not None:
        show.add(result)
        result = result.previous
    return show


def heuristic(a, b):
    x = abs(a.x - b.x)
    y = abs(a.y - b.y)
    return x + y - 0.585786 * min(x, y)


class Grid(IHeapItem):
    def __init__(self, x, y, wall, f_cost):
        self.x = x
        self.y = y
        self.wall = wall
        self.previous = None

        self.f = f_cost
        self.g = 0
        self.h = 0

        self.index = 0

    def __eq__(self, other):
        if other is None:
            return False
        return (self.x, self.y) == other

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if other is None:
            return True
        return self.f < other.f

    def __gt__(self, other):
        if other is None:
            return False
        return self.f > other.f

    def __repr__(self):
        return f"Grid({self.x} {self.y})"

    def __hash__(self):
        return hash((self.x, self.y))

    def heap_item(self) -> int:
        return self.index


def neighbours(pos, s_x, s_y):
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 == j:
                continue
            if 0 <= pos.x+i < s_x and 0 <= pos.y+j < s_y:
                yield Coordinates(pos.x + i, pos.y + j)


def a_star(maze, opened, closed, pos, end):

    if pos == end:
        return pos

    closed.add(pos)

    for n in neighbours(pos, len(maze), len(maze[0])):
        if n in closed or maze[n.x][n.y].wall:
            continue

        n = maze[n.x][n.y]
        temp_g = pos.g + heuristic(n, pos)

        contain = n not in opened

        if temp_g < n.g or contain:
            n.g = temp_g
            n.h = heuristic(n, end)
            n.f = n.g + n.h
            n.previous = pos

            if contain:
                opened.heappush(n)

    return None


def main():
    from random import randint
    from os import system

    plane = [[Grid(i, j, not randint(0, 2), 0) for j in range(N)] for i in range(N)]
    end_pos = plane[N-1][N-1]
    openset = Heap(N)
    openset.heappush(plane[0][0])
    been = set()
    display = False
    delay = 0.0

    def write(path, maze, size):
        for i in range(size):
            for j in range(size):
                if (i, j) in path:
                    print('0', end=" ")
                elif maze[i][j].wall:
                    print('\\', end=" ")
                elif maze[i][j] in been:
                    print('.', end=" ")
                else:
                    print(' ', end=" ")
            print()

    def run():
        while openset:
            current_pos = openset.rem_fir()

            if display:
                system('cls')
                write(create_path(current_pos), plane, N)
                sleep(delay)

            state = a_star(plane, openset, been, current_pos, end_pos)
            if state is not None:
                system('cls')
                write(create_path(state), plane, N)
                return "Path Found"
        return "Path Not Found"

    start = perf_counter()
    print(run())
    print((perf_counter()-start)*1000)


class Board(np.ndarray):
    def __new__(cls, width: int, height: int):
        new_board = super(Board, cls).__new__(cls, (height, width), dtype=object)
        for j in range(new_board.shape[0]):
            for i in range(new_board.shape[1]):
                new_board[j, i] = Grid(i, j, False, 0)
        return new_board

    def in_bounds(self, y, x):
        return 0 <= y < self.shape[0] and 0 <= x < self.shape[1]

    def get_neighbors(self, grid):
        for j in range(-1, 2):
            for i in range(-1, 2):
                if i == 0 == j:
                    continue
                if 0 <= grid.y + j < self.shape[0] and 0 <= grid.x + i < self.shape[1]:
                    yield self[grid.y + j, grid.x + i]


class AStar:
    def __init__(self, board):
        self.board = board

        self.open_set = Heap(self.board.shape[0] * self.board.shape[1], Grid(0, 0, True, math.inf))

        self.been_traveled = set()
        self.start_pos = None
        self.end_pos = None
        self.current_pos = None

    def step(self):
        self.current_pos = self.open_set.rem_fir()
        if self.current_pos == self.end_pos:
            return True

        self.been_traveled.add(self.current_pos)

        for neighbour in self.board.get_neighbors(self.current_pos):
            if neighbour.wall or neighbour in self.been_traveled:
                continue

            temp_g = self.current_pos.g + self.heuristic(neighbour, self.current_pos)

            contain = neighbour not in self.open_set

            if temp_g < neighbour.g or contain:
                neighbour.g = temp_g
                neighbour.h = heuristic(neighbour, self.end_pos)
                neighbour.f = neighbour.g + neighbour.h
                neighbour.previous = self.current_pos

                if contain:
                    self.open_set.heappush(neighbour)

        return False

    def calculate_path(self):
        while self.open_set:
            path_found = self.step()
            if path_found:
                return True
        return False

    @staticmethod
    def heuristic(next_pos, pos):
        x = abs(next_pos.x - pos.x)
        y = abs(next_pos.y - pos.y)
        return x + y - 0.585786 * min(x, y)

    @staticmethod
    def recreate_path(pos):
        path = set()
        while pos is not None:
            path.add(pos)
            pos = pos.previous
        return path


N = 20
if __name__ == '__main__':
    # main()
    game_board = Board(2, 4)
    print(game_board)
    print()
    astar = AStar(game_board)
    print(astar.open_set.items)
