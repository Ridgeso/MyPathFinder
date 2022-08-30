from tkinter import Button, Label, Scale, Tk, Canvas
from tkinter.constants import HORIZONTAL
import argparse

parser = argparse.ArgumentParser(description="Type of the path finding algorithm.")
parser.add_argument("-c", help="Use cython version to compile", action="store_true")
args = parser.parse_args()

if args.c:
    from build.astarc import *
else:
    from astar import *

colors = {"path": "green", "been": "red", "wall": "black", "none": "white", "start": "blue", "end": "purple"}


def fill_grid():
    color = colors["wall"]
    canvas.create_rectangle(0, 0, win_size+shift, win_size+shift, fill=colors["none"])
    for i in range(N+1):
        x = i*size
        canvas.create_line(0, x+shift, win_size+shift, x+shift, fill=color)
        canvas.create_line(x+shift, 0, x+shift, win_size+shift, fill=color)


def draw_path(pos, if_path):
    canvas.create_rectangle(
        pos.x*size+shift, pos.y*size+shift,
        pos.x*size+shift+size, pos.y*size+shift+size,
        fill=colors["been"]
    )
    if if_path:
        path = create_path(pos)
        for p in path:
            x, y = p.x*size, p.y*size
            canvas.create_rectangle(
                shift+x, shift+y,
                shift+x+size, shift+y+size,
                fill=colors["path"]
            )


def pathfinder():
    if openset:
        pos = openset.rem_fir()

        if speed.get():
            draw_path(pos, False)

        state = a_star(plane, openset, been, pos, end)
        if state is not None:
            draw_path(pos, True)
            return

        root.after(speed.get(), pathfinder)
    else:
        finished.config(text="Path Not Found")


def start_finding():
    if start is not None and end is not None:
        start_btn.config(text="Stop")
        
        start_time = perf_counter()
        openset.heappush(start)
        pathfinder()
        end_time = perf_counter()

        finished.config(text=f"Finished in {round((end_time-start_time)*1000, 1)} ms")

        start_btn.config(text="Start")


def draw_walls(event):
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        temp = plane[x][y]
        if temp == start or temp == end:
            return
        temp.wall = True
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=colors["wall"]
        )


def del_walls(event):
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        temp = plane[x][y]
        if temp == start or temp == end:
            return
        temp.wall = False
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=colors["none"]
        )


def make_start(event):
    global start
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        if start is None:
            start = plane[x][y]
            color = colors["start"]
        else:
            if plane[x][y] == start:
                start = None
                color = colors["none"]
            else:
                return
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=color
        )


def make_end(event):
    global end
    x, y = (event.x-shift)//size, (event.y-shift)//size
    if 0 <= x < N and 0 <= y < N:
        if end is None:
            end = plane[x][y]
            color = colors["end"]
        else:
            if plane[x][y] == end:
                end = None
                color = colors["none"]
            else:
                return
        x, y = x*size, y*size
        canvas.create_rectangle(
            shift+x, shift+y,
            shift+x+size, shift+y+size,
            fill=color
        )


def try_reset():
    if start_btn["text"] == "Start":
        init()
        fill_grid()
        finished.config(text="Set Start and End point to start")


def init():
    global N, plane, win_size, shift, size
    global start, end, run
    global openset, been

    N = 50
    plane = [[Grid(i, j, False, 0) for j in range(N)] for i in range(N)]
    shift = 2
    win_size = 500
    size = win_size//N
    
    start = None
    end = None
    run = False

    openset = Heap(N * N)
    been = set()


