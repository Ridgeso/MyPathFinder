import tkinter as tk
from tkinter import Button, Label, Scale, Tk, Canvas
from tkinter.constants import HORIZONTAL
import time
import argparse

parser = argparse.ArgumentParser(description="Type of the path finding algorithm.")
parser.add_argument("-c", help="Use cython version to compile", action="store_true")
args = parser.parse_args()

if args.c:
    from build.astarc import *
else:
    from astar import *


class App:
    def __init__(self, win_width: int, win_height: int) -> None:
        self.win_width = win_width
        self.win_height = win_height
        self.shift = 2
        self.board_size = 50
        self.grid_width = self.win_width // self.board_size
        self.grid_height = self.win_height // self.board_size

        self.board = Board(self.board_size, self.board_size)
        self.astar = AStar(self.board)

        self.colors = {"path": "green",
                       "been": "red",
                       "neighbor": "yellow",
                       "wall": "black",
                       "none": "white",
                       "start": "blue",
                       "end": "purple"}

        # Set Window
        self.root = Tk()
        self.root.title("Path Finder")
        self.root.geometry(f"{self.win_width + 50}x{self.win_height + 150}")

        self.canvas = Canvas(self.root, width=self.win_width + 1,
                             height=self.win_height + 1, bg="white")

        self.canvas.bind_all("<Motion>", lambda event: self.canvas.focus_set())
        self.canvas.bind("<s><Button-1>", self.set_start)
        self.canvas.bind("<e><Button-1>", self.set_end)
        self.canvas.bind("<B1-Motion>", self.set_wall)
        self.canvas.bind("<B3-Motion>", self.del_wall)

        self.fill_app()

        self.run_btn = Button(self.root, text="Start", command=self.start_finding)
        self.reset_btn = Button(self.root, text="Reset", command=self.reset)
        self.speed = Scale(self.root, from_=0, to=40, orient=HORIZONTAL)

        self.finished = Label(self.root, text="Set Start and End point to start")

        # Pack properties
        self.canvas.pack()
        self.run_btn.pack()
        self.reset_btn.pack()
        self.speed.pack()
        self.finished.pack()

    def run_app(self) -> None:
        self.root.mainloop()

    def fill_app(self) -> None:
        color = self.colors["wall"]
        self.canvas.create_rectangle(
            0, 0,
            self.win_width+self.shift, self.win_height+self.shift,
            fill=self.colors["none"]
        )
        for y in range(0, self.board_size * self.grid_height, self.grid_height):
            self.canvas.create_line(0, y + self.shift,
                                    self.win_width + self.shift,  y + self.shift,
                                    fill=color)
        for x in range(0, self.board_size * self.grid_width, self.grid_width):
            self.canvas.create_line(x + self.shift, 0,
                                    x + self.shift, self.win_height + self.shift,
                                    fill=color)

    def reset(self) -> None:
        if self.run_btn["text"] == "Start":
            # Reinitialization
            self.board = Board(self.board_size, self.board_size)
            self.astar = AStar(self.board)

            self.fill_app()
            self.finished.config(text="Set the Start and End point to start")

    def set_grid(self, y: int, x: int, grid_type: str) -> None:
        if self.board.in_bounds(y, x):
            if grid_type == "start":
                if self.astar.start_pos is None:  # Set
                    self.astar.start_pos = self.board[y, x]
                    color = self.colors["start"]
                else:  # Delete
                    if self.board[y, x] == self.astar.start_pos:
                        self.astar.start_pos = None
                        color = self.colors["none"]
                    else:
                        return
            elif grid_type == "end":  # Set
                if self.astar.end_pos is None:
                    self.astar.end_pos = self.board[y, x]
                    color = self.colors["end"]
                else:  # Delete
                    if self.board[y, x] == self.astar.end_pos:
                        self.astar.end_pos = None
                        color = self.colors["none"]
                    else:
                        return
            elif grid_type == "wallT":  # Set Wall
                grid = self.board[y, x]
                if grid == self.astar.start_pos or grid == self.astar.end_pos:
                    return
                color = self.colors["wall"]
                grid.wall = True
            elif grid_type == "wallF":  # Delete Wall
                grid = self.board[y, x]
                if grid == self.astar.start_pos or grid == self.astar.end_pos:
                    return
                color = self.colors["none"]
                grid.wall = False
            else:
                return

            y = y * self.grid_height
            x = x * self.grid_width
            self.canvas.create_rectangle(
                self.shift + x, self.shift + y,
                self.shift + x + self.grid_width, self.shift + y + self.grid_height,
                fill=color
            )

    def get_coordinates(self, y: int, x: int) -> Tuple[int, int]:
        coord_y = (y - self.shift) // self.grid_height
        coord_x = (x - self.shift) // self.grid_width
        return coord_y, coord_x

    def set_start(self, event: tk.Event) -> None:
        y, x = self.get_coordinates(event.y, event.x)
        self.set_grid(y, x, "start")

    def set_end(self, event: tk.Event) -> None:
        y, x = self.get_coordinates(event.y, event.x)
        self.set_grid(y, x, "end")

    def set_wall(self, event: tk.Event) -> None:
        y, x = self.get_coordinates(event.y, event.x)
        self.set_grid(y, x, "wallT")

    def del_wall(self, event: tk.Event) -> None:
        y, x = self.get_coordinates(event.y, event.x)
        self.set_grid(y, x, "wallF")

    def draw_path(self, pos: Grid, mode: str) -> None:
        if mode == "path":
            found_path = self.astar.recreate_path(pos)
            for p in found_path:
                y = p.y * self.grid_height
                x = p.x * self.grid_width
                self.canvas.create_rectangle(
                    x + self.shift, y + self.shift,
                    x + self.grid_width + self.shift, y + self.grid_height + self.shift,
                    fill=self.colors["path"]
                )
            return

        color = self.colors[mode]
        self.canvas.create_rectangle(
            pos.x * self.grid_width + self.shift, pos.y * self.grid_height + self.shift,
            (pos.x + 1) * self.grid_width + self.shift, (pos.y + 1) * self.grid_height + self.shift,
            fill=color
        )

    def _find_path(self) -> None:
        if self.astar.open_set:
            self.astar.current_pos = self.astar.open_set.rem_fir()

            state = self.astar.step()

            if self.speed.get():
                self.draw_path(self.astar.current_pos, "been")
                for neighbour in self.board.get_neighbors(self.astar.current_pos):
                    if neighbour.wall or neighbour not in self.astar.open_set:
                        continue
                    self.draw_path(neighbour, "neighbor")

            if state:
                self.draw_path(self.astar.current_pos, "path")
                return

            self.root.after(int(self.speed.get()), self._find_path)
        else:
            self.finished.config(text="Path Not Found")

    def start_finding(self) -> None:
        if self.astar.start_pos is not None and self.astar.end_pos is not None:
            self.run_btn.config(text="Stop")

            start_time = time.perf_counter()

            self.astar.open_set.heappush(self.astar.start_pos)
            self._find_path()

            end_time = time.perf_counter()

            self.finished.config(text=f"Finished in {round((end_time - start_time) * 1000, 1)} ms")
            self.run_btn.config(text="Start")


if __name__ == "__main__":
    app = App(500, 500)
    app.run_app()
