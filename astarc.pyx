from time import sleep, perf_counter
from random import randint

from libc.stdio cimport printf
from libc.stdlib cimport malloc, calloc, free
cimport numpy as np


cdef extern from "math.h":
    float INFINITY
    double fabs(double)


cdef struct Grid_t:
    int y, x
    bint wall
    bint been_traveled
    bint is_path
    double g, h, f
    int index
    Grid_t* previous


cdef struct Board_t:
    int height, width
    Grid_t** board
    Grid_t* neighbors[8]


cdef struct Heap_t:
    int size
    int length
    Grid_t** items


cdef struct Astar_t:
    Board_t board
    Heap_t open_set
    Grid_t* start_pos
    Grid_t* end_pos
    Grid_t* current_pos


##### GRID #####
cdef Grid_t initGrid(int y, int x):
    cdef Grid_t grid
    grid.y = y
    grid.x = x
    grid.wall = False
    grid.been_traveled = False
    grid.is_path = False
    grid.g = 0.0
    grid.h = 0.0
    grid.f = 0.0
    grid.index = 0
    grid.previous = NULL
    return grid


cdef void printGrid(Grid_t* g):
    printf("%10d %10d %10d %10.4lf %10d %p\n", g.x, g.y, g.wall, g.f, g.index, g.previous)


cdef inline bint eqGrid(Grid_t* a, Grid_t* b):
    return a.x == b.x and a.y == b.y


##### BOARD #####
cdef Board_t initBoard(int height, int width):
    cdef Board_t board
    board.height = height
    board.width = width
    board.board = <Grid_t**>malloc(height * sizeof(Grid_t*))

    cdef int j, i
    for j in range(height):
        board.board[j] = <Grid_t*>malloc(width * sizeof(Grid_t))
        for i in range(width):
            board.board[j][i] = initGrid(j, i)

    return board

cdef void freeBoard(Board_t* board):
    cdef int i
    for i in range(board.height):
        free(<void*>board.board[i])
    free(<void*>board.board)

cdef inline bint inBounds(Board_t* board, int y, int x):
    return 0 <= y < board.height and 0 <= x < board.width

cdef inline Grid_t* getGrid(Board_t* board, int y, int x):
    return &board.board[y][x]

cdef Grid_t** getNeighbors(Board_t* board, Grid_t* grid):
    cdef int neighborCount = 0
    cdef int i, j
    for j in range(-1, 2):
        for i in range(-1, 2):
            if i == 0 == j:
                continue
            if inBounds(board, grid.y + j, grid.x + i):
                board.neighbors[neighborCount] = getGrid(board, grid.y + j, grid.x + i)
                neighborCount += 1
    if neighborCount < 8:
        board.neighbors[neighborCount] = NULL
    return board.neighbors


##### Heap #####
cdef Heap_t initHeap(int size):
    cdef int i
    cdef Heap_t heap
    heap.size = size
    heap.length = 0
    heap.items = <Grid_t**>malloc(size * sizeof(Grid_t*))
    
    return heap


cdef void printHeap(Heap_t* heap):
    cdef int i
    printf("Size: %d | Length: %d\n", heap.size, heap.length)
    for i in range(heap.size):
        printf("%3d |", i)
        printGrid(heap.items[i])


cdef void freeHeap(Heap_t* heap):
    free(<void*>heap.items)


cdef void heapPush(Heap_t* heap, Grid_t* item):
    item.index = heap.length
    heap.items[heap.length] = item
    heapSortUp(heap, item)
    heap.length += 1


cdef void heapSortUp(Heap_t* heap, Grid_t* item):
    cdef int parent = (item.index - 1) // 2
    cdef Grid_t* parent_item
    while parent >= 0:
        parent_item = heap.items[parent]
        if item.f < parent_item.f:
            heapSwap(heap, parent_item, item)
        else:
            break
        parent = (item.index-1)//2


cdef Grid_t* heapRemove(Heap_t* heap):
    cdef Grid_t* first_item = heap.items[0]
    heap.length -= 1
    heap.items[0] = heap.items[heap.length]
    heap.items[0].index = 0
    heapSortDown(heap, heap.items[0])
    return first_item


cdef void heapSortDown(Heap_t* heap, Grid_t* item):
    cdef int child_left, child_right
    cdef int swap_index
    while True:
        child_left = item.index * 2 + 1
        child_right = item.index * 2 + 2
        if child_left < heap.length:
            swap_index = child_left
            if child_right < heap.length:
                if heap.items[child_left].f > heap.items[child_right].f:
                    swap_index = child_right
            if heap.items[swap_index].f < item.f:
                heapSwap(heap, item, heap.items[swap_index])
            else:
                return
        else:
            return


cdef void heapSwap(Heap_t* heap, Grid_t* item_a, Grid_t* item_b):
    heap.items[item_a.index] = item_b
    heap.items[item_b.index] = item_a
    item_a.index, item_b.index = item_b.index, item_a.index