class App:
    def __init__(self, win_width: int, win_height: int):
        self.win_width = win_width
        self.win_height = win_height
        self.shift = 2
        self.bord_seize = 50
        self.grid_width = self.win_width // self.bord_seize
        self.grid_height = self.win_height // self.bord_seize

        self.board = Board(self.bord_seize, self.bord_seize)
        self.astar = AStar(self.board)

        self.colors = {"path": "green",
                       "been": "red",
                       "wall": "black",
                       "none": "white",
                       "start": "blue",
                       "end": "purple"}

        # Set Window
        self.root = Tk()
        self.root.title("Path Finder")
        self.root.geometry(f"{self.win_width}x{self.win_height}")

        self.canvas = Canvas(self.root, width=self.win_width + self.shift,
                             height=self.win_height + self.shift, bg="white")

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

    def run(self):
        self.root.mainloop()

    def fill_app(self):
        color = colors["wall"]
        self.canvas.create_rectangle(0, 0, self.win_width+self.shift, self.win_height+self.shift, fill=colors["none"])
        for i in range(N+1):
            x = i*size
            self.canvas.create_line(0, x+shift, win_size+shift, x+shift, fill=color)
            self.canvas.create_line(x+shift, 0, x+shift, win_size+shift, fill=color)

    def reset(self):
        if self.run_btn["text"] == "Start":
            # Reinitialization
            self.board = Board(self.win_width, self.win_height)
            self.astar = AStar(self.board)

            self.fill_app()
            finished.config(text="Set the Start and End point to start")

    def draw_path(self, pos, if_path):
        self.canvas.create_rectangle(
            pos.x*size+shift, pos.y*size+shift,
            pos.x*size+shift+size, pos.y*size+shift+size,
            fill=colors["been"]
        )
        if if_path:
            path = self.astar.recreate_path()
            for p in path:
                x, y = p.x*size, p.y*size
                self.canvas.create_rectangle(
                    self.shift + x, self.shift + y,
                    self.shift + x + self.grid_width, self.shift + y + self.grid_height,
                    fill=colors["path"]
                )

    def set_grid(self, event, grid_type):
        y = (event.y - self.shift) // self.grid_height
        x = (event.x - self.shift) // self.grid_width
        if self.board.in_bounds(y, x):
            if grid_type == "start":
                if self.astar.start_pos is None:  # Set
                    self.astar.start_pos = self.board[y, x]
                    color = colors["start"]
                else:  # Delete
                    if self.board[y, x] == self.astar.start_pos:
                        self.astar.start_pos = None
                        color = colors["none"]
                    else:
                        return
            elif grid_type == "end":  # Set
                if self.astar.end_pos is None:
                    self.astar.end_pos = self.board[y, x]
                    color = colors["end"]
                else:  # Delete
                    if self.board[y, x] == self.astar.end_pos:
                        self.astar.end_pos = None
                        color = colors["none"]
                    else:
                        return
            elif grid_type == "wallT":  # Set Wall
                grid = self.board[y, x]
                if grid == start or grid == end:
                    return
                color = self.colors["wall"]
                grid.wall = True
            elif grid_type == "wallF":  # Delete Wall
                grid = self.board[y, x]
                if grid == start or grid == end:
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

    def set_start(self, event):
        self.set_grid(event, "start")

    def set_end(self, event):
        self.set_grid(event, "end")

    def set_wall(self, event):
        self.set_grid(event, "wallT")

    def del_wall(self, event):
        self.set_grid(event, "wallF")

    def _find_path(self):
        if self.astar.open_set:

            if self.speed.get():
                # TODO: draw path
                draw_path(self.astar.current_pos, False)

            state = self.astar.step()
            if state:
                # TODO: draw path
                draw_path(self.astar.current_pos, True)
                return

            self.root.after(int(self.speed.get()), self._find_path)
        else:
            self.finished.config(text="Path Not Found")

    def start_finding(self):
        if self.astar.start_pos is not None and self.astar.end_pos is not None:
            self.run_btn.config(text="Stop")

            start_time = perf_counter()
            self.astar.open_set.heappush(self.astar.start_pos)
            self._find_path()
            end_time = perf_counter()

            self.finished.config(text=f"Finished in {round((end_time - start_time) * 1000, 1)} ms")

            self.run_btn.config(text="Start")


if __name__ == "__main__":
    init()

    root = Tk()
    root.title("Path Finder")
    root.geometry(f"{win_size+50}x{win_size+150}")

    canvas = Canvas(root, width=win_size+shift, height=win_size+shift, bg="white")

    canvas.bind_all("<Motion>", lambda event: canvas.focus_set())
    canvas.bind("<B1-Motion>", draw_walls)
    canvas.bind("<B3-Motion>", del_walls)
    canvas.bind("<s><Button-1>", make_start)
    canvas.bind("<e><Button-1>", make_end)
    
    fill_grid()

    start_btn = Button(root, text="Start", command=start_finding)
    reset_btn = Button(root, text="Reset", command=try_reset)
    speed = Scale(root, from_=0, to=40, orient=HORIZONTAL)

    finished = Label(root, text="Set Start and End point to start")

    canvas.pack()
    start_btn.pack()
    reset_btn.pack()
    speed.pack()
    finished.pack()

    root.mainloop()
