from __future__ import print_function
from collections import namedtuple
from time import sleep, perf_counter

cdef extern from "math.h":
    float INFINITY
    double fabs(double)


cdef struct Coordinates:
    int x, y


cdef class Heap:
    cdef list items
    cdef int current_count

    def __cinit__(self, int size):
        self.items = [Grid(0, 0, True, INFINITY)] * (size * size)
        self.current_count = 0

    cpdef heappush(self, Grid item):
        item.index = self.current_count
        self.items[self.current_count] = item
        self._sort_up(item)
        self.current_count += 1

    cpdef Grid rem_fir(self):
        cdef Grid first_item = self.items[0]
        self.current_count -= 1
        self.items[0] = self.items[self.current_count]
        self.items[0].index = 0
        self._sort_down(self.items[0])
        return first_item

    cdef _sort_down(self, Grid item):
        cdef int child_left, child_right
        cdef int swap_index
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

    cdef _sort_up(self, Grid item):
        cdef int parent = (item.index-1)//2
        cdef Grid parent_item
        while parent >= 0:
            parent_item = self.items[parent]
            if item < parent_item:
                self._swap(parent_item, item)
            else:
                break
            parent = (item.index-1)//2

    cdef _swap(self, Grid item_a, Grid item_b):
        self.items[item_a.index] = item_b
        self.items[item_b.index] = item_a
        item_a.index, item_b.index = item_b.index, item_a.index

    def __contains__(self, Grid item):
        return self.items[item.index] == item

    def __len__(self):
        return self.current_count


cpdef set create_path(Grid result):
    cdef set show = set([result])
    result = result.previous
    while result is not None:
        show.add(result)
        result = result.previous
    return show


cdef double heuristic(Grid a, Grid b):
    cdef double x, y
    x = a.x - b.x
    y = a.y - b.y
    x = fabs(x)
    y = fabs(y)
    return x + y - 0.585786 * min(x, y)


cdef class Grid:
    cdef public int x, y
    cdef public bint wall
    cdef public double f, g, h
    cpdef public Grid previous
    cdef public int index

    def __cinit__(self, int x, int y, bint wall, double f_cost):
        self.x = x
        self.y = y
        self.wall = wall
        self.previous = None

        self.f = f_cost
        self.g = 0
        self.h = 0

        self.index = 0

    def __ne__(self, other):
        return (self.x, self.y) != other

    def __eq__(self, other):
        return (self.x, self.y) == other

    def __lt__(self, other):
        return self.f < other.f

    def __gt__(self, other):
        return self.f > other.f

    def __str__(self):
        return f"({self.x} {self.y})"

    def __hash__(self):
        return hash((self.x, self.y))


def neighbours(Grid pos, int s_x, int s_y):
    cdef int i, j
    cdef Coordinates n
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 == j:
                continue
            if 0 <= pos.x+i < s_x and 0 <= pos.y+j < s_y:
                n.x = pos.x+i
                n.y = pos.y+j
                yield n


cpdef Grid a_star(list maze, Heap opened, set closed, Grid pos, Grid end):

    if pos == end:
        return pos

    closed.add(pos)

    cdef Coordinates n
    cdef Grid current_neighbour
    for n in neighbours(pos, len(maze), len(maze[0])):
        if (n.x, n.y) in closed or maze[n.x][n.y].wall:
            continue

        current_neighbour = maze[n.x][n.y]
        temp_g = pos.g + heuristic(current_neighbour, pos)

        contain = current_neighbour not in opened

        if temp_g < current_neighbour.g or contain:
            current_neighbour.g = temp_g
            current_neighbour.h = heuristic(current_neighbour, end)
            current_neighbour.f = current_neighbour.g + current_neighbour.h
            current_neighbour.previous = pos

            if contain:
                opened.heappush(current_neighbour)

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
    run()


N = 20
if __name__ == '__main__':
    main()