from typing import Tuple, Dict
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
    win_width: int
    win_height: int
    shift: int
    board_size: int
    grid_width: int
    grid_height: int

    astar: Astar

    colors: Dict[str, str]

    root: Tk
    canvas: Canvas
    run_btn: Button
    reset_btn: Button
    speed: Scale
    finished: Label
    points_label: Label

    def __init__(self, win_width: int, win_height: int) -> None:
        self.win_width = win_width
        self.win_height = win_height
        self.shift = 2
        self.board_size = 50
        self.grid_width = self.win_width // self.board_size
        self.grid_height = self.win_height // self.board_size

        self.astar = Astar(self.board_size, self.board_size)

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

        self.finished = Label(self.root, text="Click run to start")
        self.points_label = Label(self.root, text="Use s + leftB to set Start point| Use e + leftB to set End point")

        # Pack properties
        self.canvas.pack()
        # self.run_btn.pack(side=tk.LEFT)
        self.run_btn.place(x=self.win_width//4, y=self.win_height+25)
        # self.reset_btn.pack(side=tk.TOP)
        self.reset_btn.place(x=3*self.win_width//4, y=self.win_height+25)
        self.speed.pack(pady=7)
        self.finished.pack(pady=7)
        self.points_label.pack(pady=7)

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
            del self.astar
            self.astar = Astar(self.board_size, self.board_size)

            self.fill_app()
            self.finished.config(text="Set the Start and End point to start")

    def draw_rect(self, y: int, x: int, color: str):
        self.canvas.create_rectangle(
            self.shift + x, self.shift + y,
            self.shift + x + self.grid_width, self.shift + y + self.grid_height,
            fill=color
        )

    def set_grid(self, y: int, x: int, grid_type: str) -> None:
        if self.astar.in_bounds(y, x):
            
            if grid_type == "start":
                state = self.astar.set_start(y, x)
                if state == self.astar.INSERTED:
                    color = self.colors["start"]
                elif state == self.astar.DELETED:
                    color = self.colors["none"]                
                else:
                    return

            elif grid_type == "end":  # Set
                state = self.astar.set_end(y, x)
                if state == self.astar.INSERTED:
                    color = self.colors["end"]
                elif state == self.astar.DELETED:
                    color = self.colors["none"]                
                else:
                    return

            elif grid_type == "wallT":  # Set Wall
                insertion_state = self.astar.set_wall(y, x, True)
                if insertion_state == self.astar.INSERTED:
                    color = self.colors["wall"]
                else:
                    return

            elif grid_type == "wallF":  # Delete Wall
                insertion_state = self.astar.set_wall(y, x, False)
                if insertion_state == self.astar.DELETED:
                    color = self.colors["none"]
                else:
                    return

            else:
                return

            y = y * self.grid_height
            x = x * self.grid_width
            self.draw_rect(y, x, color)

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
            found_path = self.astar.recreate_path()
            for p in found_path:
                y = p.y * self.grid_height
                x = p.x * self.grid_width
                self.draw_rect(y, x, self.colors["path"])
            return

        color = self.colors[mode]
        y = pos.y * self.grid_height
        x = pos.x * self.grid_width
        self.draw_rect(y, x, color)

    def _find_path(self) -> None:
        if self.astar.is_calculating():
            self.astar.update_current_pos()

            state = self.astar.step()

            if self.speed.get():
                self.draw_path(self.astar.current_pos, "been")
                for neighbour in self.astar.get_neighbors(self.astar.current_pos):
                    if neighbour.wall or not self.astar.contains(neighbour):
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

            self.astar.init_finding()
            self._find_path()

            end_time = time.perf_counter()

            self.finished.config(text=f"Finished in {round((end_time - start_time) * 1000, 1)} ms")
            self.run_btn.config(text="Start")


if __name__ == "__main__":
    app = App(500, 500)
    app.run_app()
