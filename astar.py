from typing import (
    Tuple, Dict, Set,
    Optional, Generic,
    Type, TypeVar, Iterator
)
import math
from abc import ABC, abstractmethod

import numpy as np
from time import sleep, perf_counter

T = TypeVar("T")
InplaceT = Tuple[Type[T], Dict]


class Heap(Generic[T]):
    size: int
    items: np.ndarray
    current_count: int

    #                             Allows to inplace initialize default T object
    def __init__(self, size: int, fill: Optional[InplaceT] = None) -> None:
        self.size = size
        self.items = np.ndarray((size,), dtype=object)
        if fill is not None:
            for item in range(self.items.shape[0]):
                self.items[item]: T = fill[0](**fill[1])
        self.current_count = 0

    def heappush(self, item: T) -> None:
        if self.current_count >= self.size:
            raise IndexError("Heap is full")
        item.heap_index = self.current_count
        self.items[self.current_count] = item
        self._sort_up(item)
        self.current_count += 1

    def _sort_up(self, item: T) -> None:
        parent = (item.heap_index - 1) // 2
        while parent >= 0:
            parent_item = self.items[parent]
            if item < parent_item:
                self._swap(parent_item, item)
            else:
                break
            parent = (item.heap_index - 1) // 2

    def rem_fir(self) -> T:
        if self.current_count < 0:
            return None
        first_item = self.items[0]
        self.current_count -= 1
        self.items[0] = self.items[self.current_count]
        self.items[0].heap_index = 0
        self._sort_down(self.items[0])
        return first_item

    def _sort_down(self, item: T) -> None:
        while True:
            child_left = item.heap_index * 2 + 1
            child_right = item.heap_index * 2 + 2
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

    def _swap(self, item_a: T, item_b: T) -> None:
        self.items[item_a.heap_index] = item_b
        self.items[item_b.heap_index] = item_a
        item_a.heap_index, item_b.heap_index = item_b.heap_index, item_a.heap_index

    def __contains__(self, item: T) -> bool:
        return self.items[item.heap_index] == item

    def __len__(self) -> int:
        return self.current_count


class IHeapItem(ABC, Generic[T]):
    @abstractmethod
    def __eq__(self, other: T) -> bool:
        pass

    @abstractmethod
    def __lt__(self, other: T) -> bool:
        pass

    @property
    @abstractmethod
    def heap_index(self) -> int:
        pass

    @heap_index.setter
    @abstractmethod
    def heap_index(self, value: int) -> None:
        pass


class Grid(IHeapItem):
    x: int
    y: int
    wall: bool
    previous: Optional['Grid']
    been_traveled: bool

    f: float
    g: float
    h: float

    index: int

    def __init__(self, x: int, y: int, wall: bool, f_cost: float) -> None:
        self.x = x
        self.y = y
        self.wall = wall
        self.previous = None
        self.been_traveled = False

        self.f = f_cost
        self.g = 0
        self.h = 0

        self.index = 0

    def __eq__(self, other: 'Grid') -> bool:
        if other is None:
            return False
        return (self.x, self.y) == (other.x, other.y)

    def __lt__(self, other: 'Grid') -> bool:
        return self.f < other.f

    def __repr__(self) -> str:
        return f"Grid({self.x} {self.y})"

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    @property
    def heap_index(self) -> int:
        return self.index

    @heap_index.setter
    def heap_index(self, value: int) -> None:
        self.index = value


