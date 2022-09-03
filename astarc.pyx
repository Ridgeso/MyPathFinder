from time import sleep, perf_counter
from random import randint

from libc.stdio cimport printf
from libc.stdlib cimport malloc, free
cimport numpy as np


cdef extern from "math.h":
    float INFINITY
    double fabs(double)


cdef class Heap:
    cdef public np.ndarray items
    cdef public int length, size

    def __cinit__(self, int size):
        self.items = np.ndarray((size,), dtype=object)
        for i in range(size):
            self.items[i] = Grid(0, 0, False, INFINITY)
        self.length = 0
        self.size = size
    
    cpdef heappush(self, Grid item):
        item.index = self.length
        self.items[self.length] = item
        self._sort_up(item)
        self.length += 1

    cdef _sort_up(self, Grid item):
        cdef int parent = (item.index - 1) // 2
        cdef Grid parent_item
        while parent >= 0:
            parent_item = self.items[parent]
            if item.f < parent_item.f:
                self._swap(parent_item, item)
            else:
                break
            parent = (item.index-1)//2

    cpdef Grid rem_fir(self):
        cdef Grid first_item = self.items[0]
        self.length -= 1
        self.items[0] = self.items[self.length]
        self.items[0].index = 0
        self._sort_down(self.items[0])
        return first_item

    cdef _sort_down(self, Grid item):
        cdef int child_left, child_right
        cdef int swap_index
        while True:
            child_left = item.index * 2 + 1
            child_right = item.index * 2 + 2
            if child_left < self.length:
                swap_index = child_left
                if child_right < self.length:
                    if self.items[child_left].f > self.items[child_right].f:
                        swap_index = child_right
                if self.items[swap_index].f < item.f:
                    self._swap(item, self.items[swap_index])
                else:
                    return
            else:
                return

    cdef _swap(self, Grid item_a, Grid item_b):
        self.items[item_a.index] = item_b
        self.items[item_b.index] = item_a
        item_a.index, item_b.index = item_b.index, item_a.index
        
    cpdef bint contains(self, Grid item):
        return self.items[item.index].eq(item)


cdef double heuristic(Grid next_pos, Grid pos):
    cdef double x, y
    x = fabs(next_pos.x - pos.x)
    y = fabs(next_pos.y - pos.y)
    return x + y - 0.585786 * min(x, y)


cdef class Grid:
    cdef public int x, y
    cdef public bint wall, been_traveled
    cdef public double g, h, f
    cdef public Grid previous
    cdef public int index

    def __cinit__(self, int x, int y, bint wall, double f):
        self.x = x
        self.y = y

        self.wall = wall
        self.been_traveled = False
        self.previous = None

        self.g = 0
        self.h = 0
        self.f = f

        self.index = 0

    cpdef eq(self, Grid other):
        return self.x == other.x and self.y == other.y

    def to_str(self):
        return f"({self.x} {self.y})"


class Board(np.ndarray):
    def __new__(cls, width, height):
        new_board = super(Board, cls).__new__(cls, (height, width), dtype=object)
        for j in range(new_board.shape[0]):
            for i in range(new_board.shape[1]):
                new_board[j, i] = Grid(i, j, False, 0)
        return new_board

    def in_bounds(self, y, x):
        return 0 <= y < self.shape[0] and 0 <= x < self.shape[1]


cpdef list get_neighbors(board, Grid grid):
    cdef list neighbors
    cdef int i, j
    neighbors = []
    for j in range(-1, 2):
        for i in range(-1, 2):
            if i == 0 and j == 0:
                continue
            if board.in_bounds(grid.y + j, grid.x + i):
                neighbors.append(board[grid.y + j, grid.x + i])
    return neighbors


cdef class AStar:
    cdef board
    cdef public Heap open_set
    cdef public Grid start_pos, end_pos, current_pos

    def __cinit__(self, board):
        self.board = board

        self.open_set = Heap(self.board.shape[0] * self.board.shape[1])

        self.start_pos = None
        self.end_pos = None
        self.current_pos = None

    cpdef bint step(self):
        if self.current_pos.eq(self.end_pos):
            return True

        self.current_pos.been_traveled = True

        cdef double temp_g
        cdef bint contain
        cdef Grid neighbor
        for neighbor in get_neighbors(self.board, self.current_pos):
            if neighbor.wall or neighbor.been_traveled:
                continue

            temp_g = self.current_pos.g + heuristic(neighbor, self.current_pos)

            contain = not self.open_set.contains(neighbor)

            if temp_g < neighbor.g or contain:
                neighbor.g = temp_g
                neighbor.h = heuristic(neighbor, self.end_pos)
                neighbor.f = neighbor.g + neighbor.h
                neighbor.previous = self.current_pos

                if contain:
                    self.open_set.heappush(neighbor)

        return False

    cpdef bint calculate_path(self):
        self.open_set.heappush(self.start_pos)
        while self.open_set.length:
            self.current_pos = self.open_set.rem_fir()
            path_found = self.step()
            if path_found:
                return True
        return False

    cpdef set recreate_path(self):
        project_path = set()
        pos = self.current_pos
        while pos is not None:
            project_path.add(pos)
            pos = pos.previous
        return project_path


def main() -> int:
    from os import system
    from time import perf_counter, sleep
    import random

    display = False
    delay = 0.5
    testit = True

    game_board = Board(6, 6)
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
                    printf('0 ')
                elif g.wall:
                    printf('\\ ')
                elif g.been_traveled:
                    printf('.')
                else:
                    printf(' ')
            printf("\n")

    def run() -> str:
        nonlocal path
        astar.open_set.heappush(astar.start_pos)
        while astar.open_set.length:
            astar.current_pos = astar.open_set.rem_fir()
            if display:
                system('cls')
                path = astar.recreate_path()
                write()
                sleep(delay)

            state = astar.step()
            if state:
                system('cls')
                path = astar.recreate_path()
                write()
                return "Path Found"
        return "Path Not Found"

    if display:
        print(run())
    else:
        start = perf_counter()
        if_path = astar.calculate_path()
        end = perf_counter() - start
        if if_path:
            path = astar.recreate_path()
        if not testit:
            print(end * 1000)
            write()

    return 0


if __name__ == '__main__':
    main()