cdef bint heapContains(Heap_t* heap, Grid_t* item):
    return eqGrid(heap.items[item.index], item)


##### Astar #####
cdef Astar_t initAstar(int height, int width):
    cdef Astar_t astar
    astar.board = initBoard(height, width)
    astar.open_set = initHeap(height * width)
    astar.start_pos = NULL
    astar.end_pos = NULL
    astar.current_pos = NULL
    return astar


cdef void freeAstar(Astar_t* astar):
    freeBoard(&astar.board)
    freeHeap(&astar.open_set)


cdef double getHeuristic(Grid_t* next_pos, Grid_t* pos):
    cdef double x, y
    x = fabs(next_pos.x - pos.x)
    y = fabs(next_pos.y - pos.y)
    return x + y - 0.585786 * min(x, y)


cdef bint stepAstar(Astar_t* astar):
    if eqGrid(astar.current_pos, astar.end_pos):
        return True
    
    astar.current_pos.been_traveled = True

    cdef double temp_g
    cdef bint contain
    cdef int i
    cdef Grid_t** neighbors = getNeighbors(&astar.board, astar.current_pos)
    for i in range(8):
        if neighbors[i] == NULL:
            break
        if neighbors[i].wall or neighbors[i].been_traveled:
            continue
        
        temp_g = astar.current_pos.g + getHeuristic(neighbors[i], astar.current_pos)
        contain = not heapContains(&astar.open_set, neighbors[i])

        if contain or temp_g < neighbors[i].g:
            neighbors[i].g = temp_g
            neighbors[i].h = getHeuristic(neighbors[i], astar.end_pos)
            neighbors[i].f = neighbors[i].g + neighbors[i].h
            neighbors[i].previous = astar.current_pos

            if contain:
                heapPush(&astar.open_set, neighbors[i])
    return False


cdef bint findPath(Astar_t* astar):
    cdef bint path_found

    heapPush(&astar.open_set, astar.start_pos)
    while astar.open_set.length:

        astar.current_pos = heapRemove(&astar.open_set)

        path_found = stepAstar(astar)
        
        if path_found:
            return True
    

    return False


cdef void recreatePath(Astar_t* astar):
    cdef Grid_t* last_pos = astar.current_pos
    while last_pos != NULL:
        last_pos.is_path = True
        last_pos = last_pos.previous


cdef void printAstar(Astar_t* astar):
    cdef int j, i
    cdef Grid_t* g
    for j in range(astar.board.height):
        for i in range(astar.board.width):
            g = getGrid(&astar.board, j, i)
            if g.is_path:
                printf('0 ')
            elif g.wall:
                printf('\\ ')
            elif g.been_traveled:
                printf('. ')
            else:
                printf('  ')
        printf("\n")


cdef class NewGrid:
    cdef public int x, y
    cdef public bint wall

    def __cinit__(self, int y, int x, bint wall):
        self.y = y
        self.x = x
        self.wall = wall

    def __hash__(self):
        return hash((self.x, self.y))
    
    def __str__(self):
        return f"Grid({self.y} {self.x})"
    # cpdef void print_grid(self):
    #     printGrid(&self.body)

    # def __eq__(self, NewGrid other):
    #     return eqGrid(&self.body, &other.body)


ctypedef int InsertionState


