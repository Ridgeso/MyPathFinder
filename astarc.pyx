from __future__ import print_function
from collections import namedtuple
from time import sleep, perf_counter
from random import randint

from libc.stdlib cimport malloc, free
cimport numpy as np

cdef extern from "math.h":
    float INFINITY
    double fabs(double)


cdef struct Grid_t:
    int x, y
    double f
    int index


cdef bint eqGrid(Grid_t a, Grid_t b):
    return a.x == b.x and a.y == b.y


cdef class Heap:
    cdef Grid_t* items
    cdef public int length
    cdef np.ndarray board

    def __cinit__(self, int size, board):
        self.items = <Grid_t*>malloc(size * sizeof(Grid_t))
        for i in range(size):
            self.items[i].f = INFINITY
        self.board = board
        self.length = 0
    
    def __dealloc__(self):
        free(<void*>self.items)

    cpdef heappush(self, Grid item):
        item.body.index = self.length
        self.items[self.length] = item.body
        self._sort_up(item.body)
        self.length += 1

    cdef _sort_up(self, Grid_t item):
        cdef int parent = (item.index-1)//2
        cdef Grid_t parent_item
        while parent >= 0:
            parent_item = self.items[parent]
            if item.f < parent_item.f:
                self._swap(parent_item, item)
            else:
                break
            parent = (item.index-1)//2

    cpdef Grid rem_fir(self):
        cdef Grid_t first_item = self.items[0]
        self.length -= 1
        self.items[0] = self.items[self.length]
        self.items[0].index = 0
        self._sort_down(self.items[0])
        return self.board[first_item.y, first_item.x]

    cdef _sort_down(self, Grid_t item):
        cdef int child_left, child_right
        cdef int swap_index
        while True:
            child_left = item.index * 2 + 1
            child_right = item.index * 2 + 2
            if child_left < self.length:
                swap_index = child_left
                if child_right < self.length:
                    if self.items[child_left].f < self.items[child_right].f:
                        swap_index = child_right
                if self.items[swap_index].f < item.f:
                    self._swap(item, self.items[swap_index])
                else:
                    return
            else:
                return

    cdef _swap(self, Grid_t item_a, Grid_t item_b):
        self.items[item_a.index] = item_b
        self.items[item_b.index] = item_a
        
        self.items[item_a.index].index = item_a.index
        self.items[item_b.index].index = item_b.index
        
    cpdef bint contains(self, Grid_t item):
        return eqGrid(self.items[item.index], item)


cdef double heuristic(Grid_t next_pos, Grid_t pos):
    cdef double x, y
    x = fabs(next_pos.x - pos.x)
    y = fabs(next_pos.y - pos.y)
    return x + y - 0.585786 * min(x, y)


cdef class Grid:
    cdef public Grid_t body
    cdef public bint wall
    cdef public double g, h
    cdef public Grid previous

    def __cinit__(self, int x, int y, bint wall):
        self.body.x = x
        self.body.y = y

        self.wall = wall
        self.previous = None

        self.g = 0
        self.h = 0
        self.body.f = 0

        self.body.index = 0

    cpdef eq(self, Grid other):
        return eqGrid(self.body, other.body)

    def __str__(self):
        return f"({self.body.x} {self.body.y})"

    def __hash__(self):
        return hash((self.body.x, self.body.y))
    
    cpdef setF(self, double new_f):
        self.body.f = new_f


class Board(np.ndarray):
    def __new__(cls, width, height):
        new_board = super(Board, cls).__new__(cls, (height, width), dtype=object)
        for j in range(new_board.shape[0]):
            for i in range(new_board.shape[1]):
                new_board[j, i] = Grid(i, j, False)
        return new_board

    def in_bounds(self, y, x):
        return 0 <= y < self.shape[0] and 0 <= x < self.shape[1]


cpdef get_neighbors(board, Grid grid):
    cdef list neighbors
    neighbors = []
    for j in range(-1, 2):
        for i in range(-1, 2):
            if i == 0 == j:
                continue
            if board.in_bounds(grid.body.y + j, grid.body.x + i):
                neighbors.append(board[grid.body.y + j, grid.body.x + i])
    return neighbors


class AStar:
    def __init__(self, board):
        self.board = board

        self.open_set = Heap(self.board.shape[0] * self.board.shape[1], self.board)

        self.been_traveled = set()
        self.start_pos = None
        self.end_pos = None
        self.current_pos = None

    def step(self):
        if self.current_pos.eq(self.end_pos):
            return True

        self.been_traveled.add(self.current_pos)

        for neighbor in get_neighbors(self.board, self.current_pos):
            if neighbor.wall or neighbor in self.been_traveled:
                continue

            temp_g = self.current_pos.g + heuristic(neighbor.body, self.current_pos.body)

            contain = not self.open_set.contains(neighbor.body)

            if temp_g < neighbor.g or contain:
                neighbor.g = temp_g
                neighbor.h = heuristic(neighbor.body, self.end_pos.body)
                neighbor.setF(neighbor.g + neighbor.h)
                neighbor.previous = self.current_pos

                if contain:
                    self.open_set.heappush(neighbor)

        return False

    def calculate_path(self):
        self.open_set.heappush(self.start_pos)
        while self.open_set.length:
            self.current_pos = self.open_set.rem_fir()
            path_found = self.step()
            if path_found:
                return True
        return False

    @staticmethod
    def recreate_path(pos):
        project_path = set()
        while pos is not None:
            project_path.add(pos)
            pos = pos.previous
        return project_path