class AStar(np.ndarray):
    open_set: Heap

    start_pos: Optional[Grid]
    end_pos: Optional[Grid]
    current_pos: Optional[Grid]

    def __new__(cls, width: int, height: int) -> 'AStar':
        self =  super(AStar, cls).__new__(cls, (height, width), dtype=object)

        for j in range(self.shape[0]):
            for i in range(self.shape[1]):
                self[j, i] = Grid(i, j, False, 0)

        self.open_set = Heap(
            self.shape[0] * self.shape[1],
            (Grid, {"x": 0, "y": 0, "wall": True, "f_cost": math.inf})
        )
        self.start_pos = None
        self.end_pos = None
        self.current_pos = None

        return self
    
    def init_finding(self) -> None:
        self.open_set.heappush(self.start_pos)

    def update_current_pos(self) -> None:
        self.current_pos = self.open_set.rem_fir()
    
    def is_calculating(self) -> bool:
        return self.open_set.current_count > 0

    def contains(self, grid: Grid) -> bool:
        return grid in self.open_set

    def step(self) -> bool:
        if self.current_pos == self.end_pos:
            return True

        self.current_pos.been_traveled = True
        
        for neighbour in self.get_neighbors(self.current_pos):
            if neighbour.wall or neighbour.been_traveled:
                continue

            temp_g = self.current_pos.g + self.heuristic(neighbour, self.current_pos)

            contain = neighbour not in self.open_set

            if temp_g < neighbour.g or contain:
                neighbour.g = temp_g
                neighbour.h = self.heuristic(neighbour, self.end_pos)
                neighbour.f = neighbour.g + neighbour.h
                neighbour.previous = self.current_pos

                if contain:
                    self.open_set.heappush(neighbour)

        return False

    def calculate_path(self) -> bool:
        self.open_set.heappush(self.start_pos)
        while self.open_set:
            self.update_current_pos()
            path_found = self.step()
            if path_found:
                return True
        return False

    @staticmethod
    def heuristic(next_pos: Grid, pos: Grid) -> float:
        x = abs(next_pos.x - pos.x)
        y = abs(next_pos.y - pos.y)
        return x + y - 0.585786 * min(x, y)

    def recreate_path(self) -> Set[Grid]:
        project_path = set()
        pos = self.current_pos
        while pos is not None:
            project_path.add(pos)
            pos = pos.previous
        return project_path
    
    def in_bounds(self, y: int, x: int) -> bool:
        return 0 <= y < self.shape[0] and 0 <= x < self.shape[1]

    def get_neighbors(self, grid: Grid) -> Iterator[Grid]:
        for j in range(-1, 2):
            for i in range(-1, 2):
                if i == 0 == j:
                    continue
                if self.in_bounds(grid.y + j, grid.x + i):
                    yield self[grid.y + j, grid.x + i]

    InsertionState = Type[int]
    INSERTED = 0x00
    DELETED  = 0x01
    SKIPED   = 0x02

    def set_start(self, y: int, x: int) -> InsertionState:
        grid = self[y, x]
        if self.start_pos is None:  # Set
            self.start_pos = grid
            return self.INSERTED
        if self.start_pos == grid:  # Delete
            self.start_pos = None
            return self.DELETED
        return self.SKIPED

    def set_end(self, y: int, x: int) -> InsertionState:
        grid = self[y, x]
        if self.end_pos is None:  # Set
            self.end_pos = grid
            return self.INSERTED
        if self.end_pos == grid:  # Delete
            self.end_pos = None
            return self.DELETED
        return self.SKIPED
    
    def set_wall(self, y: int, x: int, state: bool) -> InsertionState:
        grid = self[y, x]
        if grid == self.start_pos:
            return self.SKIPED
        if grid == self.end_pos:
            return self.SKIPED
        
        grid.wall = state

        if state:
            return self.INSERTED
        else:
            return self.DELETED


def main() -> int:
    from os import system
    import random

    display = False
    delay = 0.5
    testit = True

    astar = AStar(10, 10)
    for i in astar:
        for j in i:
            j.wall = not random.randint(0, 4)
    astar.start_pos = astar[0, 0]
    astar.end_pos = astar[-1, -1]

    path = set()

    def write() -> None:
        for level in astar:
            for g in level:
                if g in path:
                    print('0', end=" ")
                elif g.wall:
                    print('\\', end=" ")
                elif g.been_traveled:
                    print('.', end=" ")
                else:
                    print(' ', end=" ")
            print()

    def run() -> str:
        nonlocal path
        astar.open_set.heappush(astar.start_pos)
        while astar.open_set:
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