cdef class NewAstar:
    cdef int width, height
    cdef Astar_t astar

    def __cinit__(self, int width, int height):
        self.height = height
        self.width = width
        
        self.astar = initAstar(height, width)

    def __dealloc__(self):
        freeAstar(&self.astar)

    cpdef void print_board(self):
        printAstar(&self.astar)
    
    cpdef bint in_bounds(self, int y, int x):
        return inBounds(&self.astar.board, y, x)
    
    INSERTED = 0x00
    DELETED  = 0x01
    SKIPED   = 0x02

    cpdef InsertionState set_start(self, int y, int x):
        cdef Grid_t* grid = getGrid(&self.astar.board, y, x)
        
        if self.astar.start_pos == NULL:  # Set
            self.astar.start_pos = grid
            return self.INSERTED
        if eqGrid(self.astar.start_pos, grid):  # Delete
            self.astar.start_pos = NULL
            return self.DELETED
        return self.SKIPED

    cpdef InsertionState set_end(self, int y, int x):
        cdef Grid_t* grid = getGrid(&self.astar.board, y, x)
        
        if self.astar.end_pos == NULL:  # Set
            self.astar.end_pos = grid
            return self.INSERTED
        if eqGrid(self.astar.end_pos, grid):  # Delete
            self.astar.end_pos = NULL
            return self.DELETED
        return self.SKIPED
    
    cpdef InsertionState set_wall(self, int y, int x, bint state):
        cdef Grid_t* grid = getGrid(&self.astar.board, y, x)
        
        if self.astar.start_pos != NULL and eqGrid(grid, self.astar.start_pos):
            return self.SKIPED
        if self.astar.end_pos != NULL and eqGrid(grid, self.astar.end_pos):
            return self.SKIPED
        
        grid.wall = state

        if state:
            return self.INSERTED
        else:
            return self.DELETED
    
    @property
    def start_pos(self):
        return NewGrid(self.astar.start_pos.y, self.astar.start_pos.x, self.astar.start_pos.wall)

    @property
    def end_pos(self):
        return NewGrid(self.astar.end_pos.y, self.astar.end_pos.x, self.astar.end_pos.wall)

    @property
    def current_pos(self):
        return NewGrid(self.astar.current_pos.y, self.astar.current_pos.x, self.astar.current_pos.wall)

    cpdef set recreate_path(self):    
        cdef set path = set()
        cdef NewGrid add_path

        cdef Grid_t* p = self.astar.current_pos

        while p != NULL:
            add_path = NewGrid(p.y, p.x, p.wall)
            path.add(add_path)
            p = p.previous
        return path
    
    cpdef void init_finding(self):
        heapPush(&self.astar.open_set, self.astar.start_pos)

    cpdef void update_current_pos(self):
        self.astar.current_pos = heapRemove(&self.astar.open_set)
    
    cpdef bint is_calculating(self):
        return self.astar.open_set.length > 0
    
    cpdef bint contains(self, NewGrid grid):
        cdef Grid_t* g = getGrid(&self.astar.board, grid.y, grid.x)
        return heapContains(&self.astar.open_set, g)

    cpdef bint step(self):
        return stepAstar(&self.astar)

    cpdef bint calculate_path(self):
        return findPath(&self.astar)
    
    cpdef list get_neighbors(self, NewGrid pos):
        cdef list py_neighbors = []
        
        cdef Grid_t neighbor
        neighbor.y = pos.y
        neighbor.x = pos.x

        cdef Grid_t** neighbors = getNeighbors(&self.astar.board, &neighbor)
        
        cdef int i
        for i in range(8):
            if neighbors[i] == NULL:
                break
            py_neighbors.append(NewGrid(neighbors[i].y, neighbors[i].x, neighbors[i].wall))
        
        return py_neighbors


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

    cpdef bint eq(self, Grid other):
        return self.x == other.x and self.y == other.y

    def to_str(self):
        return f"({self.x} {self.y})"


class Board(np.ndarray):
    def __new__(cls, int width, int height):
        new_board = super(Board, cls).__new__(cls, (height, width), dtype=object)
        for j in range(new_board.shape[0]):
            for i in range(new_board.shape[1]):
                new_board[j, i] = Grid(i, j, False, 0)
        return new_board

    def in_bounds(self, int y, int x):
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
        cdef bint path_found

        self.open_set.heappush(self.start_pos)
        while self.open_set.length:
            self.current_pos = self.open_set.rem_fir()
            path_found = self.step()
            if path_found:
                return True
        return False

    cpdef set recreate_path(self):
        cdef set project_path

        project_path = set()
        pos = self.current_pos
        while pos is not None:
            project_path.add(pos)
            pos = pos.previous
        return project_path


def main():
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
    def write():
        for level in game_board:
            for g in level:
                if g in path:
                    printf('0')
                elif g.wall:
                    printf('\\')
                elif g.been_traveled:
                    printf('.')
                else:
                    printf(' ')
            printf("\n")

    def run():
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

def testheap():
    cdef NewAstar new_astar
    new_astar = NewAstar(4, 4)

    printf("%d\n", new_astar.set_start(0, 0))
    printf("%d\n", new_astar.set_end(3, 3))
    printf("%d\n", new_astar.set_wall(2, 2, True))

    new_astar.print_board()

    print(new_astar.start_pos)
    print(new_astar.end_pos)
    new_astar.astar.current_pos = new_astar.astar.start_pos
    print(new_astar.current_pos)
    printf("\n")

    new_astar.calculate_path()
    recreatePath(&new_astar.astar)
    new_astar.print_board()

    printf("\n")
    path = new_astar.recreate_path()
    for p in path:
        print(p)

    printf("\nPy Neighbors\n")
    py_neighbors = new_astar.get_neighbors(NewGrid(0, 0))
    for py_neighbor in py_neighbors:
        print(py_neighbor)
    # cdef bint path_found

    # printf("Initialization\n")
    # cdef Astar_t test = initAstar(10, 10)
    # test.start_pos = getGrid(&test.board, 0, 0)
    # test.end_pos = getGrid(&test.board, 9, 9)

    # cdef int j, i
    # for j in range(test.board.height):
    #     for i in range(test.board.width):
    #         test.board.board[j][i].wall = not randint(0, 3)

    # printf("Counting\n")
    # path_found = findPath(&test)
    # if path_found:
    #     printf("Backtracking\n")
    #     recreatePath(&test)
    # printf("Printing\n")
    # printAstar(&test)
    # printf("Freeing\n")
    # freeAstar(&test)
    # printf("Done\n")
    